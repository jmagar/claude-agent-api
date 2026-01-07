# Quickstart: Claude Agent API

**Feature Branch**: `001-claude-agent-api`
**Date**: 2026-01-07

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Anthropic API key
- uv package manager

## Quick Setup

### 1. Clone and Setup Environment

```bash
# Clone repository
git clone <repository-url>
cd claude-agent-api

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` with your settings:

```bash
# Required
ANTHROPIC_API_KEY=your-api-key-here

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@100.120.242.29:53432/claude_agent

# Cache (Redis)
REDIS_URL=redis://100.120.242.29:53380/0

# API Settings
API_HOST=0.0.0.0
API_PORT=54000
API_KEY=your-api-key-for-clients

# Optional
LOG_LEVEL=INFO
```

### 3. Start Infrastructure

```bash
# Start PostgreSQL and Redis
docker compose up -d

# Verify services
docker compose ps
```

### 4. Run Migrations

```bash
# Apply database migrations
uv run alembic upgrade head
```

### 5. Start API Server

```bash
# Development mode with auto-reload
uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 54000 --reload

# Or via pnpm script
pnpm dev
```

### 6. Verify Installation

```bash
# Health check
curl http://localhost:54000/api/v1/health

# Expected response:
# {"status":"ok","version":"1.0.0","dependencies":{"redis":"ok","postgres":"ok"}}
```

---

## Basic Usage

### Send a Query (Streaming)

```bash
curl -X POST http://localhost:54000/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-for-clients" \
  -d '{
    "prompt": "List the Python files in the current directory",
    "allowed_tools": ["Glob", "Read"]
  }'
```

### Send a Query (Single Response)

```bash
curl -X POST http://localhost:54000/api/v1/query/single \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-for-clients" \
  -d '{
    "prompt": "What is 2 + 2?",
    "allowed_tools": []
  }'
```

### Resume a Session

```bash
curl -X POST http://localhost:54000/api/v1/sessions/{session_id}/resume \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-for-clients" \
  -d '{
    "prompt": "Continue with the previous task"
  }'
```

---

## Python Client Example

```python
import httpx
from httpx_sse import aconnect_sse
import asyncio
import json

API_URL = "http://localhost:54000/api/v1"
API_KEY = "your-api-key-for-clients"

async def stream_query(prompt: str, allowed_tools: list[str] | None = None):
    """Stream a query to the Claude Agent API."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
    }

    payload = {
        "prompt": prompt,
        "allowed_tools": allowed_tools or [],
    }

    async with httpx.AsyncClient() as client:
        async with aconnect_sse(
            client,
            "POST",
            f"{API_URL}/query",
            json=payload,
            headers=headers,
        ) as event_source:
            session_id = None

            async for sse in event_source.aiter_sse():
                data = json.loads(sse.data)

                if sse.event == "init":
                    session_id = data["session_id"]
                    print(f"Session started: {session_id}")

                elif sse.event == "message":
                    if data["type"] == "assistant":
                        for block in data["content"]:
                            if block["type"] == "text":
                                print(f"Claude: {block['text']}")
                            elif block["type"] == "tool_use":
                                print(f"Tool: {block['name']}")

                elif sse.event == "result":
                    print(f"\nCompleted in {data['duration_ms']}ms")
                    print(f"Cost: ${data.get('total_cost_usd', 0):.6f}")

            return session_id

# Run
asyncio.run(stream_query(
    "List the files in the current directory",
    ["Glob", "Read"]
))
```

---

## TypeScript Client Example

```typescript
import { EventSourceMessage, fetchEventSource } from '@microsoft/fetch-event-source';

const API_URL = 'http://localhost:54000/api/v1';
const API_KEY = 'your-api-key-for-clients';

interface QueryRequest {
  prompt: string;
  allowed_tools?: string[];
}

async function streamQuery(request: QueryRequest): Promise<string | null> {
  let sessionId: string | null = null;

  await fetchEventSource(`${API_URL}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    },
    body: JSON.stringify(request),
    onmessage(event: EventSourceMessage) {
      const data = JSON.parse(event.data);

      switch (event.event) {
        case 'init':
          sessionId = data.session_id;
          console.log(`Session started: ${sessionId}`);
          break;

        case 'message':
          if (data.type === 'assistant') {
            for (const block of data.content) {
              if (block.type === 'text') {
                console.log(`Claude: ${block.text}`);
              } else if (block.type === 'tool_use') {
                console.log(`Tool: ${block.name}`);
              }
            }
          }
          break;

        case 'result':
          console.log(`\nCompleted in ${data.duration_ms}ms`);
          console.log(`Cost: $${data.total_cost_usd?.toFixed(6) ?? '0'}`);
          break;
      }
    },
  });

  return sessionId;
}

// Usage
streamQuery({
  prompt: 'List the files in the current directory',
  allowed_tools: ['Glob', 'Read'],
});
```

---

## Docker Compose Reference

```yaml
# docker-compose.yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: claude-agent-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: claude_agent
    ports:
      - "53432:5432"
    volumes:
      - claude_agent_postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: claude-agent-redis
    command: redis-server --appendonly yes
    ports:
      - "53380:6379"
    volumes:
      - claude_agent_redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  claude_agent_postgres_data:
  claude_agent_redis_data:
```

---

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=apps/api --cov-report=term-missing

# Run specific test file
uv run pytest tests/integration/test_query.py

# Run only unit tests
uv run pytest tests/unit/
```

---

## Troubleshooting

### Connection Refused to Database

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check logs
docker compose logs postgres
```

### Redis Connection Error

```bash
# Check if Redis is running
docker compose ps redis

# Test connection
docker compose exec redis redis-cli ping
```

### API Key Invalid

Ensure your `ANTHROPIC_API_KEY` is set correctly in `.env` and has valid credits.

### Port Already in Use

If port 54000 is in use, change `API_PORT` in `.env` and restart:

```bash
# Check what's using the port
ss -tuln | grep 54000

# Use different port
API_PORT=53001
```

---

## Next Steps

- Read the [API Documentation](contracts/openapi.yaml) for full endpoint reference
- Review [Data Models](data-model.md) for schema details
- Check [Research Notes](research.md) for SDK integration patterns
