"""Type definitions and constants for the API."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, NotRequired, Required, TypeAlias, TypedDict
from uuid import UUID

# JSON value type (recursive union for proper type safety)
JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)

# Session status values
SessionStatus = Literal["active", "completed", "error"]

# Message types
MessageType = Literal["user", "assistant", "system", "result"]

# Content block types
ContentBlockType = Literal["text", "thinking", "tool_use", "tool_result"]

# Permission modes
PermissionMode = Literal["default", "acceptEdits", "plan", "bypassPermissions"]

# Model options
ModelOption = Literal["sonnet", "opus", "haiku"]

# Valid short model names
VALID_SHORT_MODEL_NAMES: set[str] = {"sonnet", "opus", "haiku", "gpt-4"}

# Valid full model IDs (exact matches)
VALID_FULL_MODEL_IDS: set[str] = {
    "claude-opus-4-20250514",
    "claude-sonnet-4-20250514",
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-5-20250929",
    "claude-3-5-haiku-20241022",
    "claude-opus-4-5-20251101",
    "claude-opus-4-1-20250805",
    "claude-3-7-sonnet-20250219",
}

# Valid model ID prefixes (for backward compatibility with future model versions)
VALID_MODEL_PREFIXES: tuple[str, ...] = (
    "claude-sonnet-",
    "claude-opus-",
    "claude-haiku-",
    "claude-3-5-sonnet-",
    "claude-3-5-haiku-",
    "claude-3-opus-",
    "claude-3-7-sonnet-",
)

# SSE event types
SSEEventType = Literal[
    "init", "message", "partial", "result", "error", "done", "question"
]

# Hook event types
HookEventType = Literal[
    "PreToolUse",
    "PostToolUse",
    "Stop",
    "SubagentStop",
    "UserPromptSubmit",
    "PreCompact",
    "Notification",
]

# MCP transport types
McpTransportType = Literal["stdio", "sse", "http"]

# Hook decision types
HookDecision = Literal["allow", "deny", "ask"]


class ContentBlockDict(TypedDict):
    """Content block dictionary structure.

    Attributes:
        type: The content block type (text, thinking, tool_use, tool_result) - required.
        text: Text content for text blocks (optional).
        thinking: Thinking content for thinking blocks (optional).
        id: Unique identifier for tool_use blocks (optional).
        name: Tool name for tool_use blocks (optional).
        input: Tool input parameters for tool_use blocks (optional).
        tool_use_id: Reference to tool_use id for tool_result blocks (optional).
        content: Result content for tool_result blocks (optional).
        is_error: Whether tool_result represents an error (optional).
    """

    type: Required[ContentBlockType]
    text: NotRequired[str | None]
    thinking: NotRequired[str | None]
    id: NotRequired[str | None]
    name: NotRequired[str | None]
    input: NotRequired[dict[str, object] | None]
    tool_use_id: NotRequired[str | None]
    content: NotRequired[str | list[object] | None]
    is_error: NotRequired[bool | None]


class UsageDict(TypedDict):
    """Token usage dictionary.

    Attributes:
        input_tokens: Number of input tokens consumed (optional).
        output_tokens: Number of output tokens generated (optional).
        cache_read_input_tokens: Number of cached input tokens read (optional).
        cache_creation_input_tokens: Number of input tokens used for cache creation (optional).
    """

    input_tokens: NotRequired[int]
    output_tokens: NotRequired[int]
    cache_read_input_tokens: NotRequired[int]
    cache_creation_input_tokens: NotRequired[int]


class InitEventDataDict(TypedDict):
    """Init event data structure."""

    session_id: str
    model: str
    tools: list[str]
    mcp_servers: list["McpServerStatusDict"]
    plugins: list[str]
    commands: list[str]


class McpServerStatusDict(TypedDict):
    """MCP server status dictionary."""

    name: Required[str]
    status: Required[Literal["connected", "failed"]]
    error: NotRequired[str | None]


class MessageEventDataDict(TypedDict):
    """Message event data structure.

    Attributes:
        type: Message type (user, assistant, system, result) - required.
        content: List of content blocks in the message - required.
        model: Model identifier used for this message (optional).
        uuid: Unique identifier for the message (optional).
        usage: Token usage statistics for this message (optional).
        parent_tool_use_id: Parent tool use ID for nested tool calls (optional).
    """

    type: Required[MessageType]
    content: Required[list[ContentBlockDict]]
    model: NotRequired[str | None]
    uuid: NotRequired[str | None]
    usage: NotRequired[UsageDict | None]
    parent_tool_use_id: NotRequired[str | None]


class ResultEventDataDict(TypedDict):
    """Result event data structure.

    Attributes:
        session_id: Session identifier - required.
        is_error: Whether the session ended with an error - required.
        duration_ms: Session duration in milliseconds (optional).
        num_turns: Number of conversation turns (optional).
        total_cost_usd: Total estimated cost in USD (optional).
        usage: Aggregate token usage statistics (optional).
        model_usage: Per-model token usage breakdown (optional).
        result: Final result text from the agent (optional).
        structured_output: Structured output if requested (optional).
    """

    session_id: Required[str]
    is_error: Required[bool]
    duration_ms: NotRequired[int]
    num_turns: NotRequired[int]
    total_cost_usd: NotRequired[float | None]
    usage: NotRequired[UsageDict | None]
    model_usage: NotRequired[dict[str, UsageDict] | None]
    result: NotRequired[str | None]
    structured_output: NotRequired[dict[str, object] | None]


class ErrorEventDataDict(TypedDict):
    """Error event data structure."""

    code: str
    message: str
    details: dict[str, object] | None


class DoneEventDataDict(TypedDict):
    """Done event data structure.

    Attributes:
        reason: Reason for session completion (completed, interrupted, error) - required.
    """

    reason: Required[Literal["completed", "interrupted", "error"]]


class HookPayloadDict(TypedDict):
    """Webhook hook payload structure.

    Attributes:
        hook_event: Type of hook event being triggered - required.
        session_id: Session identifier - required.
        tool_name: Name of tool being invoked (optional).
        tool_input: Input parameters for the tool (optional).
        tool_result: Result from tool execution (optional).
    """

    hook_event: Required[HookEventType]
    session_id: Required[str]
    tool_name: NotRequired[str | None]
    tool_input: NotRequired[dict[str, object] | None]
    tool_result: NotRequired[dict[str, object] | None]


class HookResponseDict(TypedDict):
    """Webhook hook response structure.

    Attributes:
        decision: Hook decision (allow, deny, ask) - required.
        reason: Human-readable reason for the decision (optional).
        modified_input: Modified tool input parameters (optional).
    """

    decision: Required[HookDecision]
    reason: NotRequired[str | None]
    modified_input: NotRequired[dict[str, object] | None]


# Data Classes


@dataclass
class SessionData:
    """Session data structure returned from repository."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    status: str
    model: str
    working_directory: str | None
    total_turns: int
    total_cost_usd: float | None
    parent_session_id: UUID | None
    metadata: dict[str, JsonValue] | None


@dataclass
class MessageData:
    """Message data structure returned from repository."""

    id: UUID
    session_id: UUID
    message_type: str
    content: dict[str, JsonValue]
    created_at: datetime


@dataclass
class CheckpointData:
    """Checkpoint data structure returned from repository."""

    id: UUID
    session_id: UUID
    user_message_uuid: str
    created_at: datetime
    files_modified: list[str]


@dataclass
class AgentMessage:
    """Agent message structure from SDK client."""

    type: str
    data: dict[str, JsonValue]
