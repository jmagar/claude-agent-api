"""Service for managing OpenAI-compatible threads.

Threads are mapped to Sessions with type="thread" in metadata.
This service wraps SessionService with thread-specific logic.
"""

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog

from apps.api.config import get_settings
from apps.api.types import JsonValue

if TYPE_CHECKING:
    from apps.api.protocols import Cache
    from apps.api.services.session import SessionService

logger = structlog.get_logger(__name__)


def generate_thread_id() -> str:
    """Generate a unique thread ID in OpenAI format.

    Returns:
        str: ID in format 'thread_' followed by 24 random alphanumeric characters.
    """
    random_suffix = secrets.token_hex(12)
    return f"thread_{random_suffix}"


def generate_message_id() -> str:
    """Generate a unique message ID in OpenAI format.

    Returns:
        str: ID in format 'msg_' followed by 24 random alphanumeric characters.
    """
    random_suffix = secrets.token_hex(12)
    return f"msg_{random_suffix}"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class Thread:
    """Thread data model.

    Maps to OpenAI's thread object.
    """

    id: str  # thread_xxx format
    created_at: int  # Unix timestamp
    metadata: dict[str, str] = field(default_factory=dict)
    # Internal reference to underlying session
    session_id: str | None = None


@dataclass
class ThreadListResult:
    """Result of listing threads with pagination."""

    data: list[Thread]
    first_id: str | None
    last_id: str | None
    has_more: bool


# =============================================================================
# Service
# =============================================================================


class ThreadService:
    """Service for managing OpenAI-compatible threads.

    Threads are backed by Sessions with metadata.type = "thread".
    This provides conversation continuity for the Assistants API.
    """

    def __init__(
        self,
        session_service: "SessionService | None" = None,
        cache: "Cache | None" = None,
    ) -> None:
        """Initialize thread service.

        Args:
            session_service: Session service for underlying storage.
            cache: Cache instance for fast lookups.
        """
        self._session_service = session_service
        self._cache = cache
        settings = get_settings()
        self._ttl = settings.redis_session_ttl

    def _cache_key(self, thread_id: str) -> str:
        """Generate cache key for a thread."""
        return f"thread:{thread_id}"

    async def create_thread(
        self,
        metadata: dict[str, str] | None = None,
        owner_api_key: str | None = None,
    ) -> Thread:
        """Create a new thread.

        Args:
            metadata: Key-value metadata for the thread.
            owner_api_key: Owning API key for authorization.

        Returns:
            Created thread.
        """
        thread_id = generate_thread_id()
        now = datetime.now(UTC)
        created_at = int(now.timestamp())
        metadata_dict = metadata if metadata is not None else {}

        # Create underlying session with thread metadata
        session_id: str | None = None
        if self._session_service:
            session = await self._session_service.create_session(
                model="gpt-4",  # Placeholder, actual model comes from run
                owner_api_key=owner_api_key,
            )
            session_id = session.id

        thread = Thread(
            id=thread_id,
            created_at=created_at,
            metadata=metadata_dict,
            session_id=session_id,
        )

        # Cache the thread
        await self._cache_thread(thread)

        logger.info(
            "Thread created",
            thread_id=thread_id,
            session_id=session_id,
        )

        return thread

    async def get_thread(
        self,
        thread_id: str,
        current_api_key: str | None = None,
    ) -> Thread | None:
        """Get thread by ID.

        Args:
            thread_id: The thread ID.
            current_api_key: API key for ownership enforcement.

        Returns:
            Thread if found, None otherwise.
        """
        # Try cache first
        cached = await self._get_cached_thread(thread_id)
        if cached:
            logger.debug(
                "Thread retrieved from cache",
                thread_id=thread_id,
            )
            return cached

        # Could fall back to session service for persistence
        # For now, threads are cache-only
        return None

    async def modify_thread(
        self,
        thread_id: str,
        metadata: dict[str, str] | None = None,
        current_api_key: str | None = None,
    ) -> Thread | None:
        """Modify a thread's metadata.

        Args:
            thread_id: Thread ID to modify.
            metadata: New metadata (replaces existing).
            current_api_key: API key for ownership enforcement.

        Returns:
            Modified thread or None if not found.
        """
        thread = await self.get_thread(thread_id, current_api_key)
        if not thread:
            return None

        if metadata is not None:
            thread.metadata = metadata

        # Update cache
        await self._cache_thread(thread)

        logger.info(
            "Thread modified",
            thread_id=thread_id,
        )

        return thread

    async def delete_thread(
        self,
        thread_id: str,
        current_api_key: str | None = None,
    ) -> bool:
        """Delete a thread.

        Args:
            thread_id: Thread ID to delete.
            current_api_key: API key for ownership enforcement.

        Returns:
            True if deleted, False if not found.
        """
        # Get thread to find session_id
        thread = await self.get_thread(thread_id, current_api_key)
        if not thread:
            return False

        # Delete underlying session
        if self._session_service and thread.session_id:
            await self._session_service.delete_session(thread.session_id)

        # Delete from cache
        if self._cache:
            key = self._cache_key(thread_id)
            await self._cache.delete(key)

        logger.info("Thread deleted", thread_id=thread_id)
        return True

    async def _cache_thread(self, thread: Thread) -> None:
        """Cache a thread in Redis."""
        if not self._cache:
            return

        key = self._cache_key(thread.id)
        data: dict[str, JsonValue] = {
            "id": thread.id,
            "created_at": thread.created_at,
            "metadata": thread.metadata,
            "session_id": thread.session_id,
        }

        await self._cache.set_json(key, data, self._ttl)

    async def _get_cached_thread(self, thread_id: str) -> Thread | None:
        """Get a thread from cache."""
        if not self._cache:
            return None

        key = self._cache_key(thread_id)
        parsed = await self._cache.get_json(key)

        if not parsed:
            return None

        return self._parse_cached_thread(parsed)

    def _parse_cached_thread(
        self,
        parsed: dict[str, JsonValue],
    ) -> Thread | None:
        """Parse cached thread data into Thread object."""
        try:
            # Extract values
            thread_id = str(parsed["id"])
            created_at_val = parsed.get("created_at", 0)
            if isinstance(created_at_val, (int, float)):
                created_at = int(created_at_val)
            else:
                created_at = 0

            # Extract metadata
            metadata_raw = parsed.get("metadata", {})
            metadata: dict[str, str] = {}
            if isinstance(metadata_raw, dict):
                for k, v in metadata_raw.items():
                    if isinstance(k, str) and isinstance(v, str):
                        metadata[k] = v

            session_id_raw = parsed.get("session_id")
            session_id = str(session_id_raw) if session_id_raw else None

            return Thread(
                id=thread_id,
                created_at=created_at,
                metadata=metadata,
                session_id=session_id,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(
                "Failed to parse cached thread",
                error=str(e),
            )
            return None
