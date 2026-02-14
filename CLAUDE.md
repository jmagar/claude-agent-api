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

## Debug Mode & Swagger Docs

Set `DEBUG=true` in `.env` to enable:
- `/docs` - Swagger UI (OpenAPI interactive docs)
- `/redoc` - ReDoc (alternative API docs)

**Production**: Keep `DEBUG=false` to disable docs endpoints.

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

## Makefile Shortcuts

Convenient aliases for common workflows:

```bash
# Development
make dev          # Start API in foreground (replaces uvicorn command)
make dev-api      # Start API in background with logging
make dev-restart  # Restart dev server
make status       # Check server health

# Testing
make test-fast    # Unit + contract tests (fast, no SDK)
make test-cov     # Tests with coverage report
make check        # Lint + typecheck

# Database
make db-reset     # Full database reset (down, up, migrate)

# Logs
make logs-api     # Tail API logs
```

Run `make help` for all available commands.

## Code Style

- **Protocols**: Use `typing.Protocol` for abstractions, implementations in `adapters/`
- **Async**: All I/O operations use async/await
- **Logging**: structlog with correlation IDs
- **TDD**: RED-GREEN-REFACTOR for all features

### Testing Gotchas

- **pytest-asyncio disabled**: Tests use `anyio` instead to avoid event loop conflicts with FastAPI's BaseHTTPMiddleware (see pyproject.toml `-p no:asyncio` flag)
- **Test isolation**: conftest.py uses FileLock for cross-platform test database migration coordination across pytest-xdist workers
- **E2E tests**: Mark expensive tests with `@pytest.mark.e2e` - excluded from default runs

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

## Dependency Injection

All routes use FastAPI dependency injection for services. **Never instantiate services directly in routes.**

### Service Injection Example

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from apps.api.dependencies import (
    ApiKey,
    ProjectSvc,
    AgentSvc,
    get_project_service,
    get_agent_service,
)

router = APIRouter()

@router.get("/projects")
async def list_projects(
    api_key: ApiKey,
    project_svc: ProjectSvc,
) -> list[ProjectResponse]:
    """List all projects for the authenticated API key."""
    projects = await project_svc.list_projects(api_key)
    return [ProjectResponse.from_protocol(p) for p in projects]

@router.post("/agents")
async def create_agent(
    api_key: ApiKey,
    agent_svc: AgentSvc,
    request: CreateAgentRequest,
) -> AgentResponse:
    """Create a new agent configuration."""
    agent = await agent_svc.create_agent(api_key, request.to_protocol())
    return AgentResponse.from_protocol(agent)
```

### Available Service Dependencies

| Dependency Type | Provider Function | Purpose |
|----------------|-------------------|---------|
| `ApiKey` | `get_api_key()` | Authenticated API key extraction |
| `ProjectSvc` | `get_project_service()` | Project CRUD operations |
| `AgentSvc` | `get_agent_service()` | Agent configuration management |
| `ToolPresetSvc` | `get_tool_preset_service()` | Tool preset CRUD |
| `McpServerConfigSvc` | `get_mcp_server_config_service()` | MCP server configuration |
| `McpDiscoverySvc` | `get_mcp_discovery_service()` | MCP filesystem discovery |
| `McpShareSvc` | `get_mcp_share_service()` | MCP share token management |
| `SkillCrudSvc` | `get_skills_crud_service()` | Skills CRUD operations |
| `SlashCommandSvc` | `get_slash_command_service()` | Slash command CRUD |

All service types are annotated type aliases defined in `dependencies.py` using `Annotated[ServiceClass, Depends(provider)]`.

### Testing with DI Overrides

```python
import pytest
from fastapi.testclient import TestClient
from apps.api.dependencies import get_project_service
from apps.api.main import app

@pytest.fixture
def mock_project_service():
    """Mock project service for testing."""
    class MockProjectService:
        async def list_projects(self, api_key: str):
            return [{"id": "test-1", "name": "Test Project"}]
    return MockProjectService()

def test_list_projects(mock_project_service):
    """Test project listing with mocked service."""
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    client = TestClient(app)
    response = client.get(
        "/api/v1/projects",
        headers={"X-API-Key": "test-key"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1

    app.dependency_overrides.clear()
```

### Anti-Patterns to Avoid

**DON'T** instantiate services directly:
```python
# ❌ WRONG
@router.get("/projects")
async def list_projects(cache: RedisCache):
    project_svc = ProjectService(cache)  # Direct instantiation
    return await project_svc.list_projects()
```

**DON'T** create helper functions:
```python
# ❌ WRONG
def _get_project_service(cache: RedisCache) -> ProjectService:
    return ProjectService(cache)

@router.get("/projects")
async def list_projects(cache: RedisCache):
    project_svc = _get_project_service(cache)  # Helper anti-pattern
    return await project_svc.list_projects()
```

**DO** use dependency injection:
```python
# ✅ CORRECT
@router.get("/projects")
async def list_projects(
    api_key: ApiKey,
    project_svc: ProjectSvc,
):
    return await project_svc.list_projects(api_key)
```

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

**Core API Specs** (reference when working on native `/api/v1/*` endpoints):
- [Feature Spec](specs/001-claude-agent-api/spec.md) - Overall feature requirements and acceptance criteria
- [Implementation Plan](specs/001-claude-agent-api/plan.md) - Phased implementation strategy
- [API Contract](specs/001-claude-agent-api/contracts/openapi.yaml) - OpenAPI schema (source of truth for endpoints)

**OpenAI Compatibility** (reference when working on `/v1/*` endpoints):
- [OpenAI Feature Spec](specs/openai-api/spec.md) - OpenAI API compatibility requirements
- [OpenAI Implementation Plan](specs/openai-api/plan.md) - Translation layer implementation approach
- [OpenAI Architectural Decisions](specs/openai-api/decisions.md) - Key design decisions and trade-offs

**MCP Configuration System** (reference when working on MCP server features):
- [Server-Side MCP Spec](specs/server-side-mcp/spec.md) - Three-tier configuration system overview
- [Server-Side MCP Requirements](specs/server-side-mcp/requirements.md) - Security, validation, and isolation requirements
- [Server-Side MCP Design](specs/server-side-mcp/design.md) - Loader, injector, and validator architecture

<!-- MANUAL ADDITIONS START -->

## Port Assignments

| Service | Port | Description |
|---------|------|-------------|
| API | 54000 | FastAPI server |
| PostgreSQL | 54432 | Database (docker-compose) |
| Redis | 54379 | Cache/pub-sub (docker-compose) |
| Neo4j (Bolt) | 54687 | Graph database (docker-compose) |
| Neo4j (HTTP) | 54474 | Graph database HTTP (docker-compose) |
| Qdrant | 53333 | Vector database ⚠️ **EXTERNAL** |
| TEI | 52000 | Text Embeddings Inference ⚠️ **EXTERNAL** (100.74.16.82) |

**Note**: Qdrant and TEI are external services (not managed by docker-compose). Verify connectivity before starting.

## Required Environment Variables

```bash
# API & Database
DATABASE_URL=postgresql://postgres:postgres@localhost:54432/claude_agent
REDIS_URL=redis://localhost:54379
API_KEY=                # API key for client authentication

# Neo4j
NEO4J_URL=bolt://localhost:54687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=neo4jpassword

# External Services
QDRANT_URL=http://localhost:53333
TEI_URL=http://100.74.16.82:52000
```

## SDK Notes

- Use `ClaudeSDKClient` (not `query()`) for sessions, hooks, and checkpointing
- SDK requires Claude Code CLI installed: `npm install -g @anthropic-ai/claude-code`
- File checkpointing needs `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1` env var

## Common Pitfalls

**Session Management:**
- **Session Cleanup**: `ClaudeSDKClient` sessions must be explicitly closed with `.close()` to prevent resource leaks and connection exhaustion
- **Session State**: Failed requests can leave sessions in inconsistent state - always check session status before reusing

**MCP Configuration:**
- **Discovery Caching**: File-based MCP servers discovered via `.claude.json` are cached on first load - restart server to refresh after config changes
- **Environment Variables**: MCP env var resolution happens at load time - changes to `.env` require server restart
- **SSRF Prevention**: Internal URLs (localhost, 10.x.x.x, 169.254.x.x) are blocked for security - use external IPs or proper networking

**Type Safety:**
- **External Library Types**: If `ty check` fails on external library types that return `Any`, create a typed adapter function in `adapters/` instead of using `# type: ignore`
- **JsonValue Pattern**: Use the `JsonValue` recursive union type alias for unknown JSON structures instead of `dict[str, Any]`
- **Protocol vs Concrete**: Always inject Protocol interfaces in constructors, never concrete implementations (breaks testability)

**Testing:**
- **Database Sync**: Always run `make db-reset` after schema changes or migrations to ensure test database matches dev database
- **Test Isolation**: Never mutate `app_state` without restoring original values in `finally` block (causes test pollution)
- **Async Event Loop**: Tests use `anyio` instead of `pytest-asyncio` to avoid BaseHTTPMiddleware conflicts - don't override this

**Dependencies:**
- **Circular Imports**: Watch for circular dependencies between `response_helpers.py` and `responses.py` - use `TYPE_CHECKING` guards and local imports
- **Service Instantiation**: Never instantiate services directly in routes - always use FastAPI `Depends()` injection
- **Redis Patterns**: When scanning Redis keys, filter patterns like `session:owner:*` separately from `session:{id}` keys to avoid type mismatches

## Mem0 OSS Integration

The API integrates [Mem0 OSS](https://mem0.ai/) for persistent, graph-enhanced memory across conversations.

**Embedding Model:** Qwen/Qwen3-Embedding-0.6B (1024 dimensions) via TEI at http://100.74.16.82:52000

### Architecture

```
Request →
  mem0.search(user_id=api_key) → inject memories →
  Claude response →
  mem0.add(conversation, user_id=api_key)
```

### Configuration

**Complete Mem0 Configuration:**

```python
from mem0 import Memory
import os

config = {
    # LLM Provider (for memory extraction)
    "llm": {
        "provider": "openai",
        "config": {
            "base_url": "https://cli-api.tootie.tv/v1",
            "model": "gemini-3-flash-preview",
            "api_key": os.environ.get("LLM_API_KEY", "")
        }
    },

    # Embedder (TEI on remote host - Qwen/Qwen3-Embedding-0.6B)
    "embedder": {
        "provider": "openai",  # TEI exposes OpenAI-compatible API
        "config": {
            "model": "text-embedding-3-small",  # Dummy model name (TEI ignores this)
            "openai_base_url": "http://100.74.16.82:52000/v1",
            "embedding_dims": 1024,  # Qwen/Qwen3-Embedding-0.6B output dimension
            "api_key": "not-needed"  # TEI doesn't require auth
        }
    },

    # Vector Store (Qdrant)
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 53333,
            "collection_name": "mem0_memories",
            "embedding_model_dims": 1024,  # Must match embedder
            "distance": "cosine",
            "on_disk": True
        }
    },

    # Graph Store (Neo4j)
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": "bolt://localhost:54687",
            "username": "neo4j",
            "password": "neo4jpassword",
            "database": "neo4j"
        }
    },

    "version": "v1.1"
}

memory = Memory.from_config(config)
```

### Stack Details

| Component | Service | Model/Version | Dimensions |
|-----------|---------|---------------|------------|
| **LLM** | cli-api.tootie.tv | gemini-3-flash-preview | - |
| **Embeddings** | TEI (100.74.16.82:52000) | Qwen/Qwen3-Embedding-0.6B | 1024 |
| **Vector DB** | Qdrant (localhost:53333) | - | 1024 |
| **Graph DB** | Neo4j (localhost:54687) | 5-community | - |
| **History** | SQLite | ~/.mem0/history.db | - |

### Multi-Tenant Isolation

Mem0 provides built-in multi-tenancy through scoping parameters:

```python
# Map API key to user_id for tenant isolation
memory.add(
    messages="User prefers technical explanations",
    user_id=api_key,  # Tenant isolation
    agent_id="main",
    metadata={"category": "preferences"}
)

# Search scoped to specific tenant
results = memory.search(
    query="What are the user's preferences?",
    user_id=api_key,  # Only returns this tenant's memories
    agent_id="main"
)
```

**Isolation Guarantees:**
- Vector store: Filters applied at query time using user/agent IDs
- Graph store: Entities and relationships tagged with ownership metadata
- No cross-contamination: API keys cannot access each other's memories

### Graph Memory Features

- **Automatic Entity Extraction**: Extracts entities and relationships from conversations
- **Dual Storage**: Embeddings in Qdrant, relationships in Neo4j
- **Contextual Retrieval**: Returns vector matches plus related graph context
- **Per-Request Toggle**: Disable graph operations with `enable_graph=False` for performance

### Performance Considerations

- **Graph Operations**: Add ~100-200ms latency per request
- **Disable for High-Frequency**: Use `enable_graph=False` for routine conversations
- **Enable for Context**: Use graph for queries requiring relationship understanding

<!-- MANUAL ADDITIONS END -->
