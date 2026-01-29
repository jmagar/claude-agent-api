# Remediation Guide - High Priority Fixes

**Date:** 2026-01-29
**Target Completion:** 2026-01-31
**Effort Estimate:** 5-6 hours for production readiness

---

## 1. Fix 20 Type Errors (ty strict mode)

### Issue Summary
`uv run ty check` reports 20 errors across the codebase. Most are fixable without major refactoring.

### Error Breakdown

#### Group A: Async Iteration (1 error - HIGH PRIORITY)

**Location:** `apps/api/routes/openai/chat.py:79`

```python
# BEFORE: Type error - not async-iterable
async for event in native_events:
    # native_events is a Coroutine, not AsyncIterator
```

**Fix:** Ensure `native_events` is awaited first:

```python
# AFTER: Properly awaited async generator
native_events_gen = native_events  # This should be an AsyncIterator
async for event in native_events_gen:
    # Parse event
```

**Action Items:**
- [ ] Review `native_events` generator function
- [ ] Ensure it returns `AsyncIterator[dict[str, str]]`
- [ ] Test SSE streaming end-to-end

#### Group B: Protocol Variance (2 errors - HIGH PRIORITY)

**Location:** `apps/api/routes/openai/dependencies.py:40`

```python
# BEFORE: Type mismatch
def get_model_mapper() -> ModelMapper:
    return ModelMapper()  # Protocol type vs implementation

# BEFORE: Type mismatch in translator init
return RequestTranslatorImpl(model_mapper)  # Expected Protocol, found Impl
```

**Root Cause:**
- `protocols.py` defines `ModelMapper` protocol
- `services/openai/models.py` defines `ModelMapperImpl` class
- Dependency injection returns wrong type

**Fix:** Ensure protocol conformance:

```python
# In protocols.py - Protocol definition
class ModelMapper(Protocol):
    def map_openai_to_claude(self, model_name: str) -> str: ...
    def map_claude_to_openai(self, model_name: str) -> str: ...

# In services/openai/models.py - Implementation
class ModelMapperImpl:
    def map_openai_to_claude(self, model_name: str) -> str: ...
    def map_claude_to_openai(self, model_name: str) -> str: ...

# In dependencies.py - Return protocol, not implementation
def get_model_mapper() -> ModelMapper:
    impl: ModelMapper = ModelMapperImpl()  # Type as protocol
    return impl
```

**Action Items:**
- [ ] Check `protocols.py` for `ModelMapper` definition
- [ ] Verify `ModelMapperImpl` implements all protocol methods
- [ ] Use protocol type in dependency functions
- [ ] Add explicit type annotation: `impl: ModelMapper = ModelMapperImpl()`

#### Group C: Cast Operations (7 errors - MEDIUM PRIORITY)

**Location:** `apps/api/services/agent/handlers.py:473`

```python
# BEFORE: Overly broad cast type
mapped = map_sdk_content_block(block)
blocks.append(ContentBlockSchema(**cast("dict[str, object]", mapped)))
# ↑ object type too broad, loses type info
```

**Fix:** Use TypedDict instead of cast:

```python
# AFTER: Proper typed dictionary
from typing import TypedDict

class ContentBlockDict(TypedDict):
    type: Literal["text", "thinking", "tool_use", "tool_result"]
    content: str
    thinking: str | None
    tool_use_id: str | None

def map_sdk_content_block(block: dict) -> ContentBlockDict:
    return cast(ContentBlockDict, {
        "type": block.get("type"),
        "content": block.get("content"),
        # ... other fields
    })

blocks.append(ContentBlockSchema(**mapped))  # No cast needed
```

**Action Items:**
- [ ] Define `ContentBlockDict` TypedDict
- [ ] Update `map_sdk_content_block()` return type
- [ ] Remove `cast("dict[str, object]", ...)` calls
- [ ] Let type checker infer types from TypedDict

#### Group D: Other Type Mismatches (10 errors - LOW PRIORITY)

These are mostly datetime coercion issues and can be fixed incrementally:

**Location:** `apps/api/routes/skills.py` (8 ignores)

```python
# BEFORE: Datetime coercion
created_at=s.created_at,  # type: ignore[arg-type]
```

**Fix:** Ensure consistent datetime types:

```python
# AFTER: Explicit datetime handling
def _to_iso_string(dt: datetime) -> str:
    """Convert datetime to ISO format string."""
    return dt.isoformat()

created_at=_to_iso_string(s.created_at),
```

**Action Items:**
- [ ] Create datetime utility functions
- [ ] Apply consistently across routes
- [ ] Remove `# type: ignore` comments
- [ ] Run `ty check` after each fix

### Implementation Steps

```bash
# 1. Check current errors
uv run ty check 2>&1 | grep "error\[" > /tmp/errors.txt

# 2. Fix async iteration first (OpenAI chat)
# - Review apps/api/routes/openai/chat.py
# - Test: uv run pytest tests/integration/openai/

# 3. Fix protocol variance
# - Review apps/api/protocols.py
# - Review apps/api/routes/openai/dependencies.py
# - Test: uv run pytest tests/unit/openai/

# 4. Fix cast operations
# - Create TypedDict for content blocks
# - Update services/agent/handlers.py
# - Test: uv run pytest tests/unit/agent/

# 5. Fix datetime coercion
# - Create datetime utilities
# - Apply to routes/skills.py, routes/tool_presets.py
# - Test: uv run pytest tests/unit/routes/

# 6. Final verification
uv run ty check  # Should pass with 0 errors
```

**Estimated Time:** 2-3 hours

---

## 2. Remove .env from Git History

### Issue Summary
`.env` file is in git history and may contain secrets (API keys, database URLs, Redis URLs).

### Risk Assessment

- **Severity:** CRITICAL
- **Secrets at Risk:** API keys, database credentials, Redis URL
- **Current Status:** `.gitignore` is configured but `.env` was previously committed

### Verification

```bash
# Check if .env is in git history
git log --all --full-history -- .env

# Check if it's in current index
git ls-files | grep .env
```

### Remediation Steps

#### Option 1: Using git-filter-repo (Recommended)

```bash
cd /home/jmagar/workspace/claude-agent-api

# Install git-filter-repo if needed
pip install git-filter-repo

# Remove .env from entire history
git-filter-repo --path .env --invert-paths

# Force push to all remotes
git push --force-with-lease --all
git push --force-with-lease --tags
```

#### Option 2: Using BFG Repo-Cleaner (Alternative)

```bash
# Install BFG
brew install bfg  # or apt-get install bfg

# Remove .env from history
bfg --delete-files .env

# Clean and push
git reflog expire --expire=now --all
git gc --prune=now
git push --force
```

### Secret Rotation (MANDATORY)

After removing from git history, rotate ALL secrets:

```bash
# 1. Generate new API key
# - Login to Anthropic console
# - Create new API key
# - Update in: config.py, .env.example, CI/CD

# 2. PostgreSQL credentials
# - Create new database user
# - Update DATABASE_URL in: config.py, .env.example

# 3. Redis credentials (if auth enabled)
# - Update REDIS_URL in: config.py, .env.example

# 4. Update all systems
# - Environment variables in deployment
# - CI/CD secrets (GitHub Actions)
# - Docker secrets (if applicable)
```

### Verification Checklist

```bash
# Verify .env is removed from history
git log --all --full-history -p -- .env | head -20
# Should return empty

# Verify .gitignore is configured correctly
cat .gitignore | grep .env
# Should show: .env (in .gitignore)

# Verify .env.example has no secrets
grep -E "sk-|pk_|password.*=" .env.example
# Should return empty (only placeholders)

# Test local setup still works
rm -f .env
cp .env.example .env
# Edit with new credentials
uv sync
```

### Implementation Steps

1. **Backup current repo**
   ```bash
   git clone --mirror . /tmp/claude-agent-api-backup.git
   ```

2. **Remove from history**
   ```bash
   git-filter-repo --path .env --invert-paths
   ```

3. **Verify history is clean**
   ```bash
   git log --all --full-history -- .env | wc -l  # Should be 0
   ```

4. **Rotate secrets**
   - [ ] Anthropic API key
   - [ ] PostgreSQL URL
   - [ ] Redis URL
   - [ ] Any other API keys

5. **Update references**
   - [ ] `.env.example` - use placeholders only
   - [ ] GitHub Actions secrets
   - [ ] Docker compose environment variables
   - [ ] Production deployment config

6. **Force push to all remotes**
   ```bash
   git push --force-with-lease --all
   git push --force-with-lease --tags
   ```

**Estimated Time:** 1 hour

---

## 3. Add HTTPS Documentation & Security Headers

### Issue Summary
API binds to `0.0.0.0` without HTTPS requirement. Depends on reverse proxy.

### Current Setup
```yaml
api_host: str = Field(default="0.0.0.0", ...)
api_port: int = Field(default=54000, ...)
# No HTTPS enforcement - relies on proxy
```

### Action Items

#### A. Create Security Documentation

**File:** `.docs/SECURITY.md`

```markdown
# Security Guide

## HTTPS Configuration (MANDATORY)

The Claude Agent API does **NOT** enforce HTTPS internally.
This is by design - the API expects to run behind a reverse proxy.

### Production Deployment

#### Option 1: Caddy (Recommended)

```caddy
api.example.com {
    reverse_proxy localhost:54000 {
        header_up X-Forwarded-For {http.request.header.CF-Connecting-IP}
        header_up X-Forwarded-Proto https
    }
}
```

#### Option 2: NGINX

```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://localhost:54000;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Configuration Settings

For reverse proxy setup, enable:

```bash
TRUST_PROXY_HEADERS=true
```

This enables:
- X-Forwarded-For header parsing
- X-Forwarded-Proto header parsing
- Proper client IP detection
```

**Action Items:**
- [ ] Create `.docs/SECURITY.md`
- [ ] Document Caddy configuration
- [ ] Document NGINX configuration
- [ ] Add to README.md

#### B. Add Security Headers Middleware

**Location:** `apps/api/middleware/security.py`

```python
"""Security headers middleware."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers."""
        response = await call_next(request)

        # HSTS: Enforce HTTPS for 1 year
        response.headers["Strict-Transport-Security"] = \
            "max-age=31536000; includeSubDomains; preload"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Disable MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response
```

**Integration in main.py:**

```python
from apps.api.middleware.security import SecurityHeadersMiddleware

# In create_app():
app.add_middleware(SecurityHeadersMiddleware)  # Add before CORS
```

**Action Items:**
- [ ] Create `middleware/security.py`
- [ ] Add to `main.py` middleware stack
- [ ] Test headers: `curl -i http://localhost:54000/health | grep -i "Strict-Transport"`
- [ ] Add to `SECURITY.md` documentation

#### C. Update README.md

**Add to README.md:**

```markdown
## Security

The API uses a reverse proxy (Caddy, NGINX) for HTTPS termination.

### Requirements

- HTTPS enabled on reverse proxy
- Valid TLS certificate
- Security headers configured (see `.docs/SECURITY.md`)

### Example Deployment

See `.docs/SECURITY.md` for complete Caddy and NGINX configurations.
```

**Action Items:**
- [ ] Update README.md with security section
- [ ] Link to `.docs/SECURITY.md`
- [ ] Add deployment checklist

**Estimated Time:** 2 hours

---

## Validation Checklist

### Before Merging

```bash
# 1. Type checking
uv run ty check
# Expected: 0 errors

# 2. Linting
uv run ruff check .
uv run ruff format --check .
# Expected: All checks passed

# 3. Tests
uv run pytest --cov=apps/api
# Expected: 927 passed, coverage ≥ 83%

# 4. Git history
git log --all --full-history -- .env | wc -l
# Expected: 0 (no .env in history)

# 5. Security headers test
curl -i http://localhost:54000/health | grep -E "Strict-Transport|X-Frame|Content-Security"
# Expected: All security headers present

# 6. Documentation
ls -la .docs/
# Expected: AUDIT_REPORT.md, REMEDIATION_GUIDE.md, SECURITY.md
```

### Integration Testing

```bash
# Start services
docker compose up -d

# Run migrations
uv run alembic upgrade head

# Start dev server
uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 54000 --reload &

# Test health endpoint
curl http://localhost:54000/health

# Test with API key
curl -H "X-API-Key: test-key" http://localhost:54000/api/v1/projects

# Stop server
pkill -f uvicorn
```

---

## Timeline & Prioritization

### Phase 1: Critical Fixes (Hours 0-4)

- [ ] **Hour 0-1:** Fix async iteration type error (OpenAI chat)
- [ ] **Hour 1-2:** Fix protocol variance (ModelMapper)
- [ ] **Hour 2-3:** Remove .env from git history
- [ ] **Hour 3-4:** Rotate all secrets

### Phase 2: Documentation & Security (Hours 4-6)

- [ ] **Hour 4-5:** Create `.docs/SECURITY.md`
- [ ] **Hour 5-6:** Add security headers middleware

### Phase 3: Validation (Hour 6+)

- [ ] Run full test suite
- [ ] Verify no type errors
- [ ] Test security headers
- [ ] Deploy to staging

---

## Success Criteria

### Production Readiness

- ✅ `uv run ty check` passes with 0 errors
- ✅ `git log --all --full-history -- .env | wc -l` equals 0
- ✅ All secrets rotated (API keys, DB credentials)
- ✅ `.docs/SECURITY.md` created with deployment instructions
- ✅ Security headers middleware deployed
- ✅ All tests pass (927 passed, ≥83% coverage)
- ✅ README.md updated with security section

### Deployment Checklist

- ✅ HTTPS reverse proxy configured
- ✅ Security headers enabled
- ✅ API key authentication verified
- ✅ Database connection working
- ✅ Redis cache working
- ✅ Rate limiting tested
- ✅ Monitoring configured (structured logging)

---

## Post-Launch Improvements

After reaching production readiness, schedule these improvements:

### Phase A: Code Refactoring (8-10 hours)
- Split `SessionService` (767 lines)
- Refactor oversized functions (29 functions > 50 lines)
- Extract helper functions

### Phase B: Test Coverage (6-8 hours)
- Increase coverage from 83% to 85%+
- Add E2E tests for critical paths

### Phase C: Documentation (4 hours)
- Create Architecture Decision Records (ADRs)
- Add performance tuning guide
- Database schema documentation

---

**Generated:** 2026-01-29
**Estimated Completion:** 2026-01-31 (5-6 hours of work)
**Next Review:** Post-deployment validation
