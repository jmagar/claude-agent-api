"""Protocol interfaces for dependency injection."""

from typing import TYPE_CHECKING, Protocol, TypedDict, runtime_checkable
from uuid import UUID

from apps.api.types import JsonValue

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence

    from apps.api.models.session import Checkpoint, Session, SessionMessage
    from apps.api.schemas.openai.requests import ChatCompletionRequest
    from apps.api.schemas.openai.responses import (
        OpenAIChatCompletion,
        OpenAIModelInfo,
    )
    from apps.api.schemas.requests.query import QueryRequest
    from apps.api.schemas.responses import SingleQueryResponse
    from apps.api.services.agent import QueryResponseDict
    from apps.api.types import AgentMessage


class MemorySearchResult(TypedDict):
    """Result from memory search."""

    id: str
    memory: str
    score: float
    metadata: dict[str, JsonValue]


@runtime_checkable
class SessionRepository(Protocol):
    """Protocol for session persistence operations."""

    async def create(
        self,
        session_id: UUID,
        model: str,
        working_directory: str | None = None,
        parent_session_id: UUID | None = None,
        metadata: dict[str, object] | None = None,
        owner_api_key: str | None = None,
    ) -> "Session":
        """Create a new session record.

        Args:
            session_id: Unique session identifier.
            model: Claude model used for the session.
            working_directory: Working directory path.
            parent_session_id: Parent session ID for forks.
            metadata: Additional session metadata.
            owner_api_key: Owning API key for authorization checks.

        Returns:
            Created session.
        """
        ...

    async def get(self, session_id: UUID) -> "Session | None":
        """Get a session by ID.

        Args:
            session_id: Session identifier.

        Returns:
            Session or None if not found.
        """
        ...

    async def update(
        self,
        session_id: UUID,
        status: str | None = None,
        total_turns: int | None = None,
        total_cost_usd: float | None = None,
    ) -> "Session | None":
        """Update a session record.

        Args:
            session_id: Session identifier.
            status: New status value.
            total_turns: Updated turn count.
            total_cost_usd: Updated cost.

        Returns:
            Updated session or None if not found.
        """
        ...

    async def list_sessions(
        self,
        status: str | None = None,
        owner_api_key: str | None = None,
        limit: int = 50,
        offset: int = 0,
        *,
        filter_by_owner_or_public: bool = False,
    ) -> tuple["Sequence[Session]", int]:
        """List sessions with optional filtering.

        Args:
            status: Filter by status.
            owner_api_key: Filter by owner API key (exact match).
            limit: Maximum results.
            offset: Pagination offset.
            filter_by_owner_or_public: If True, returns sessions where
                owner_api_key is NULL (public) OR matches the provided key.
                This is the secure multi-tenant filter.

        Returns:
            Tuple of session list and total count.
        """
        ...

    async def add_message(
        self,
        session_id: UUID,
        message_type: str,
        content: dict[str, object],
    ) -> "SessionMessage":
        """Add a message to a session.

        Args:
            session_id: Session identifier.
            message_type: Type of message (user, assistant, system, result).
            content: Message content.

        Returns:
            Created message.
        """
        ...

    async def get_messages(
        self,
        session_id: UUID,
        limit: int | None = None,
    ) -> "Sequence[SessionMessage]":
        """Get messages for a session.

        Args:
            session_id: Session identifier.
            limit: Maximum messages to return.

        Returns:
            List of messages.
        """
        ...

    async def add_checkpoint(
        self,
        session_id: UUID,
        user_message_uuid: str,
        files_modified: list[str],
    ) -> "Checkpoint":
        """Add a checkpoint to a session.

        Args:
            session_id: Session identifier.
            user_message_uuid: UUID from user message.
            files_modified: List of modified file paths.

        Returns:
            Created checkpoint.
        """
        ...

    async def get_checkpoints(self, session_id: UUID) -> "Sequence[Checkpoint]":
        """Get checkpoints for a session.

        Args:
            session_id: Session identifier.

        Returns:
            List of checkpoints.
        """
        ...


@runtime_checkable
class Cache(Protocol):
    """Protocol for caching operations."""

    async def get(self, key: str) -> str | None:
        """Get a value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None.
        """
        ...

    async def cache_set(self, key: str, value: str, ttl: int | None = None) -> bool:
        """Set a value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds.

        Returns:
            True if successful.
        """
        ...

    async def delete(self, key: str) -> bool:
        """Delete a value from cache.

        Args:
            key: Cache key.

        Returns:
            True if deleted.
        """
        ...

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key.

        Returns:
            True if exists.
        """
        ...

    async def add_to_set(self, key: str, value: str) -> bool:
        """Add value to a set.

        Args:
            key: Set key.
            value: Value to add.

        Returns:
            True if added.
        """
        ...

    async def remove_from_set(self, key: str, value: str) -> bool:
        """Remove value from a set.

        Args:
            key: Set key.
            value: Value to remove.

        Returns:
            True if removed.
        """
        ...

    async def set_members(self, key: str) -> set[str]:
        """Get all members of a set.

        Args:
            key: Set key.

        Returns:
            Set of values.
        """
        ...

    async def acquire_lock(
        self, key: str, ttl: int = 300, value: str | None = None
    ) -> str | None:
        """Acquire a distributed lock.

        Args:
            key: Lock key.
            ttl: Lock TTL in seconds.
            value: Lock value for ownership. Generated if None.

        Returns:
            Lock value if acquired, None otherwise.
        """
        ...

    async def release_lock(self, key: str, value: str) -> bool:
        """Release a distributed lock.

        Args:
            key: Lock key.
            value: Lock value for ownership verification.

        Returns:
            True if released.
        """
        ...

    async def ping(self) -> bool:
        """Check cache connectivity.

        Returns:
            True if connected.
        """
        ...

    async def scan_keys(self, pattern: str, max_keys: int = 1000) -> list[str]:
        """Scan for keys matching pattern.

        DEPRECATED: Only use for scoped patterns (e.g., 'run:{thread_id}:*').
        NEVER use for unbounded patterns (e.g., 'session:*' without scope).

        WARNING: O(N) operation that scans entire Redis keyspace. Dangerous in
        production with many keys. Prefer indexed lookups (e.g., owner index sets).

        Args:
            pattern: Redis SCAN pattern. MUST be scoped to bounded entity.
            max_keys: Safety limit (default: 1000, max: 10000).

        Returns:
            List of matching keys (up to max_keys).
        """
        ...

    async def clear(self) -> bool:
        """Clear all cached entries.

        Returns:
            True if the cache was cleared.
        """
        ...

    async def get_json(self, key: str) -> dict[str, "JsonValue"] | None:
        """Get a JSON value from cache.

        Args:
            key: Cache key.

        Returns:
            Parsed JSON dict or None.
        """
        ...

    async def get_many_json(
        self, keys: list[str]
    ) -> list[dict[str, "JsonValue"] | None]:
        """Get multiple JSON values from cache.

        Args:
            keys: List of cache keys.

        Returns:
            List of parsed JSON dicts aligned with keys order (None for missing/invalid keys).
        """
        ...

    async def set_json(
        self,
        key: str,
        value: dict[str, "JsonValue"],
        ttl: int | None = None,
    ) -> bool:
        """Set a JSON value in cache.

        Args:
            key: Cache key.
            value: Dict to cache as JSON.
            ttl: Time to live in seconds.

        Returns:
            True if successful.
        """
        ...


@runtime_checkable
class ModelMapper(Protocol):
    """Protocol for Claude model mapping."""

    def to_claude(self, model: str) -> str:
        """Get Claude CLI model identifier from any model name."""
        ...

    def to_full_name(self, model: str) -> str:
        """Get full model name from any model identifier."""
        ...

    def list_models(self) -> list["OpenAIModelInfo"]:
        """List available Claude models."""
        ...

    def get_model_info(self, model: str) -> "OpenAIModelInfo":
        """Get model info for a specific model."""
        ...


@runtime_checkable
class RequestTranslator(Protocol):
    """Protocol for OpenAI request translation."""

    def translate(
        self, request: "ChatCompletionRequest", permission_mode: str | None = None
    ) -> "QueryRequest":
        """Translate OpenAI request to Claude query request."""
        ...


@runtime_checkable
class ResponseTranslator(Protocol):
    """Protocol for OpenAI response translation."""

    def translate(
        self, response: "SingleQueryResponse", original_model: str
    ) -> "OpenAIChatCompletion":
        """Translate Claude response to OpenAI response."""
        ...


@runtime_checkable
class AgentService(Protocol):
    """Protocol for agent service used by routes."""

    async def query_stream(
        self, request: "QueryRequest", api_key: str = ""
    ) -> "AsyncIterator[dict[str, str]]":
        """Stream a query to the agent."""
        ...

    async def query_single(
        self, request: "QueryRequest", api_key: str = ""
    ) -> "QueryResponseDict":
        """Execute a query and return the full response."""
        ...


@runtime_checkable
class AgentClient(Protocol):
    """Protocol for Claude Agent SDK client operations."""

    async def query(
        self,
        prompt: str,
        session_id: str | None = None,
        options: dict[str, object] | None = None,
    ) -> "AsyncIterator[AgentMessage]":
        """Send a query to the agent.

        Args:
            prompt: User prompt.
            session_id: Optional session ID for resume.
            options: Additional options.

        Yields:
            Agent messages.
        """
        ...

    async def interrupt(self, session_id: str) -> bool:
        """Interrupt a running query.

        Args:
            session_id: Session to interrupt.

        Returns:
            True if interrupted.
        """
        ...

    async def rewind_files(self, user_message_uuid: str) -> bool:
        """Rewind files to a checkpoint.

        Args:
            user_message_uuid: Checkpoint UUID.

        Returns:
            True if successful.
        """
        ...


@runtime_checkable
class MemoryProtocol(Protocol):
    """Protocol for memory operations."""

    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        enable_graph: bool = True,
    ) -> list[MemorySearchResult]:
        """Search memories for a user.

        Args:
            query: Search query string.
            user_id: User identifier for multi-tenant isolation.
            limit: Maximum results to return.
            enable_graph: Include graph context in search.

        Returns:
            List of memory search results.
        """
        ...

    async def add(
        self,
        messages: str,
        user_id: str,
        metadata: dict[str, JsonValue] | None = None,
        enable_graph: bool = True,
    ) -> list[dict[str, JsonValue]]:
        """Add memories from conversation.

        Args:
            messages: Content to extract memories from.
            user_id: User identifier for multi-tenant isolation.
            metadata: Optional metadata to attach to memories.
            enable_graph: Enable graph memory extraction.

        Returns:
            List of created memory records.
        """
        ...

    async def get_all(
        self,
        user_id: str,
    ) -> list[dict[str, JsonValue]]:
        """Get all memories for a user.

        Args:
            user_id: User identifier for multi-tenant isolation.

        Returns:
            List of all memories for the user.
        """
        ...

    async def delete(
        self,
        memory_id: str,
        user_id: str,
    ) -> None:
        """Delete a specific memory.

        Args:
            memory_id: Memory identifier to delete.
            user_id: User identifier for authorization.
        """
        ...

    async def delete_all(
        self,
        user_id: str,
    ) -> None:
        """Delete all memories for a user.

        Args:
            user_id: User identifier for authorization.
        """
        ...
