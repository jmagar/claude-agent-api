# Known Issues and Limitations

**Last Updated:** 2026-01-10 02:09:16
**Project:** Claude Agent API
**Version:** 1.0.0-dev

This document tracks known issues, limitations, and workarounds in the codebase. Issues are prioritized by severity and impact on production deployments.

---

## High Priority Issues

### PERF-001: N+1 Query Problem in Session Loading

**Severity:** HIGH
**Impact:** 4x slower session retrieval (1 query becomes 4 queries)
**Affected Code:** `apps/api/models/session.py:67-79`

**Description:**
Eager loading with `selectin` strategy causes multiple database queries per session retrieval:
1. Main session SELECT
2. Messages SELECT (via selectin)
3. Checkpoints SELECT (via selectin)
4. Parent session SELECT (via selectin)

Listing 50 sessions = 200+ queries (4 queries × 50 sessions).

**Cause:**
```python
# apps/api/models/session.py
messages: Mapped[list["SessionMessage"]] = relationship(
    "SessionMessage",
    lazy="selectin",  # ⚠️ Triggers separate SELECT
)
```

**Workaround:** None - requires code change

**Fix:**
```python
# Option 1: Use joinedload for single query
from sqlalchemy.orm import joinedload

stmt = (
    select(Session)
    .where(Session.id == session_id)
    .options(
        joinedload(Session.messages),
        joinedload(Session.checkpoints),
        joinedload(Session.parent_session)
    )
)

# Option 2: Use lazy="raise" and load explicitly when needed
lazy="raise"  # Forces explicit loading, prevents accidental N+1
```

**Status:** Documented in `docs/performance-analysis-2026-01-10.md`
**Tracking:** Performance report section 1.1
**Fix Timeline:** Next sprint

---

### PERF-002: Missing Index on owner_api_key

**Severity:** HIGH
**Impact:** 100x slower authorization filtering
**Affected Code:** `apps/api/models/session.py:50` (sessions.owner_api_key column)

**Description:**
Session ownership filtering is performed in application code instead of database queries because `owner_api_key` column lacks an index. This loads ALL sessions into memory before filtering.

**Cause:**
```python
# apps/api/services/session.py:399-404
if current_api_key:
    sessions = [s for s in sessions if s.owner_api_key == current_api_key]
    # ⚠️ Application-level filtering - should be database query with index
```

**Workaround:** Application-level filtering (slow, loads all sessions)

**Fix:**
```sql
-- Migration: Add index
CREATE INDEX idx_sessions_owner_api_key ON sessions (owner_api_key);

-- Then change service code to filter in database:
stmt = select(Session)
if current_api_key:
    stmt = stmt.where(Session.owner_api_key == current_api_key)
```

**Status:** Documented in `docs/performance-analysis-2026-01-10.md`
**Tracking:** Performance report section 1.2
**Fix Timeline:** Next sprint

---

## Medium Priority Issues

### SCALE-001: Distributed Lock Contention Limits Horizontal Scaling

**Severity:** MEDIUM
**Impact:** Scaling limited to 3-5 instances (diminishing returns beyond that)
**Affected Code:** `apps/api/services/session.py:108-191`

**Description:**
Distributed locking with exponential backoff causes lock contention when scaling beyond 3-5 API instances. All instances compete for the same Redis lock, leading to increased latency (10ms → 500ms → 5-second timeout).

**Cause:**
```python
# apps/api/services/session.py
async def _with_session_lock(session_id, ...):
    retry_delay = 0.01  # 10ms
    while True:
        lock_value = await self._cache.acquire_lock(lock_key, ttl=lock_ttl)
        if lock_value:
            break
        if elapsed >= acquire_timeout:  # 5 seconds
            raise TimeoutError(...)
        await asyncio.sleep(retry_delay)  # ⚠️ No jitter - thundering herd
        retry_delay = min(retry_delay * 2, 0.5)
```

**Workaround:** Limit deployments to 3-5 instances

**Fix Options:**
1. **Add jitter to prevent thundering herd:**
   ```python
   import random
   await asyncio.sleep(retry_delay * (1 + random.uniform(-0.1, 0.1)))
   ```

2. **Use optimistic locking (version counters):**
   ```sql
   UPDATE sessions SET version = version + 1, status = ?
   WHERE id = ? AND version = ?  -- Fails if version changed
   ```

3. **Reduce lock scope (only lock writes, not reads)**

**Status:** Documented in `docs/performance-analysis-2026-01-10.md`
**Tracking:** Performance report section 5.1
**Fix Timeline:** Next release

---

### PERF-003: Application-Level Filtering Instead of Database Queries

**Severity:** MEDIUM
**Impact:** Loads 10,000 sessions to filter to 10 (999x unnecessary data transfer)
**Affected Code:** `apps/api/services/session.py:384-404`

**Description:**
Session listing loads ALL sessions from cache/database, then filters in Python. This wastes memory and network bandwidth.

**Cause:**
```python
# Load all sessions
all_keys = await self._cache.scan_keys("session:*")
cached_rows = await self._cache.get_many_json(all_keys)

# Filter in Python (after loading everything)
if current_api_key:
    sessions = [s for s in sessions if s.owner_api_key == current_api_key]
```

**Workaround:** None - all sessions are loaded

**Fix:**
```python
# Use database filtering with index
async def list_sessions(self, current_api_key: str | None = None):
    stmt = select(Session)
    if current_api_key:
        stmt = stmt.where(Session.owner_api_key == current_api_key)
    stmt = stmt.limit(page_size).offset(offset)
    return await self._db.execute(stmt)
```

**Status:** Documented in `docs/performance-analysis-2026-01-10.md`
**Tracking:** Performance report section 1.1
**Fix Timeline:** Next sprint (combined with PERF-002)

---

### PERF-004: SSE Backpressure Missing

**Severity:** MEDIUM
**Impact:** Memory exhaustion with slow clients
**Affected Code:** `apps/api/routes/query.py:58-135`

**Description:**
SSE streaming lacks backpressure control. If a client consumes events slower than the agent produces them, events accumulate in memory unbounded.

**Cause:**
```python
async def event_generator():
    async for event in agent_service.query_stream(query):
        yield event  # ⚠️ No bounded queue
```

**Workaround:** None - monitor memory usage

**Fix:**
```python
async def event_generator():
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)  # Bounded queue

    async def producer():
        async for event in agent_service.query_stream(query):
            await queue.put(event)  # Blocks when full (backpressure)
        await queue.put(None)

    producer_task = asyncio.create_task(producer())
    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            yield event
    finally:
        producer_task.cancel()
```

**Status:** Documented in `docs/performance-analysis-2026-01-10.md`
**Tracking:** Performance report section 3.3
**Fix Timeline:** Next release

---

### SEC-001: Duplicate Authentication Logic

**Severity:** MEDIUM
**Impact:** Maintenance burden, risk of inconsistency
**Affected Code:**
- `apps/api/middleware/auth.py:62-74`
- `apps/api/dependencies.py:132-156`

**Description:**
Authentication is implemented in TWO places:
1. `ApiKeyAuthMiddleware` - validates at middleware level
2. `verify_api_key` dependency - validates at route level

This creates maintenance burden and risk that one is updated without the other, leading to inconsistent security behavior.

**Cause:** Architectural decision to have both middleware and dependency auth

**Workaround:** Ensure both stay synchronized

**Fix:**
1. Remove either middleware or dependency auth (not both)
2. Prefer dependency injection for FastAPI (more testable)
3. If middleware needed for pre-route checks, remove dependency version

**Status:** Documented in `.docs/security-audit-owasp-2026-01-10.md`
**Tracking:** Security audit section A01
**Fix Timeline:** Next sprint (decide on single auth mechanism)

---

### A07-001: Proxy Header Trust Configuration

**Severity:** MEDIUM
**Impact:** IP-based features fail behind proxy
**Affected Code:** `apps/api/config.py:37`

**Description:**
`TRUST_PROXY_HEADERS` defaults to `false`, which means the API doesn't trust `X-Forwarded-For` headers. This is secure but breaks IP-based features (like IP rate limiting) when deployed behind a reverse proxy.

**Cause:**
```python
# apps/api/config.py
trust_proxy_headers: bool = Field(
    default=False,  # ⚠️ Secure default but breaks proxy deployments
    description="Trust X-Forwarded-For and related headers",
)
```

**Workaround:**
- Set `TRUST_PROXY_HEADERS=true` in production behind trusted proxy
- Document proxy IP whitelist

**Fix:**
1. Document proxy deployment requirements in README
2. Add validation that proxy headers are ONLY trusted behind known proxies
3. Consider environment-specific defaults (false for dev, true for prod)

**Status:** Documented in `.docs/security-audit-owasp-2026-01-10.md`
**Tracking:** Security audit section A07
**Fix Timeline:** Document in deployment guide

---

## Low Priority Issues

### CODE-001: metadata_ Naming Workaround

**Severity:** LOW
**Impact:** Developer confusion
**Affected Code:** `apps/api/models/session.py:56-60`

**Description:**
The `Session` model uses `metadata_` as the attribute name but `"metadata"` as the database column name. This workaround is necessary because SQLAlchemy's `Base` class already uses `metadata` for table metadata.

**Cause:**
```python
# apps/api/models/session.py
metadata_: Mapped[dict[str, object] | None] = mapped_column(
    "metadata",  # Column name in database
    JSONB,
    nullable=True,
)
# Attribute name differs from column name to avoid SQLAlchemy conflict
```

**Workaround:** Use `metadata_` in Python code, `metadata` in SQL

**Fix:**
```python
# Breaking change - rename to session_metadata
session_metadata: Mapped[dict[str, object] | None] = mapped_column(
    "session_metadata",  # More explicit name
    JSONB,
    nullable=True,
)
```

**Status:** Previously undocumented
**Tracking:** This document
**Fix Timeline:** Consider for v2.0 (breaking change)

---

### CODE-002: Protocol/Implementation Naming Collision

**Severity:** LOW
**Impact:** Type confusion, breaks typing.Protocol best practices
**Affected Code:**
- `apps/api/protocols.py:19` - Protocol `SessionRepository`
- `apps/api/adapters/session_repo.py:15` - Concrete class `SessionRepository`

**Description:**
The protocol and its implementation have the same name (`SessionRepository`). This violates typing best practices and can cause import confusion.

**Cause:**
```python
# apps/api/protocols.py
class SessionRepository(Protocol):  # Protocol
    ...

# apps/api/adapters/session_repo.py
class SessionRepository:  # Concrete class
    ...
```

**Workaround:** Rely on import context (which SessionRepository is imported)

**Fix:**
```python
# Rename protocol to be explicit
class SessionRepositoryProtocol(Protocol):
    ...

# Concrete class keeps simple name
class SessionRepository:
    ...
```

**Status:** Previously undocumented
**Tracking:** This document
**Fix Timeline:** Consider for v2.0 (breaking change)

---

### PERF-005: Redis Connection Pool Size

**Severity:** LOW
**Impact:** Connection pool exhaustion with high concurrency
**Affected Code:** `apps/api/config.py:64`

**Description:**
Redis max connections (50) may be insufficient when running multiple Uvicorn workers with high concurrency.

**Cause:**
```python
# apps/api/config.py
redis_max_connections: int = Field(default=50, ge=5, le=200)

# With 10 workers × 5 concurrent requests = 50 connections (at limit)
```

**Workaround:** Increase `REDIS_MAX_CONNECTIONS` env var

**Fix:**
```python
# Scale with expected concurrency
redis_max_connections = max(db_pool_size + db_max_overflow, 50)
# Example: 30 DB connections → 50 Redis connections (adequate)
```

**Status:** Documented in `docs/performance-analysis-2026-01-10.md`
**Tracking:** Performance report section 2.5
**Fix Timeline:** Monitor in production, adjust if needed

---

## Architectural Limitations

### Horizontal Scaling Capacity

**Limitation:** API instances scale optimally to 3-5 instances
**Beyond 5 instances:** Diminishing returns due to distributed lock contention

**Details:**
- 1 instance: ~50-100 concurrent sessions
- 3 instances: ~100-200 concurrent sessions
- 5 instances: ~150-250 concurrent sessions
- 10 instances: ~200-300 concurrent sessions (only 20% efficiency)

**Recommendation:** Use 3-5 instances for production, scale vertically (more CPU/RAM) instead of horizontally beyond that.

**Related:** SCALE-001

---

### SSE Connection Limits

**Limitation:** ~1,600 concurrent SSE connections per instance
**Cause:** Uvicorn worker capacity (80% of 2,000 connections)

**Details:**
- Uvicorn default: 500 connections per worker
- With 4 workers: 2,000 total connections
- SSE holds connections open: ~80% capacity = 1,600 streams
- Remaining 20% for regular requests: ~400 requests

**Recommendation:** Use dedicated SSE workers or increase worker count for high SSE load.

**Related:** Performance report section 3.4

---

### File Descriptor Limits

**Limitation:** Default OS limit (1,024 FDs) insufficient for production
**Required:** 65,536 FDs for 1,600 SSE connections

**Details:**
- Database connections: 30 FDs
- Redis connections: 50 FDs
- SSE connections: 1,600 FDs
- SDK processes: ~10 FDs per session
- Total: ~1,700-2,000 FDs

**Fix:**
```yaml
# docker-compose.yaml
services:
  api:
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
```

**Related:** Performance report section 6.3

---

## Fixed Issues (For Reference)

### SEC-008: Webhook Fail-Open Bypass (FIXED)

**Status:** ✅ FIXED in commit 73c1f12
**Fix Date:** 2026-01-09
**Severity:** MEDIUM (when unfixed)

**Description:** Webhook hooks had fail-open behavior - if webhook timed out, tool use was auto-approved.

**Fix Applied:** Changed default to fail-closed (deny on timeout)

**Verification:** `apps/api/services/webhook.py:190-205`

**Related:** Security audit section A04

---

## Workarounds Summary

| Issue ID | Workaround | Performance Impact |
|----------|------------|-------------------|
| PERF-001 | None | 4x slower queries |
| PERF-002 | App-level filtering | 100x slower filtering |
| PERF-003 | None | Loads all sessions |
| PERF-004 | Monitor memory | Risk of OOM |
| SCALE-001 | Limit to 3-5 instances | 20% efficiency loss |
| SEC-001 | Keep both in sync | Maintenance burden |
| CODE-001 | Use `metadata_` | Developer confusion |
| CODE-002 | Import context | Type confusion |

---

## Issue Tracking

**Security Issues:** See `.docs/security-audit-owasp-2026-01-10.md`
**Performance Issues:** See `docs/performance-analysis-2026-01-10.md`
**Documentation Issues:** See `.docs/documentation-review-2026-01-10.md`

**Next Review:** 2026-02-10 (monthly)

---

## Contributing

When adding a new known issue:

1. Assign an ID: `CATEGORY-NNN` (e.g., PERF-006, SEC-009, CODE-003)
2. Set severity: LOW / MEDIUM / HIGH / CRITICAL
3. Describe impact with metrics
4. Provide affected code locations
5. Document current workaround (if any)
6. Propose fix with code example
7. Update "Related" cross-references

**Template:**
```markdown
### CATEGORY-NNN: Issue Title

**Severity:** (LOW / MEDIUM / HIGH / CRITICAL)
**Impact:** (Quantify the impact)
**Affected Code:** `file/path.py:line-range`

**Description:**
(What is the issue?)

**Cause:**
```python
# Code snippet showing the problematic code
```

**Workaround:** (Current mitigation or "None")

**Fix:**
```python
# Code snippet showing the proposed fix
```

**Status:** (Where is it documented?)
**Tracking:** (Link to related docs)
**Fix Timeline:** (When will it be fixed?)
```
