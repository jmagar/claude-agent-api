"""Pydantic response models for API endpoints."""

from datetime import datetime
from typing import Literal, Protocol, cast

from pydantic import BaseModel, Field


class UsageSchema(BaseModel):
    """Token usage information."""

    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


class ContentBlockSchema(BaseModel):
    """Content block in a message."""

    type: Literal["text", "thinking", "tool_use", "tool_result"]
    # Text block fields
    text: str | None = None
    # Thinking block fields
    thinking: str | None = None
    # Tool use block fields
    id: str | None = None
    name: str | None = None
    input: dict[str, object] | None = None
    # Tool result block fields
    tool_use_id: str | None = None
    content: str | list[object] | None = None
    is_error: bool | None = None


class McpServerStatusSchema(BaseModel):
    """MCP server connection status."""

    name: str
    status: Literal["connected", "failed"]
    error: str | None = None


class McpSharePayloadResponse(BaseModel):
    """Payload returned for an MCP share token."""

    name: str
    config: dict[str, object]
    created_at: str


class McpShareCreateResponse(BaseModel):
    """Response for MCP share token creation."""

    share_token: str
    name: str
    config: dict[str, object]
    created_at: str


class ToolPresetResponse(BaseModel):
    """Tool preset response schema."""

    id: str
    name: str
    description: str | None = None
    allowed_tools: list[str]
    disallowed_tools: list[str] = Field(default_factory=list)
    is_system: bool = False
    created_at: datetime


class ToolPresetListResponse(BaseModel):
    """List of tool presets."""

    presets: list[ToolPresetResponse]


class ProjectResponse(BaseModel):
    """Project response schema."""

    id: str
    name: str
    path: str
    created_at: datetime
    last_accessed_at: datetime | None = None
    session_count: int | None = None
    metadata: dict[str, object] | None = None


class ProjectListResponse(BaseModel):
    """Project list response."""

    projects: list[ProjectResponse]
    total: int


class AgentDefinitionResponse(BaseModel):
    """Agent definition response schema."""

    id: str
    name: str
    description: str
    prompt: str
    tools: list[str] | None = None
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
    created_at: datetime
    updated_at: datetime | None = None
    is_shared: bool | None = None
    share_url: str | None = None


class AgentListResponse(BaseModel):
    """Agent list response."""

    agents: list[AgentDefinitionResponse]


class SkillDefinitionResponse(BaseModel):
    """Skill definition response schema."""

    id: str
    name: str
    description: str
    content: str
    enabled: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_shared: bool | None = None
    share_url: str | None = None
    source: Literal["filesystem", "database"] = "database"
    path: str | None = None  # Filesystem path for filesystem-sourced skills


class SkillListResponse(BaseModel):
    """Skill list response."""

    skills: list[SkillDefinitionResponse]


class SlashCommandDefinitionResponse(BaseModel):
    """Slash command definition response schema."""

    id: str
    name: str
    description: str
    content: str
    enabled: bool = True
    created_at: datetime
    updated_at: datetime | None = None


class SlashCommandListResponse(BaseModel):
    """Slash command list response."""

    commands: list[SlashCommandDefinitionResponse]


class McpServerConfigResponse(BaseModel):
    """MCP server configuration response schema."""

    id: str
    name: str
    transport_type: str
    command: str | None = None
    args: list[str] | None = None
    url: str | None = None
    headers: dict[str, str] | None = None
    env: dict[str, str] | None = None
    enabled: bool = True
    status: str = "active"
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, object] | None = None
    source: Literal["filesystem", "database"] = "database"


class McpServerListResponse(BaseModel):
    """MCP server list response."""

    servers: list[McpServerConfigResponse]


class McpResourceResponse(BaseModel):
    """MCP server resource response schema."""

    uri: str
    name: str | None = None
    description: str | None = None
    mimeType: str | None = None


class McpResourceListResponse(BaseModel):
    """MCP server resource list response."""

    resources: list[McpResourceResponse]


class McpResourceContentResponse(BaseModel):
    """MCP server resource content response."""

    uri: str
    mimeType: str | None = None
    text: str | None = None


class CommandInfoSchema(BaseModel):
    """Information about an available slash command."""

    name: str
    path: str


class InitEventData(BaseModel):
    """Data for init event."""

    session_id: str
    model: str
    tools: list[str]
    mcp_servers: list[McpServerStatusSchema] = Field(default_factory=list)
    plugins: list[str] = Field(default_factory=list)
    commands: list[CommandInfoSchema] = Field(default_factory=list)
    permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"] = (
        "default"
    )


class MessageEventData(BaseModel):
    """Data for message event."""

    type: Literal["user", "assistant", "system"]
    content: list[ContentBlockSchema]
    model: str | None = None
    uuid: str | None = None
    usage: UsageSchema | None = None
    parent_tool_use_id: str | None = None


class QuestionEventData(BaseModel):
    """Data for question event (AskUserQuestion)."""

    tool_use_id: str
    question: str
    session_id: str


class ContentDeltaSchema(BaseModel):
    """Delta content for partial messages."""

    type: Literal["text_delta", "thinking_delta", "input_json_delta"]
    text: str | None = None
    thinking: str | None = None
    partial_json: str | None = None


class PartialMessageEventData(BaseModel):
    """Data for partial message event."""

    type: Literal["content_block_start", "content_block_delta", "content_block_stop"]
    index: int
    content_block: ContentBlockSchema | None = None
    delta: ContentDeltaSchema | None = None


class TodoEventData(BaseModel):
    """Data for todo event (TodoWrite tool use)."""

    todos: list[dict[str, object]]


class ResultEventData(BaseModel):
    """Data for result event."""

    session_id: str
    is_error: bool
    is_complete: bool = True
    stop_reason: (
        Literal["completed", "max_turns_reached", "interrupted", "error"] | None
    ) = None
    duration_ms: int
    num_turns: int
    total_cost_usd: float | None = None
    usage: UsageSchema | None = None
    model_usage: dict[str, UsageSchema] | None = None
    result: str | None = None
    structured_output: dict[str, object] | None = None


class ErrorEventData(BaseModel):
    """Data for error event."""

    code: str
    message: str
    details: dict[str, object] | None = None


class DoneEventData(BaseModel):
    """Data for done event."""

    reason: Literal["completed", "interrupted", "error"] = "completed"


# SSE Event Types
class InitEvent(BaseModel):
    """Initial system event with session info."""

    event: Literal["init"] = "init"
    data: InitEventData


class MessageEvent(BaseModel):
    """Agent message event."""

    event: Literal["message"] = "message"
    data: MessageEventData


class QuestionEvent(BaseModel):
    """Question event for AskUserQuestion."""

    event: Literal["question"] = "question"
    data: QuestionEventData


class PartialMessageEvent(BaseModel):
    """Partial content delta event."""

    event: Literal["partial"] = "partial"
    data: PartialMessageEventData


class TodoEvent(BaseModel):
    """Todo tracking event."""

    event: Literal["todo"] = "todo"
    data: TodoEventData


class ResultEvent(BaseModel):
    """Final result event."""

    event: Literal["result"] = "result"
    data: ResultEventData


class ErrorEvent(BaseModel):
    """Error event (mid-stream)."""

    event: Literal["error"] = "error"
    data: ErrorEventData


class DoneEvent(BaseModel):
    """Stream completion event."""

    event: Literal["done"] = "done"
    data: DoneEventData


# Session Response Types
class SessionResponse(BaseModel):
    """Session details response."""

    id: str
    status: Literal["active", "completed", "error"]
    model: str
    created_at: datetime
    updated_at: datetime
    total_turns: int
    total_cost_usd: float | None = None
    parent_session_id: str | None = None


class SessionWithMetaResponse(BaseModel):
    """Session response with metadata fields."""

    id: str
    mode: Literal["brainstorm", "code"]
    status: Literal["active", "completed", "error"]
    project_id: str | None = None
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None = None
    total_turns: int | None = None
    total_cost_usd: float | None = None
    parent_session_id: str | None = None
    tags: list[str] | None = None
    duration_ms: int | None = None
    usage: dict[str, object] | None = None
    model_usage: dict[str, object] | None = None
    metadata: dict[str, object] | None = None

    class _SessionLike(Protocol):
        id: object
        status: object
        created_at: datetime
        updated_at: datetime
        total_turns: object
        total_cost_usd: object
        parent_session_id: object
        session_metadata: dict[str, object] | None

    @classmethod
    def from_session(
        cls,
        session: object,
        metadata: dict[str, object] | None = None,
    ) -> "SessionWithMetaResponse":
        """Create SessionWithMetaResponse from session object.

        Args:
            session: Session object with attributes (id, status, created_at, etc.)
            metadata: Session metadata dictionary. If None, extracted from session.session_metadata.

        Returns:
            SessionWithMetaResponse instance.
        """
        session_obj = cast("SessionWithMetaResponse._SessionLike", session)
        # Extract metadata from session if not provided
        if metadata is None:
            metadata = session_obj.session_metadata or {}
            if metadata is None:
                metadata = {}

        # Extract session attributes
        session_id = str(session_obj.id)
        status_raw = str(session_obj.status)
        created_at = session_obj.created_at
        updated_at = session_obj.updated_at
        total_turns = int(getattr(session_obj, "total_turns", 0))
        total_cost_raw = getattr(session_obj, "total_cost_usd", None)
        parent_id_raw = getattr(session_obj, "parent_session_id", None)

        # Validate status
        status_val: Literal["active", "completed", "error"]
        if status_raw == "active":
            status_val = "active"
        elif status_raw == "completed":
            status_val = "completed"
        elif status_raw == "error":
            status_val = "error"
        else:
            status_val = "active"

        # Extract metadata fields
        session_mode = metadata.get("mode", "code")
        mode: Literal["brainstorm", "code"] = (
            "brainstorm" if session_mode == "brainstorm" else "code"
        )
        project_id_raw = metadata.get("project_id")
        title_raw = metadata.get("title")
        tags_raw = metadata.get("tags")

        return cls(
            id=session_id,
            mode=mode,
            status=status_val,
            project_id=str(project_id_raw) if project_id_raw else None,
            title=str(title_raw) if title_raw else None,
            created_at=created_at,
            updated_at=updated_at,
            total_turns=total_turns,
            total_cost_usd=float(total_cost_raw) if total_cost_raw is not None else None,
            parent_session_id=str(parent_id_raw) if parent_id_raw else None,
            tags=cast("list[str] | None", tags_raw) if isinstance(tags_raw, list) else None,
            metadata=metadata,
        )


class SessionListResponse(BaseModel):
    """Paginated session list."""

    sessions: list[SessionResponse]
    total: int
    page: int
    page_size: int


class SessionWithMetaListResponse(BaseModel):
    """Paginated session list with metadata."""

    sessions: list[SessionWithMetaResponse]
    total: int
    page: int
    page_size: int


# Checkpoint Response Types
class CheckpointResponse(BaseModel):
    """Checkpoint details."""

    id: str
    session_id: str
    user_message_uuid: str
    created_at: datetime
    files_modified: list[str]


class CheckpointListResponse(BaseModel):
    """List of checkpoints for a session."""

    checkpoints: list[CheckpointResponse]


# Skill Response Types
class SkillResponse(BaseModel):
    """Skill information."""

    name: str
    description: str | None = None
    path: str | None = None


class SkillDiscoveryResponse(BaseModel):
    """Skill discovery response."""

    skills: list[SkillResponse]


# Single Query Response (non-streaming)
class SingleQueryResponse(BaseModel):
    """Response for non-streaming query."""

    session_id: str
    model: str
    content: list[ContentBlockSchema]
    is_error: bool
    is_complete: bool = True
    stop_reason: (
        Literal["completed", "max_turns_reached", "interrupted", "error"] | None
    ) = None
    duration_ms: int
    num_turns: int
    total_cost_usd: float | None = None
    usage: UsageSchema | None = None
    result: str | None = None
    structured_output: dict[str, object] | None = None


# Session Control Response Types
class StatusResponse(BaseModel):
    """Generic status response for session operations."""

    status: str
    session_id: str


class ControlEventResponse(BaseModel):
    """Response for control event operations."""

    status: Literal["accepted", "unknown_type"]
    session_id: str
    permission_mode: (
        Literal["default", "acceptEdits", "plan", "bypassPermissions"] | None
    ) = None


class RewindResponse(BaseModel):
    """Response for checkpoint rewind operations."""

    status: Literal["validated"]
    checkpoint_id: str
    message: str
