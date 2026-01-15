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

## Development Environment Note

We are developing inside a code-server container. When we deploy docker services, they are run on the container host. To be able to successfully reach those hosts you can use the host's Tailscale IP, `100.120.242.29`. The code-server container's docker compose also contains extra hosts: `host.docker.internal:host-gateway`, so you should also be able to use `http://host.docker.internal:<port>`.

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

**Note:** mypy configuration is retained during migration but ty is the primary type checker.

## Key Patterns

- Protocol-based dependency injection via FastAPI `Depends()`
- SSE streaming with sse-starlette and bounded queues
- Session storage: Redis (cache) + PostgreSQL (durability)
- Webhook-based hooks for tool approval

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

<!-- MANUAL ADDITIONS START -->

## Port Assignments

| Service | Port | Description |
|---------|------|-------------|
| API | 54000 | FastAPI server |
| PostgreSQL | 53432 | Database |
| Redis | 53380 | Cache/pub-sub |

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
