.PHONY: dev dev-api dev-web dev-all dev-stop dev-stop-api dev-stop-web dev-restart test test-unit test-fast test-cov lint typecheck fmt check clean db-up db-down db-migrate db-reset logs logs-api logs-web status help

# Colors
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[0;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
BOLD := \033[1m
RESET := \033[0m

# Configuration
LOG_DIR := .logs
API_LOG := $(LOG_DIR)/api.log
WEB_LOG := $(LOG_DIR)/web.log

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev-all     - Start both API and web servers (with logging)"
	@echo "  make dev-api     - Start API server only (with logging)"
	@echo "  make dev-web     - Start web server only (with logging)"
	@echo "  make dev         - Start API server in foreground (no logging)"
	@echo "  make dev-stop    - Stop all dev servers"
	@echo "  make dev-restart - Restart all dev servers"
	@echo "  make logs        - Tail all logs"
	@echo "  make logs-api    - Tail API logs"
	@echo "  make logs-web    - Tail web logs"
	@echo "  make status      - Check server status"
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run all tests"
	@echo "  make test-unit   - Run unit tests only"
	@echo "  make test-fast   - Run unit + contract tests (no SDK)"
	@echo "  make test-cov    - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint        - Run ruff linter"
	@echo "  make fmt         - Format code with ruff"
	@echo "  make typecheck   - Run mypy type checker"
	@echo "  make check       - Run lint + typecheck"
	@echo ""
	@echo "Database:"
	@echo "  make db-up       - Start PostgreSQL and Redis"
	@echo "  make db-down     - Stop PostgreSQL and Redis"
	@echo "  make db-migrate  - Run database migrations"
	@echo "  make db-reset    - Reset database (down, up, migrate)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean       - Remove cache files"

# Create logs directory
$(LOG_DIR):
	@mkdir -p $(LOG_DIR)

# Development servers
dev:
	uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 54000 --reload

dev-api: $(LOG_DIR)
	@echo "$(CYAN)→ Starting API server$(RESET) (logs: $(API_LOG))"
	@if [ -f $(LOG_DIR)/api.pid ]; then \
		PID=$$(cat $(LOG_DIR)/api.pid); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "  Stopping existing API server (PID: $$PID)..."; \
			kill $$PID 2>/dev/null || true; \
			sleep 1; \
		fi; \
		rm -f $(LOG_DIR)/api.pid; \
	fi
	@bash -c "nohup uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 54000 --reload > $(API_LOG) 2>&1 & echo \$$! > $(LOG_DIR)/api.pid"
	@echo "  Waiting for API to be ready..."
	@count=0; \
	while [ $$count -lt 10 ]; do \
		sleep 1; \
		count=$$((count + 1)); \
		if curl -s http://localhost:54000/api/v1/health > /dev/null 2>&1; then \
			echo "$(GREEN)✓ API server ready$(RESET) on $(BLUE)http://localhost:54000$(RESET) (PID: $$(cat $(LOG_DIR)/api.pid))"; \
			exit 0; \
		fi; \
	done; \
	echo "$(RED)✗ API server failed to start$(RESET) (check logs: make logs-api)" >&2; \
	exit 1

dev-web: $(LOG_DIR)
	@echo "$(CYAN)→ Starting web server$(RESET) (logs: $(WEB_LOG))"
	@if [ -f $(LOG_DIR)/web.pid ]; then \
		PID=$$(cat $(LOG_DIR)/web.pid); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "  Stopping existing web server (PID: $$PID)..."; \
			kill $$PID 2>/dev/null || true; \
			sleep 1; \
		fi; \
		rm -f $(LOG_DIR)/web.pid; \
	fi
	@bash -c "cd apps/web; nohup pnpm dev > ../../$(WEB_LOG) 2>&1 & echo \$$! > ../../$(LOG_DIR)/web.pid"
	@echo "  Waiting for web server to be ready..."
	@count=0; \
	while [ $$count -lt 10 ]; do \
		sleep 1; \
		count=$$((count + 1)); \
		if curl -s http://localhost:53002 > /dev/null 2>&1; then \
			echo "$(GREEN)✓ Web server ready$(RESET) on $(BLUE)http://localhost:53002$(RESET) (PID: $$(cat $(LOG_DIR)/web.pid))"; \
			exit 0; \
		fi; \
	done; \
	echo "$(RED)✗ Web server failed to start$(RESET) (check logs: make logs-web)" >&2; \
	exit 1

dev-all: dev-api dev-web
	@echo ""
	@echo "$(BOLD)$(GREEN)════════════════════════════════════════$(RESET)"
	@echo "$(BOLD)$(GREEN)✓ All services running$(RESET)"
	@echo "$(BOLD)$(GREEN)════════════════════════════════════════$(RESET)"
	@echo ""
	@echo "$(BOLD)Services:$(RESET)"
	@echo "  API:  $(BLUE)http://localhost:54000$(RESET) (PID: $$(cat $(LOG_DIR)/api.pid))"
	@echo "  Web:  $(BLUE)http://localhost:53002$(RESET) (PID: $$(cat $(LOG_DIR)/web.pid))"
	@echo ""
	@echo "$(BOLD)Commands:$(RESET)"
	@echo "  $(CYAN)make logs$(RESET)       # View all logs"
	@echo "  $(CYAN)make status$(RESET)     # Check service health"
	@echo "  $(CYAN)make dev-stop$(RESET)   # Stop all services"
	@echo ""

dev-stop-api:
	@if [ -f $(LOG_DIR)/api.pid ]; then \
		PID=$$(cat $(LOG_DIR)/api.pid); \
		if ps -p $$PID > /dev/null 2>&1; then \
			kill $$PID 2>/dev/null && echo "$(GREEN)✓ API server stopped$(RESET) (PID: $$PID)" || echo "$(RED)  Failed to stop API server$(RESET)"; \
		else \
			echo "  API server not running (stale PID file)"; \
		fi; \
		rm -f $(LOG_DIR)/api.pid; \
	else \
		echo "  API server not running"; \
	fi

dev-stop-web:
	@if [ -f $(LOG_DIR)/web.pid ]; then \
		PID=$$(cat $(LOG_DIR)/web.pid); \
		if ps -p $$PID > /dev/null 2>&1; then \
			kill $$PID 2>/dev/null && echo "$(GREEN)✓ Web server stopped$(RESET) (PID: $$PID)" || echo "$(RED)  Failed to stop web server$(RESET)"; \
		else \
			echo "  Web server not running (stale PID file)"; \
		fi; \
		rm -f $(LOG_DIR)/web.pid; \
	else \
		echo "  Web server not running"; \
	fi

dev-stop: dev-stop-api dev-stop-web

dev-restart: dev-stop dev-all

# Testing
test:
	uv run pytest tests/ -v

test-unit:
	uv run pytest tests/unit -v

test-fast:
	uv run pytest tests/unit tests/contract -v

test-cov:
	uv run pytest tests/ -v --cov=apps.api --cov-report=term-missing --cov-report=html --cov-fail-under=80

# Code quality
lint:
	uv run ruff check .

fmt:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy apps/api tests/

check: lint typecheck

# Database
db-up:
	docker compose up -d postgres redis

db-down:
	docker compose down

db-migrate:
	uv run alembic upgrade head

db-reset: db-down db-up
	@echo "Waiting for PostgreSQL to be ready..."
	@for i in $$(seq 1 60); do \
		docker compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1 && break || sleep 1; \
	done
	@docker compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1 || (echo "PostgreSQL not ready after 60s" >&2 && exit 1)
	$(MAKE) db-migrate

# Logs
logs:
	@tail -f $(API_LOG) $(WEB_LOG)

logs-api:
	@tail -f $(API_LOG)

logs-web:
	@tail -f $(WEB_LOG)

# Status
status:
	@echo "$(BOLD)$(BLUE)════════════════════════════════════════$(RESET)"
	@echo "$(BOLD)$(BLUE)Service Status$(RESET)"
	@echo "$(BOLD)$(BLUE)════════════════════════════════════════$(RESET)"
	@echo ""
	@if [ -f $(LOG_DIR)/api.pid ]; then \
		PID=$$(cat $(LOG_DIR)/api.pid); \
		if ps -p $$PID > /dev/null 2>&1; then \
			if curl -s http://localhost:54000/api/v1/health > /dev/null 2>&1; then \
				echo "$(GREEN)✓ API:$(RESET)  Running (PID: $$PID) - $(BLUE)http://localhost:54000$(RESET)"; \
			else \
				echo "$(YELLOW)⚠ API:$(RESET)  Process running but not responding (PID: $$PID)"; \
			fi; \
		else \
			echo "$(RED)✗ API:$(RESET)  Not running (stale PID: $$PID)"; \
		fi; \
	else \
		echo "$(RED)✗ API:$(RESET)  Not running"; \
	fi
	@echo ""
	@if [ -f $(LOG_DIR)/web.pid ]; then \
		PID=$$(cat $(LOG_DIR)/web.pid); \
		if ps -p $$PID > /dev/null 2>&1; then \
			if curl -s http://localhost:53002 > /dev/null 2>&1; then \
				echo "$(GREEN)✓ Web:$(RESET)  Running (PID: $$PID) - $(BLUE)http://localhost:53002$(RESET)"; \
			else \
				echo "$(YELLOW)⚠ Web:$(RESET)  Process running but not responding (PID: $$PID)"; \
			fi; \
		else \
			echo "$(RED)✗ Web:$(RESET)  Not running (stale PID: $$PID)"; \
		fi; \
	else \
		echo "$(RED)✗ Web:$(RESET)  Not running"; \
	fi
	@echo ""

# Cleanup
clean:
	rm -rf .cache .pytest_cache .mypy_cache .ruff_cache $(LOG_DIR)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
