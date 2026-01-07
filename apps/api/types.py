"""Type definitions and constants for the API."""

from typing import Literal, TypedDict

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


# Built-in tools list
BUILT_IN_TOOLS: list[str] = [
    "Read",
    "Write",
    "Edit",
    "MultiEdit",
    "Bash",
    "Glob",
    "Grep",
    "LS",
    "WebFetch",
    "WebSearch",
    "Task",
    "TodoWrite",
    "NotebookEdit",
    "NotebookRead",
    "AskUserQuestion",
    "Skill",  # T116c: Skill tool for invoking skills
    "SlashCommand",  # Slash command invocation
]


class ContentBlockDict(TypedDict, total=False):
    """Content block dictionary structure."""

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
    """Token usage dictionary."""

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
    """Message event data structure."""

    type: MessageType
    content: list[ContentBlockDict]
    model: str | None
    uuid: str | None
    usage: UsageDict | None
    parent_tool_use_id: str | None


class ResultEventDataDict(TypedDict, total=False):
    """Result event data structure."""

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
    """Done event data structure."""

    reason: Literal["completed", "interrupted", "error"]


class HookPayloadDict(TypedDict, total=False):
    """Webhook hook payload structure."""

    hook_event: HookEventType
    session_id: str
    tool_name: str | None
    tool_input: dict[str, object] | None
    tool_result: dict[str, object] | None


class HookResponseDict(TypedDict, total=False):
    """Webhook hook response structure."""

    decision: HookDecision
    reason: str | None
    modified_input: dict[str, object] | None
