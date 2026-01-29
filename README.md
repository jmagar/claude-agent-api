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

### Native Claude Agent SDK Endpoints

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

### OpenAI-Compatible Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/chat/completions` | Create chat completion (streaming/non-streaming) |
| `GET` | `/v1/models` | List available models |
| `GET` | `/v1/models/{model_id}` | Get model information |

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

## OpenAI API Compatibility

The API provides **drop-in OpenAI compatibility** at the `/v1/*` endpoints, allowing you to use the OpenAI Python client with minimal changes.

### Supported Endpoints

- **`POST /v1/chat/completions`** - Chat completions (streaming and non-streaming)
- **`GET /v1/models`** - List available models
- **`GET /v1/models/{model_id}`** - Get model information

### Usage with OpenAI Python Client

```python
from openai import OpenAI

# Initialize client with custom base URL
client = OpenAI(
    base_url="http://localhost:54000/v1",
    api_key="your-api-key",  # Your API key
)

# Non-streaming completion
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2 + 2?"}
    ]
)
print(response.choices[0].message.content)

# Streaming completion
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Count to 5"}],
    stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")

# List available models
models = client.models.list()
for model in models.data:
    print(f"- {model.id}")
```

### Model Name Mapping

OpenAI model names are automatically mapped to Claude models:

| OpenAI Model | Claude Model |
|--------------|--------------|
| `gpt-4` | `sonnet` |
| `gpt-3.5-turbo` | `haiku` |
| `gpt-4o` | `opus` |

The response will contain the **actual Claude model name** used (e.g., `sonnet`), not the OpenAI model name.

### Supported Parameters

| Parameter | Supported | Notes |
|-----------|-----------|-------|
| `model` | ✅ | Mapped to Claude model names |
| `messages` | ✅ | System messages → `system_prompt`, user/assistant → concatenated prompt |
| `stream` | ✅ | SSE streaming supported |
| `user` | ✅ | User identifier for tracking |
| `temperature` | ⚠️ | Accepted but ignored (not supported by Claude Agent SDK) |
| `top_p` | ⚠️ | Accepted but ignored (not supported by Claude Agent SDK) |
| `max_tokens` | ⚠️ | Accepted but ignored (SDK uses `max_turns` instead) |
| `stop` | ⚠️ | Accepted but ignored (not supported by Claude Agent SDK) |
| `n` | ❌ | Not supported (multiple completions) |
| `presence_penalty` | ❌ | Not supported |
| `frequency_penalty` | ❌ | Not supported |
| `logit_bias` | ❌ | Not supported |
| `tools` / `tool_choice` | ❌ | Not yet implemented (planned for Phase 2) |

**Note**: Parameters marked with ⚠️ are accepted for compatibility but log structured warnings and are not passed to the Claude Agent SDK.

### Unsupported Parameters Rationale

The Claude Agent SDK does not support sampling controls (`temperature`, `top_p`) or output token limits (`max_tokens`). The SDK uses `max_turns` (conversation turn limit) instead of `max_tokens` (output token limit), which have incompatible semantics and cannot be reliably converted.

### Authentication

The OpenAI endpoints support both authentication methods:

1. **Bearer Token** (OpenAI-style):

### Error Format

Errors follow the OpenAI error format:

```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "Unknown OpenAI model: gpt-5",
    "code": "invalid_model"
  }
}
```

Error type mapping:
- **`401`** → `authentication_error`
- **`400`** → `invalid_request_error`
- **`404`** → `invalid_request_error`
- **`429`** → `rate_limit_exceeded`
- **`5xx`** → `api_error`

### Streaming Format

OpenAI streaming uses Server-Sent Events (SSE) with the following format:

```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"sonnet","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"sonnet","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"sonnet","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

- First chunk always contains `delta.role="assistant"`
- Subsequent chunks contain `delta.content` with text
- Final chunk has `finish_reason` (`"stop"`, `"length"`, or `"error"`)
- Stream ends with `[DONE]` marker

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
| PostgreSQL | 54432 | Database |
| Redis | 54379 | Cache/pub-sub |

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

## CI/CD

GitHub Actions runs automated checks on every push and pull request:

- **Linting**: Ruff checks code style and common errors
- **Type Checking**: mypy verifies type safety with strict mode
- **Testing**: Fast test suite (unit + contract tests) with PostgreSQL and Redis

The CI pipeline ensures code quality and catches issues before merge. All checks must pass before merging to `main`.

### Branch Protection

To enforce CI checks in your repository:
1. Go to Settings > Branches > Add rule
2. Branch name pattern: `main`
3. Enable "Require status checks to pass before merging"
4. Select: `test` (the job name from ci.yml)

## Documentation

- [API Specification](specs/001-claude-agent-api/contracts/openapi.yaml)
- [Quick Start Guide](specs/001-claude-agent-api/quickstart.md)
- [Data Model](specs/001-claude-agent-api/data-model.md)
- [Feature Spec](specs/001-claude-agent-api/spec.md)

## License

MIT
