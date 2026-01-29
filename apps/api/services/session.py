"""Session management service with distributed state support.

This service implements a dual-storage architecture:
- PostgreSQL: Source of truth for session data (durability)
- Redis: Cache layer for performance (fast reads)

Key Features:
- Cache-aside pattern: Read from cache, fallback to DB
- Dual-write on create: Write to DB first, then cache
- Distributed locking: Prevent race conditions
- Graceful degradation: Works without Redis (single-instance mode)

Enables horizontal scaling by using Redis for shared state.
See ADR-001 for architecture details.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal, TypedDict, TypeVar
from uuid import UUID, uuid4

import structlog

from apps.api.config import get_settings
from apps.api.exceptions.session import SessionNotFoundError
from apps.api.types import JsonValue

T = TypeVar("T")

if TYPE_CHECKING:
    from apps.api.adapters.session_repo import SessionRepository
    from apps.api.models.session import Session as SessionModel
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
    owner_api_key: str | None


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
    owner_api_key: str | None = None


@dataclass
class SessionListResult:
    """Result of listing sessions."""

    sessions: list[Session]
    total: int
    page: int
    page_size: int


class SessionService:
    """Service for managing agent sessions."""

    # Lock retry configuration
    _LOCK_INITIAL_RETRY_DELAY = 0.01  # Start with 10ms
    _LOCK_MAX_RETRY_DELAY = 0.5  # Cap at 500ms

    def __init__(
        self,
        cache: "Cache | None" = None,
        db_repo: "SessionRepository | None" = None,
    ) -> None:
        """Initialize session service.

        Args:
            cache: Cache instance implementing Cache protocol.
            db_repo: Optional SessionRepository for PostgreSQL persistence.
                   Required for dual-write and database fallback functionality.
        """
        self._cache = cache
        self._db_repo = db_repo
        settings = get_settings()
        self._ttl = settings.redis_session_ttl

    def _cache_key(self, session_id: str) -> str:
        """Generate cache key for a session."""
        return f"session:{session_id}"

    async def _with_session_lock(
        self,
        session_id: str,
        operation: str,
        func: Callable[[], Awaitable[T]],
        acquire_timeout: float = 5.0,
        lock_ttl: int = 30,
    ) -> T:
        """Execute operation with distributed lock on session.

        Args:
            session_id: The session ID to lock.
            operation: Description of operation (for logging).
            func: Async function to execute while holding lock.
            acquire_timeout: How long to wait to acquire the lock (seconds).
            lock_ttl: How long the lock remains valid (seconds).
                     Must be > expected operation duration to prevent
                     concurrent access if operation runs long.

        Returns:
            Result from func.

        Raises:
            TimeoutError: If lock cannot be acquired within acquire_timeout.
        """
        if not self._cache:
            # No cache = no distributed locking needed (single-instance mode)
            return await func()

        lock_key = f"session_lock:{session_id}"
        lock_value = None
        start_time = time.monotonic()

        # Retry loop with exponential backoff
        retry_delay = self._LOCK_INITIAL_RETRY_DELAY
        max_retry_delay = self._LOCK_MAX_RETRY_DELAY

        while True:
            # Try to acquire lock
            lock_value = await self._cache.acquire_lock(
                lock_key,
                ttl=lock_ttl,
            )

            if lock_value is not None:
                # Lock acquired successfully
                break

            # Check if we've exceeded timeout
            elapsed = time.monotonic() - start_time
            if elapsed >= acquire_timeout:
                logger.warning(
                    "Failed to acquire session lock after timeout",
                    session_id=session_id,
                    operation=operation,
                    timeout=acquire_timeout,
                    elapsed=elapsed,
                )
                raise TimeoutError(f"Could not acquire lock for session {session_id}")

            # Wait before retrying (exponential backoff)
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)

        try:
            logger.debug(
                "Acquired session lock",
                session_id=session_id,
                operation=operation,
            )

            # Execute operation while holding lock
            result = await func()

            return result

        finally:
            # Always release lock
            await self._cache.release_lock(lock_key, lock_value)
            logger.debug(
                "Released session lock",
                session_id=session_id,
                operation=operation,
            )

    async def create_session(
        self,
        model: str,
        session_id: str | None = None,
        parent_session_id: str | None = None,
        owner_api_key: str | None = None,
    ) -> Session:
        """Create a new session with dual-write to PostgreSQL and Redis.

        Args:
            model: Claude model name.
            session_id: Optional session ID (generates UUID if None).
            parent_session_id: ID of parent session if forked.
            owner_api_key: Owning API key for authorization checks.

        Returns:
            Created session.

        Implementation:
        1. Write to PostgreSQL first (source of truth)
        2. Write to Redis cache (performance)
        3. If Redis write fails, log but don't fail (cache is optional)

        This ensures sessions are durable even if Redis fails (P0-2).
        """
        from uuid import UUID

        # Generate session ID if not provided
        if session_id is None:
            session_id = str(uuid4())

        # Create session object
        now = datetime.now(UTC)
        session = Session(
            id=session_id,
            model=model,
            status="active",
            total_turns=0,
            total_cost_usd=None,
            parent_session_id=parent_session_id,
            owner_api_key=owner_api_key,
            created_at=now,
            updated_at=now,
        )

        # Write to PostgreSQL first (source of truth)
        if self._db_repo:
            try:
                await self._db_repo.create(
                    session_id=UUID(session_id),
                    model=model,
                    parent_session_id=UUID(parent_session_id)
                    if parent_session_id
                    else None,
                    owner_api_key=owner_api_key,
                )
                logger.info(
                    "Session created in database",
                    session_id=session_id,
                    model=model,
                    parent_session_id=parent_session_id,
                )
            except Exception as e:
                logger.error(
                    "Failed to create session in database",
                    session_id=session_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

        # Write to Redis cache (best-effort)
        # TRANSACTION BOUNDARY NOTE: No distributed transaction between DB and Redis.
        # If cache write fails after DB succeeds:
        # - Session exists in PostgreSQL (source of truth) - data is DURABLE
        # - Cache-aside pattern will repopulate Redis on next get_session() call
        # - This is acceptable eventual consistency, not data loss
        try:
            await self._cache_session(session)
            logger.info(
                "Session cached in Redis",
                session_id=session_id,
                model=model,
            )
        except Exception as e:
            # Cache write failure is non-fatal - DB is source of truth
            # Cache-aside pattern in get_session() will repopulate on next read
            logger.warning(
                "Failed to cache session in Redis (continuing - cache-aside will recover)",
                session_id=session_id,
                error=str(e),
            )

        return session

    async def get_session(
        self,
        session_id: str,
        current_api_key: str | None = None,
    ) -> Session | None:
        """Get session by ID with PostgreSQL fallback.

        Args:
            session_id: The session ID.
            current_api_key: API key for ownership enforcement.

        Returns:
            Session if found, None otherwise.

        Implementation:
        1. Check Redis cache (fast path)
        2. If cache miss, query PostgreSQL (fallback)
        3. Re-cache the result for future requests (cache-aside pattern)

        This ensures sessions survive Redis restarts (P0-2 fix).
        """
        # Try cache first (fast path)
        cached = await self._get_cached_session(session_id)
        if cached:
            logger.debug(
                "Session retrieved from cache",
                session_id=session_id,
                source="redis",
            )
            return self._enforce_owner(cached, current_api_key)

        # Cache miss: fall back to PostgreSQL
        logger.debug(
            "Session cache miss, querying database",
            session_id=session_id,
            source="postgres",
        )

        if not self._db_repo:
            logger.debug("No database repository configured", session_id=session_id)
            return None

        try:
            # Query PostgreSQL
            from uuid import UUID

            db_session = await self._db_repo.get(UUID(session_id))

            if not db_session:
                logger.debug("Session not found in database", session_id=session_id)
                return None

            # Map SQLAlchemy model to service model
            session = self._map_db_to_service(db_session)

            session = self._enforce_owner(session, current_api_key)

            # Re-cache for future requests (cache-aside pattern)
            await self._cache_session(session)

            logger.info(
                "Session retrieved from database and re-cached",
                session_id=session_id,
                model=session.model,
            )

            return session

        except Exception as e:
            logger.error(
                "Failed to retrieve session from database",
                session_id=session_id,
                error=str(e),
                exc_info=True,
            )
            return None

    async def list_sessions(
        self,
        page: int = 1,
        page_size: int = 20,
        current_api_key: str | None = None,
    ) -> SessionListResult:
        """List sessions with pagination using bulk cache reads or DB repository.

        When current_api_key is provided and db_repo is available, uses efficient
        indexed DB query. Otherwise, falls back to cache scan.

        Args:
            page: Page number (1-indexed).
            page_size: Number of sessions per page.
            current_api_key: API key for ownership filtering.
                           If provided, only returns sessions owned by this key.

        Returns:
            Paginated session list.
        """
        # Use db_repo for owner-filtered queries (efficient indexed lookup)
        if current_api_key is not None and self._db_repo is not None:
            offset = (page - 1) * page_size
            db_sessions, total = await self._db_repo.list_sessions(
                owner_api_key=current_api_key,
                limit=page_size,
                offset=offset,
            )
            # Convert DB models to service Session objects
            sessions = [self._map_db_to_service(s) for s in db_sessions]
            return SessionListResult(
                sessions=sessions,
                total=total,
                page=page,
                page_size=page_size,
            )

        # Use owner index for cache-based owner filtering (efficient)
        cached_sessions: list[Session] = []

        if self._cache and current_api_key is not None:
            # Use owner index set to get session IDs for this owner
            owner_index_key = f"session:owner:{current_api_key}"
            session_ids = await self._cache.set_members(owner_index_key)

            # Bulk fetch session data
            keys = [self._cache_key(session_id) for session_id in session_ids]
            cached_rows = await self._cache.get_many_json(keys)

            # Parse sessions
            for parsed in cached_rows:
                if not parsed:
                    continue
                session = self._parse_cached_session(parsed)
                if session:
                    cached_sessions.append(session)

        elif self._cache:
            # WARNING: Full cache scan path - should be avoided in production.
            # This path is only reached when no owner filter is provided AND
            # db_repo is not available. Prefer using indexed DB queries.
            logger.warning(
                "session_list_full_scan",
                msg="Using full cache scan - consider adding owner filter for efficiency",
            )
            pattern = "session:*"
            all_keys = await self._cache.scan_keys(pattern, max_keys=1000)

            # Bulk fetch all session data in one Redis roundtrip
            cached_rows = await self._cache.get_many_json(all_keys)

            # Parse each cached session
            for _key, parsed in zip(all_keys, cached_rows, strict=True):
                if not parsed:
                    continue
                session = self._parse_cached_session(parsed)
                if session:
                    cached_sessions.append(session)

        # Sort by created_at descending
        cached_sessions.sort(key=lambda s: s.created_at, reverse=True)

        # Calculate pagination
        total = len(cached_sessions)
        start = (page - 1) * page_size
        end = start + page_size
        page_sessions = cached_sessions[start:end]

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
        increment_turns: bool = False,
        current_api_key: str | None = None,
    ) -> Session | None:
        """Update a session with distributed locking.

        Locks are applied at the business operation level (not infrastructure)
        to prevent race conditions during read-modify-write cycles.

        Args:
            session_id: Session ID to update.
            status: New status.
            total_turns: Updated turn count (or None to keep/increment).
            total_cost_usd: Updated cost.
            increment_turns: If True, atomically increment total_turns by 1.
            current_api_key: API key for ownership enforcement.

        Returns:
            Updated session or None if not found.

        Raises:
            SessionNotFoundError: If session not owned by current_api_key.
        """
        from uuid import UUID

        async def _do_update() -> Session | None:
            session = await self.get_session(
                session_id, current_api_key=current_api_key
            )
            if not session:
                return None

            # Apply updates
            if status is not None:
                session.status = status
            if total_turns is not None:
                session.total_turns = total_turns
            if increment_turns:
                session.total_turns += 1
            if total_cost_usd is not None:
                session.total_cost_usd = total_cost_usd

            session.updated_at = datetime.now(UTC)

            # Update database first (source of truth)
            if self._db_repo:
                await self._db_repo.update(
                    session_id=UUID(session_id),
                    status=session.status,
                    total_turns=session.total_turns,
                    total_cost_usd=session.total_cost_usd,
                )

            # Update cache only after DB write succeeds
            await self._cache_session(session)

            logger.info(
                "Session updated",
                session_id=session_id,
                status=session.status,
                total_turns=session.total_turns,
            )

            return session

        # Apply distributed lock at BUSINESS OPERATION level (not cache level)
        # This ensures the entire read-modify-write cycle is atomic
        return await self._with_session_lock(
            session_id,
            "update_session",
            _do_update,
        )

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        if self._cache:
            owner_api_key: str | None = None
            cached_session = await self._get_cached_session(session_id)
            if cached_session:
                owner_api_key = cached_session.owner_api_key
            elif self._db_repo:
                try:
                    db_session = await self._db_repo.get(UUID(session_id))
                except (TypeError, ValueError):
                    db_session = None
                if db_session:
                    owner_api_key = db_session.owner_api_key

            key = self._cache_key(session_id)
            if owner_api_key:
                owner_index_key = f"session:owner:{owner_api_key}"
                await self._cache.remove_from_set(owner_index_key, session_id)

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
        """Cache a session in Redis and update owner index.

        Args:
            session: Session to cache.
        """
        if not self._cache:
            return

        key = self._cache_key(session.id)
        data: dict[str, JsonValue] = {
            "id": session.id,
            "model": session.model,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "total_turns": session.total_turns,
            "total_cost_usd": session.total_cost_usd,
            "parent_session_id": session.parent_session_id,
            "owner_api_key": session.owner_api_key,
        }

        await self._cache.set_json(key, data, self._ttl)

        # Maintain owner index for efficient owner-filtered queries
        if session.owner_api_key:
            owner_index_key = f"session:owner:{session.owner_api_key}"
            await self._cache.add_to_set(owner_index_key, session.id)

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

        return self._parse_cached_session(parsed)

    def _parse_cached_session(
        self,
        parsed: dict[str, JsonValue],
    ) -> Session | None:
        """Parse cached session data into Session object.

        Args:
            parsed: Parsed JSON dict from cache.

        Returns:
            Session object or None if parsing fails.

        Note:
            This extracts the parsing logic from _get_cached_session
            for reuse in list_sessions bulk operations.
        """
        try:
            # Extract values with proper type casting
            session_id_val = str(parsed["id"])
            model_val = str(parsed["model"])
            status_raw = str(parsed["status"])
            created_at_val = str(parsed["created_at"])
            updated_at_val = str(parsed["updated_at"])

            # Validate status is one of the allowed values
            status_val: Literal["active", "completed", "error"]
            if status_raw == "active":
                status_val = "active"
            elif status_raw == "completed":
                status_val = "completed"
            elif status_raw == "error":
                status_val = "error"
            else:
                status_val = "active"  # Default to active for invalid values

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
            owner_raw = parsed.get("owner_api_key")
            owner_val = str(owner_raw) if owner_raw is not None else None

            # Parse datetimes and normalize to naive (remove timezone info)
            created_dt = datetime.fromisoformat(created_at_val)
            updated_dt = datetime.fromisoformat(updated_at_val)

            # Convert to naive if timezone-aware
            if created_dt.tzinfo is not None:
                created_dt = created_dt.replace(tzinfo=None)
            if updated_dt.tzinfo is not None:
                updated_dt = updated_dt.replace(tzinfo=None)

            return Session(
                id=session_id_val,
                model=model_val,
                status=status_val,
                created_at=created_dt,
                updated_at=updated_dt,
                total_turns=total_turns_val,
                total_cost_usd=total_cost_val,
                parent_session_id=parent_id_val,
                owner_api_key=owner_val,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(
                "Failed to parse cached session",
                error=str(e),
            )
            return None

    def _map_db_to_service(self, db_session: "SessionModel") -> Session:
        """Map SQLAlchemy Session model to service Session dataclass.

        Args:
            db_session: SQLAlchemy Session model from database.

        Returns:
            Service-layer Session dataclass.
        """
        # Validate and cast status to Literal type
        status_raw = db_session.status
        status_val: Literal["active", "completed", "error"]
        if status_raw == "active":
            status_val = "active"
        elif status_raw == "completed":
            status_val = "completed"
        elif status_raw == "error":
            status_val = "error"
        else:
            status_val = "active"  # Default to active for invalid values

        return Session(
            id=str(db_session.id),
            model=db_session.model,
            status=status_val,
            total_turns=db_session.total_turns,
            total_cost_usd=(
                float(db_session.total_cost_usd)
                if db_session.total_cost_usd is not None
                else None
            ),
            parent_session_id=(
                str(db_session.parent_session_id)
                if db_session.parent_session_id
                else None
            ),
            owner_api_key=db_session.owner_api_key,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
        )

    def _enforce_owner(
        self,
        session: Session,
        current_api_key: str | None,
    ) -> Session:
        """Enforce that the current API key owns the session."""
        if (
            current_api_key
            and session.owner_api_key
            and session.owner_api_key != current_api_key
        ):
            raise SessionNotFoundError(session.id)
        return session
