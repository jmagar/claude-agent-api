# Suggested Commands

## Setup
- `uv sync`
- `docker compose up -d`
- `uv run alembic upgrade head`

## Dev
- `make dev` (foreground)
- `make dev-api` (background with logs in `.logs/api.log`)
- `make dev-stop`
- `make dev-restart`
- `make status`

## Logs
- `make logs`
- `make logs-api`

## Tests
- `make test`
- `make test-unit`
- `make test-fast`
- `make test-cov`
- `uv run pytest`

## Quality
- `make lint`
- `make fmt`
- `make typecheck`
- `make check`
- `uv run ruff check .`
- `uv run ruff format .`
- `uv run ty check`

## DB
- `make db-up`
- `make db-down`
- `make db-migrate`
- `make db-reset`

Source: `README.md`, `CLAUDE.md`, `Makefile`.