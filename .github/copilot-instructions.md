# Claude Agent API & Web - AI Coding Agent Instructions

## Project Overview

Monorepo framework for an AI Agent platform.
- **`apps/api`**: FastAPI/Python service wrapping Claude Agent SDK using Protocol-based architecture.
- **`apps/web`**: Next.js 14+ frontend for the chat interface.

## ⚠️ Critical Environment Rules

### 1. Networking (Code-Server Container)
We develop inside a container (code-server) but Docker services run on the **host**.
- **NEVER** use `localhost` for Docker services (Postgres, Redis).
- **ALWAYS** use the host Tailscale IP: `100.120.242.29`
- **Database**: `postgresql+asyncpg://user:pass@100.120.242.29:53432/db`
- **Redis**: `redis://100.120.242.29:53380/0`
- **Web**: Access via `http://100.120.242.29:3000` (if running locally) or through port forwarding.

### 2. Authentication (Claude Max)
- **DO NOT SET** `ANTHROPIC_API_KEY`.
- We use a **Claude Max Subscription** via the `claude-code` CLI.
- Setting the env var breaks authentication.
- Verify auth: `claude-code whoami` in the terminal.

## Backend Architecture (`apps/api`)

### Protocol-Based Dependency Injection (Critical)
**Rule**: Services must depend on `typing.Protocol` interfaces, never concrete classes.

1.  **Define Protocol**: `apps/api/protocols.py`
2.  **Implement**: `apps/api/adapters/` (e.g., `session_repo.py`)
3.  **Inject**: `apps/api/dependencies.py` using `Approved[Type, Depends(factory)]`

```python
# Protocol
class SessionRepository(Protocol):
    async def get(self, sid: str) -> Session: ...

# Dependency Alias (Use this in routes)
SessionRepo = Annotated[SessionRepository, Depends(get_session_repo)]
```

### Agent Service
- **Location**: `apps/api/services/agent/`
- **Streaming**: Uses SSE (Server-Sent Events) via `query_stream()`.
- **Events**: `init` -> `message` (chunks) -> `result` -> `done`.

### Type Safety (Zero Tolerance)
**Rule**: No `Any`. No implicit `Any`. No `# type: ignore`.
- Use `ty` (Astral's fast type checker) via `uv run ty check` or `make typecheck`.
- Replace `Any` with `TypedDict`, `Protocol`, or `object`.

## Frontend Architecture (`apps/web`)

- **Framework**: Next.js 16 (App Router).
- **Styling**: Tailwind CSS + Shadcn UI (inferred from components.json/utils).
- **State**: Check `contexts/` for global state management.
- **Testing**: Jest (`npm test`) and Playwright.

## Essential Workflow Commands

| Task | Command | Notes |
| :--- | :--- | :--- |
| **Start API** | `make dev` | Hot-reloading FastAPI server on :54000 |
| **Run API Tests** | `make test` | All tests (Unit + Contract + Integration) |
| **Fast Tests** | `make test-fast` | Skips slow SDK integration tests |
| **Lint API** | `make lint` | Runs `ruff` |
| **Type Check API** | `make check`| Runs `ruff` + `ty` |
| **DB Reset** | `make db-reset` | Recreates DB and runs migrations |

## Testing Strategy

- **Unit (`tests/unit`)**: Mock everything. **MUST** use `mock_claude_sdk` fixture for agent tests.
- **Contract (`tests/contract`)**: Validate OpenAPI specs against implementation.
- **Integration**: Real SDK calls (require explicit enable).
- **Concurrency**: Use `@pytest.mark.anyio`, **NOT** `pytest-asyncio`.

## Directory Structure

```text
apps/
├── api/                 # FastAPI Backend
│   ├── protocols.py     # Core interfaces (start here)
│   ├── adapters/        # Concrete implementations (Redis, Postgres)
│   ├── services/        # Business logic (Agent, Session)
│   ├── routes/          # API Endpoints
│   └── schemas/         # Pydantic models (Requests/Responses)
└── web/                 # Next.js Frontend
    ├── app/             # App Router pages
    ├── components/      # React components
    └── lib/             # Shared utilities
```
