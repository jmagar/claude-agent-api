"""Type definitions and constants for the API."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, TypedDict
from uuid import UUID

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
VALID_SHORT_MODEL_NAMES: set[str] = {"sonnet", "opus", "haiku"}

# Valid model ID prefixes (for full model identifiers)
# These match patterns like "claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022"
VALID_MODEL_PREFIXES: tuple[str, ...] = (
    "claude-sonnet-",
    "claude-opus-",
    "claude-haiku-",
    "claude-3-5-sonnet-",
    "claude-3-5-haiku-",
    "claude-3-opus-",
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


class ContentBlockDict(TypedDict, total=False):
    """Content block dictionary structure.

    All fields are optional (total=False).

    Attributes:
        type: The content block type (text, thinking, tool_use, tool_result).
        text: Text content for text blocks (optional).
        thinking: Thinking content for thinking blocks (optional).
        id: Unique identifier for tool_use blocks (optional).
        name: Tool name for tool_use blocks (optional).
        input: Tool input parameters for tool_use blocks (optional).
        tool_use_id: Reference to tool_use id for tool_result blocks (optional).
        content: Result content for tool_result blocks (optional).
        is_error: Whether tool_result represents an error (optional).
    """

    type: ContentBlockType
    text: str | None
    thinking: str | None
    id: str | None
    name: str | None
    input: dict[str, object] | None
    tool_use_id: str | None
    content: str | list[object] | None
    is_error: bool | None


class UsageDict(TypedDict, total=False):
    """Token usage dictionary.

    All fields are optional (total=False).

    Attributes:
        input_tokens: Number of input tokens consumed (optional).
        output_tokens: Number of output tokens generated (optional).
        cache_read_input_tokens: Number of cached input tokens read (optional).
        cache_creation_input_tokens: Number of input tokens used for cache creation (optional).
    """

    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int


class InitEventDataDict(TypedDict):
    """Init event data structure."""

    session_id: str
    model: str
    tools: list[str]
    mcp_servers: list["McpServerStatusDict"]
    plugins: list[str]
    commands: list[str]


class McpServerStatusDict(TypedDict, total=False):
    """MCP server status dictionary."""

    name: str
    status: Literal["connected", "failed"]
    error: str | None


class MessageEventDataDict(TypedDict, total=False):
    """Message event data structure.

    All fields are optional (total=False).

    Attributes:
        type: Message type (user, assistant, system, result) (optional).
        content: List of content blocks in the message (optional).
        model: Model identifier used for this message (optional).
        uuid: Unique identifier for the message (optional).
        usage: Token usage statistics for this message (optional).
        parent_tool_use_id: Parent tool use ID for nested tool calls (optional).
    """

    type: MessageType
    content: list[ContentBlockDict]
    model: str | None
    uuid: str | None
    usage: UsageDict | None
    parent_tool_use_id: str | None


class ResultEventDataDict(TypedDict, total=False):
    """Result event data structure.

    All fields are optional (total=False).

    Attributes:
        session_id: Session identifier (optional).
        is_error: Whether the session ended with an error (optional).
        duration_ms: Session duration in milliseconds (optional).
        num_turns: Number of conversation turns (optional).
        total_cost_usd: Total estimated cost in USD (optional).
        usage: Aggregate token usage statistics (optional).
        model_usage: Per-model token usage breakdown (optional).
        result: Final result text from the agent (optional).
        structured_output: Structured output if requested (optional).
    """

    session_id: str
    is_error: bool
    duration_ms: int
    num_turns: int
    total_cost_usd: float | None
    usage: UsageDict | None
    model_usage: dict[str, UsageDict] | None
    result: str | None
    structured_output: dict[str, object] | None


class ErrorEventDataDict(TypedDict):
    """Error event data structure."""

    code: str
    message: str
    details: dict[str, object] | None


class DoneEventDataDict(TypedDict, total=False):
    """Done event data structure.

    All fields are optional (total=False).

    Attributes:
        reason: Reason for session completion (completed, interrupted, error) (optional).
    """

    reason: Literal["completed", "interrupted", "error"]


class HookPayloadDict(TypedDict, total=False):
    """Webhook hook payload structure.

    All fields are optional (total=False).

    Attributes:
        hook_event: Type of hook event being triggered (optional).
        session_id: Session identifier (optional).
        tool_name: Name of tool being invoked (optional).
        tool_input: Input parameters for the tool (optional).
        tool_result: Result from tool execution (optional).
    """

    hook_event: HookEventType
    session_id: str
    tool_name: str | None
    tool_input: dict[str, object] | None
    tool_result: dict[str, object] | None


class HookResponseDict(TypedDict, total=False):
    """Webhook hook response structure.

    All fields are optional (total=False).

    Attributes:
        decision: Hook decision (allow, deny, ask) (optional).
        reason: Human-readable reason for the decision (optional).
        modified_input: Modified tool input parameters (optional).
    """

    decision: HookDecision
    reason: str | None
    modified_input: dict[str, object] | None


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
    metadata: dict[str, object] | None


@dataclass
class MessageData:
    """Message data structure returned from repository."""

    id: UUID
    session_id: UUID
    message_type: str
    content: dict[str, object]
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
    data: dict[str, object]
