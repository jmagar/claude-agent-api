.PHONY: dev dev-stop test lint typecheck fmt clean db-up db-down db-migrate help

# Default target
help:
	@echo "Available commands:"
	@echo "  make dev         - Start dev server with hot reload"
	@echo "  make dev-stop    - Stop the dev server"
	@echo "  make dev-restart - Restart the dev server"
	@echo "  make test        - Run all tests"
	@echo "  make test-unit   - Run unit tests only"
	@echo "  make test-fast   - Run unit + contract tests (no SDK)"
	@echo "  make lint        - Run ruff linter"
	@echo "  make fmt         - Format code with ruff"
	@echo "  make typecheck   - Run mypy type checker"
	@echo "  make check       - Run lint + typecheck"
	@echo "  make db-up       - Start PostgreSQL and Redis"
	@echo "  make db-down     - Stop PostgreSQL and Redis"
	@echo "  make db-migrate  - Run database migrations"
	@echo "  make clean       - Remove cache files"

# Development server
dev:
	uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 54000 --reload

dev-stop:
	@PID=$$(lsof -ti :54000 2>/dev/null) && kill $$PID 2>/dev/null && echo "Dev server stopped (PID $$PID)" || echo "No dev server running on port 54000"

dev-restart: dev-stop dev

# Testing
test:
	uv run pytest tests/ -v

test-unit:
	uv run pytest tests/unit -v

test-fast:
	uv run pytest tests/unit tests/contract -v

test-cov:
	uv run pytest --cov=apps/api --cov-report=term-missing

# Code quality
lint:
	uv run ruff check .

fmt:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy apps/api

check: lint typecheck

# Database
db-up:
	docker compose up -d postgres redis

db-down:
	docker compose down

db-migrate:
	uv run alembic upgrade head

# Cleanup
clean:
	rm -rf .cache .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
