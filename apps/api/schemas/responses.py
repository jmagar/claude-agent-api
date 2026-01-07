"""Pydantic response models for API endpoints."""

from datetime import datetime
from typing import Literal

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


class InitEventData(BaseModel):
    """Data for init event."""

    session_id: str
    model: str
    tools: list[str]
    mcp_servers: list[McpServerStatusSchema] = Field(default_factory=list)
    plugins: list[str] = Field(default_factory=list)
    commands: list[str] = Field(default_factory=list)


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


class SessionListResponse(BaseModel):
    """Paginated session list."""

    sessions: list[SessionResponse]
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
    duration_ms: int
    num_turns: int
    total_cost_usd: float | None = None
    usage: UsageSchema | None = None
    result: str | None = None
    structured_output: dict[str, object] | None = None
