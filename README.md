# Claude Agent API

HTTP API service wrapping the Claude Agent Python SDK with full feature parity.

## Features

- **SSE Streaming** - Real-time agent responses via Server-Sent Events
- **Session Management** - Resume, fork, and maintain conversation context
- **Tool Configuration** - Control which tools agents can access
- **MCP Integration** - Connect external Model Context Protocol servers
- **Custom Subagents** - Define specialized agents for task delegation
- **File Checkpointing** - Track and rewind file changes
- **Webhook Hooks** - Intercept agent lifecycle events
- **Structured Output** - JSON schema-validated responses
- **Rate Limiting** - Protect against abuse with configurable limits

## Architecture

```text
apps/api/
├── main.py              # FastAPI application
├── config.py            # Settings (pydantic-settings)
├── routes/              # API endpoints
│   ├── query.py         # POST /query, /query/single
│   ├── sessions.py      # Session CRUD operations
│   ├── skills.py        # Skill listing
│   ├── websocket.py     # WebSocket streaming
│   └── health.py        # Health checks
├── services/            # Business logic
│   ├── agent.py         # Claude Agent SDK wrapper
│   ├── session.py       # Session management
│   └── webhook.py       # Hook callbacks
├── schemas/             # Pydantic models
├── models/              # SQLAlchemy models
└── adapters/            # Protocol implementations
```

### Distributed Session Management

The API uses a **dual-storage architecture** for sessions:

1. **PostgreSQL** - Source of truth for all session data
2. **Redis** - Cache layer + active session tracking

**Benefits:**
- ✅ Horizontal scaling (deploy N instances)
- ✅ Data durability (survives Redis restarts)
- ✅ Performance (Redis caching for hot path)

**Active Session Tracking:**
- Active sessions tracked in Redis: `active_session:{session_id}`
- Visible across all API instances
- Auto-cleanup via TTL (2 hours)

**Session Lifecycle:**
1. Create: Write to PostgreSQL → Cache in Redis
2. Read: Check Redis → Fallback to PostgreSQL
3. Update: Distributed lock → Update both stores
4. Delete: Remove from both Redis and PostgreSQL

See [ADR-001](docs/adr/0001-distributed-session-state.md) for details.

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- [uv](https://docs.astral.sh/uv/) package manager
- Claude Code CLI: `npm install -g @anthropic-ai/claude-code`

### Setup

```bash
# Clone and install
git clone <repository-url>
cd claude-agent-api
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start infrastructure
docker compose up -d

# Run migrations
uv run alembic upgrade head

# Start server
uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 54000 --reload
```

### Verify Installation

```bash
curl http://localhost:54000/api/v1/health
# {"status":"ok","version":"1.0.0","dependencies":{"redis":"ok","postgres":"ok"}}
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/query` | Stream agent response (SSE) |
| `POST` | `/api/v1/query/single` | Single response (no streaming) |
| `GET` | `/api/v1/sessions/{id}` | Get session details |
| `POST` | `/api/v1/sessions/{id}/resume` | Resume session |
| `POST` | `/api/v1/sessions/{id}/fork` | Fork session |
| `DELETE` | `/api/v1/sessions/{id}` | Delete session |
| `GET` | `/api/v1/skills` | List available skills |
| `GET` | `/api/v1/health` | Health check |

## Usage Examples

### Streaming Query

```bash
curl -X POST http://localhost:54000/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "prompt": "List Python files in the current directory",
    "allowed_tools": ["Glob", "Read"]
  }'
```

### Single Response Query

```bash
curl -X POST http://localhost:54000/api/v1/query/single \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "prompt": "What is 2 + 2?",
    "allowed_tools": []
  }'
```

### Resume Session

```bash
curl -X POST http://localhost:54000/api/v1/sessions/{session_id}/resume \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"prompt": "Continue with the previous task"}'
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEY` | Yes | - | API key for client authentication |
| `DATABASE_URL` | No | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `REDIS_URL` | No | `redis://...` | Redis connection string |
| `LOG_LEVEL` | No | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `DEBUG` | No | `false` | Enable debug mode (exposes /docs) |
| `ENABLE_FILE_CHECKPOINTING` | No | `false` | Enable SDK file checkpointing |
| `REQUEST_TIMEOUT` | No | `300` | Request timeout in seconds |
| `RATE_LIMIT_QUERY_PER_MINUTE` | No | `10` | Query endpoint rate limit |

### Port Assignments

| Service | Port | Description |
|---------|------|-------------|
| API | 54000 | FastAPI server |
| PostgreSQL | 53432 | Database |
| Redis | 53380 | Cache/pub-sub |

## Development

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=apps/api --cov-report=term-missing

# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy apps/api
```

## Documentation

- [API Specification](specs/001-claude-agent-api/contracts/openapi.yaml)
- [Quick Start Guide](specs/001-claude-agent-api/quickstart.md)
- [Data Model](specs/001-claude-agent-api/data-model.md)
- [Feature Spec](specs/001-claude-agent-api/spec.md)

## License

MIT
