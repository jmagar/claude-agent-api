"""Query endpoints for agent interactions."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Literal
from uuid import uuid4

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
    # Create or use existing session
    if not query.session_id:
        model = query.model or "sonnet"
        session_id = str(uuid4())
        await session_service.create_session(model=model, session_id=session_id)
        # Update query with the new session_id
        query.session_id = session_id

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events with disconnect monitoring."""
        session_id = query.session_id
        is_error = False
        num_turns = 0
        try:
            async for event in agent_service.query_stream(query):
                # Check for client disconnect
                if await request.is_disconnected():
                    # Interrupt the session if client disconnected
                    if session_id:
                        await agent_service.interrupt(session_id)
                    break

                # Track turns and errors from events
                if '"event": "message"' in event:
                    num_turns += 1
                if '"event": "error"' in event:
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
