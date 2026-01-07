# Claude Agent API

HTTP API service wrapping the Claude Agent Python SDK with full feature parity.

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI + claude-agent-sdk
- **Database**: PostgreSQL (sessions, audit) + Redis (cache, pub/sub)
- **Testing**: pytest, pytest-asyncio, httpx-sse

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

# Development Environment Note
WE are developing inside a code-server container, when we deploy docker services, they are run on the container host. To be able to successfully reach those hosts you can use the hosts Tailscale IP, 100.120.242.29. The code-server container's docker compose also containers extra hosts: "host.docker.internal:host-gateway", so you should also be able to use http://host.docker.internal:<port>

# Anthropic API Key Unnecessary
Do not set environment variable ANTHROPIC_API_KEY, we are logged in with our CLaude Max subscription which we can use the Claude Agent SDK with, if you set that variable, then using our Claude Max subscription will NOT worko


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
uv run mypy apps/api
```

## Code Style

- **Strict typing**: mypy strict mode, no `Any`
- **Protocols**: Use `typing.Protocol` for abstractions, implementations in `adapters/`
- **Async**: All I/O operations use async/await
- **Logging**: structlog with correlation IDs
- **TDD**: RED-GREEN-REFACTOR for all features

## Key Patterns

- Protocol-based dependency injection via FastAPI `Depends()`
- SSE streaming with sse-starlette and bounded queues
- Session storage: Redis (cache) + PostgreSQL (durability)
- Webhook-based hooks for tool approval

## Specs

- [Feature Spec](specs/001-claude-agent-api/spec.md)
- [Implementation Plan](specs/001-claude-agent-api/plan.md)
- [API Contract](specs/001-claude-agent-api/contracts/openapi.yaml)

<!-- MANUAL ADDITIONS START -->

## Port Assignments

| Service | Port | Description |
|---------|------|-------------|
| API | 54000 | FastAPI server |
| PostgreSQL | 53432 | Database |
| Redis | 53380 | Cache/pub-sub |

## Required Environment Variables

```bash
ANTHROPIC_API_KEY=      # Required - Claude API key
DATABASE_URL=           # PostgreSQL connection string
REDIS_URL=              # Redis connection string
API_KEY=                # API key for client authentication
```

## SDK Notes

- Use `ClaudeSDKClient` (not `query()`) for sessions, hooks, and checkpointing
- SDK requires Claude Code CLI installed: `npm install -g @anthropic-ai/claude-code`
- File checkpointing needs `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1` env var

<!-- MANUAL ADDITIONS END -->
