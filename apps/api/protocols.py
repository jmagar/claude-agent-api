"""Protocol interfaces for dependency injection."""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Literal, Protocol, TypedDict, runtime_checkable
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
    from apps.api.services.commands import CommandsService
    from apps.api.services.memory import MemoryService
    from apps.api.types import AgentMessage


class MemorySearchResult(TypedDict):
    """Result from memory search."""

    id: str
    memory: str
    score: float
    metadata: dict[str, JsonValue]


class AgentRecord(TypedDict):
    """Agent configuration record."""

    id: str
    name: str
    description: str
    prompt: str
    tools: list[str] | None
    model: str | None
    created_at: str
    updated_at: str | None
    is_shared: bool | None
    share_url: str | None
    share_token: str | None


class ProjectRecord(TypedDict):
    """Project record."""

    id: str
    name: str
    path: str
    created_at: str
    last_accessed_at: str | None
    session_count: int | None
    metadata: dict[str, JsonValue] | None


class ToolPresetRecord(TypedDict):
    """Tool preset record."""

    id: str
    name: str
    description: str | None
    allowed_tools: list[str]
    disallowed_tools: list[str]
    is_system: bool
    created_at: str


class SlashCommandRecord(TypedDict):
    """Slash command record."""

    id: str
    name: str
    description: str
    content: str
    enabled: bool
    created_at: str
    updated_at: str | None


class SkillRecord(TypedDict):
    """Skill record."""

    id: str
    name: str
    description: str
    content: str
    enabled: bool
    created_at: str
    updated_at: str | None
    is_shared: bool | None
    share_url: str | None


class McpServerRecord(TypedDict):
    """MCP server configuration record."""

    id: str
    name: str
    transport_type: str
    command: str | None
    args: list[str] | None
    url: str | None
    headers: dict[str, str] | None
    env: dict[str, str] | None
    enabled: bool
    status: str
    error: str | None
    created_at: str
    updated_at: str | None
    metadata: dict[str, JsonValue] | None
    resources: list[dict[str, JsonValue]] | None


class McpServerInfo(TypedDict, total=False):
    """MCP server configuration from filesystem discovery."""

    name: str
    type: str
    command: str | None
    args: list[str]
    url: str | None
    headers: dict[str, str]
    env: dict[str, str]


@runtime_checkable
class SessionRepositoryProtocol(Protocol):
    """Protocol for session persistence operations."""

    async def create(
        self,
        session_id: UUID,
        model: str,
        working_directory: str | None = None,
        parent_session_id: UUID | None = None,
        metadata: dict[str, JsonValue] | None = None,
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
        content: dict[str, JsonValue],
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
    ) -> "AsyncGenerator[dict[str, str], None]":
        """Stream a query to the agent."""
        ...

    async def query_single(
        self, request: "QueryRequest", api_key: str = ""
    ) -> "QueryResponseDict":
        """Execute a query and return the full response."""
        ...

    async def submit_answer(self, session_id: str, answer: str) -> bool:
        """Submit an answer to a pending question.

        Args:
            session_id: Session ID to submit answer to.
            answer: User's answer to the question.

        Returns:
            True if answer was submitted successfully.
        """
        ...

    async def interrupt(self, session_id: str) -> bool:
        """Interrupt a running query.

        Args:
            session_id: Session ID to interrupt.

        Returns:
            True if interrupted successfully.
        """
        ...

    async def update_permission_mode(
        self,
        session_id: str,
        permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"],
    ) -> bool:
        """Update permission mode for an active session.

        Args:
            session_id: Session to update.
            permission_mode: New permission mode.

        Returns:
            True if updated successfully.
        """
        ...


@runtime_checkable
class AgentClient(Protocol):
    """Protocol for Claude Agent SDK client operations."""

    async def query(
        self,
        prompt: str,
        session_id: str | None = None,
        options: dict[str, JsonValue] | None = None,
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


@runtime_checkable
class QueryRunner(Protocol):
    """Protocol for query runner implementations (stream/single)."""

    async def run(
        self,
        request: "QueryRequest",
        commands_service: "CommandsService",
        session_id_override: str | None = None,
        api_key: str = "",
        memory_service: "MemoryService | None" = None,
    ) -> object:
        """Execute query with optional parameters.

        Args:
            request: Query request to execute.
            commands_service: Commands service for slash command detection.
            session_id_override: Optional session ID override.
            api_key: API key for scoped configuration.
            memory_service: Optional memory service for context injection.

        Returns:
            Query result (type varies by implementation: AsyncIterator or dict).
        """
        ...


# --- CRUD Service Protocols (for DI Refactor) ---


@runtime_checkable
class AgentConfigProtocol(Protocol):
    """Protocol for agent CRUD operations.

    This protocol represents the CRUD service for agent configurations,
    distinct from the AgentService protocol which handles orchestration.
    """

    async def list_agents(self) -> list[AgentRecord]:
        """List all agents.

        Returns:
            List of agent records.
        """
        ...

    async def create_agent(
        self,
        name: str,
        description: str,
        prompt: str,
        tools: list[str] | None,
        model: str | None,
    ) -> AgentRecord:
        """Create a new agent.

        Args:
            name: Agent name.
            description: Agent description.
            prompt: System prompt.
            tools: Available tools list.
            model: Claude model identifier.

        Returns:
            Created agent record.
        """
        ...

    async def get_agent(self, agent_id: str) -> AgentRecord | None:
        """Get agent by ID.

        Args:
            agent_id: Agent identifier.

        Returns:
            Agent record or None if not found.
        """
        ...

    async def update_agent(
        self,
        agent_id: str,
        name: str,
        description: str,
        prompt: str,
        tools: list[str] | None,
        model: str | None,
    ) -> AgentRecord | None:
        """Update an agent.

        Args:
            agent_id: Agent identifier.
            name: Updated name.
            description: Updated description.
            prompt: Updated prompt.
            tools: Updated tools list.
            model: Updated model.

        Returns:
            Updated agent record or None if not found.
        """
        ...

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent.

        Args:
            agent_id: Agent identifier.

        Returns:
            True if deleted successfully.
        """
        ...

    async def share_agent(self, agent_id: str, share_url: str) -> AgentRecord | None:
        """Mark agent as shared and generate token.

        Args:
            agent_id: Agent identifier.
            share_url: Shareable URL.

        Returns:
            Updated agent record or None if not found.
        """
        ...


@runtime_checkable
class ProjectProtocol(Protocol):
    """Protocol for project CRUD operations."""

    async def list_projects(self) -> list[ProjectRecord]:
        """List all projects.

        Returns:
            List of project records.
        """
        ...

    async def create_project(
        self,
        name: str,
        path: str | None,
        metadata: dict[str, JsonValue] | None,
    ) -> ProjectRecord | None:
        """Create a new project.

        Args:
            name: Project name.
            path: Project path.
            metadata: Additional metadata.

        Returns:
            Created project record or None if duplicate.
        """
        ...

    async def get_project(self, project_id: str) -> ProjectRecord | None:
        """Get project by ID.

        Args:
            project_id: Project identifier.

        Returns:
            Project record or None if not found.
        """
        ...

    async def update_project(
        self,
        project_id: str,
        name: str | None,
        metadata: dict[str, JsonValue] | None,
    ) -> ProjectRecord | None:
        """Update a project.

        Args:
            project_id: Project identifier.
            name: Updated name.
            metadata: Updated metadata.

        Returns:
            Updated project record or None if not found.
        """
        ...

    async def delete_project(self, project_id: str) -> bool:
        """Delete a project.

        Args:
            project_id: Project identifier.

        Returns:
            True if deleted successfully.
        """
        ...


@runtime_checkable
class ToolPresetProtocol(Protocol):
    """Protocol for tool preset CRUD operations."""

    async def list_presets(self) -> list[ToolPresetRecord]:
        """List all tool presets.

        Returns:
            List of tool preset records.
        """
        ...

    async def create_preset(
        self,
        name: str,
        description: str | None,
        allowed_tools: list[str],
        disallowed_tools: list[str],
        is_system: bool = False,
    ) -> ToolPresetRecord:
        """Create a new tool preset.

        Args:
            name: Preset name.
            description: Preset description.
            allowed_tools: List of allowed tools.
            disallowed_tools: List of disallowed tools.
            is_system: Whether this is a system preset.

        Returns:
            Created tool preset record.
        """
        ...

    async def get_preset(self, preset_id: str) -> ToolPresetRecord | None:
        """Get tool preset by ID.

        Args:
            preset_id: Preset identifier.

        Returns:
            Tool preset record or None if not found.
        """
        ...

    async def update_preset(
        self,
        preset_id: str,
        name: str,
        description: str | None,
        allowed_tools: list[str],
        disallowed_tools: list[str],
    ) -> ToolPresetRecord | None:
        """Update a tool preset.

        Args:
            preset_id: Preset identifier.
            name: Updated name.
            description: Updated description.
            allowed_tools: Updated allowed tools.
            disallowed_tools: Updated disallowed tools.

        Returns:
            Updated tool preset record or None if not found.
        """
        ...

    async def delete_preset(self, preset_id: str) -> bool:
        """Delete a tool preset.

        Args:
            preset_id: Preset identifier.

        Returns:
            True if deleted successfully.
        """
        ...


@runtime_checkable
class McpServerConfigProtocol(Protocol):
    """Protocol for MCP server configuration operations."""

    async def list_servers_for_api_key(self, api_key: str) -> list[McpServerRecord]:
        """List all MCP servers for a specific API key.

        Args:
            api_key: API key for multi-tenant isolation.

        Returns:
            List of MCP server records.
        """
        ...

    async def get_server(self, api_key: str, name: str) -> McpServerRecord | None:
        """Get MCP server config by name for an API key.

        Args:
            api_key: API key for scoping.
            name: Server name.

        Returns:
            MCP server record or None if not found.
        """
        ...

    async def create_server(
        self,
        api_key: str,
        name: str,
        config: dict[str, JsonValue],
    ) -> McpServerRecord:
        """Create a new MCP server config.

        Args:
            api_key: API key for scoping.
            name: Server name.
            config: Server configuration.

        Returns:
            Created MCP server record.
        """
        ...

    async def update_server(
        self,
        api_key: str,
        name: str,
        config: dict[str, JsonValue],
    ) -> bool:
        """Update an MCP server config.

        Args:
            api_key: API key for scoping.
            name: Server name.
            config: Updated configuration.

        Returns:
            True if updated successfully.
        """
        ...

    async def delete_server(self, api_key: str, name: str) -> bool:
        """Delete an MCP server config.

        Args:
            api_key: API key for scoping.
            name: Server name.

        Returns:
            True if deleted successfully.
        """
        ...


@runtime_checkable
class McpDiscoveryProtocol(Protocol):
    """Protocol for MCP server filesystem discovery."""

    def discover_servers(self) -> dict[str, McpServerInfo]:
        """Discover MCP servers from filesystem configs.

        Returns:
            Dict mapping server name to server info.
        """
        ...

    def get_enabled_servers(
        self, disabled_servers: list[str] | None = None
    ) -> dict[str, McpServerInfo]:
        """Get enabled servers filtering out disabled ones.

        Args:
            disabled_servers: List of server names to exclude.

        Returns:
            Dict mapping server name to server info (enabled only).
        """
        ...


@runtime_checkable
class SkillsProtocol(Protocol):
    """Protocol for skill discovery operations."""

    def discover_skills(self) -> list[dict[str, str]]:
        """Discover skills from filesystem.

        Returns:
            List of skill info dictionaries.
        """
        ...


@runtime_checkable
class SlashCommandProtocol(Protocol):
    """Protocol for slash command CRUD operations."""

    async def list_commands(self) -> list[SlashCommandRecord]:
        """List all slash commands.

        Returns:
            List of slash command records.
        """
        ...

    async def create_command(
        self,
        name: str,
        description: str,
        content: str,
        enabled: bool,
    ) -> SlashCommandRecord:
        """Create a new slash command.

        Args:
            name: Command name.
            description: Command description.
            content: Command content.
            enabled: Whether command is enabled.

        Returns:
            Created slash command record.
        """
        ...

    async def get_command(self, command_id: str) -> SlashCommandRecord | None:
        """Get slash command by ID.

        Args:
            command_id: Command identifier.

        Returns:
            Slash command record or None if not found.
        """
        ...

    async def update_command(
        self,
        command_id: str,
        name: str,
        description: str,
        content: str,
        enabled: bool,
    ) -> SlashCommandRecord | None:
        """Update a slash command.

        Args:
            command_id: Command identifier.
            name: Updated name.
            description: Updated description.
            content: Updated content.
            enabled: Updated enabled status.

        Returns:
            Updated slash command record or None if not found.
        """
        ...

    async def delete_command(self, command_id: str) -> bool:
        """Delete a slash command.

        Args:
            command_id: Command identifier.

        Returns:
            True if deleted successfully.
        """
        ...


@runtime_checkable
class SkillCrudProtocol(Protocol):
    """Protocol for skill CRUD operations."""

    async def list_skills(self) -> list[SkillRecord]:
        """List all skills.

        Returns:
            List of skill records.
        """
        ...

    async def create_skill(
        self,
        name: str,
        description: str,
        content: str,
        enabled: bool,
    ) -> SkillRecord:
        """Create a new skill.

        Args:
            name: Skill name.
            description: Skill description.
            content: Skill content.
            enabled: Whether skill is enabled.

        Returns:
            Created skill record.
        """
        ...

    async def get_skill(self, skill_id: str) -> SkillRecord | None:
        """Get skill by ID.

        Args:
            skill_id: Skill identifier.

        Returns:
            Skill record or None if not found.
        """
        ...

    async def update_skill(
        self,
        skill_id: str,
        name: str,
        description: str,
        content: str,
        enabled: bool,
    ) -> SkillRecord | None:
        """Update a skill.

        Args:
            skill_id: Skill identifier.
            name: Updated name.
            description: Updated description.
            content: Updated content.
            enabled: Updated enabled status.

        Returns:
            Updated skill record or None if not found.
        """
        ...

    async def delete_skill(self, skill_id: str) -> bool:
        """Delete a skill.

        Args:
            skill_id: Skill identifier.

        Returns:
            True if deleted successfully.
        """
        ...
