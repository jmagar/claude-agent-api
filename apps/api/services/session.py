"""Session management service."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

import structlog

if TYPE_CHECKING:
    from apps.api.adapters.cache import RedisCache

logger = structlog.get_logger(__name__)


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

    def __init__(self, cache: "RedisCache | None" = None) -> None:
        """Initialize session service.

        Args:
            cache: RedisCache instance for caching.
        """
        self._cache = cache
        self._ttl = 3600  # 1 hour default TTL

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
            # Use the underlying Redis client for scan
            cursor: int = 0
            all_keys: list[str] = []

            while True:
                cursor_result = await self._cache._client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100,
                )
                cursor = int(cursor_result[0])
                all_keys.extend(
                    [k.decode() if isinstance(k, bytes) else k for k in cursor_result[1]]
                )
                if cursor == 0:
                    break

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
        data = {
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
            return Session(
                id=parsed["id"],
                model=parsed["model"],
                status=parsed["status"],
                created_at=datetime.fromisoformat(parsed["created_at"]),
                updated_at=datetime.fromisoformat(parsed["updated_at"]),
                total_turns=parsed.get("total_turns", 0),
                total_cost_usd=parsed.get("total_cost_usd"),
                parent_session_id=parsed.get("parent_session_id"),
            )
        except KeyError as e:
            logger.warning(
                "Failed to parse cached session",
                session_id=session_id,
                error=str(e),
            )
            return None
