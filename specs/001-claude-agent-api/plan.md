# Implementation Plan: Claude Agent API

**Branch**: `001-claude-agent-api` | **Date**: 2026-01-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-claude-agent-api/spec.md`

## Summary

Build an HTTP API service wrapping the Claude Agent Python SDK (`claude-agent-sdk`) that exposes all SDK capabilities through RESTful endpoints and Server-Sent Events (SSE) streaming. The API enables autonomous Claude agent interactions with full feature parity including sessions, subagents, MCP servers, hooks, file checkpointing, and structured outputs.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: claude-agent-sdk, FastAPI, Pydantic, pydantic-settings, SQLAlchemy[asyncio], asyncpg, redis[asyncio], sse-starlette, httpx, structlog, tenacity, alembic
**Storage**: PostgreSQL (sessions, audit logs) + Redis (session cache, pub/sub for hooks)
**Testing**: pytest, pytest-asyncio, httpx, httpx-sse
**Target Platform**: Linux server (self-hosted, Docker Compose)
**Project Type**: Single Python service (FastAPI backend)
**Performance Goals**: 100 concurrent agent sessions, <2s time-to-first-token, 1000 events/sec streaming throughput
**Constraints**: <200ms p95 for non-streaming endpoints, session persistence across restarts
**Scale/Scope**: Single service deployment, 10k sessions/day

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Research-Driven Development** | PASS | SDK documentation researched, FastAPI SSE patterns documented |
| **II. Verification-First** | PASS | TDD methodology enforced, test requirements in spec |
| **III. Security by Default** | PASS | API keys via env vars, no secrets in code, permission modes |
| **IV. Modularity and Simplicity** | PASS | Protocol-based DI, routers per domain, <50 line functions |
| **V. Test-Driven Development** | PASS | RED-GREEN-REFACTOR enforced per spec guidelines |
| **VI. Self-Hosted Infrastructure** | PASS | PostgreSQL + Redis via Docker Compose, no cloud services |
| **VII. Permission-Based Operations** | PASS | Explicit permission modes, hook system for approval |
| **VIII. Tactical Revisions** | PASS | Minimal scope, no feature creep |

**Gate Status**: PASS - All constitution principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/001-claude-agent-api/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── openapi.yaml     # OpenAPI 3.1 specification
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
apps/
└── api/
    ├── __init__.py
    ├── main.py              # FastAPI app entry point
    ├── config.py            # Settings via pydantic-settings
    ├── protocols.py         # Protocol interfaces (Repository, Cache, etc.)
    ├── types.py             # Type aliases and TypedDicts
    ├── exceptions.py        # Custom exceptions
    ├── dependencies.py      # FastAPI dependencies
    ├── middleware/
    │   ├── __init__.py
    │   ├── correlation.py   # Correlation ID middleware
    │   └── logging.py       # Request logging middleware
    ├── schemas/
    │   ├── __init__.py
    │   ├── requests.py      # Pydantic request models
    │   ├── responses.py     # Pydantic response models
    │   └── messages.py      # SDK message type mappings
    ├── models/
    │   ├── __init__.py
    │   └── session.py       # SQLAlchemy session model
    ├── adapters/
    │   ├── __init__.py
    │   ├── session_repo.py  # Session repository implementation
    │   └── cache.py         # Redis cache implementation
    ├── services/
    │   ├── __init__.py
    │   ├── agent.py         # Claude Agent SDK wrapper
    │   └── session.py       # Session management service
    └── routes/
        ├── __init__.py
        ├── health.py        # Health check endpoints
        ├── query.py         # Query/stream endpoints
        └── sessions.py      # Session management endpoints (includes hook webhooks via services/webhook.py)

tests/
├── conftest.py              # Shared fixtures
├── contract/
│   └── test_openapi.py      # Contract tests against OpenAPI spec
├── integration/
│   ├── test_query.py        # Query endpoint integration tests
│   ├── test_sessions.py     # Session management tests
│   └── test_streaming.py    # SSE streaming tests
└── unit/
    ├── test_agent_service.py
    ├── test_session_service.py
    └── test_schemas.py

alembic/
├── alembic.ini
├── env.py
└── versions/
```

**Structure Decision**: Single FastAPI application in `apps/api/` with Protocol-based dependency injection. No frontend - API-only service. Database models in `models/`, Protocol interfaces in `protocols.py`, concrete implementations in `adapters/`.

## Complexity Tracking

No constitution violations requiring justification. Design follows established patterns:
- Single service (not microservices)
- Protocol + DI pattern (standard FastAPI pattern)
- PostgreSQL + Redis (both required for different purposes)

## Key Design Decisions

### 1. SDK Integration Pattern

Use `ClaudeSDKClient` (not `query()`) for:
- Session persistence with `resume` parameter
- Interrupt support via `interrupt()` method
- Hooks support (PreToolUse, PostToolUse, Stop)
- File checkpointing with `rewind_files()`

```python
async with ClaudeSDKClient(options) as client:
    await client.query(prompt, session_id=session_id)
    async for message in client.receive_response():
        yield message
```

### 2. Streaming Architecture

Use `sse-starlette.EventSourceResponse` with:
- Bounded queue (maxsize=100) for backpressure
- Client disconnect monitoring via `request.is_disconnected()`
- Error events instead of exceptions mid-stream
- Keepalive pings every 15 seconds

### 3. Session Storage

- **Redis**: Active session cache, quick lookups, TTL-based expiration
- **PostgreSQL**: Session history, audit trail, durability

### 4. Permission System

Three-tier permission model:
- `default`: Standard permission checks via `can_use_tool` callback
- `acceptEdits`: Auto-approve file modifications
- `bypassPermissions`: Skip all permission checks (dangerous)

### 5. Hook Implementation

Hooks execute server-side via HTTP callbacks:
- PreToolUse: POST to webhook URL with tool details
- PostToolUse: POST with tool result
- Stop: POST on agent completion

Webhook responses determine behavior (allow/deny/ask).

---

## Post-Design Constitution Check

*Re-evaluated after Phase 1 design completion.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Research-Driven** | PASS | research.md complete with SDK APIs, SSE patterns, dependency versions |
| **II. Verification-First** | PASS | Test structure defined, contract tests planned against OpenAPI spec |
| **III. Security by Default** | PASS | API key auth, env-based secrets, permission modes, no PII in logs |
| **IV. Modularity** | PASS | Protocol interfaces in protocols.py, implementations in adapters/, <50 line functions |
| **V. TDD** | PASS | Test directories created, fixtures planned, RED-GREEN-REFACTOR methodology |
| **VI. Self-Hosted** | PASS | PostgreSQL + Redis via Docker Compose, no cloud services |
| **VII. Permission-Based** | PASS | Three permission modes, hook system for tool approval |
| **VIII. Tactical** | PASS | Scope matches spec requirements, no feature creep |

**Post-Design Gate Status**: PASS - Design adheres to all constitution principles.

---

## Generated Artifacts

| Artifact | Status | Description |
|----------|--------|-------------|
| [research.md](research.md) | Complete | SDK APIs, SSE patterns, architecture decisions |
| [data-model.md](data-model.md) | Complete | Database entities, Pydantic schemas, type mappings |
| [contracts/openapi.yaml](contracts/openapi.yaml) | Complete | OpenAPI 3.1 specification for all endpoints |
| [quickstart.md](quickstart.md) | Complete | Setup guide, usage examples, troubleshooting |
| [tasks.md](tasks.md) | Complete | Implementation tasks organized by user story |

---

## Next Steps

1. Run `/speckit.tasks` to generate implementation tasks
2. Review generated tasks and adjust priorities if needed
3. Begin implementation following TDD methodology
