# Research: Claude Agent API

**Feature Branch**: `001-claude-agent-api`
**Date**: 2026-01-07

## Executive Summary

This document consolidates research findings for building an HTTP API wrapper around the Claude Agent Python SDK. All technical unknowns have been resolved through documentation review and best practices analysis.

---

## 1. Claude Agent Python SDK

### Decision: Use `ClaudeSDKClient` over `query()`

**Rationale**: `ClaudeSDKClient` provides session management, interrupt support, hooks, and file checkpointing - all required for feature parity.

**Alternatives Considered**:
- `query()` function: Simpler but lacks session persistence, hooks, and interrupt support

### Package Installation

```bash
uv add claude-agent-sdk
```

### Core API Classes

#### ClaudeSDKClient

Primary interface for stateful agent interactions:

```python
class ClaudeSDKClient:
    def __init__(self, options: ClaudeAgentOptions | None = None)
    async def connect(self, prompt: str | AsyncIterable[dict] | None = None) -> None
    async def query(self, prompt: str | AsyncIterable[dict], session_id: str = "default") -> None
    async def receive_messages(self) -> AsyncIterator[Message | StreamEvent]
    async def receive_response(self) -> AsyncIterator[Message | StreamEvent]
    async def interrupt(self) -> None
    async def rewind_files(self, user_message_id: str) -> None
    async def disconnect(self) -> None
    # Additional methods
    def get_server_info(self) -> dict[str, Any] | None
    async def set_model(self, model: str | None = None) -> None
    async def set_permission_mode(self, mode: str) -> None
```

#### ClaudeAgentOptions

Full configuration dataclass:

```python
@dataclass
class ClaudeAgentOptions:
    # Tool configuration
    tools: list[str] | ToolsPreset | None = None    # Tool preset or list
    allowed_tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)

    # Prompt and system configuration
    system_prompt: str | SystemPromptPreset | None = None
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    permission_mode: PermissionMode | None = None  # 'default', 'acceptEdits', 'plan', 'bypassPermissions'

    # Session management
    continue_conversation: bool = False
    resume: str | None = None                        # Resume session by ID
    fork_session: bool = False                       # Fork instead of continue

    # Model configuration
    model: str | None = None                         # 'sonnet', 'opus', 'haiku'
    fallback_model: str | None = None                # Fallback if primary unavailable
    max_turns: int | None = None
    max_budget_usd: float | None = None              # Cost limit
    max_thinking_tokens: int | None = None           # Extended thinking limit
    betas: list[Literal['context-1m-2025-08-07']] = field(default_factory=list)  # Beta features

    # Environment and paths
    cwd: str | Path | None = None
    cli_path: str | Path | None = None               # Path to Claude CLI
    env: dict[str, str] = field(default_factory=dict)
    settings: str | None = None                      # Path to settings file
    add_dirs: list[str | Path] = field(default_factory=list)  # Additional directories

    # Callbacks and hooks
    can_use_tool: CanUseTool | None = None          # Permission callback
    hooks: dict[HookEvent, list[HookMatcher]] | None = None
    stderr: Callable[[str], None] | None = None     # Callback for stderr output

    # Features
    enable_file_checkpointing: bool = False
    output_format: OutputFormat | None = None       # Structured outputs
    agents: dict[str, AgentDefinition] | None = None  # Subagents
    include_partial_messages: bool = False

    # Additional configuration
    setting_sources: list[SettingSource] | None = None
    extra_args: dict[str, str | None] = field(default_factory=dict)
    permission_prompt_tool_name: str | None = None
    max_buffer_size: int | None = None
    user: str | None = None                          # User identifier
    plugins: list[SdkPluginConfig] = field(default_factory=list)  # Local plugins
    sandbox: SandboxSettings | None = None           # Sandbox configuration
```

### Message Types

```python
Message = UserMessage | AssistantMessage | SystemMessage | ResultMessage

@dataclass
class UserMessage:
    content: str | list[ContentBlock]
    uuid: str | None = None              # For checkpointing
    parent_tool_use_id: str | None = None  # If from subagent tool call

@dataclass
class AssistantMessage:
    content: list[ContentBlock]
    model: str
    parent_tool_use_id: str | None = None  # If from subagent
    error: Literal[
        'authentication_failed', 'billing_error', 'rate_limit',
        'invalid_request', 'server_error', 'unknown'
    ] | None = None

@dataclass
class SystemMessage:
    subtype: str
    data: dict[str, Any]

@dataclass
class ResultMessage:
    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    result: str | None = None
    structured_output: Any = None        # Parsed structured output

ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock
```

### Session Management

**Resume Session**:
```python
options = ClaudeAgentOptions(resume="session-xyz")
```

**Fork Session**:
```python
options = ClaudeAgentOptions(resume="session-xyz", fork_session=True)
```

**Session ID**: Obtained from `ResultMessage.session_id` or `SystemMessage` init event.

### Built-in Tools

```python
BUILT_IN_TOOLS = [
    "Read",           # File reading
    "Write",          # File creation/overwrite
    "Edit",           # File editing
    "Bash",           # Shell commands
    "Glob",           # Pattern matching
    "Grep",           # Text search
    "WebFetch",       # Web content
    "WebSearch",      # Web search
    "Task",           # Subagent invocation (REQUIRED for subagents)
    "TodoWrite",      # Task tracking
    "NotebookEdit",   # Jupyter notebooks
    "MultiEdit",      # Multiple file edits
]
```

### Subagent Definition

```python
@dataclass
class AgentDefinition:
    description: str      # When to use this agent (for automatic invocation)
    prompt: str           # System prompt for subagent
    tools: list[str] | None = None  # Allowed tools (inherits if None)
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
```

**Key Constraint**: Subagents cannot have `Task` tool (no nested subagents).

### MCP Server Configuration

Three transport types supported:

```python
# Stdio transport
mcp_servers = {
    "custom": McpServerConfig(
        command="python",
        args=["my_server.py"],
        env={"API_KEY": "${API_KEY:-default}"}
    )
}

# SSE transport
mcp_servers = {
    "remote": McpServerConfig(
        type="sse",
        url="https://api.example.com/sse",
        headers={"Authorization": "Bearer ${TOKEN}"}
    )
}

# HTTP transport
mcp_servers = {
    "http-server": McpServerConfig(
        type="http",
        url="https://api.example.com/mcp",
        headers={"X-API-Key": "${API_KEY}"}
    )
}
```

### Hooks

```python
HookEvent = Literal[
    "PreToolUse",       # Before tool execution (can block)
    "PostToolUse",      # After tool execution
    "UserPromptSubmit", # When user submits prompt
    "Stop",             # When execution stops
    "SubagentStop",     # When subagent completes
    "PreCompact",       # Before message compaction
]

# Hook configuration
options = ClaudeAgentOptions(
    hooks={
        'PreToolUse': [
            HookMatcher(matcher='Write|Edit', hooks=[my_hook_callback]),
        ]
    }
)

# Hook callback signature
async def my_hook_callback(input_data: dict, tool_use_id: str, context: HookContext) -> dict:
    # Return empty dict to allow, or:
    return {
        'hookSpecificOutput': {
            'hookEventName': input_data['hook_event_name'],
            'permissionDecision': 'deny',  # or 'allow', 'ask'
            'permissionDecisionReason': 'Reason here'
        }
    }
```

### File Checkpointing

Enable file checkpointing to support rewinding file changes:

```python
options = ClaudeAgentOptions(
    enable_file_checkpointing=True
)

# Later, rewind to a checkpoint using user message ID
await client.rewind_files(user_message_id)
```

**Note**: Checkpoint IDs are obtained from `UserMessage.uuid` fields in the message stream.

### Structured Output

```python
output_format = OutputFormat(
    type="json_schema",
    schema={
        "type": "object",
        "properties": {...},
        "required": [...]
    }
)
```

### Custom Tools

The SDK supports defining custom tools via the `@tool` decorator:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, SdkMcpTool
from pydantic import BaseModel

# Define input schema
class WeatherInput(BaseModel):
    location: str

# Use @tool decorator with explicit parameters
@tool(
    name="get_weather",
    description="Get current weather for a location",
    input_schema=WeatherInput
)
async def get_weather(input: WeatherInput) -> dict[str, Any]:
    return {"result": f"Weather for {input.location}: Sunny, 72°F"}

# Create MCP server from decorated tools
mcp_server = create_sdk_mcp_server(
    name="custom-tools",
    version="1.0.0",
    tools=[get_weather]
)

# Use in options
options = ClaudeAgentOptions(
    mcp_servers={"custom-tools": mcp_server}
)
```

**Key Points**:
- `@tool(name, description, input_schema)` - decorator requires all three parameters
- `input_schema` can be a Pydantic model or dict schema
- Handler must be async and return `dict[str, Any]`
- `create_sdk_mcp_server(name, version, tools)` - name is required
- Returns `McpSdkServerConfig` for use in options

### Error Handling

```python
from claude_agent_sdk import (
    CLINotFoundError,      # CLI not installed
    CLIConnectionError,    # Connection to CLI failed
    ProcessError,          # Process failed (has exit_code, stderr)
    CLIJSONDecodeError,    # Invalid JSON response
    ClaudeSDKError         # Base SDK error
)
```

### Streaming Input Modes

The SDK supports two input modes:

1. **Single Message Mode** (HTTP POST): Standard request-response with SSE streaming output
   - `POST /api/v1/query` - Send prompt, receive SSE stream
   - `POST /api/v1/query/single` - Send prompt, receive JSON response
   - Supports images via `images` field (base64 or URL)

2. **Streaming Input Mode** (WebSocket): Bidirectional streaming for real-time interaction
   - `WS /api/v1/query/ws` - WebSocket endpoint for bidirectional streaming
   - Allows sending additional messages during agent execution
   - Supports real-time interruption via `interrupt` message type
   - Required for AsyncGenerator-style input to SDK

```python
# WebSocket message types (client → server)
{
    "type": "prompt",
    "content": "Continue with the task",
    "images": [...]  # optional
}

{
    "type": "interrupt"
}

# Server → client uses same SSE event structure as HTTP streaming
```

---

## 2. FastAPI SSE Streaming

### Decision: Use `sse-starlette` library

**Rationale**: Production-ready, W3C SSE compliant, built-in keepalive, proper error handling.

**Alternatives Considered**:
- Native `StreamingResponse`: Works but requires manual SSE formatting
- Custom implementation: Higher maintenance burden

### Package Installation

```bash
uv add sse-starlette httpx-sse
```

### Basic Implementation

```python
from fastapi import FastAPI, Request
from sse_starlette import EventSourceResponse

app = FastAPI()

async def event_generator(request: Request):
    event_id = 0
    while True:
        if await request.is_disconnected():
            break

        yield {
            "event": "message",
            "id": str(event_id),
            "data": f"Event payload {event_id}",
        }
        event_id += 1
        await asyncio.sleep(0.1)

@app.get("/stream")
async def stream_events(request: Request):
    return EventSourceResponse(
        event_generator(request),
        ping=15,  # Keepalive every 15 seconds
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
```

### Client Disconnection Handling

```python
async def monitored_stream(request: Request):
    try:
        while True:
            if await request.is_disconnected():
                break
            yield {"data": "event"}
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        pass  # Client disconnected
    finally:
        # Cleanup resources
        pass
```

### Backpressure with Bounded Queue

```python
import asyncio

async def bounded_stream(request: Request):
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)

    async def producer():
        while not await request.is_disconnected():
            try:
                await asyncio.wait_for(queue.put(event), timeout=1.0)
            except asyncio.TimeoutError:
                continue  # Queue full, retry

    async def consumer():
        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                yield event
            except asyncio.TimeoutError:
                yield {"comment": "keepalive"}

    producer_task = asyncio.create_task(producer())
    try:
        async for event in consumer():
            yield event
    finally:
        producer_task.cancel()
```

### Error Handling (Mid-Stream)

Cannot change HTTP status once streaming starts. Use error events:

```python
async def error_wrapped_generator(source, request):
    try:
        async for item in source:
            if await request.is_disconnected():
                break
            yield {"data": item}
    except Exception as e:
        yield {
            "event": "error",
            "data": json.dumps({
                "type": type(e).__name__,
                "message": str(e)
            })
        }
    finally:
        yield {"event": "done", "data": "completed"}
```

### Testing with httpx-sse

```python
import pytest
import httpx
from httpx_sse import aconnect_sse
from httpx import ASGITransport

@pytest.mark.anyio
async def test_sse_endpoint():
    transport = ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with aconnect_sse(client, "GET", "/stream") as event_source:
            events = []
            async for sse in event_source.aiter_sse():
                events.append(sse)
                if len(events) >= 5:
                    break

            assert len(events) == 5
```

---

## 3. Session Storage Architecture

### Decision: PostgreSQL + Redis Hybrid

**Rationale**:
- Redis: Fast lookups, TTL expiration, pub/sub for real-time events
- PostgreSQL: Durable session history, audit trail, complex queries

**Alternatives Considered**:
- Redis only: Lacks durability and query capability
- PostgreSQL only: Too slow for active session lookups

### Redis Usage

```python
# Session cache
await redis.setex(f"session:{session_id}", ttl=3600, value=json.dumps(metadata))
await redis.get(f"session:{session_id}")

# Active connections tracking
await redis.sadd("active_sessions", session_id)
await redis.srem("active_sessions", session_id)
```

### PostgreSQL Schema

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    model VARCHAR(50) NOT NULL,
    total_turns INT NOT NULL DEFAULT 0,
    total_cost_usd DECIMAL(10, 6),
    metadata JSONB
);

CREATE TABLE session_messages (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id),
    message_type VARCHAR(20) NOT NULL,
    content JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 4. API Design Patterns

### Decision: REST + SSE Hybrid

**Rationale**: REST for CRUD operations, SSE for streaming responses.

**Endpoints**:
- `POST /api/v1/query` - Streaming query (returns SSE)
- `POST /api/v1/query/single` - Single message mode (returns JSON)
- `GET /api/v1/sessions/{id}` - Get session details
- `POST /api/v1/sessions/{id}/resume` - Resume session
- `POST /api/v1/sessions/{id}/fork` - Fork session
- `POST /api/v1/sessions/{id}/rewind` - Rewind to checkpoint
- `POST /api/v1/sessions/{id}/interrupt` - Interrupt running query
- `GET /api/v1/health` - Health check

### Versioning

URL path versioning: `/api/v1/`

---

## 5. Hook Webhook Architecture

### Decision: HTTP Callbacks

**Rationale**: Decoupled, language-agnostic, can be implemented by any backend.

**Flow**:
1. Client registers webhook URLs in query request
2. Server calls webhook on hook event
3. Webhook returns allow/deny/ask decision
4. Server applies decision to tool execution

```python
# Request format
{
    "prompt": "...",
    "hooks": {
        "PreToolUse": {
            "url": "https://example.com/webhooks/pre-tool",
            "headers": {"Authorization": "Bearer ..."},
            "timeout": 30
        }
    }
}

# Webhook payload
{
    "hook_event": "PreToolUse",
    "session_id": "...",
    "tool_name": "Write",
    "tool_input": {...}
}

# Webhook response
{
    "decision": "allow",  // or "deny", "ask"
    "reason": "...",
    "modified_input": {...}  // optional
}
```

---

## 6. Dependency Versions

Based on PyPI research (January 2026):

```toml
[project]
dependencies = [
    "claude-agent-sdk>=0.1.18",     
    "fastapi>=0.128.0",
    "uvicorn[standard]>=0.40.0",
    "pydantic>=2.12.0",
    "pydantic-settings>=2.12.0",
    "sqlalchemy[asyncio]>=2.0.45",
    "asyncpg>=0.31.0",
    "redis>=7.0.0",                   
    "sse-starlette>=3.0.0",           
    "httpx>=0.28.0",
    "structlog>=25.5.0",
    "tenacity>=9.1.0",
    "alembic>=1.17.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0.0",                 
    "pytest-asyncio>=1.3.0",          
    "httpx-sse>=0.4.0",
    "mypy>=1.19.0",
    "ruff>=0.14.0",
    "interrogate>=1.7.0",
]
```

## 7. Outstanding Considerations

### Handled by Implementation

1. **Session expiration**: Implement TTL in Redis, cleanup job for PostgreSQL
2. **Concurrent session access**: Use Redis distributed locks
3. **Large message handling**: Stream chunks, don't buffer entire response
4. **MCP server lifecycle**: Start on first use, cleanup on session end

### Deferred to Operations

1. **Horizontal scaling**: Requires sticky sessions or shared state
2. **Rate limiting**: Implement with `slowapi` per spec guidelines
3. **Metrics/monitoring**: Use structlog with correlation IDs

---

## Sources

- [Claude Agent Python SDK Documentation](https://platform.claude.com/docs/en/agent-sdk/python.md)
- [Claude Agent SDK Sessions](https://platform.claude.com/docs/en/agent-sdk/sessions.md)
- [Claude Agent SDK Hooks](https://platform.claude.com/docs/en/agent-sdk/hooks.md)
- [Claude Agent SDK Subagents](https://platform.claude.com/docs/en/agent-sdk/subagents.md)
- [sse-starlette GitHub](https://github.com/sysid/sse-starlette)
- [httpx-sse GitHub](https://github.com/florimondmanca/httpx-sse)
- [FastAPI Streaming Documentation](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
