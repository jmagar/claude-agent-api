"""Session management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from apps.api.dependencies import ApiKey, get_cache
from apps.api.exceptions import SessionNotFoundError
from apps.api.schemas.requests import AnswerRequest, ForkRequest, ResumeRequest
from apps.api.schemas.responses import SessionListResponse, SessionResponse
from apps.api.services.agent import AgentService
from apps.api.services.session import SessionService

router = APIRouter(prefix="/sessions", tags=["Sessions"])


# Service instances
_agent_service: AgentService | None = None
_session_service: SessionService | None = None


def get_agent_service() -> AgentService:
    """Get or create agent service instance."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


async def get_session_service() -> SessionService:
    """Get or create session service instance."""
    global _session_service
    if _session_service is None:
        cache = await get_cache()
        _session_service = SessionService(cache=cache)
    return _session_service


@router.get("")
async def list_sessions(
    _api_key: ApiKey,
    session_service: Annotated[SessionService, Depends(get_session_service)],
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
) -> SessionListResponse:
    """List all sessions with pagination.

    Args:
        _api_key: Validated API key (via dependency).
        session_service: Session service instance.
        page: Page number (1-indexed).
        page_size: Number of sessions per page (max 100).

    Returns:
        Paginated list of sessions.
    """
    result = await session_service.list_sessions(page=page, page_size=page_size)

    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s.id,
                status=s.status,
                model=s.model,
                created_at=s.created_at,
                updated_at=s.updated_at,
                total_turns=s.total_turns,
                total_cost_usd=s.total_cost_usd,
                parent_session_id=s.parent_session_id,
            )
            for s in result.sessions
        ],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    _api_key: ApiKey,
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> SessionResponse:
    """Get session details by ID.

    Args:
        session_id: Session ID to retrieve.
        _api_key: Validated API key (via dependency).
        session_service: Session service instance.

    Returns:
        Session details.

    Raises:
        SessionNotFoundError: If session doesn't exist.
    """
    session = await session_service.get_session(session_id)
    if not session:
        raise SessionNotFoundError(session_id)

    return SessionResponse(
        id=session.id,
        status=session.status,
        model=session.model,
        created_at=session.created_at,
        updated_at=session.updated_at,
        total_turns=session.total_turns,
        total_cost_usd=session.total_cost_usd,
        parent_session_id=session.parent_session_id,
    )


@router.post("/{session_id}/answer")
async def answer_question(
    session_id: str,
    answer: AnswerRequest,
    _api_key: ApiKey,
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> dict[str, str]:
    """Answer an AskUserQuestion from the agent.

    This endpoint is used to respond to questions posed by the agent
    during a streaming session via the AskUserQuestion tool.

    Args:
        session_id: Session ID that posed the question.
        answer: The user's answer to the question.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.

    Returns:
        Status response indicating the answer was received.

    Raises:
        SessionNotFoundError: If the session is not active or doesn't exist.
    """
    success = await agent_service.submit_answer(session_id, answer.answer)

    if not success:
        raise SessionNotFoundError(session_id)

    return {"status": "accepted", "session_id": session_id}


@router.post("/{session_id}/resume")
async def resume_session(
    session_id: str,
    request: ResumeRequest,
    _api_key: ApiKey,
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> StreamingResponse:
    """Resume an existing session with a new prompt.

    Args:
        session_id: Session ID to resume.
        request: Resume request with prompt.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.
        session_service: Session service instance.

    Returns:
        SSE stream of agent events.

    Raises:
        SessionNotFoundError: If session doesn't exist.
    """
    # Verify session exists
    session = await session_service.get_session(session_id)
    if not session:
        raise SessionNotFoundError(session_id)

    # Build query request from resume request
    from apps.api.schemas.requests import QueryRequest

    query_request = QueryRequest(
        prompt=request.prompt,
        images=request.images,
        session_id=session_id,
        fork_session=False,
        allowed_tools=request.allowed_tools or [],
        disallowed_tools=request.disallowed_tools or [],
        permission_mode=request.permission_mode or "default",
        max_turns=request.max_turns,
        hooks=request.hooks,
    )

    return StreamingResponse(
        agent_service.query_stream(query_request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/fork")
async def fork_session(
    session_id: str,
    request: ForkRequest,
    _api_key: ApiKey,
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> StreamingResponse:
    """Fork an existing session into a new branch.

    Creates a new session that inherits the conversation history
    from the parent session up to the fork point.

    Args:
        session_id: Parent session ID to fork from.
        request: Fork request with prompt and optional overrides.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.
        session_service: Session service instance.

    Returns:
        SSE stream of agent events for the new session.

    Raises:
        SessionNotFoundError: If parent session doesn't exist.
    """
    # Verify parent session exists
    session = await session_service.get_session(session_id)
    if not session:
        raise SessionNotFoundError(session_id)

    # Build query request with fork flag
    from apps.api.schemas.requests import QueryRequest

    query_request = QueryRequest(
        prompt=request.prompt,
        images=request.images,
        session_id=session_id,
        fork_session=True,  # Key difference from resume
        allowed_tools=request.allowed_tools or [],
        disallowed_tools=request.disallowed_tools or [],
        permission_mode=request.permission_mode or "default",
        max_turns=request.max_turns,
        model=request.model or session.model,
        hooks=request.hooks,
    )

    return StreamingResponse(
        agent_service.query_stream(query_request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/interrupt")
async def interrupt_session(
    session_id: str,
    _api_key: ApiKey,
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> dict[str, str]:
    """Interrupt a running session.

    Signals the agent to stop processing and return control
    to the user. The session remains valid and can be resumed.

    Args:
        session_id: Session ID to interrupt.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.

    Returns:
        Status response indicating interrupt was sent.

    Raises:
        SessionNotFoundError: If session doesn't exist or isn't active.
    """
    success = await agent_service.interrupt(session_id)

    if not success:
        raise SessionNotFoundError(session_id)

    return {"status": "interrupted", "session_id": session_id}
