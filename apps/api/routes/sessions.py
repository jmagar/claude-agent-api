"""Session CRUD endpoints."""


from uuid import UUID

from fastapi import APIRouter, Query

from apps.api.dependencies import ApiKey, SessionSvc
from apps.api.exceptions import SessionNotFoundError, ValidationError
from apps.api.schemas.requests.sessions import PromoteRequest, UpdateTagsRequest
from apps.api.schemas.responses import (
    SessionResponse,
    SessionWithMetaListResponse,
    SessionWithMetaResponse,
)
from apps.api.utils.response_helpers import map_session_with_metadata

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("")
async def list_sessions(
    _api_key: ApiKey,
    session_service: SessionSvc,
    mode: str | None = None,
    project_id: str | None = None,
    tags: list[str] | None = Query(default=None),
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> SessionWithMetaListResponse:
    """<summary>List sessions with metadata filtering.</summary>"""

    # Use service layer for business logic (includes ownership enforcement and filtering)
    result = await session_service.list_sessions(
        current_api_key=_api_key,
        mode=mode,
        project_id=project_id,
        tags=tags,
        search=search,
        page=page,
        page_size=page_size,
    )
    sessions = result.sessions
    total = result.total

    mapped = []
    for s in sessions:
        metadata = s.session_metadata or {}
        mapped.append(map_session_with_metadata(s, metadata))

    return SessionWithMetaListResponse(
        sessions=mapped,
        total=total,
        page=page,
        page_size=page_size,
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
        ValidationError: If session_id is not a valid UUID.
        SessionNotFoundError: If session doesn't exist.
    """
    # Validate UUID format
    try:
        UUID(session_id)
    except ValueError as e:
        raise ValidationError(
            message=f"Invalid session ID format: {session_id}",
            field="session_id",
        ) from e

    session = await session_service.get_session(
        session_id,
        current_api_key=_api_key,
    )
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


@router.post("/{session_id}/promote", response_model=SessionWithMetaResponse)
async def promote_session(
    session_id: str,
    request: PromoteRequest,
    _api_key: ApiKey,
    session_service: SessionSvc,
) -> SessionWithMetaResponse:
    """Promote a brainstorm session to code mode.

    Raises:
        ValidationError: If session_id is not a valid UUID.
        SessionNotFoundError: If session doesn't exist.
    """
    # Validate UUID format
    try:
        UUID(session_id)
    except ValueError as e:
        raise ValidationError(
            message=f"Invalid session ID format: {session_id}",
            field="session_id",
        ) from e

    updated = await session_service.promote_session(
        session_id=session_id,
        project_id=request.project_id,
        current_api_key=_api_key,
    )
    if not updated:
        raise SessionNotFoundError(session_id)

    return map_session_with_metadata(updated)


@router.patch("/{session_id}/tags", response_model=SessionWithMetaResponse)
async def update_session_tags(
    session_id: str,
    request: UpdateTagsRequest,
    _api_key: ApiKey,
    session_service: SessionSvc,
) -> SessionWithMetaResponse:
    """Update session tags.

    Raises:
        ValidationError: If session_id is not a valid UUID.
        SessionNotFoundError: If session doesn't exist.
    """
    # Validate UUID format
    try:
        UUID(session_id)
    except ValueError as e:
        raise ValidationError(
            message=f"Invalid session ID format: {session_id}",
            field="session_id",
        ) from e

    updated = await session_service.update_tags(
        session_id=session_id,
        tags=request.tags,
        current_api_key=_api_key,
    )
    if not updated:
        raise SessionNotFoundError(session_id)

    return map_session_with_metadata(updated)
