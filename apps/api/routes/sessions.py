"""Session management endpoints."""

from fastapi import APIRouter, Query
from sse_starlette import EventSourceResponse

from apps.api.dependencies import (
    AgentSvc,
    ApiKey,
    CheckpointSvc,
    SessionSvc,
    ShutdownState,
)
from apps.api.exceptions import InvalidCheckpointError, SessionNotFoundError
from apps.api.schemas.requests import (
    AnswerRequest,
    ControlRequest,
    ForkRequest,
    QueryRequest,
    ResumeRequest,
    RewindRequest,
)
from apps.api.schemas.responses import (
    CheckpointListResponse,
    CheckpointResponse,
    SessionListResponse,
    SessionResponse,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("")
async def list_sessions(
    _api_key: ApiKey,
    session_service: SessionSvc,
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
    session_service: SessionSvc,
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
    agent_service: AgentSvc,
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
    agent_service: AgentSvc,
    session_service: SessionSvc,
    _shutdown: ShutdownState,
) -> EventSourceResponse:
    """Resume an existing session with a new prompt.

    Args:
        session_id: Session ID to resume.
        request: Resume request with prompt.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.
        session_service: Session service instance.
        _shutdown: Shutdown state check (via dependency, rejects if shutting down).

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

    return EventSourceResponse(
        agent_service.query_stream(query_request),
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
    _api_key: ApiKey,
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
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.
        session_service: Session service instance.
        _shutdown: Shutdown state check (via dependency, rejects if shutting down).

    Returns:
        SSE stream of agent events for the new session.

    Raises:
        SessionNotFoundError: If parent session doesn't exist.
    """
    # Verify parent session exists
    parent_session = await session_service.get_session(session_id)
    if not parent_session:
        raise SessionNotFoundError(session_id)

    # Create a NEW session for the fork, referencing the parent
    model = request.model or parent_session.model
    forked_session = await session_service.create_session(
        model=model,
        parent_session_id=session_id,
    )

    # Build query request with fork flag and NEW session_id
    query_request = QueryRequest(
        prompt=request.prompt,
        images=request.images,
        session_id=forked_session.id,  # Use the NEW session ID
        fork_session=True,  # Key difference from resume
        allowed_tools=request.allowed_tools or [],
        disallowed_tools=request.disallowed_tools or [],
        permission_mode=request.permission_mode or "default",
        max_turns=request.max_turns,
        model=model,
        hooks=request.hooks,
    )

    return EventSourceResponse(
        agent_service.query_stream(query_request),
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


@router.post("/{session_id}/control")
async def send_control_event(
    session_id: str,
    request: ControlRequest,
    _api_key: ApiKey,
    agent_service: AgentSvc,
) -> dict[str, str]:
    """Send a control event to an active session (FR-015).

    Control events allow dynamic changes during streaming, such as
    changing the permission mode mid-session.

    Args:
        session_id: Session ID to send control event to.
        request: Control request with event type and data.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.

    Returns:
        Status response indicating control event was processed.

    Raises:
        SessionNotFoundError: If session doesn't exist or isn't active.
    """
    if request.type == "permission_mode_change":
        # permission_mode is guaranteed to be not None by the validator
        assert request.permission_mode is not None
        success = await agent_service.update_permission_mode(
            session_id, request.permission_mode
        )

        if not success:
            raise SessionNotFoundError(session_id)

        return {
            "status": "accepted",
            "session_id": session_id,
            "permission_mode": request.permission_mode,
        }

    # Future control event types would go here
    return {"status": "unknown_type", "session_id": session_id}


@router.get("/{session_id}/checkpoints")
async def list_session_checkpoints(
    session_id: str,
    _api_key: ApiKey,
    session_service: SessionSvc,
    checkpoint_service: CheckpointSvc,
) -> CheckpointListResponse:
    """List all checkpoints for a session (T102).

    Returns all file checkpoints created during the session, which can be
    used to rewind the session to a previous state.

    Args:
        session_id: Session ID to get checkpoints for.
        _api_key: Validated API key (via dependency).
        session_service: Session service instance.
        checkpoint_service: Checkpoint service instance.

    Returns:
        List of checkpoints for the session.

    Raises:
        SessionNotFoundError: If session doesn't exist.
    """
    # Verify session exists
    session = await session_service.get_session(session_id)
    if not session:
        raise SessionNotFoundError(session_id)

    # Get checkpoints for the session
    checkpoints = await checkpoint_service.list_checkpoints(session_id)

    return CheckpointListResponse(
        checkpoints=[
            CheckpointResponse(
                id=cp.id,
                session_id=cp.session_id,
                user_message_uuid=cp.user_message_uuid,
                created_at=cp.created_at,
                files_modified=cp.files_modified,
            )
            for cp in checkpoints
        ]
    )


@router.post("/{session_id}/rewind")
async def rewind_to_checkpoint(
    session_id: str,
    request: RewindRequest,
    _api_key: ApiKey,
    session_service: SessionSvc,
    checkpoint_service: CheckpointSvc,
) -> dict[str, str]:
    """Rewind session files to a checkpoint state (T103).

    Restores files to their state at the specified checkpoint. This allows
    reverting changes made by the agent during the session.

    Args:
        session_id: Session ID to rewind.
        request: Rewind request with checkpoint_id.
        _api_key: Validated API key (via dependency).
        session_service: Session service instance.
        checkpoint_service: Checkpoint service instance.

    Returns:
        Status response with checkpoint_id that was rewound to.

    Raises:
        SessionNotFoundError: If session doesn't exist.
        InvalidCheckpointError: If checkpoint is invalid or doesn't belong to session.
    """
    # Verify session exists
    session = await session_service.get_session(session_id)
    if not session:
        raise SessionNotFoundError(session_id)

    # Validate checkpoint belongs to this session
    is_valid = await checkpoint_service.validate_checkpoint(
        session_id=session_id,
        checkpoint_id=request.checkpoint_id,
    )

    if not is_valid:
        raise InvalidCheckpointError(
            checkpoint_id=request.checkpoint_id,
            session_id=session_id,
        )

    # TODO: Actually rewind files using agent SDK when available
    # For now, validation passed but file restoration is not yet implemented.
    # Return "validated" status to indicate checkpoint exists and belongs to session,
    # but actual file restoration requires SDK support (T104).

    return {
        "status": "validated",
        "checkpoint_id": request.checkpoint_id,
        "message": "Checkpoint validated. File restoration pending SDK support.",
    }
