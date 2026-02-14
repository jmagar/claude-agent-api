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

import secrets
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal, TypeVar
from uuid import UUID, uuid4

import structlog
from sqlalchemy.exc import IntegrityError, OperationalError

from apps.api.config import get_settings
from apps.api.exceptions.base import APIError
from apps.api.exceptions.session import SessionNotFoundError
from apps.api.services.session_cache_manager import SessionCacheManager
from apps.api.services.session_lock_manager import SessionLockManager
from apps.api.services.session_metadata_manager import SessionMetadataManager
from apps.api.services.session_models import (
    Session,
    SessionListResult,
)
from apps.api.types import JsonValue
from apps.api.utils.crypto import hash_api_key
from apps.api.utils.session_utils import parse_session_status

T = TypeVar("T")

if TYPE_CHECKING:
    from apps.api.models.session import Session as SessionModel
    from apps.api.protocols import Cache, SessionRepositoryProtocol

logger = structlog.get_logger(__name__)


class SessionService:
    """Service for managing agent sessions."""

    def __init__(
        self,
        cache: "Cache | None" = None,
        db_repo: "SessionRepositoryProtocol | None" = None,
    ) -> None:
        """Initialize session service.

        Args:
            cache: Cache instance implementing Cache protocol.
            db_repo: Optional session repository for PostgreSQL persistence.
                   Required for dual-write and database fallback functionality.
        """
        self._cache = cache
        self._db_repo = db_repo
        settings = get_settings()
        self._ttl = settings.redis_session_ttl
        self._cache_manager = SessionCacheManager(cache=cache, ttl=self._ttl)
        self._lock_manager = SessionLockManager(cache=cache)
        self._metadata_manager = SessionMetadataManager(db_repo=db_repo)

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
        return await self._lock_manager.with_session_lock(
            session_id=session_id,
            operation=operation,
            func=func,
            acquire_timeout=acquire_timeout,
            lock_ttl=lock_ttl,
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
        # Phase 3: Compute hash for owner API key (plaintext never stored)
        owner_api_key_hash = hash_api_key(owner_api_key) if owner_api_key else None
        session = Session(
            id=session_id,
            model=model,
            status="active",
            total_turns=0,
            total_cost_usd=None,
            parent_session_id=parent_session_id,
            owner_api_key_hash=owner_api_key_hash,
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
            except IntegrityError as e:
                logger.error(
                    "session_already_exists",
                    session_id=session_id,
                    error_id="ERR_SESSION_ALREADY_EXISTS",
                    exc_info=True,
                )
                raise APIError(
                    message="Session already exists",
                    code="ALREADY_EXISTS",
                    status_code=409,
                ) from e
            except OperationalError as e:
                logger.error(
                    "database_unavailable_during_session_create",
                    session_id=session_id,
                    error_id="ERR_DB_UNAVAILABLE",
                    exc_info=True,
                )
                raise APIError(
                    message="Database temporarily unavailable",
                    code="DATABASE_UNAVAILABLE",
                    status_code=503,
                ) from e
            except Exception as e:
                logger.error(
                    "Failed to create session in database",
                    session_id=session_id,
                    error=str(e),
                    error_id="ERR_SESSION_CREATE_FAILED",
                    exc_info=True,
                )
                raise APIError(
                    message="Failed to create session",
                    code="INTERNAL_ERROR",
                    status_code=500,
                ) from e

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
        except (ConnectionError, TimeoutError) as e:
            logger.error(
                "redis_unavailable",
                error_id="ERR_REDIS_UNAVAILABLE",
                session_id=session_id,
                error=str(e),
                exc_info=True,
            )
            # Distributed sessions REQUIRE Redis - if cache is configured, it's a critical failure
            if self._cache is not None:
                raise APIError(
                    message="Session caching failed. Distributed sessions require Redis.",
                    code="CACHE_UNAVAILABLE",
                    status_code=503,
                ) from e
            # Single-instance (no cache configured) can tolerate this branch never executing
            logger.warning(
                "continuing_without_cache",
                mode="single-instance",
                session_id=session_id,
            )
        except Exception as e:
            # Other cache errors (serialization, etc.) are logged but non-fatal
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

        except OperationalError as e:
            logger.error(
                "database_operational_error",
                error_id="ERR_DB_OPERATIONAL",
                session_id=session_id,
                error=str(e),
                exc_info=True,
            )
            raise APIError(
                message="Database temporarily unavailable",
                code="DATABASE_UNAVAILABLE",
                status_code=503,
            ) from e
        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Failed to retrieve session from database",
                session_id=session_id,
                error=str(e),
                error_id="ERR_SESSION_GET_FAILED",
                exc_info=True,
            )
            raise APIError(
                message="Failed to retrieve session",
                code="INTERNAL_ERROR",
                status_code=500,
            ) from e

    async def list_sessions(
        self,
        page: int = 1,
        page_size: int = 20,
        current_api_key: str | None = None,
        mode: str | None = None,
        project_id: str | None = None,
        tags: list[str] | None = None,
        search: str | None = None,
    ) -> SessionListResult:
        """List sessions with pagination using bulk cache reads or DB repository.

        When current_api_key is provided and db_repo is available, uses efficient
        indexed DB query. Otherwise, falls back to cache scan.

        Args:
            page: Page number (1-indexed).
            page_size: Number of sessions per page.
            current_api_key: API key for ownership filtering.
                           If provided, only returns sessions owned by this key.
            mode: Filter by metadata mode.
            project_id: Filter by metadata project_id.
            tags: Filter by metadata tags (must contain all tags).
            search: Case-insensitive metadata title search.

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
                mode=mode,
                project_id=project_id,
                tags=tags,
                search=search,
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
            owner_api_key_hash = hash_api_key(current_api_key)
            cached_sessions = await self._cache_manager.list_sessions_for_owner(
                owner_api_key_hash
            )

        elif self._cache:
            # WARNING: Full cache scan path - should be avoided in production.
            # This path is only reached when no owner filter is provided AND
            # db_repo is not available. Prefer using indexed DB queries.
            logger.warning(
                "session_list_full_scan",
                msg="Using full cache scan - consider adding owner filter for efficiency",
            )
            cached_sessions = await self._cache_manager.list_all_sessions(max_keys=1000)

        # Sort by created_at descending
        cached_sessions.sort(key=lambda s: s.created_at, reverse=True)

        # Apply metadata filters for cache-backed listing paths
        filtered_sessions = [
            s
            for s in cached_sessions
            if self._matches_metadata_filters(s, mode, project_id, tags, search)
        ]

        # Calculate pagination
        total = len(filtered_sessions)
        start = (page - 1) * page_size
        end = start + page_size
        page_sessions = filtered_sessions[start:end]

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
            # Phase 3: Get hash directly (plaintext column no longer exists)
            owner_api_key_hash: str | None = None
            cached_session = await self._get_cached_session(session_id)
            if cached_session:
                owner_api_key_hash = cached_session.owner_api_key_hash
            elif self._db_repo:
                try:
                    db_session = await self._db_repo.get(UUID(session_id))
                except ValueError as e:
                    # Expected: malformed UUID string (e.g., user input)
                    logger.debug(
                        "invalid_uuid_format",
                        session_id=session_id,
                        error=str(e),
                    )
                    db_session = None
                except TypeError as e:
                    # Unexpected: wrong type passed (programming bug)
                    logger.error(
                        "uuid_type_error",
                        session_id=session_id,
                        session_id_type=type(session_id).__name__,
                        error=str(e),
                        error_id="ERR_UUID_TYPE_ERROR",
                        exc_info=True,
                    )
                    raise
                if db_session:
                    owner_api_key_hash = db_session.owner_api_key_hash

            result = await self._cache_manager.delete_session(
                session_id=session_id,
                owner_api_key_hash=owner_api_key_hash,
            )
            if result:
                # Delete from database as well to prevent zombie sessions
                # (cache-aside pattern would re-cache from DB on next access)
                if self._db_repo:
                    try:
                        await self._db_repo.delete_session(UUID(session_id))
                    except (ValueError, TypeError):
                        # UUID parsing already handled above; DB delete is best-effort
                        pass
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
        return await self._cache_manager.session_exists(session_id)

    async def promote_session(
        self,
        session_id: str,
        project_id: str,
        current_api_key: str,
    ) -> Session | None:
        """Promote a brainstorm session to code mode.

        Args:
            session_id: Session ID to promote.
            project_id: Project ID to associate with the promoted session.
            current_api_key: API key for ownership enforcement.

        Returns:
            Updated session or None if not found.

        Raises:
            SessionNotFoundError: If session not owned by current_api_key.
        """
        from uuid import UUID

        # Get session with ownership check
        session = await self.get_session(session_id, current_api_key=current_api_key)
        if not session:
            return None

        # Read metadata from DB source of truth to avoid overwriting existing fields
        metadata = await self._get_session_metadata_for_update(session_id)
        metadata.update({"mode": "code", "project_id": project_id})

        # Update in database
        if self._db_repo:
            updated = await self._db_repo.update_metadata(UUID(session_id), metadata)
            if updated is None:
                return None

            # Update cache
            await self._cache_session(self._map_db_to_service(updated))

            logger.info(
                "Session promoted to code mode",
                session_id=session_id,
                project_id=project_id,
            )

            return self._map_db_to_service(updated)

        return None

    async def update_tags(
        self,
        session_id: str,
        tags: list[str],
        current_api_key: str,
    ) -> Session | None:
        """Update session tags.

        Args:
            session_id: Session ID to update.
            tags: New tags to set.
            current_api_key: API key for ownership enforcement.

        Returns:
            Updated session or None if not found.

        Raises:
            SessionNotFoundError: If session not owned by current_api_key.
        """
        from uuid import UUID

        # Get session with ownership check
        session = await self.get_session(session_id, current_api_key=current_api_key)
        if not session:
            return None

        # Read metadata from DB source of truth to avoid overwriting existing fields
        metadata = await self._get_session_metadata_for_update(session_id)
        metadata["tags"] = tags

        # Update in database
        if self._db_repo:
            updated = await self._db_repo.update_metadata(UUID(session_id), metadata)
            if updated is None:
                return None

            # Update cache
            await self._cache_session(self._map_db_to_service(updated))

            logger.info(
                "Session tags updated",
                session_id=session_id,
                tags=tags,
            )

            return self._map_db_to_service(updated)

        return None

    async def _cache_session(self, session: Session) -> None:
        """Cache a session in Redis and update owner index.

        Args:
            session: Session to cache.
        """
        await self._cache_manager.cache_session(session)

    async def _get_cached_session(self, session_id: str) -> Session | None:
        """Get a session from cache.

        Args:
            session_id: Session ID to retrieve.

        Returns:
            Session if found in cache.
        """
        return await self._cache_manager.get_cached_session(session_id)

    def _map_db_to_service(self, db_session: "SessionModel") -> Session:
        """Map SQLAlchemy Session model to service Session dataclass.

        Args:
            db_session: SQLAlchemy Session model from database.

        Returns:
            Service-layer Session dataclass.
        """
        # Validate and cast status to Literal type
        status_raw = db_session.status
        status_val = parse_session_status(status_raw)

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
            owner_api_key_hash=db_session.owner_api_key_hash,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
            session_metadata=(
                dict(db_session.session_metadata)
                if db_session.session_metadata is not None
                else None
            ),
        )

    def _matches_metadata_filters(
        self,
        session: Session,
        mode: str | None,
        project_id: str | None,
        tags: list[str] | None,
        search: str | None,
    ) -> bool:
        """Check whether a session matches metadata filter constraints."""
        metadata = session.session_metadata or {}

        if mode is not None and metadata.get("mode") != mode:
            return False

        if project_id is not None and metadata.get("project_id") != project_id:
            return False

        if tags:
            metadata_tags_raw = metadata.get("tags")
            metadata_tags = (
                metadata_tags_raw
                if isinstance(metadata_tags_raw, list)
                and all(isinstance(tag, str) for tag in metadata_tags_raw)
                else []
            )
            if not set(tags).issubset(set(metadata_tags)):
                return False

        if search:
            title_raw = metadata.get("title")
            title = title_raw if isinstance(title_raw, str) else ""
            if search.lower() not in title.lower():
                return False

        return True

    async def _get_session_metadata_for_update(
        self,
        session_id: str,
    ) -> dict[str, JsonValue]:
        """Fetch existing metadata from DB for safe metadata merge updates."""
        return await self._metadata_manager.get_session_metadata_for_update(session_id)

    def _enforce_owner(
        self,
        session: Session,
        current_api_key: str | None,
    ) -> Session:
        """Enforce that the current API key owns the session using hash-based comparison.

        Args:
            session: Session to check ownership for.
            current_api_key: API key from the current request.

        Returns:
            Session if ownership check passes.

        Raises:
            SessionNotFoundError: If ownership check fails (logged with structured data).

        Security Model (fail closed):
            - No API key in request: allow access (anonymous/public session)
            - API key in request + session has hash: verify via hash comparison
            - API key in request + session lacks hash: DENY (cannot verify ownership)
        """
        if not current_api_key:
            # No API key in request - allow access (anonymous/public session)
            return session

        if not session.owner_api_key_hash:
            # SECURITY: Fail closed - request has API key but session lacks hash
            # Cannot verify ownership, so deny access to prevent bypass attacks
            # This handles cached sessions from before hashing was implemented
            logger.warning(
                "ownership_check_failed_missing_hash",
                session_id=session.id,
                has_session_hash=False,
                has_request_key=True,
            )
            raise SessionNotFoundError(session.id)

        # Hash the request API key and compare to stored hash
        request_hash = hash_api_key(current_api_key)

        # Constant-time comparison of hashes
        if not secrets.compare_digest(session.owner_api_key_hash, request_hash):
            logger.warning(
                "ownership_check_failed",
                session_id=session.id,
                has_session_hash=True,
                has_request_key=True,
            )
            raise SessionNotFoundError(session.id)

        return session
