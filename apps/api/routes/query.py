"""Query endpoints for agent interactions."""

import asyncio
import json
import re
from collections.abc import AsyncGenerator
from typing import Literal

from fastapi import APIRouter, Request
from sse_starlette import EventSourceResponse

from apps.api.dependencies import AgentSvc, ApiKey, SessionSvc
from apps.api.schemas.requests import QueryRequest
from apps.api.schemas.responses import SingleQueryResponse
from apps.api.services.agent import QueryResponseDict

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("")
async def query_stream(
    request: Request,
    query: QueryRequest,
    _api_key: ApiKey,
    agent_service: AgentSvc,
    session_service: SessionSvc,
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
        api_key: Validated API key.
        agent_service: Agent service instance.
        session_service: Session service instance.

    Returns:
        SSE event stream.
    """
    # Note: Session is created by agent_service.query_stream which emits
    # the session_id in the init event. We extract it for tracking.
    # DO NOT set query.session_id here - that would cause the SDK to try
    # to resume a non-existent conversation!

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events with disconnect monitoring."""
        # Will be populated from init event
        session_id: str | None = query.session_id  # Only set if resuming
        is_error = False
        num_turns = 0
        try:
            async for event in agent_service.query_stream(query):
                # Extract session_id from init event for tracking
                if session_id is None and "event: init" in event:
                    # Parse the init event to get session_id
                    # Extract the JSON data from SSE format (event: init\ndata: {...})
                    data_match = re.search(r'data: ({.*})', event)
                    if data_match:
                        try:
                            init_data = json.loads(data_match.group(1))
                            session_id = init_data.get("session_id")
                            if session_id:
                                # Create session in our service
                                model = init_data.get("model", "sonnet")
                                await session_service.create_session(
                                    model=model, session_id=session_id
                                )
                        except json.JSONDecodeError:
                            pass

                # Check for client disconnect
                if await request.is_disconnected():
                    # Interrupt the session if client disconnected
                    if session_id:
                        await agent_service.interrupt(session_id)
                    break

                # Track turns and errors from events
                if "event: message" in event:
                    num_turns += 1
                if "event: error" in event:
                    is_error = True

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
    _api_key: ApiKey,
    agent_service: AgentSvc,
) -> QueryResponseDict:
    """Execute a non-streaming query to the agent.

    Returns complete response after agent finishes.

    Args:
        query: Query request body.
        api_key: Validated API key.
        agent_service: Agent service instance.

    Returns:
        Complete query response.
    """
    return await agent_service.query_single(query)
