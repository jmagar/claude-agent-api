"""Service for managing OpenAI-compatible assistants.

This service implements a dual-storage architecture:
- PostgreSQL: Source of truth for assistant data (durability)
- Redis: Cache layer for performance (fast reads)

Follows the cache-aside pattern for read operations.
"""

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import (
    TYPE_CHECKING,
    NotRequired,
    Protocol,
    TypedDict,
    cast,
    runtime_checkable,
)

import structlog

from apps.api.config import get_settings
from apps.api.exceptions.assistant import AssistantNotFoundError
from apps.api.models.assistant import generate_assistant_id
from apps.api.types import JsonValue
from apps.api.utils.crypto import hash_api_key

if TYPE_CHECKING:
    from apps.api.protocols import Cache

logger = structlog.get_logger(__name__)


# =============================================================================
# Type Definitions
# =============================================================================


class DbAssistantDict(TypedDict):
    """Type definition for database assistant object."""

    id: str
    model: str
    created_at: datetime
    updated_at: datetime
    name: NotRequired[str | None]
    description: NotRequired[str | None]
    instructions: NotRequired[str | None]
    tools: NotRequired[list[dict[str, object]]]
    metadata_: NotRequired[dict[str, str] | None]
    owner_api_key_hash: NotRequired[str | None]
    temperature: NotRequired[float | None]
    top_p: NotRequired[float | None]
    response_format: NotRequired[dict[str, str] | None]


@runtime_checkable
class DbAssistant(Protocol):
    """Protocol for database assistant object returned from repository.

    Note: Uses metadata_ (trailing underscore) to avoid conflicts with Python's
    metadata attribute. The actual database column is named assistant_metadata
    following the {table_name}_metadata naming convention.
    """

    id: str
    model: str
    created_at: datetime
    updated_at: datetime
    name: str | None
    description: str | None
    instructions: str | None
    tools: list[dict[str, object]]
    metadata_: dict[str, str] | None
    owner_api_key_hash: str | None
    temperature: float | None
    top_p: float | None


# =============================================================================
# Repository Protocol
# =============================================================================


@runtime_checkable
class AssistantRepository(Protocol):
    """Protocol for assistant database repository."""

    async def create(
        self,
        assistant_id: str,
        model: str,
        name: str | None,
        description: str | None,
        instructions: str | None,
        tools: list[dict[str, object]],
        metadata: dict[str, str],
        owner_api_key: str | None,
        temperature: float | None = None,
        top_p: float | None = None,
    ) -> None:
        """Create assistant in database."""
        ...

    async def get(self, assistant_id: str) -> DbAssistant | None:
        """Get assistant by ID."""
        ...

    async def list_assistants(
        self,
        owner_api_key: str | None = None,
        limit: int = 20,
        offset: int = 0,
        order: str = "desc",
        after: str | None = None,
        before: str | None = None,
    ) -> tuple[list[DbAssistant], int]:
        """List assistants with pagination."""
        ...

    async def update(
        self,
        assistant_id: str,
        model: str | None = None,
        name: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        tools: list[dict[str, object]] | None = None,
        metadata: dict[str, str] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
    ) -> bool:
        """Update assistant. Returns True if updated."""
        ...

    async def delete(self, assistant_id: str) -> bool:
        """Delete assistant. Returns True if deleted."""
        ...


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class Assistant:
    """Assistant data model."""

    id: str
    model: str
    created_at: datetime
    updated_at: datetime
    name: str | None = None
    description: str | None = None
    instructions: str | None = None
    tools: list[dict[str, object]] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    owner_api_key_hash: str | None = None
    temperature: float | None = None
    top_p: float | None = None
    response_format: dict[str, str] | None = None


@dataclass
class AssistantListResult:
    """Result of listing assistants with pagination."""

    data: list[Assistant]
    first_id: str | None
    last_id: str | None
    has_more: bool


# =============================================================================
# Service
# =============================================================================


class AssistantService:
    """Service for managing OpenAI-compatible assistants."""

    def __init__(
        self,
        cache: "Cache | None" = None,
        db_repo: AssistantRepository | None = None,
    ) -> None:
        """Initialize assistant service.

        Args:
            cache: Cache instance implementing Cache protocol.
            db_repo: Optional AssistantRepository for PostgreSQL persistence.
        """
        self._cache = cache
        self._db_repo = db_repo
        settings = get_settings()
        self._ttl = settings.redis_session_ttl

    def _cache_key(self, assistant_id: str) -> str:
        """Generate cache key for an assistant."""
        return f"assistant:{assistant_id}"

    async def create_assistant(
        self,
        model: str,
        name: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        tools: list[dict[str, object]] | None = None,
        metadata: dict[str, str] | None = None,
        owner_api_key: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
    ) -> Assistant:
        """Create a new assistant.

        Args:
            model: Model to use (e.g., "gpt-4").
            name: Assistant name.
            description: Assistant description.
            instructions: System instructions.
            tools: List of tool configurations.
            metadata: Key-value metadata.
            owner_api_key: API key that owns this assistant.
                          If None, assistant is PUBLIC (accessible to all API keys).
            temperature: Sampling temperature.
            top_p: Nucleus sampling parameter.

        Security Notes:
            - Public assistants (owner_api_key=None) bypass ownership checks
            - NULL owner_api_key indicates a globally accessible assistant
            - Private assistants require matching API key for access
            - Ownership is enforced in get_assistant() via _enforce_owner()

        Multi-Tenant Isolation:
            - Public assistants visible to all tenants (owner_api_key=None)
            - Private assistants filtered by owner_api_key in list operations
            - Redis cache uses hashed owner index: assistant:owner:<hash>

        Returns:
            Created assistant.
        """
        assistant_id = generate_assistant_id()
        now = datetime.now(UTC)
        tools_list = tools if tools is not None else []
        metadata_dict = metadata if metadata is not None else {}

        # Phase 3: Hash the API key (plaintext is never stored)
        owner_api_key_hash = hash_api_key(owner_api_key) if owner_api_key else None

        assistant = Assistant(
            id=assistant_id,
            model=model,
            name=name,
            description=description,
            instructions=instructions,
            tools=tools_list,
            metadata=metadata_dict,
            owner_api_key_hash=owner_api_key_hash,
            temperature=temperature,
            top_p=top_p,
            created_at=now,
            updated_at=now,
        )

        # Write to PostgreSQL first (source of truth)
        if self._db_repo:
            try:
                await self._db_repo.create(
                    assistant_id=assistant_id,
                    model=model,
                    name=name,
                    description=description,
                    instructions=instructions,
                    tools=tools_list,
                    metadata=metadata_dict,
                    owner_api_key=owner_api_key,  # Repository hashes internally
                    temperature=temperature,
                    top_p=top_p,
                )
                logger.info(
                    "Assistant created in database",
                    assistant_id=assistant_id,
                    model=model,
                )
            except Exception as e:
                logger.error(
                    "Failed to create assistant in database",
                    assistant_id=assistant_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

        # Write to cache (best-effort)
        try:
            await self._cache_assistant(assistant)
            logger.info(
                "Assistant cached in Redis",
                assistant_id=assistant_id,
            )
        except Exception as e:
            logger.warning(
                "Failed to cache assistant (continuing)",
                assistant_id=assistant_id,
                error=str(e),
            )

        return assistant

    async def get_assistant(
        self,
        assistant_id: str,
        current_api_key: str | None = None,
    ) -> Assistant | None:
        """Get assistant by ID.

        Args:
            assistant_id: The assistant ID.
            current_api_key: API key for ownership enforcement.

        Returns:
            Assistant if found, None otherwise.
        """
        # Try cache first
        cached = await self._get_cached_assistant(assistant_id)
        if cached:
            logger.debug(
                "Assistant retrieved from cache",
                assistant_id=assistant_id,
            )
            return self._enforce_owner(cached, current_api_key)

        # Fall back to database
        if not self._db_repo:
            return None

        try:
            db_assistant = await self._db_repo.get(assistant_id)
            if not db_assistant:
                return None

            assistant = self._map_db_to_service(db_assistant)
            assistant = self._enforce_owner(assistant, current_api_key)

            # Re-cache
            await self._cache_assistant(assistant)

            logger.info(
                "Assistant retrieved from database and re-cached",
                assistant_id=assistant_id,
            )

            return assistant

        except Exception as e:
            logger.error(
                "Failed to retrieve assistant from database",
                assistant_id=assistant_id,
                error=str(e),
                exc_info=True,
            )
            return None

    async def list_assistants(
        self,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
        before: str | None = None,
        owner_api_key: str | None = None,
    ) -> AssistantListResult:
        """List assistants with pagination.

        Args:
            limit: Maximum number of results.
            order: Sort order ("asc" or "desc").
            after: Cursor for pagination (return items after this ID).
            before: Cursor for pagination (return items before this ID).
            owner_api_key: Filter by owner API key.

        Returns:
            Paginated assistant list.
        """
        if not self._db_repo:
            return AssistantListResult(
                data=[],
                first_id=None,
                last_id=None,
                has_more=False,
            )

        try:
            db_assistants, _total = await self._db_repo.list_assistants(
                owner_api_key=owner_api_key,
                limit=limit + 1,  # Fetch one extra to detect has_more
                offset=0,
                order=order,
                after=after,
                before=before,
            )

            # Check if there are more results
            has_more = len(db_assistants) > limit
            if has_more:
                db_assistants = db_assistants[:limit]

            assistants = [self._map_db_to_service(a) for a in db_assistants]

            return AssistantListResult(
                data=assistants,
                first_id=assistants[0].id if assistants else None,
                last_id=assistants[-1].id if assistants else None,
                has_more=has_more,
            )

        except Exception as e:
            logger.error(
                "Failed to list assistants",
                error=str(e),
                exc_info=True,
            )
            return AssistantListResult(
                data=[],
                first_id=None,
                last_id=None,
                has_more=False,
            )

    async def update_assistant(
        self,
        assistant_id: str,
        model: str | None = None,
        name: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        tools: list[dict[str, object]] | None = None,
        metadata: dict[str, str] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        current_api_key: str | None = None,
    ) -> Assistant | None:
        """Update an assistant.

        Args:
            assistant_id: Assistant ID to update.
            model: New model.
            name: New name.
            description: New description.
            instructions: New instructions.
            tools: New tools.
            metadata: New metadata.
            temperature: New temperature.
            top_p: New top_p.
            current_api_key: API key for ownership enforcement.

        Returns:
            Updated assistant or None if not found.
        """
        # Get existing assistant
        assistant = await self.get_assistant(assistant_id, current_api_key)
        if not assistant:
            return None

        # Apply updates
        if model is not None:
            assistant.model = model
        if name is not None:
            assistant.name = name
        if description is not None:
            assistant.description = description
        if instructions is not None:
            assistant.instructions = instructions
        if tools is not None:
            assistant.tools = tools
        if metadata is not None:
            assistant.metadata = metadata
        if temperature is not None:
            assistant.temperature = temperature
        if top_p is not None:
            assistant.top_p = top_p

        assistant.updated_at = datetime.now(UTC)

        # Update database
        if self._db_repo:
            await self._db_repo.update(
                assistant_id=assistant_id,
                model=model,
                name=name,
                description=description,
                instructions=instructions,
                tools=tools,
                metadata=metadata,
                temperature=temperature,
                top_p=top_p,
            )

        # Update cache
        await self._cache_assistant(assistant)

        logger.info(
            "Assistant updated",
            assistant_id=assistant_id,
        )

        return assistant

    async def delete_assistant(
        self,
        assistant_id: str,
        _current_api_key: str | None = None,
    ) -> bool:
        """Delete an assistant.

        Args:
            assistant_id: Assistant ID to delete.
            _current_api_key: API key for ownership enforcement.

        Returns:
            True if deleted, False if not found.
        """
        # Get assistant to extract owner_api_key before deletion
        assistant = await self.get_assistant(assistant_id, _current_api_key)

        # Delete from database first
        if self._db_repo:
            deleted = await self._db_repo.delete(assistant_id)
            if not deleted:
                return False

        # Delete from cache
        if self._cache:
            key = self._cache_key(assistant_id)
            await self._cache.delete(key)

            # Phase 3: Remove from owner index using hash directly
            if assistant and assistant.owner_api_key_hash:
                owner_index_key = f"assistant:owner:{assistant.owner_api_key_hash}"
                await self._cache.remove_from_set(owner_index_key, assistant_id)

        logger.info("Assistant deleted", assistant_id=assistant_id)
        return True

    async def _cache_assistant(self, assistant: Assistant) -> None:
        """Cache an assistant in Redis."""
        if not self._cache:
            return

        key = self._cache_key(assistant.id)
        # Build data dict - tools and metadata need to be cast for JsonValue compatibility
        tools_json: list[JsonValue] = cast("list[JsonValue]", assistant.tools)
        metadata_json: dict[str, JsonValue] = cast(
            "dict[str, JsonValue]", assistant.metadata
        )
        data: dict[str, JsonValue] = {
            "id": assistant.id,
            "model": assistant.model,
            "name": assistant.name,
            "description": assistant.description,
            "instructions": assistant.instructions,
            "tools": tools_json,
            "metadata": metadata_json,
            "owner_api_key_hash": assistant.owner_api_key_hash,
            "temperature": assistant.temperature,
            "top_p": assistant.top_p,
            "created_at": assistant.created_at.isoformat(),
            "updated_at": assistant.updated_at.isoformat(),
        }

        await self._cache.set_json(key, data, self._ttl)

        # Phase 3: Add to owner index using hash directly
        if assistant.owner_api_key_hash:
            owner_index_key = f"assistant:owner:{assistant.owner_api_key_hash}"
            await self._cache.add_to_set(owner_index_key, assistant.id)

    async def _get_cached_assistant(self, assistant_id: str) -> Assistant | None:
        """Get an assistant from cache."""
        if not self._cache:
            return None

        key = self._cache_key(assistant_id)
        parsed = await self._cache.get_json(key)

        if not parsed:
            return None

        return self._parse_cached_assistant(parsed)

    def _parse_cached_assistant(
        self,
        parsed: dict[str, JsonValue],
    ) -> Assistant | None:
        """Parse cached assistant data into Assistant object."""
        try:
            # Extract timestamps
            created_at_str = str(parsed.get("created_at", ""))
            updated_at_str = str(parsed.get("updated_at", ""))

            created_at = datetime.fromisoformat(created_at_str)
            updated_at = datetime.fromisoformat(updated_at_str)

            # Normalize to naive (remove timezone info)
            if created_at.tzinfo is not None:
                created_at = created_at.replace(tzinfo=None)
            if updated_at.tzinfo is not None:
                updated_at = updated_at.replace(tzinfo=None)

            # Extract tools and metadata with proper typing
            tools_raw = parsed.get("tools", [])
            tools: list[dict[str, object]] = []
            if isinstance(tools_raw, list):
                for tool in tools_raw:
                    if isinstance(tool, dict):
                        # Cast dict[str, JsonValue] to dict[str, object]
                        tools.append(dict(tool))

            metadata_raw = parsed.get("metadata", {})
            metadata: dict[str, str] = {}
            if isinstance(metadata_raw, dict):
                for k, v in metadata_raw.items():
                    if isinstance(k, str) and isinstance(v, str):
                        metadata[k] = v

            return Assistant(
                id=str(parsed["id"]),
                model=str(parsed["model"]),
                name=str(parsed["name"]) if parsed.get("name") else None,
                description=str(parsed["description"])
                if parsed.get("description")
                else None,
                instructions=str(parsed["instructions"])
                if parsed.get("instructions")
                else None,
                tools=tools,
                metadata=metadata,
                owner_api_key_hash=str(parsed["owner_api_key_hash"])
                if parsed.get("owner_api_key_hash")
                else None,
                temperature=float(str(parsed["temperature"]))
                if parsed.get("temperature")
                else None,
                top_p=float(str(parsed["top_p"])) if parsed.get("top_p") else None,
                created_at=created_at,
                updated_at=updated_at,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(
                "Failed to parse cached assistant",
                error=str(e),
            )
            return None

    def _map_db_to_service(self, db_assistant: DbAssistant) -> Assistant:
        """Map database assistant to service assistant."""
        return Assistant(
            id=db_assistant.id,
            model=db_assistant.model,
            name=db_assistant.name,
            description=db_assistant.description,
            instructions=db_assistant.instructions,
            tools=db_assistant.tools,
            metadata=db_assistant.metadata_ or {},
            owner_api_key_hash=db_assistant.owner_api_key_hash,
            temperature=db_assistant.temperature,
            top_p=db_assistant.top_p,
            created_at=db_assistant.created_at,
            updated_at=db_assistant.updated_at,
        )

    def _enforce_owner(
        self,
        assistant: Assistant,
        current_api_key: str | None,
    ) -> Assistant:
        """Enforce that the current API key owns the assistant.

        Args:
            assistant: The assistant to check ownership for.
            current_api_key: The API key from the request (plaintext).

        Returns:
            The assistant if ownership check passes.

        Raises:
            AssistantNotFoundError: If ownership check fails.

        Phase 3:
            Uses hash-based comparison for security.
        """
        if current_api_key and assistant.owner_api_key_hash:
            # Phase 3: Hash the incoming key and compare to stored hash
            request_hash = hash_api_key(current_api_key)
            if not secrets.compare_digest(assistant.owner_api_key_hash, request_hash):
                raise AssistantNotFoundError(assistant.id)
        return assistant
