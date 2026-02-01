"""Session control endpoints (resume, fork, interrupt, control)."""

from fastapi import APIRouter
from sse_starlette import EventSourceResponse

from apps.api.dependencies import (
    AgentSvc,
    ApiKey,
    SessionSvc,
    ShutdownState,
)
from apps.api.exceptions import SessionNotFoundError
from apps.api.schemas.requests.control import ControlRequest
from apps.api.schemas.requests.query import QueryRequest
from apps.api.schemas.requests.sessions import ForkRequest, ResumeRequest
from apps.api.schemas.responses import ControlEventResponse, StatusResponse

router = APIRouter(prefix="/sessions", tags=["Session Control"])


@router.post("/{session_id}/resume")
async def resume_session(
    session_id: str,
    request: ResumeRequest,
    api_key: ApiKey,
    agent_service: AgentSvc,
    session_service: SessionSvc,
    _shutdown: ShutdownState,
) -> EventSourceResponse:
    """Resume an existing session with a new prompt.

    Args:
        session_id: Session ID to resume.
        request: Resume request with prompt.
        api_key: Validated API key (via dependency).
        agent_service: Agent service instance.
        session_service: Session service instance.
        _shutdown: Shutdown state check (via dependency, rejects if shutting down).

    Returns:
        SSE stream of agent events.

    Raises:
        SessionNotFoundError: If session doesn't exist.
    """
    # Verify session exists
    session = await session_service.get_session(
        session_id,
        current_api_key=api_key,
    )
    if not session:
        raise SessionNotFoundError(session_id)

    # Build query request from resume request
    query_request = QueryRequest(
        prompt=request.prompt,
        images=request.images,
        session_id=session_id,
        fork_session=False,
        continue_conversation=True,
        allowed_tools=request.allowed_tools or [],
        disallowed_tools=request.disallowed_tools or [],
        permission_mode=request.permission_mode or "bypassPermissions",
        max_turns=request.max_turns,
        hooks=request.hooks,
    )

    return EventSourceResponse(
        agent_service.query_stream(query_request, api_key),
        ping=15,
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/fork")
async def fork_session(
    session_id: str,
    request: ForkRequest,
    api_key: ApiKey,
    agent_service: AgentSvc,
    session_service: SessionSvc,
    _shutdown: ShutdownState,
) -> EventSourceResponse:
    """Fork an existing session into a new branch.

    Creates a new session that inherits the conversation history
    from the parent session up to the fork point.

    Args:
        session_id: Parent session ID to fork from.
        request: Fork request with prompt and optional overrides.
        api_key: Validated API key (via dependency).
        agent_service: Agent service instance.
        session_service: Session service instance.
        _shutdown: Shutdown state check (via dependency, rejects if shutting down).

    Returns:
        SSE stream of agent events for the new session.

    Raises:
        SessionNotFoundError: If parent session doesn't exist.
    """
    # Verify parent session exists
    parent_session = await session_service.get_session(
        session_id,
        current_api_key=api_key,
    )
    if not parent_session:
        raise SessionNotFoundError(session_id)

    # Create a NEW session for the fork, referencing the parent
    model = request.model or parent_session.model
    forked_session = await session_service.create_session(
        model=model,
        parent_session_id=session_id,
        owner_api_key=api_key,
    )

    # Build query request with fork flag and NEW session_id
    query_request = QueryRequest(
        prompt=request.prompt,
        images=request.images,
        session_id=forked_session.id,  # Use the NEW session ID
        fork_session=True,  # Key difference from resume
        allowed_tools=request.allowed_tools or [],
        disallowed_tools=request.disallowed_tools or [],
        permission_mode=request.permission_mode or "bypassPermissions",
        max_turns=request.max_turns,
        model=model,
        hooks=request.hooks,
    )

    return EventSourceResponse(
        agent_service.query_stream(query_request, api_key),
        ping=15,
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/interrupt")
async def interrupt_session(
    session_id: str,
    _api_key: ApiKey,
    agent_service: AgentSvc,
    session_service: SessionSvc,
) -> StatusResponse:
    """Interrupt a running session.

    Signals the agent to stop processing and return control
    to the user. The session remains valid and can be resumed.

    Args:
        session_id: Session ID to interrupt.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.
        session_service: Session service instance.

    Returns:
        Status response indicating interrupt was sent.

    Raises:
        SessionNotFoundError: If session doesn't exist or isn't active.
    """
    # Verify session exists and user owns it
    session = await session_service.get_session(session_id, current_api_key=_api_key)
    if not session:
        raise SessionNotFoundError(session_id)

    success = await agent_service.interrupt(session_id)

    if not success:
        raise SessionNotFoundError(session_id)

    return StatusResponse(status="interrupted", session_id=session_id)


@router.post("/{session_id}/control")
async def send_control_event(
    session_id: str,
    request: ControlRequest,
    _api_key: ApiKey,
    agent_service: AgentSvc,
    session_service: SessionSvc,
) -> ControlEventResponse:
    """Send a control event to an active session (FR-015).

    Control events allow dynamic changes during streaming, such as
    changing the permission mode mid-session.

    Args:
        session_id: Session ID to send control event to.
        request: Control request with event type and data.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.
        session_service: Session service instance.

    Returns:
        Status response indicating control event was processed.

    Raises:
        SessionNotFoundError: If session doesn't exist or isn't active.
    """
    # Verify session exists and user owns it
    session = await session_service.get_session(session_id, current_api_key=_api_key)
    if not session:
        raise SessionNotFoundError(session_id)

    if request.type == "permission_mode_change" and request.permission_mode is not None:
        success = await agent_service.update_permission_mode(
            session_id, request.permission_mode
        )

        if not success:
            raise SessionNotFoundError(session_id)

        return ControlEventResponse(
            status="accepted",
            session_id=session_id,
            permission_mode=request.permission_mode,
        )

    # Future control event types would go here
    return ControlEventResponse(status="unknown_type", session_id=session_id)
