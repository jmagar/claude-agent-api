# Data Model: Claude Agent API

**Feature Branch**: `001-claude-agent-api`
**Date**: 2026-01-07

## Overview

This document defines the data model for the Claude Agent API, including database entities, Pydantic schemas, and SDK type mappings.

---

## Database Entities (PostgreSQL)

### Session

Persistent record of agent conversation sessions.

```python
class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, completed, error
    model: Mapped[str] = mapped_column(String(50))
    working_directory: Mapped[str | None] = mapped_column(String(500))
    total_turns: Mapped[int] = mapped_column(default=0)
    total_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    parent_session_id: Mapped[UUID | None] = mapped_column(ForeignKey("sessions.id"))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)

    # Relationships
    messages: Mapped[list["SessionMessage"]] = relationship(back_populates="session")
    checkpoints: Mapped[list["Checkpoint"]] = relationship(back_populates="session")
```

**Validation Rules**:
- `status` must be one of: `active`, `completed`, `error`
- `model` must be valid Claude model identifier
- `total_turns` >= 0
- `total_cost_usd` >= 0 if set

**State Transitions**:
- `active` → `completed` (on ResultMessage with is_error=False)
- `active` → `error` (on ResultMessage with is_error=True)
- No transitions from `completed` or `error`

---

### SessionMessage

Individual messages within a session (for audit/replay).

```python
class SessionMessage(Base):
    __tablename__ = "session_messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.id"), index=True)
    message_type: Mapped[str] = mapped_column(String(20))  # user, assistant, system, result
    content: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    session: Mapped["Session"] = relationship(back_populates="messages")
```

**Validation Rules**:
- `message_type` must be one of: `user`, `assistant`, `system`, `result`
- `content` must be valid JSON

---

### Checkpoint

File state snapshots for rewind capability.

```python
class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.id"), index=True)
    user_message_uuid: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    files_modified: Mapped[list[str]] = mapped_column(ARRAY(String))

    # Relationships
    session: Mapped["Session"] = relationship(back_populates="checkpoints")
```

**Validation Rules**:
- `user_message_uuid` must be unique across all checkpoints
- `files_modified` must be list of absolute file paths

---

## Redis Cache Structures

### Active Session Cache

```
Key: session:{session_id}
TTL: 3600 seconds (1 hour)
Value: JSON
{
    "id": "uuid",
    "status": "active",
    "model": "claude-sonnet-4-5",
    "created_at": "2026-01-07T12:00:00Z",
    "last_activity": "2026-01-07T12:05:00Z"
}
```

### Active Connections Set

```
Key: active_connections
Type: SET
Members: session_id values
```

### Session Lock

```
Key: session_lock:{session_id}
TTL: 300 seconds (5 minutes)
Value: connection_id
```

---

## Pydantic Request Schemas

### ImageContentSchema

```python
class ImageContentSchema(BaseModel):
    """Image content for multimodal prompts."""

    type: Literal["base64", "url"] = "base64"
    media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"]
    data: str = Field(..., description="Base64-encoded image data or URL")
```

### QueryRequest

```python
class QueryRequest(BaseModel):
    """Request to send a query to the agent."""

    prompt: str = Field(..., min_length=1, max_length=100000)
    images: list[ImageContentSchema] | None = Field(None, description="Images to include with prompt")
    session_id: str | None = Field(None, description="Resume existing session")
    fork_session: bool = Field(False, description="Fork instead of continue")
    continue_conversation: bool = Field(False, description="Continue without resume ID")

    # Tool configuration
    allowed_tools: list[str] = Field(default_factory=list)
    disallowed_tools: list[str] = Field(default_factory=list)

    # Permission settings
    permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"] = "default"
    permission_prompt_tool_name: str | None = Field(None, description="Custom tool for permission prompts")

    # Model selection
    model: str | None = Field(None, description="Claude model to use")

    # Execution limits
    max_turns: int | None = Field(None, ge=1, le=1000)
    max_buffer_size: int | None = Field(None, description="Max message buffer size")
    cwd: str | None = Field(None, description="Working directory")
    add_dirs: list[str] = Field(default_factory=list, description="Additional directories to include")
    env: dict[str, str] = Field(default_factory=dict)

    # System prompt customization
    system_prompt: str | None = None
    system_prompt_append: str | None = Field(None, description="Append to default system prompt (preset+append mode)")
    output_style: str | None = Field(None, description="Output style from .claude/output-styles/")
    settings: str | None = Field(None, description="Path to settings file")
    setting_sources: list[Literal["project", "user"]] | None = None

    # Subagents
    agents: dict[str, AgentDefinitionSchema] | None = None

    # MCP servers
    mcp_servers: dict[str, McpServerConfigSchema] | None = None

    # Plugins
    plugins: list[SdkPluginConfigSchema] | None = None

    # Hooks (webhook URLs)
    hooks: HooksConfigSchema | None = None

    # File checkpointing
    enable_file_checkpointing: bool = False

    # Structured output
    output_format: OutputFormatSchema | None = None

    # Streaming options
    include_partial_messages: bool = Field(False, description="Include partial messages in stream")

    # Sandbox configuration
    sandbox: SandboxSettingsSchema | None = None

    # User identification
    user: str | None = Field(None, description="User identifier for tracking")

    # Extra CLI arguments
    extra_args: dict[str, str | None] = Field(default_factory=dict, description="Additional CLI arguments")
```

### AgentDefinitionSchema

```python
class AgentDefinitionSchema(BaseModel):
    """Definition for a custom subagent."""

    description: str = Field(..., min_length=1, max_length=1000)
    prompt: str = Field(..., min_length=1, max_length=50000)
    tools: list[str] | None = None
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None

    @model_validator(mode="after")
    def validate_no_task_tool(self) -> Self:
        if self.tools and "Task" in self.tools:
            raise ValueError("Subagents cannot have Task tool (no nested subagents)")
        return self
```

### McpServerConfigSchema

```python
class McpServerConfigSchema(BaseModel):
    """Configuration for an MCP server."""

    # Stdio transport
    command: str | None = None
    args: list[str] = Field(default_factory=list)

    # Remote transports
    type: Literal["stdio", "sse", "http"] = "stdio"
    url: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)

    # Environment
    env: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_transport(self) -> Self:
        if self.type == "stdio" and not self.command:
            raise ValueError("stdio transport requires 'command'")
        if self.type in ("sse", "http") and not self.url:
            raise ValueError(f"{self.type} transport requires 'url'")
        return self
```

### HooksConfigSchema

```python
class HooksConfigSchema(BaseModel):
    """Webhook configuration for hooks."""

    pre_tool_use: HookWebhookSchema | None = Field(None, alias="PreToolUse")
    post_tool_use: HookWebhookSchema | None = Field(None, alias="PostToolUse")
    stop: HookWebhookSchema | None = Field(None, alias="Stop")
    subagent_stop: HookWebhookSchema | None = Field(None, alias="SubagentStop")
    user_prompt_submit: HookWebhookSchema | None = Field(None, alias="UserPromptSubmit")
    pre_compact: HookWebhookSchema | None = Field(None, alias="PreCompact")
    notification: HookWebhookSchema | None = Field(None, alias="Notification")


class HookWebhookSchema(BaseModel):
    """Webhook configuration for a hook event."""

    url: HttpUrl
    headers: dict[str, str] = Field(default_factory=dict)
    timeout: int = Field(30, ge=1, le=300)
    matcher: str | None = Field(None, description="Regex pattern for tool names")
```

### OutputFormatSchema

```python
class OutputFormatSchema(BaseModel):
    """Structured output format specification."""

    type: Literal["json", "json_schema"] = "json_schema"
    schema_: dict | None = Field(None, alias="schema")

    @model_validator(mode="after")
    def validate_schema_requirement(self) -> Self:
        if self.type == "json_schema" and not self.schema_:
            raise ValueError("json_schema type requires 'schema' field")
        return self

    @field_validator("schema_")
    @classmethod
    def validate_json_schema(cls, v: dict | None) -> dict | None:
        if v is not None and "type" not in v:
            raise ValueError("JSON schema must have 'type' property")
        return v
```

### SdkPluginConfigSchema

```python
class SdkPluginConfigSchema(BaseModel):
    """Configuration for an SDK plugin."""

    name: str = Field(..., min_length=1, description="Plugin name")
    path: str | None = Field(None, description="Path to plugin directory")
    enabled: bool = Field(True, description="Whether plugin is enabled")
```

### SandboxSettingsSchema

```python
class SandboxSettingsSchema(BaseModel):
    """Sandbox configuration for agent execution."""

    enabled: bool = Field(True, description="Enable sandbox mode")
    allowed_paths: list[str] = Field(default_factory=list, description="Paths accessible in sandbox")
    network_access: bool = Field(False, description="Allow network access in sandbox")
```

### ResumeRequest

```python
class ResumeRequest(BaseModel):
    """Request to resume an existing session."""

    prompt: str = Field(..., min_length=1, max_length=100000)
    images: list[ImageContentSchema] | None = Field(None, description="Images to include")

    # Optional configuration overrides
    allowed_tools: list[str] | None = Field(None, description="Override allowed tools")
    disallowed_tools: list[str] | None = Field(None, description="Override disallowed tools")
    permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"] | None = None
    max_turns: int | None = Field(None, ge=1, le=1000)
    hooks: HooksConfigSchema | None = None
```

### ForkRequest

```python
class ForkRequest(BaseModel):
    """Request to fork an existing session."""

    prompt: str = Field(..., min_length=1, max_length=100000)
    images: list[ImageContentSchema] | None = Field(None, description="Images to include")

    # Optional configuration overrides (inherited from parent if not specified)
    allowed_tools: list[str] | None = Field(None, description="Override allowed tools")
    disallowed_tools: list[str] | None = Field(None, description="Override disallowed tools")
    permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"] | None = None
    max_turns: int | None = Field(None, ge=1, le=1000)
    model: str | None = Field(None, description="Override model for forked session")
    hooks: HooksConfigSchema | None = None
```

---

## Pydantic Response Schemas

### StreamEvent

Base for all SSE events.

```python
class StreamEvent(BaseModel):
    """Base SSE event."""

    event: str
    id: str | None = None
    data: dict


class InitEvent(StreamEvent):
    """Initial system event with session info."""

    event: Literal["init"] = "init"
    data: InitEventData


class InitEventData(BaseModel):
    session_id: str
    model: str
    tools: list[str]
    mcp_servers: list[McpServerStatus]
    plugins: list[str]
    commands: list[str]


class McpServerStatus(BaseModel):
    name: str
    status: Literal["connected", "failed"]
    error: str | None = None
```

### MessageEvent

```python
class MessageEvent(StreamEvent):
    """Agent message event."""

    event: Literal["message"] = "message"
    data: MessageEventData


class MessageEventData(BaseModel):
    type: Literal["user", "assistant", "system"]
    content: list[ContentBlockSchema]
    model: str | None = None
    uuid: str | None = None  # For checkpoints
    usage: UsageSchema | None = None
    parent_tool_use_id: str | None = None  # Present when message is from subagent context


class ContentBlockSchema(BaseModel):
    type: Literal["text", "thinking", "tool_use", "tool_result"]
    # Type-specific fields
    text: str | None = None
    thinking: str | None = None
    id: str | None = None  # tool_use
    name: str | None = None  # tool_use
    input: dict | None = None  # tool_use
    tool_use_id: str | None = None  # tool_result
    content: str | list | None = None  # tool_result
    is_error: bool | None = None  # tool_result
```

### PartialMessageEvent

Sent when `include_partial_messages: true` is set. Streams content deltas as they're generated.

```python
class PartialMessageEvent(StreamEvent):
    """Partial content delta event (when include_partial_messages is enabled)."""

    event: Literal["partial"] = "partial"
    data: PartialMessageEventData


class PartialMessageEventData(BaseModel):
    """Delta content for streaming partial messages."""

    type: Literal["content_block_start", "content_block_delta", "content_block_stop"]
    index: int  # Index of content block in the message

    # For content_block_start
    content_block: ContentBlockSchema | None = None

    # For content_block_delta
    delta: ContentDeltaSchema | None = None


class ContentDeltaSchema(BaseModel):
    """Delta content being streamed."""

    type: Literal["text_delta", "thinking_delta", "input_json_delta"]
    text: str | None = None  # For text_delta
    thinking: str | None = None  # For thinking_delta
    partial_json: str | None = None  # For input_json_delta (partial tool input)
```

### ResultEvent

```python
class ResultEvent(StreamEvent):
    """Final result event."""

    event: Literal["result"] = "result"
    data: ResultEventData


class ResultEventData(BaseModel):
    session_id: str
    is_error: bool
    duration_ms: int
    num_turns: int
    total_cost_usd: float | None = None
    usage: UsageSchema | None = None
    model_usage: dict[str, UsageSchema] | None = None
    result: str | None = None
    structured_output: dict | None = None  # Present when output_format was specified


class UsageSchema(BaseModel):
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
```

### ErrorEvent

```python
class ErrorEvent(StreamEvent):
    """Error event (mid-stream)."""

    event: Literal["error"] = "error"
    data: ErrorEventData


class ErrorEventData(BaseModel):
    code: str
    message: str
    details: dict | None = None
```

### DoneEvent

```python
class DoneEvent(StreamEvent):
    """Stream completion event."""

    event: Literal["done"] = "done"
    data: DoneEventData


class DoneEventData(BaseModel):
    reason: Literal["completed", "interrupted", "error"] = "completed"
```

### SessionResponse

```python
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
```

### CheckpointResponse

```python
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
```

### HealthResponse

```python
class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["ok", "degraded", "unhealthy"]
    version: str | None = None  # API version string (e.g., "1.0.0")
    dependencies: dict[str, DependencyStatus]


class DependencyStatus(BaseModel):
    status: Literal["ok", "error"]
    latency_ms: float | None = None
    error: str | None = None
```

---

## SDK Type Mappings

### SDK Message → API Event

| SDK Type | API Event Type |
|----------|---------------|
| `SystemMessage` (subtype="init") | `InitEvent` |
| `UserMessage` | `MessageEvent` (type="user") |
| `AssistantMessage` | `MessageEvent` (type="assistant") |
| `SystemMessage` (other) | `MessageEvent` (type="system") |
| `ResultMessage` | `ResultEvent` |

### SDK ContentBlock → API ContentBlock

| SDK Type | API `type` Field |
|----------|-----------------|
| `TextBlock` | `"text"` |
| `ThinkingBlock` | `"thinking"` |
| `ToolUseBlock` | `"tool_use"` |
| `ToolResultBlock` | `"tool_result"` |

### AskUserQuestion Tool Handling

When the agent uses the `AskUserQuestion` tool, it appears in the stream as a `tool_use` content block:

```json
{
  "event": "message",
  "data": {
    "type": "assistant",
    "content": [
      {
        "type": "tool_use",
        "id": "toolu_123",
        "name": "AskUserQuestion",
        "input": {
          "question": "Which database should I use for this project?"
        }
      }
    ]
  }
}
```

**Client Response Options**:

1. **HTTP API**: Resume the session with the answer as the prompt:
   ```
   POST /api/v1/sessions/{session_id}/resume
   {"prompt": "Use PostgreSQL"}
   ```

2. **WebSocket API**: Send a prompt message:
   ```json
   {"type": "prompt", "content": "Use PostgreSQL"}
   ```

The agent will receive the answer and continue execution.

---

## Entity Relationships

```
Session (1) ──────< (N) SessionMessage
    │
    └──< (N) Checkpoint
    │
    └──< (0..1) Session (parent_session_id for forks)
```

---

## Indexes

```sql
-- Session lookups
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX idx_sessions_parent ON sessions(parent_session_id) WHERE parent_session_id IS NOT NULL;

-- Message lookups
CREATE INDEX idx_messages_session_id ON session_messages(session_id);
CREATE INDEX idx_messages_created_at ON session_messages(created_at);

-- Checkpoint lookups
CREATE INDEX idx_checkpoints_session_id ON checkpoints(session_id);
CREATE UNIQUE INDEX idx_checkpoints_uuid ON checkpoints(user_message_uuid);
```
