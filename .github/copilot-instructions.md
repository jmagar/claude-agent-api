# Claude Agent API - AI Coding Agent Instructions

## Project Overview

FastAPI service that wraps the Claude Agent Python SDK, providing HTTP/SSE endpoints for streaming agent interactions. Uses protocol-based dependency injection with PostgreSQL (sessions/audit) and Redis (cache/pub-sub).

## Architecture & Key Patterns

### Protocol-Based DI (Critical Pattern)

All abstractions use `typing.Protocol` with implementations in `adapters/`. Services depend on protocol interfaces, NOT concrete classes:

```python
# apps/api/protocols.py - Define interface
class SessionRepository(Protocol):
    async def create(...) -> SessionData: ...

# apps/api/adapters/session_repo.py - Implementation
class SessionRepository:  # Same name, implements protocol
    async def create(...) -> SessionData: ...

# apps/api/dependencies.py - Injection
def get_session_repo() -> SessionRepository:
    return SessionRepository(...)  # Returns concrete type
```

**Dependencies are type aliases** pointing to `Annotated[Type, Depends(factory)]`:
- `AgentSvc = Annotated[AgentService, Depends(get_agent_service)]`
- Use these aliases in route signatures, never the factory functions directly

### Agent Service Architecture

**Location**: `apps/api/services/agent/` (now a package, not single file)

- `service.py` - Main `AgentService` class
- `handlers.py` - `MessageHandler` for SDK event processing
- `hooks.py` - `HookExecutor` for webhook callbacks
- `options.py` - `OptionsBuilder` for SDK configuration
- `types.py` - Typed response/context structures
- `utils.py` - Helper functions

**Streaming Pattern**: `query_stream()` returns `AsyncGenerator[dict[str, str], None]` with SSE events:
1. `init` - Session info (session_id, model)
2. `message` - Agent messages (user/assistant/system)
3. `result` - Final stats (turns, cost, usage)
4. `error` - Error events
5. `done` - Stream completion

### Request Schema Organization

Schemas split by category in `apps/api/schemas/requests/`:
- `query.py` - `QueryRequest` (prompt, tools, model config)
- `sessions.py` - Session management requests
- `control.py` - Session control (resume/fork/delete)
- `config.py` - Configuration schemas (hooks, MCP, subagents)

**Key validation patterns**:
- Use `@field_validator` for custom validation logic
- Use `@model_validator` for cross-field validation
- Model names use aliases: `model: str = Field("sonnet-4-20250514", alias="model")`

## Type Safety (STRICTLY ENFORCED)

**ZERO TOLERANCE for `Any` types.** This is non-negotiable.

- **NO `Any`**: Never use `typing.Any` or `dict[str, Any]`
- **NO implicit Any**: All parameters/returns must be explicitly typed
- **NO `# type: ignore`**: Fix the issue, don't silence it

**Instead of `Any`, use**:
- `dict[str, Any]` → `TypedDict` with explicit fields
- `list[Any]` → `list[SpecificType]`
- Unknown JSON → `dict[str, object]` (object is the root type, more specific than Any)

**Enforcement**: `mypy --strict` must pass. Run `make typecheck` before committing.

## Testing Architecture

### Test Categories

1. **Unit** (`tests/unit/`) - Pure logic, mocked dependencies
2. **Contract** (`tests/contract/`) - OpenAPI spec validation
3. **Integration** (`tests/integration/`) - Real SDK calls (requires Claude Max, skipped in CI)
4. **E2E** (`tests/e2e/`) - Full stack with real infrastructure

### Mock Strategy

**SDK Mocking** (`tests/mocks/claude_sdk.py`):
```python
from tests.mocks.claude_sdk import mock_claude_sdk

@pytest.mark.anyio
async def test_something(mock_claude_sdk: None) -> None:
    # Automatically patches claude_agent_sdk.ClaudeSDKClient
    # Returns mock responses without real API calls
```

**Key fixture**: `mock_claude_sdk` - Patches SDK globally, use in ALL tests except integration tests

### Important Test Notes

- **pytest-asyncio disabled**: Use `@pytest.mark.anyio` instead (see `pyproject.toml` addopts)
- **Integration tests skip by default**: Require `ALLOW_REAL_CLAUDE_API=1` env var
- **Parallel execution**: Tests run with `-n auto` (pytest-xdist)
- **DB/Redis**: Tests use real infrastructure at `100.120.242.29` (code-server container environment)

## Development Environment

### ⚠️ CRITICAL: Container Networking (READ THIS FIRST)

**We are developing inside a code-server container on an Unraid host.**

- **NEVER use `localhost` for Docker services** - It will NOT work
- **ALWAYS use `100.120.242.29` (host Tailscale IP)** or `host.docker.internal`
- Database URL: `postgresql+asyncpg://user:pass@100.120.242.29:53432/db`
- Redis URL: `redis://100.120.242.29:53380/0`

**Why**: Docker Compose services run on the Unraid host, NOT inside the code-server container. `localhost` points to the code-server container itself, where nothing is listening.

### ⚠️ CRITICAL: Claude Max Authentication (DO NOT IGNORE)

**DO NOT set `ANTHROPIC_API_KEY` environment variable.**

This is the #1 most common mistake. The Claude Agent SDK supports TWO authentication methods:
1. **API Key** (`ANTHROPIC_API_KEY` env var) - For paid API users
2. **Claude Max Subscription** - For Claude Max users (what we use)

**Setting `ANTHROPIC_API_KEY` will BREAK Claude Max authentication.** The SDK will try to use the API key instead of your Claude Max session, causing authentication failures.

**How to verify correct setup**:
```bash
# These should be UNSET or empty
echo $ANTHROPIC_API_KEY        # Should output nothing
env | grep ANTHROPIC_API_KEY   # Should return nothing

# You must be logged in via Claude Code CLI
claude-code whoami             # Should show your account
```

If you see authentication errors, check if `ANTHROPIC_API_KEY` is set and unset it.

### Essential Commands

```bash
# Dev workflow
make dev              # Start server (port 54000)
make dev-restart      # Kill & restart
make test-fast        # Unit + contract (no SDK)
make test             # All tests
make check            # Lint + typecheck

# Database
make db-up            # Start Postgres + Redis
make db-migrate       # Run Alembic migrations
make db-reset         # Full reset (down, up, migrate)

# Direct commands (when Makefile not enough)
uv sync               # Install dependencies
uv run pytest tests/unit -v -k test_name  # Run specific test
```

### Port Assignments

- API: `54000`
- PostgreSQL: `53432` (host), `5432` (container)
- Redis: `53380` (host), `6379` (container)

## Common Patterns & Anti-Patterns

### ✅ DO

- Use protocol-based DI with implementations in `adapters/`
- Use type aliases for dependencies: `AgentSvc`, `SessionSvc`, `ApiKey`
- Split large services into packages with specialized modules
- Mock SDK in unit tests with `mock_claude_sdk` fixture
- Use `@dataclass` for internal data structures
- Use `TypedDict` for dictionary types with known structure
- Validate with pydantic `@field_validator` and `@model_validator`

### ❌ DON'T

- Use `Any` types (use `object` or specific types)
- **Set `ANTHROPIC_API_KEY`** (breaks Claude Max auth - see Development Environment section)
- **Use `localhost` for Docker services** (wrong container - use `100.120.242.29`)
- Import concrete adapters in services (use protocols)
- Use `pytest-asyncio` decorator (use `@pytest.mark.anyio`)
- Create sessions in routes (let `AgentService.query_stream` handle it)
- Mix test categories (keep unit/integration/contract separate)

## File Organization

```
apps/api/
├── main.py              # FastAPI app with lifespan
├── config.py            # pydantic-settings
├── protocols.py         # Protocol interfaces
├── dependencies.py      # DI factories
├── middleware/          # Auth, logging, correlation, rate limiting
├── schemas/
│   ├── requests/        # Split by category (query, sessions, config)
│   ├── responses.py     # SSE event models
│   └── messages.py      # SDK message types
├── services/
│   ├── agent/           # Package with handlers, hooks, options
│   ├── session.py       # Session lifecycle
│   ├── webhook.py       # Hook callbacks
│   └── checkpoint.py    # File checkpointing
├── adapters/            # Protocol implementations
│   ├── cache.py         # RedisCache
│   └── session_repo.py  # SessionRepository
└── routes/              # Endpoint definitions
```
## SDK Integration Notes

### Authentication (Critical)

**The Claude Agent SDK works with Claude Max subscription WITHOUT an API key.**

- **DO NOT set `ANTHROPIC_API_KEY`** - We use Claude Max auth, not API key auth
- If `ANTHROPIC_API_KEY` is set, the SDK ignores Claude Max authentication
- Verify auth: `claude-code whoami` (must show logged-in user)
- See "Development Environment" section for detailed authentication setup

### SDK Usage

- **SDK Client**: Import from `claude_agent_sdk.ClaudeSDKClient`
- **Streaming**: SDK uses async generators: `query()` then `receive_response()`
- **Checkpointing**: Requires `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1` env var
- **Session IDs**: SDK generates UUIDs, extract from `init` event
- **Message Types**: SDK returns `AssistantMessage`, `QuestionMessage`, etc.
- **Message Types**: SDK returns `AssistantMessage`, `QuestionMessage`, etc.

## Code Style

- **Formatting**: ruff (line-length 88)
- **Imports**: isort via ruff, `apps` is first-party
- **Docstrings**: Google style with Args/Returns/Raises
- **Async**: All I/O is async/await
- **Logging**: structlog with correlation IDs (added by middleware)
- **Error Handling**: Custom exceptions in `apps/api/exceptions/` inherit from `APIError`

## When Adding Features

1. Define protocol in `protocols.py` if new abstraction needed
2. Create pydantic schemas in `schemas/requests/` or `schemas/responses.py`
3. Implement logic in appropriate `services/` module
4. Add adapter in `adapters/` if protocol implementation needed
5. Create route in `routes/`, use dependency type aliases
6. Write unit tests with mocked dependencies
7. Add contract test if new endpoint/schema
8. Run `make check` before committing

## References

- Full spec: `specs/001-claude-agent-api/spec.md`
- API contract: `specs/001-claude-agent-api/contracts/openapi.yaml`
- Refactor plans: `docs/plans/` (dated markdown files)
