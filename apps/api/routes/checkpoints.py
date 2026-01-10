"""Checkpoint management endpoints."""

from fastapi import APIRouter

from apps.api.dependencies import (
    ApiKey,
    CheckpointSvc,
    SessionSvc,
)
from apps.api.exceptions import InvalidCheckpointError, SessionNotFoundError
from apps.api.schemas.requests.control import RewindRequest
from apps.api.schemas.responses import (
    CheckpointListResponse,
    CheckpointResponse,
    RewindResponse,
)

router = APIRouter(prefix="/sessions", tags=["Checkpoints"])


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
    session = await session_service.get_session(
        session_id,
        current_api_key=_api_key,
    )
    if not session:
        raise SessionNotFoundError(session_id)

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
) -> RewindResponse:
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
    session = await session_service.get_session(
        session_id,
        current_api_key=_api_key,
    )
    if not session:
        raise SessionNotFoundError(session_id)

    is_valid = await checkpoint_service.validate_checkpoint(
        session_id=session_id,
        checkpoint_id=request.checkpoint_id,
    )

    if not is_valid:
        raise InvalidCheckpointError(
            checkpoint_id=request.checkpoint_id,
            session_id=session_id,
        )

    return RewindResponse(
        status="validated",
        checkpoint_id=request.checkpoint_id,
        message="Checkpoint validated. File restoration pending SDK support.",
    )
