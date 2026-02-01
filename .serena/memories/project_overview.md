# Project Overview

- **Purpose**: HTTP API service wrapping the Claude Agent Python SDK with full feature parity.
- **Architecture**: FastAPI backend with protocol-based DI, SSE streaming, sessions (Postgres + Redis), MCP integration, OpenAI-compatible endpoints.
- **Structure**:
  - `apps/api/`: FastAPI app (config, routes, services, adapters, schemas, models)
  - `tests/`: unit, contract, integration
  - `alembic/`: migrations
- **Tech stack**:
  - Python 3.11+, FastAPI, uvicorn
  - Postgres (async SQLAlchemy + asyncpg)
  - Redis
  - claude-agent-sdk
  - structlog, sse-starlette

Source: `README.md`, `CLAUDE.md`.