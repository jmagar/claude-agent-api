# Claude Agent API

HTTP API service wrapping the Claude Agent Python SDK with full feature parity.

## Features

- SSE streaming for real-time agent responses
- Session management with resume/fork capabilities
- Tool configuration and restrictions
- MCP server integration
- Custom subagent definitions
- File checkpointing and rewind
- Webhook-based hooks for agent lifecycle events
- Structured JSON output support

## Quick Start

```bash
# Install dependencies
uv sync

# Start infrastructure
docker compose up -d

# Run migrations
uv run alembic upgrade head

# Start server
uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 54000 --reload
```

## Documentation

- [API Specification](specs/001-claude-agent-api/contracts/openapi.yaml)
- [Quick Start Guide](specs/001-claude-agent-api/quickstart.md)
- [Data Model](specs/001-claude-agent-api/data-model.md)

## License

MIT
