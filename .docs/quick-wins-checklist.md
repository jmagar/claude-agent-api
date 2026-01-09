# Quick Wins Checklist - Framework Best Practices
**Generated**: 2026-01-09
**Priority**: Immediate impact improvements

## Critical (Fix This Week)

### 1. Replace BaseHTTPMiddleware (4-6 hours)
**Impact**: HIGH - Fixes SSE/WebSocket stability issues

**Files to Update**:
- /mnt/cache/workspace/claude-agent-api/apps/api/middleware/correlation.py
- /mnt/cache/workspace/claude-agent-api/apps/api/middleware/logging.py
- /mnt/cache/workspace/claude-agent-api/apps/api/middleware/auth.py

**Pattern to Use**:
```python
from starlette.types import ASGIApp, Receive, Scope, Send

class CorrelationIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            # Middleware logic here
            pass
        await self.app(scope, receive, send)
```

**After Fix**:
- Remove `-p no:asyncio` from pytest config
- Test SSE streams under load
- Verify WebSocket connections stable

---

### 2. ✅ Add Redis Connection Pool (30 minutes) - COMPLETED
**Impact**: MEDIUM - Prevents connection exhaustion
**Status**: Fixed - Settings now configurable

**File**: /mnt/cache/workspace/claude-agent-api/apps/api/adapters/cache.py:105

**Change**:
```python
client = redis.from_url(
    redis_url,
    encoding="utf-8",
    decode_responses=False,
    max_connections=50,        # ← ADD THIS
    socket_connect_timeout=5,  # ← ADD THIS
    socket_timeout=5,          # ← ADD THIS
)
```

---

### 3. Add Dockerfile (1 hour)
**Impact**: MEDIUM - Simplifies deployment

**Create**: /mnt/cache/workspace/claude-agent-api/Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application
COPY apps/ ./apps/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Run migrations and start
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 54000"]
```

---

## High Priority (This Sprint)

### 4. Add Database Index (1 hour)
**Status**: N/A (PERF-001 fixed via Redis bulk fetch instead)
**Impact**: HIGH - N+1 cache reads eliminated

**Note**: Session listing performance issue was resolved by implementing bulk cache reads using Redis `mget` command. Database index not needed for this specific issue.

---

### 5. Session Ownership Check (2-3 hours)
**Impact**: HIGH - Critical security fix

**Files to Update**:
- /mnt/cache/workspace/claude-agent-api/apps/api/models/session.py (add owner_api_key column)
- /mnt/cache/workspace/claude-agent-api/apps/api/services/session.py (add ownership check)

**Pattern**:
```python
# In SessionService.get_session()
session = await self._repo.get(session_id)
if session and session.owner_api_key != current_api_key:
    raise SessionNotFoundError(session_id)  # Don't leak existence
```

---

## Medium Priority (Next Sprint)

### 6. Clean Ruff Violations (15 minutes)
```bash
uv run ruff check apps/api --fix
```

**Violations**:
- 3x TC006: runtime-cast-value
- 1x RUF100: unused-noqa
- 1x TC003: typing-only-standard-library-import

---

### 7. Add Request Size Limits (30 minutes)
**File**: /mnt/cache/workspace/claude-agent-api/apps/api/main.py

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Add after CORSMiddleware
app.add_middleware(
    RequestBodySizeLimitMiddleware,
    max_body_size=10 * 1024 * 1024,  # 10MB
)
```

---

### 8. Add Performance Tests (4 hours)
**Create**: /mnt/cache/workspace/claude-agent-api/tests/performance/

```python
# test_load.py
import pytest
import httpx

@pytest.mark.performance
async def test_concurrent_sessions():
    """Test 100 concurrent session creations."""
    async with httpx.AsyncClient() as client:
        tasks = [
            client.post("/api/v1/sessions", json={...})
            for _ in range(100)
        ]
        results = await asyncio.gather(*tasks)
        assert all(r.status_code == 201 for r in results)
```

---

## Low Priority (Backlog)

### 9. Increase Docstring Coverage (2-3 days)
**Target**: 70% (currently 54%)

**Focus Areas**:
- Internal helpers in services/
- Utility functions in adapters/
- Private methods (marked with leading underscore)

---

### 10. Add OpenTelemetry Tracing (1 week)
**Dependencies**:
```toml
dependencies = [
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-instrumentation-fastapi>=0.41b0",
]
```

**Pattern**:
```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = create_app()
FastAPIInstrumentor.instrument_app(app)
```

---

## Validation Commands

After each change, run:

```bash
# Type checking
uv run mypy apps/api --strict

# Linting
uv run ruff check apps/api

# Format
uv run ruff format apps/api

# Tests
uv run pytest

# Coverage
uv run pytest --cov=apps/api --cov-report=term-missing
```

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| mypy strict | ✅ Pass | ✅ Pass |
| Ruff violations | 5 | 0 |
| Test coverage | 82% | 85% |
| Docstring coverage | 54% | 70% |
| BaseHTTPMiddleware usage | 3 files | 0 files |
| Connection pools configured | 1/2 | 2/2 |
| Security tests | 0 | 5+ |
| Performance tests | 0 | 3+ |

---

## Estimated Total Effort

- **Critical**: 6-8 hours
- **High Priority**: 4-5 hours
- **Medium Priority**: 5-6 hours
- **Low Priority**: 2-3 weeks

**Total Sprint Effort**: 15-19 hours (2-3 days)

---

**Note**: Focus on Critical and High Priority items first. These provide immediate stability, security, and performance improvements.
