"""Protocol interfaces for dependency injection."""

from typing import TYPE_CHECKING, Protocol, runtime_checkable
from uuid import UUID

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from apps.api.schemas.openai.requests import ChatCompletionRequest
    from apps.api.schemas.openai.responses import (
        OpenAIChatCompletion,
        OpenAIModelInfo,
    )
    from apps.api.schemas.requests.query import QueryRequest
    from apps.api.schemas.responses import SingleQueryResponse
    from apps.api.services.agent import QueryResponseDict
    from apps.api.types import (
        AgentMessage,
        CheckpointData,
        JsonValue,
        MessageData,
        SessionData,
    )


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
    ) -> "SessionData":
        """Create a new session record.

        Args:
            session_id: Unique session identifier.
            model: Claude model used for the session.
            working_directory: Working directory path.
            parent_session_id: Parent session ID for forks.
            metadata: Additional session metadata.

        Returns:
            Created session data.
        """
        ...

    async def get(self, session_id: UUID) -> "SessionData | None":
        """Get a session by ID.

        Args:
            session_id: Session identifier.

        Returns:
            Session data or None if not found.
        """
        ...

    async def update(
        self,
        session_id: UUID,
        status: str | None = None,
        total_turns: int | None = None,
        total_cost_usd: float | None = None,
    ) -> "SessionData | None":
        """Update a session record.

        Args:
            session_id: Session identifier.
            status: New status value.
            total_turns: Updated turn count.
            total_cost_usd: Updated cost.

        Returns:
            Updated session data or None if not found.
        """
        ...

    async def list_sessions(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list["SessionData"], int]:
        """List sessions with optional filtering.

        Args:
            status: Filter by status.
            limit: Maximum results.
            offset: Pagination offset.

        Returns:
            Tuple of session list and total count.
        """
        ...

    async def add_message(
        self,
        session_id: UUID,
        message_type: str,
        content: dict[str, object],
    ) -> "MessageData":
        """Add a message to a session.

        Args:
            session_id: Session identifier.
            message_type: Type of message (user, assistant, system, result).
            content: Message content.

        Returns:
            Created message data.
        """
        ...

    async def get_messages(
        self,
        session_id: UUID,
        limit: int | None = None,
    ) -> list["MessageData"]:
        """Get messages for a session.

        Args:
            session_id: Session identifier.
            limit: Maximum messages to return.

        Returns:
            List of message data.
        """
        ...

    async def add_checkpoint(
        self,
        session_id: UUID,
        user_message_uuid: str,
        files_modified: list[str],
    ) -> "CheckpointData":
        """Add a checkpoint to a session.

        Args:
            session_id: Session identifier.
            user_message_uuid: UUID from user message.
            files_modified: List of modified file paths.

        Returns:
            Created checkpoint data.
        """
        ...

    async def get_checkpoints(self, session_id: UUID) -> list["CheckpointData"]:
        """Get checkpoints for a session.

        Args:
            session_id: Session identifier.

        Returns:
            List of checkpoint data.
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

    async def scan_keys(self, pattern: str) -> list[str]:
        """Scan for keys matching pattern.

        Args:
            pattern: Glob-style pattern (e.g., 'session:*').

        Returns:
            List of matching keys.
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

    def translate(self, request: "ChatCompletionRequest") -> "QueryRequest":
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
