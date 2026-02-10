"""Query endpoints for agent interactions."""

from typing import Literal

import structlog
from fastapi import APIRouter, HTTPException, Request
from sse_starlette import EventSourceResponse

from apps.api.dependencies import (
    AgentSvc,
    ApiKey,
    QueryEnrichment,
    SessionSvc,
    ShutdownState,
)
from apps.api.routes.query_stream import QueryStreamEventGenerator
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
        query: Query request with prompt and session options.
        api_key: Validated API key for authentication.
        agent_service: Agent service for executing queries.
        session_service: Session service for state management.
        enrichment_service: Service for enriching queries with context.
        _shutdown: Shutdown state for graceful degradation.

    Returns:
        SSE event stream.
    """
    # Enrich query with configured MCP servers from filesystem
    query = enrichment_service.enrich_query(query)

    # Create event generator for streaming response
    generator = QueryStreamEventGenerator(
        request=request,
        query=query,
        api_key=api_key,
        agent_service=agent_service,
        session_service=session_service,
    )

    return EventSourceResponse(
        generator.generate(),
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
            # Fail the request if session persistence fails - don't return
            # a session_id that doesn't exist in the database
            raise HTTPException(
                status_code=500,
                detail=f"Failed to persist session: {e!s}",
            ) from e

    return result
