"""Session management service."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal, TypedDict
from uuid import uuid4

import structlog

from apps.api.config import get_settings

if TYPE_CHECKING:
    from apps.api.protocols import Cache

logger = structlog.get_logger(__name__)


class CachedSessionData(TypedDict):
    """TypedDict for session data stored in Redis cache."""

    id: str
    model: str
    status: Literal["active", "completed", "error"]
    created_at: str  # ISO format
    updated_at: str  # ISO format
    total_turns: int
    total_cost_usd: float | None
    parent_session_id: str | None


@dataclass
class Session:
    """Session data model."""

    id: str
    model: str
    status: Literal["active", "completed", "error"]
    created_at: datetime
    updated_at: datetime
    total_turns: int = 0
    total_cost_usd: float | None = None
    parent_session_id: str | None = None


@dataclass
class SessionListResult:
    """Result of listing sessions."""

    sessions: list[Session]
    total: int
    page: int
    page_size: int


class SessionService:
    """Service for managing agent sessions."""

    def __init__(self, cache: "Cache | None" = None) -> None:
        """Initialize session service.

        Args:
            cache: Cache instance implementing Cache protocol.
        """
        self._cache = cache
        settings = get_settings()
        self._ttl = settings.redis_session_ttl

    def _cache_key(self, session_id: str) -> str:
        """Generate cache key for a session."""
        return f"session:{session_id}"

    async def create_session(
        self,
        model: str,
        session_id: str | None = None,
        parent_session_id: str | None = None,
    ) -> Session:
        """Create a new session.

        Args:
            model: Claude model name.
            session_id: Optional custom session ID.
            parent_session_id: ID of parent session if forked.

        Returns:
            Created session.
        """
        now = datetime.now(UTC)
        session = Session(
            id=session_id or str(uuid4()),
            model=model,
            status="active",
            created_at=now,
            updated_at=now,
            total_turns=0,
            total_cost_usd=None,
            parent_session_id=parent_session_id,
        )

        # Cache the session
        await self._cache_session(session)

        logger.info(
            "Session created",
            session_id=session.id,
            model=model,
            parent_session_id=parent_session_id,
        )

        return session

    async def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID.

        Args:
            session_id: Session ID to retrieve.

        Returns:
            Session if found, None otherwise.
        """
        # Try cache first
        cached = await self._get_cached_session(session_id)
        if cached:
            return cached

        # TODO: Implement database fallback
        logger.debug("Session not found", session_id=session_id)
        return None

    async def list_sessions(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> SessionListResult:
        """List sessions with pagination.

        Args:
            page: Page number (1-indexed).
            page_size: Number of sessions per page.

        Returns:
            Paginated session list.
        """
        # Get all session keys from cache
        sessions: list[Session] = []

        if self._cache:
            pattern = "session:*"
            # Use scan_keys method from Cache protocol
            all_keys = await self._cache.scan_keys(pattern)

            # Get sessions
            for key in all_keys:
                session_id = key.replace("session:", "")
                session = await self._get_cached_session(session_id)
                if session:
                    sessions.append(session)

        # Sort by created_at descending
        sessions.sort(key=lambda s: s.created_at, reverse=True)

        # Calculate pagination
        total = len(sessions)
        start = (page - 1) * page_size
        end = start + page_size
        page_sessions = sessions[start:end]

        return SessionListResult(
            sessions=page_sessions,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_session(
        self,
        session_id: str,
        status: Literal["active", "completed", "error"] | None = None,
        total_turns: int | None = None,
        total_cost_usd: float | None = None,
    ) -> Session | None:
        """Update a session.

        Args:
            session_id: Session ID to update.
            status: New status.
            total_turns: Updated turn count.
            total_cost_usd: Updated cost.

        Returns:
            Updated session or None if not found.
        """
        session = await self.get_session(session_id)
        if not session:
            return None

        # Apply updates
        if status is not None:
            session.status = status
        if total_turns is not None:
            session.total_turns = total_turns
        if total_cost_usd is not None:
            session.total_cost_usd = total_cost_usd

        session.updated_at = datetime.now(UTC)

        # Update cache
        await self._cache_session(session)

        logger.info(
            "Session updated",
            session_id=session_id,
            status=session.status,
            total_turns=session.total_turns,
        )

        return session

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        if self._cache:
            key = self._cache_key(session_id)
            result = await self._cache.delete(key)
            if result:
                logger.info("Session deleted", session_id=session_id)
                return True

        return False

    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists.

        Args:
            session_id: Session ID to check.

        Returns:
            True if session exists.
        """
        if self._cache:
            key = self._cache_key(session_id)
            return await self._cache.exists(key)
        return False

    async def _cache_session(self, session: Session) -> None:
        """Cache a session in Redis.

        Args:
            session: Session to cache.
        """
        if not self._cache:
            return

        key = self._cache_key(session.id)
        data: dict[str, object] = {
            "id": session.id,
            "model": session.model,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "total_turns": session.total_turns,
            "total_cost_usd": session.total_cost_usd,
            "parent_session_id": session.parent_session_id,
        }

        await self._cache.set_json(key, data, self._ttl)

    async def _get_cached_session(self, session_id: str) -> Session | None:
        """Get a session from cache.

        Args:
            session_id: Session ID to retrieve.

        Returns:
            Session if found in cache.
        """
        if not self._cache:
            return None

        key = self._cache_key(session_id)
        parsed = await self._cache.get_json(key)

        if not parsed:
            return None

        try:
            # Extract values with proper type casting
            session_id_val = str(parsed["id"])
            model_val = str(parsed["model"])
            status_raw = str(parsed["status"])
            created_at_val = str(parsed["created_at"])
            updated_at_val = str(parsed["updated_at"])

            # Validate status is one of the allowed values
            if status_raw not in ("active", "completed", "error"):
                status_val: Literal["active", "completed", "error"] = "active"
            else:
                status_val = status_raw  # type: ignore[assignment]

            # Get optional values with proper type handling
            total_turns_raw = parsed.get("total_turns", 0)
            if isinstance(total_turns_raw, int):
                total_turns_val = total_turns_raw
            elif isinstance(total_turns_raw, (str, float)):
                total_turns_val = int(total_turns_raw)
            else:
                total_turns_val = 0

            total_cost_raw = parsed.get("total_cost_usd")
            if total_cost_raw is None:
                total_cost_val = None
            elif isinstance(total_cost_raw, (int, float, str)):
                total_cost_val = float(total_cost_raw)
            else:
                total_cost_val = None

            parent_id_raw = parsed.get("parent_session_id")
            parent_id_val = str(parent_id_raw) if parent_id_raw is not None else None

            return Session(
                id=session_id_val,
                model=model_val,
                status=status_val,
                created_at=datetime.fromisoformat(created_at_val),
                updated_at=datetime.fromisoformat(updated_at_val),
                total_turns=total_turns_val,
                total_cost_usd=total_cost_val,
                parent_session_id=parent_id_val,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(
                "Failed to parse cached session",
                session_id=session_id,
                error=str(e),
            )
            return None
