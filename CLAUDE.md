# Claude Agent API

HTTP API service wrapping the Claude Agent Python SDK with full feature parity.

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI + claude-agent-sdk
- **Database**: PostgreSQL (sessions, audit) + Redis (cache, pub/sub)
- **Testing**: pytest, pytest-asyncio, httpx-sse
- **Type Checking**: ty (Astral's fast type checker)

## Project Structure

```text
apps/
└── api/
    ├── main.py              # FastAPI entry point
    ├── config.py            # Settings (pydantic-settings)
    ├── protocols.py         # Protocol interfaces
    ├── exceptions.py        # Custom exceptions
    ├── dependencies.py      # FastAPI dependencies
    ├── middleware/          # Correlation ID, logging
    ├── schemas/             # Pydantic request/response models
    ├── models/              # SQLAlchemy models
    ├── adapters/            # Protocol implementations
    ├── services/            # Business logic
    └── routes/              # API endpoints

tests/
├── conftest.py
├── contract/                # OpenAPI contract tests
├── integration/             # Endpoint integration tests
└── unit/                    # Unit tests

alembic/                     # Database migrations
```

## Anthropic API Key Unnecessary

Do not set environment variable `ANTHROPIC_API_KEY`, we are logged in with our Claude Max subscription which we can use the Claude Agent SDK with. If you set that variable, then using our Claude Max subscription will NOT work.

## Commands

```bash
# Install dependencies
uv sync

# Start infrastructure
docker compose up -d

# Run migrations
uv run alembic upgrade head

# Start dev server
uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 54000 --reload

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=apps/api --cov-report=term-missing

# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run ty check
```

## Code Style

- **Protocols**: Use `typing.Protocol` for abstractions, implementations in `adapters/`
- **Async**: All I/O operations use async/await
- **Logging**: structlog with correlation IDs
- **TDD**: RED-GREEN-REFACTOR for all features

## Type Safety (STRICTLY ENFORCED)

**ZERO TOLERANCE FOR `Any` TYPES.** This is non-negotiable.

- **NO `Any`**: Never use `typing.Any` or `dict[str, Any]`
- **NO implicit Any**: All function parameters and returns must be explicitly typed
- **NO `# type: ignore`**: Fix the type issue instead of ignoring it

**What to use instead of `Any`:**

| Instead of | Use |
|------------|-----|
| `Any` | Specific type, `object`, `TypeVar`, or `Protocol` |
| `dict[str, Any]` | `TypedDict` with explicit fields |
| `list[Any]` | `list[SpecificType]` or generic `list[T]` |
| `Callable[..., Any]` | `Callable[[Args], ReturnType]` or `Protocol` |
| Unknown JSON | `JsonValue` type alias (recursive union) |

**Enforcement:**

```bash
# ty must pass with strict error rules
uv run ty check

# ruff will catch Any usage
uv run ruff check . --select=ANN401
```

If external libraries return `Any`, wrap them in typed adapter functions.

**Note:** ty is the primary type checker. mypy configuration is retained in pyproject.toml for reference only.

## Key Patterns

- Protocol-based dependency injection via FastAPI `Depends()`
- SSE streaming with sse-starlette and bounded queues
- Session storage: Redis (cache) + PostgreSQL (durability)
- Webhook-based hooks for tool approval

## Server-Side MCP Configuration

The API supports **automatic MCP server configuration injection** using a three-tier configuration system. This enables all requests to access configured MCP tools without requiring per-request configuration.

### Three-Tier Configuration System

MCP servers can be configured at three levels with clear precedence:

1. **Application-Level** (`.mcp-server-config.json` file in project root)
   - Global server configurations available to all API keys
   - Supports environment variable resolution with `${VAR_NAME}` syntax
   - Cached on first load for performance

2. **API-Key-Level** (Redis database, scoped per API key)
   - Per-tenant MCP server configurations
   - Complete isolation between API keys (multi-tenant safe)
   - Managed via `/api/v1/mcp-servers` endpoints

3. **Request-Level** (QueryRequest.mcp_servers field)
   - Per-request override capability
   - Highest precedence (replaces all server-side configs)
   - Explicit opt-out with empty dict `{}`

**Precedence Order:** Application < API-Key < Request (lowest to highest)

### Configuration File Format

Create `.mcp-server-config.json` in the project root:

```json
{
  "mcpServers": {
    "github": {
      "type": "stdio",
      "command": "mcp-github",
      "args": ["--repo", "myorg/myrepo"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "postgres": {
      "type": "stdio",
      "command": "mcp-postgres",
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    },
    "slack": {
      "type": "sse",
      "url": "https://api.slack.com/mcp",
      "headers": {
        "Authorization": "Bearer ${SLACK_TOKEN}"
      },
      "enabled": false
    }
  }
}
```

See `.mcp-server-config.json.example` for comprehensive examples.

### Environment Variable Resolution

Environment variables are resolved **server-side** at load time using `${VAR_NAME}` syntax:

- Variables must match pattern: `${[A-Z_][A-Z0-9_]*}` (uppercase, underscores, numbers)
- Missing variables log warnings and leave placeholder unchanged
- Resolution happens recursively in nested objects and arrays
- Values are cached after first resolution

**Security:** Environment variables are resolved from the server's environment, NOT user input. This prevents injection attacks.

### API-Key Scoped Configuration

Per-tenant MCP servers can be managed via REST API:

```bash
# Create server for API key
curl -X POST http://localhost:54000/api/v1/mcp-servers \
  -H "X-API-Key: tenant-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom-tool",
    "transport_type": "stdio",
    "command": "python custom_tool.py",
    "enabled": true
  }'

# List servers (scoped to API key)
curl http://localhost:54000/api/v1/mcp-servers \
  -H "X-API-Key: tenant-key-123"
```

**Isolation:** API keys cannot access each other's MCP servers. Redis keys use pattern: `mcp_server:{api_key}:{name}`.

### Request-Level Override

Control MCP configuration per-request via the `mcp_servers` field:

```python
# Use server-side configs (application + api-key)
request = QueryRequest(prompt="...", mcp_servers=None)

# Explicitly disable all MCP servers
request = QueryRequest(prompt="...", mcp_servers={})

# Provide custom configs (replaces all server-side)
request = QueryRequest(
    prompt="...",
    mcp_servers={
        "custom": {
            "type": "stdio",
            "command": "custom-mcp-server"
        }
    }
)
```

### Merge Behavior

When `mcp_servers` is `None` (or omitted), the API merges configurations:

```
Final Config = Application Config ← API-Key Config
```

Same-name servers from API-key tier **completely replace** application-tier servers (not deep merge).

### Security Features

1. **Credential Sanitization**: Sensitive fields (api_key, token, password, etc.) are redacted in logs
2. **Command Injection Prevention**: Shell metacharacters (`;`, `|`, `` ` ``, etc.) are blocked
3. **SSRF Prevention**: Internal URLs (localhost, 10.x.x.x, 169.254.169.254, etc.) are rejected
4. **Multi-Tenant Isolation**: API keys cannot access other tenants' configurations

### OpenAI Compatibility

Server-side MCP configurations are **automatically available** to OpenAI-compatible endpoints:

```bash
# Tools from .mcp-server-config.json are accessible
curl -X POST http://localhost:54000/v1/chat/completions \
  -H "Authorization: Bearer api-key-123" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Use MCP tool to..."}]
  }'
```

No client-side MCP configuration needed - servers are injected automatically.

### Implementation Details

- **Loader**: `McpConfigLoader` handles file I/O, env var resolution, and merge logic
- **Injector**: `McpConfigInjector` coordinates all three tiers before SDK execution
- **Validator**: `ConfigValidator` enforces security rules (command injection, SSRF, credentials)
- **Storage**: `McpServerConfigService` manages Redis storage with API-key scoping

For detailed requirements and design decisions, see:
- [Server-Side MCP Spec](specs/server-side-mcp/spec.md)
- [Requirements](specs/server-side-mcp/requirements.md)
- [Design](specs/server-side-mcp/design.md)

## OpenAI API Compatibility

The API provides **OpenAI-compatible endpoints** at `/v1/*` for drop-in compatibility with OpenAI clients and tools.

### Architecture

The OpenAI compatibility layer is **isolated** in the `/v1` namespace with zero impact on existing `/api/v1` endpoints:

```text
apps/api/
├── routes/
│   ├── openai/              # OpenAI-compatible routes
│   │   ├── chat.py          # POST /v1/chat/completions
│   │   ├── models.py        # GET /v1/models, GET /v1/models/{model_id}
│   │   └── dependencies.py  # DI providers
│   └── [existing routes]    # Native endpoints unchanged
├── services/
│   ├── openai/              # Translation layer
│   │   ├── translator.py    # RequestTranslator, ResponseTranslator
│   │   ├── streaming.py     # StreamingAdapter
│   │   ├── models.py        # ModelMapper
│   │   └── errors.py        # ErrorTranslator
│   └── [existing services]
└── middleware/
    ├── openai_auth.py       # BearerAuthMiddleware (Bearer → X-API-Key)
    └── [existing middleware]
```

### Translation Components

1. **RequestTranslator**: Converts OpenAI `ChatCompletionRequest` to Claude `QueryRequest`
   - System messages → `system_prompt` field
   - User/assistant messages → concatenated prompt with role prefixes
   - Model name mapping via `ModelMapper`
   - Unsupported parameters logged with structured warnings

2. **ResponseTranslator**: Converts Claude `SingleQueryResponse` to OpenAI `ChatCompletion`
   - Content blocks (text only) → concatenated message content
   - Stop reason mapping: `completed` → `stop`, `max_turns_reached` → `length`, etc.
   - Usage data: `input_tokens` → `prompt_tokens`, `output_tokens` → `completion_tokens`

3. **StreamingAdapter**: Transforms Claude SSE events to OpenAI streaming chunks
   - Native `partial` events → OpenAI `delta.content` chunks
   - Native `result` events → OpenAI finish_reason chunk
   - Maintains consistent completion ID across all chunks
   - Yields `[DONE]` marker at stream end

4. **ModelMapper**: Bidirectional OpenAI ↔ Claude model name mapping
   - Hardcoded mapping: `gpt-4` → `sonnet`, `gpt-3.5-turbo` → `haiku`, `gpt-4o` → `opus`
   - Validates unknown model names with `ValueError`
   - List models endpoint returns OpenAI-formatted model info

5. **ErrorTranslator**: Maps API errors to OpenAI error format
   - Status code → error type mapping (401 → `authentication_error`, etc.)
   - Preserves error message and code from `APIError`

6. **BearerAuthMiddleware**: Extracts Bearer tokens for OpenAI compatibility
   - Only affects `/v1/*` routes (not `/api/v1/*`)
   - Extracts `Authorization: Bearer <token>` → `X-API-Key: <token>`
   - Preserves existing `X-API-Key` headers (no overwriting)

### Design Decisions

- **Message Concatenation**: OpenAI message arrays → single prompt string with role prefixes (`USER: content\n\n`)
- **Unsupported Parameters**: Accept but ignore `temperature`, `top_p`, `max_tokens`, `stop` (not supported by Claude Agent SDK)
- **Model Names in Responses**: Return actual Claude model name (e.g., `sonnet`), not OpenAI name (e.g., `gpt-4`)
- **Type Safety**: All JSON structures use `TypedDict` (zero `Any` types), Pydantic only for request validation
- **Error Format**: Exception handlers check route prefix (`/v1/*`) to apply OpenAI error format selectively
- **Middleware Order**: `ApiKeyAuthMiddleware` registered BEFORE `BearerAuthMiddleware` (executes in reverse order)

### Limitations

- **No Sampling Controls**: Claude Agent SDK does not support `temperature`, `top_p`, `max_tokens`, or `stop` sequences
- **Token vs Turn Limits**: SDK uses `max_turns` (conversation turn limit), not `max_tokens` (output token limit) - incompatible semantics
- **Tool Calling**: Not yet implemented (planned for Phase 2)
- **Multiple Completions**: `n` parameter not supported (SDK returns single response only)
- **Logprobs**: Not supported by Claude Agent SDK

### Testing

- **Unit Tests**: ≥90% coverage for all OpenAI service modules (translator, streaming, models, errors)
- **Integration Tests**: ≥80% coverage for OpenAI routes (chat, models)
- **Contract Tests**: Real OpenAI Python client validates end-to-end compatibility

## Specs

- [Feature Spec](specs/001-claude-agent-api/spec.md)
- [Implementation Plan](specs/001-claude-agent-api/plan.md)
- [API Contract](specs/001-claude-agent-api/contracts/openapi.yaml)
- [OpenAI Feature Spec](specs/openai-api/spec.md)
- [OpenAI Implementation Plan](specs/openai-api/plan.md)
- [OpenAI Architectural Decisions](specs/openai-api/decisions.md)
- [Server-Side MCP Spec](specs/server-side-mcp/spec.md)
- [Server-Side MCP Requirements](specs/server-side-mcp/requirements.md)
- [Server-Side MCP Design](specs/server-side-mcp/design.md)

<!-- MANUAL ADDITIONS START -->

## Port Assignments

| Service | Port | Description |
|---------|------|-------------|
| API | 54000 | FastAPI server |
| PostgreSQL | 54432 | Database |
| Redis | 54379 | Cache/pub-sub |

## Required Environment Variables

```bash
DATABASE_URL=           # PostgreSQL connection string
REDIS_URL=              # Redis connection string
API_KEY=                # API key for client authentication
```

## SDK Notes

- Use `ClaudeSDKClient` (not `query()`) for sessions, hooks, and checkpointing
- SDK requires Claude Code CLI installed: `npm install -g @anthropic-ai/claude-code`
- File checkpointing needs `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1` env var

<!-- MANUAL ADDITIONS END -->
