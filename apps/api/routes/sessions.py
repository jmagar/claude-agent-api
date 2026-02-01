"""Session CRUD endpoints."""

import secrets
from typing import Literal, cast
from uuid import UUID

from fastapi import APIRouter, Query

from apps.api.adapters.session_repo import SessionRepository
from apps.api.dependencies import ApiKey, DbSession, SessionSvc
from apps.api.exceptions import APIError, SessionNotFoundError
from apps.api.models.session import Session
from apps.api.schemas.requests.sessions import PromoteRequest
from apps.api.schemas.responses import (
    SessionResponse,
    SessionWithMetaListResponse,
    SessionWithMetaResponse,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("")
async def list_sessions(
    _api_key: ApiKey,
    db_session: DbSession,
    mode: str | None = None,
    project_id: str | None = None,
    tags: list[str] | None = Query(default=None),
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> SessionWithMetaListResponse:
    """<summary>List sessions with metadata filtering.</summary>"""
    repo = SessionRepository(db_session)

    # Security: filter by owner at DB level (public OR owned by this key)
    sessions, _ = await repo.list_sessions(
        owner_api_key=_api_key,
        filter_by_owner_or_public=True,
        limit=10000,
        offset=0,
    )

    # Metadata filtering (JSONB queries are complex, filter in memory)
    def matches_metadata(session: Session) -> bool:
        metadata = session.metadata_ or {}
        session_mode = metadata.get("mode", "code")
        if mode and session_mode != mode:
            return False
        if project_id and str(metadata.get("project_id")) != project_id:
            return False
        if tags:
            session_tags = metadata.get("tags", [])
            if not isinstance(session_tags, list) or not all(
                tag in session_tags for tag in tags
            ):
                return False
        if search:
            title = str(metadata.get("title", "")).lower()
            if search.lower() not in title:
                return False
        return True

    filtered = [session for session in sessions if matches_metadata(session)]
    start = (page - 1) * page_size
    page_sessions = filtered[start : start + page_size]

    mapped = []
    for s in page_sessions:
        metadata = s.metadata_ or {}
        session_mode = metadata.get("mode", "code")
        mapped.append(
            SessionWithMetaResponse(
                id=str(s.id),
                mode="brainstorm" if session_mode == "brainstorm" else "code",
                status=cast("Literal['active', 'completed', 'error']", s.status),
                project_id=str(metadata.get("project_id"))
                if metadata.get("project_id")
                else None,
                title=str(metadata.get("title")) if metadata.get("title") else None,
                created_at=s.created_at,
                updated_at=s.updated_at,
                total_turns=s.total_turns,
                total_cost_usd=float(s.total_cost_usd)
                if s.total_cost_usd is not None
                else None,
                parent_session_id=str(s.parent_session_id)
                if s.parent_session_id
                else None,
                tags=cast("list[str] | None", metadata.get("tags"))
                if isinstance(metadata.get("tags"), list)
                else None,
                metadata=metadata,
            )
        )

    return SessionWithMetaListResponse(
        sessions=mapped,
        total=len(filtered),
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
        SessionNotFoundError: If session doesn't exist.
    """
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
    db_session: DbSession,
) -> SessionWithMetaResponse:
    """Promote a brainstorm session to code mode."""
    repo = SessionRepository(db_session)
    session = await repo.get(UUID(session_id))
    if not session or (session.owner_api_key and not secrets.compare_digest(session.owner_api_key, _api_key)):
        raise SessionNotFoundError(session_id)

    metadata = dict(session.metadata_ or {})
    metadata.update({"mode": "code", "project_id": request.project_id})

    updated = await repo.update_metadata(UUID(session_id), metadata)
    if updated is None:
        raise SessionNotFoundError(session_id)

    mode = metadata.get("mode", "code")
    project_id = metadata.get("project_id")
    tags = metadata.get("tags")
    title = metadata.get("title")

    return SessionWithMetaResponse(
        id=str(updated.id),
        mode="code" if mode != "brainstorm" else "brainstorm",
        status=cast("Literal['active', 'completed', 'error']", updated.status),
        project_id=str(project_id) if project_id else None,
        title=str(title) if title else None,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
        total_turns=updated.total_turns,
        total_cost_usd=float(updated.total_cost_usd)
        if updated.total_cost_usd is not None
        else None,
        parent_session_id=str(updated.parent_session_id)
        if updated.parent_session_id
        else None,
        tags=cast("list[str] | None", tags) if isinstance(tags, list) else None,
        metadata=metadata,
    )


@router.patch("/{session_id}/tags", response_model=SessionWithMetaResponse)
async def update_session_tags(
    session_id: str,
    request: dict[str, object],
    _api_key: ApiKey,
    db_session: DbSession,
) -> SessionWithMetaResponse:
    """<summary>Update session tags.</summary>"""
    tags = request.get("tags")
    if not isinstance(tags, list):
        raise APIError(
            message="Tags must be a list",
            code="VALIDATION_ERROR",
            status_code=400,
        )

    repo = SessionRepository(db_session)
    session = await repo.get(UUID(session_id))
    if not session or (session.owner_api_key and not secrets.compare_digest(session.owner_api_key, _api_key)):
        raise SessionNotFoundError(session_id)

    metadata = dict(session.metadata_ or {})
    metadata["tags"] = tags

    updated = await repo.update_metadata(UUID(session_id), metadata)
    if updated is None:
        raise SessionNotFoundError(session_id)

    session_mode = metadata.get("mode", "code")
    return SessionWithMetaResponse(
        id=str(updated.id),
        mode="brainstorm" if session_mode == "brainstorm" else "code",
        status=cast("Literal['active', 'completed', 'error']", updated.status),
        project_id=str(metadata.get("project_id"))
        if metadata.get("project_id")
        else None,
        title=str(metadata.get("title")) if metadata.get("title") else None,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
        total_turns=updated.total_turns,
        total_cost_usd=float(updated.total_cost_usd)
        if updated.total_cost_usd is not None
        else None,
        parent_session_id=str(updated.parent_session_id)
        if updated.parent_session_id
        else None,
        tags=cast("list[str] | None", tags),
        metadata=metadata,
    )
