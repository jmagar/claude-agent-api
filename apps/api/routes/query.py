"""Query endpoints for agent interactions."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sse_starlette import EventSourceResponse

from apps.api.dependencies import ApiKey
from apps.api.schemas.requests import QueryRequest
from apps.api.schemas.responses import SingleQueryResponse
from apps.api.services.agent import AgentService

router = APIRouter(prefix="/query", tags=["Query"])

# Service instance (could be injected via dependency)
_agent_service: AgentService | None = None


def get_agent_service() -> AgentService:
    """Get or create agent service instance."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


@router.post("")
async def query_stream(
    request: Request,
    query: QueryRequest,
    _api_key: ApiKey,
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
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

    Returns:
        SSE event stream.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events with disconnect monitoring."""
        try:
            async for event in agent_service.query_stream(query):
                # Check for client disconnect
                if await request.is_disconnected():
                    # Interrupt the session if client disconnected
                    if query.session_id:
                        await agent_service.interrupt(query.session_id)
                    break

                yield event

        except asyncio.CancelledError:
            # Client disconnected
            if query.session_id:
                await agent_service.interrupt(query.session_id)
            raise

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
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> dict[str, Any]:
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
