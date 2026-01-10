"""Session CRUD endpoints."""

from fastapi import APIRouter, Query

from apps.api.dependencies import ApiKey, SessionSvc
from apps.api.exceptions import SessionNotFoundError
from apps.api.schemas.responses import SessionListResponse, SessionResponse

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
    result = await session_service.list_sessions(
        page=page,
        page_size=page_size,
        current_api_key=_api_key,
    )

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
