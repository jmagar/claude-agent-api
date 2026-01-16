"""Query endpoints for agent interactions."""

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Literal

import structlog
from fastapi import APIRouter, Request
from sse_starlette import EventSourceResponse

from apps.api.dependencies import (
    AgentSvc,
    ApiKey,
    QueryEnrichment,
    SessionSvc,
    ShutdownState,
)
from apps.api.schemas.requests.query import QueryRequest
from apps.api.schemas.responses import SingleQueryResponse
from apps.api.services.agent import QueryResponseDict

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("")
async def query_stream(
    request: Request,
    query: QueryRequest,
    api_key: ApiKey,
    agent_service: AgentSvc,
    session_service: SessionSvc,
    enrichment_service: QueryEnrichment,
    _shutdown: ShutdownState,
) -> EventSourceResponse:
    """Execute a streaming query to the agent.

    Returns SSE stream with the following events:
    - init: Initial event with session info
    - message: Agent messages (user, assistant, system)
    - question: When agent asks for user input
    - partial: Partial content deltas (if enabled)
    - result: Final result with stats
    - error: Error events
    - done: Stream completion

    Args:
        request: FastAPI request object.
        query: Query request body.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.
        session_service: Session service instance.
        enrichment_service: Query enrichment service for auto-injecting MCP servers.
        _shutdown: Shutdown state check (via dependency, rejects if shutting down).

    Returns:
        SSE event stream.
    """
    # Enrich query with configured MCP servers from filesystem
    query = enrichment_service.enrich_query(query)

    # Note: Session is created by agent_service.query_stream which emits
    # the session_id in the init event. We extract it for tracking.
    # DO NOT set query.session_id here - that would cause the SDK to try
    # to resume a non-existent conversation!

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        """Generate SSE events with disconnect monitoring."""
        # Will be populated from init event
        session_id: str | None = query.session_id  # Only set if resuming
        is_error = False
        num_turns = 0
        total_cost_usd: float | None = None
        try:
            async for event in agent_service.query_stream(query, api_key):
                event_type = event.get("event", "")
                event_data = event.get("data", "{}")

                # Track turns and errors from events
                if event_type == "message":
                    num_turns += 1
                if event_type == "error":
                    is_error = True
                if event_type == "result":
                    try:
                        result_data = json.loads(event_data)
                        if "turns" in result_data:
                            num_turns = result_data["turns"]
                        if "total_cost_usd" in result_data:
                            total_cost_usd = result_data["total_cost_usd"]
                    except json.JSONDecodeError:
                        pass

                # Extract session_id from init event for tracking
                if session_id is None and event_type == "init":
                    try:
                        init_data = json.loads(event_data)
                        session_id = init_data.get("session_id")
                        if session_id:
                            # Create session in our service
                            model = init_data.get("model", "sonnet")
                            await session_service.create_session(
                                model=model,
                                session_id=session_id,
                                owner_api_key=api_key,
                            )
                    except json.JSONDecodeError as e:
                        logger.error(
                            "Failed to parse init event",
                            error=str(e),
                            event_data=event_data,
                        )
                        yield {
                            "event": "error",
                            "data": json.dumps(
                                {
                                    "error": "Session initialization failed",
                                    "details": "Invalid init event format",
                                }
                            ),
                        }
                        return
                    except Exception as e:
                        logger.error(
                            "Failed to create session",
                            error=str(e),
                            session_id=session_id,
                        )
                        yield {
                            "event": "error",
                            "data": json.dumps(
                                {"error": "Session creation failed", "details": str(e)}
                            ),
                        }
                        return

                # Check for client disconnect
                if await request.is_disconnected():
                    # Interrupt the session if client disconnected
                    if session_id:
                        await agent_service.interrupt(session_id)
                    break

                yield event

        except asyncio.CancelledError:
            # Client disconnected
            if session_id:
                await agent_service.interrupt(session_id)
            raise
        finally:
            # Update session status when stream completes
            if session_id:
                status: Literal["completed", "error"] = (
                    "error" if is_error else "completed"
                )
                await session_service.update_session(
                    session_id=session_id,
                    status=status,
                    total_turns=num_turns,
                    total_cost_usd=total_cost_usd,
                    current_api_key=api_key,
                )

    return EventSourceResponse(
        event_generator(),
        ping=15,  # Keepalive every 15 seconds
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post("/single", response_model=SingleQueryResponse)
async def query_single(
    query: QueryRequest,
    api_key: ApiKey,
    agent_service: AgentSvc,
    session_service: SessionSvc,
    enrichment_service: QueryEnrichment,
    _shutdown: ShutdownState,
) -> QueryResponseDict:
    """Execute a non-streaming query to the agent.

    Returns complete response after agent finishes.

    Args:
        query: Query request body.
        api_key: Validated API key (via dependency).
        agent_service: Agent service instance.
        session_service: Session service instance.
        enrichment_service: Query enrichment service for auto-injecting MCP servers.
        _shutdown: Shutdown state check (via dependency, rejects if shutting down).

    Returns:
        Complete query response.
    """
    # Enrich query with configured MCP servers from filesystem
    query = enrichment_service.enrich_query(query)

    # Execute the query
    result = await agent_service.query_single(query, api_key)

    # Persist the session if this is a new session (not resuming)
    if query.session_id is None:
        try:
            session_id = result["session_id"]
            model = result["model"]
            await session_service.create_session(
                model=model,
                session_id=session_id,
                owner_api_key=api_key,
            )

            # Update session status based on result
            status: Literal["completed", "error"] = (
                "error" if result["is_error"] else "completed"
            )
            await session_service.update_session(
                session_id=session_id,
                status=status,
                total_turns=result["num_turns"],
                total_cost_usd=result.get("total_cost_usd"),
                current_api_key=api_key,
            )
        except Exception as e:
            logger.error(
                "Failed to persist session for single query",
                error=str(e),
                session_id=result.get("session_id"),
            )
            # Don't fail the request if session persistence fails
            # Return the result anyway

    return result
