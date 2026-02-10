# Known Issues and Limitations

**Last Updated:** 2026-02-06
**Project:** Claude Agent API
**Version:** 1.0.0-dev

This document tracks known issues, limitations, and workarounds in the codebase. Issues are prioritized by severity and impact on production deployments.

---

## High Priority Issues

_No high priority issues at this time. Previous high priority issues (PERF-001, PERF-002, PERF-003) have been resolved._

---

## Medium Priority Issues

### SCALE-001: Distributed Lock Contention Limits Horizontal Scaling

**Severity:** MEDIUM
**Impact:** Scaling limited to 3-5 instances (diminishing returns beyond that)
**Affected Code:** `apps/api/services/session.py:110-172`

**Description:**
Distributed locking with exponential backoff causes lock contention when scaling beyond 3-5 API instances. All instances compete for the same Redis lock, leading to increased latency (10ms → 500ms → 5-second timeout). The retry logic lacks jitter, which can cause thundering herd problems.

**Cause:**
```python
# apps/api/services/session.py:143-172
retry_delay = self._LOCK_INITIAL_RETRY_DELAY
max_retry_delay = self._LOCK_MAX_RETRY_DELAY

while True:
    lock_value = await self._cache.acquire_lock(lock_key, ttl=lock_ttl)
    if lock_value:
        break
    if elapsed >= acquire_timeout:
        raise TimeoutError(...)
    await asyncio.sleep(retry_delay)  # ⚠️ No jitter - thundering herd
    retry_delay = min(retry_delay * 2, max_retry_delay)
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

**Status:** Verified present in current codebase (2026-02-06)
**Tracking:** Performance report section 5.1
**Fix Timeline:** Next release

---

### PERF-004: SSE Backpressure Missing

**Severity:** MEDIUM
**Impact:** Memory exhaustion with slow clients
**Affected Code:** `apps/api/routes/query.py:78-108`

**Description:**
SSE streaming lacks backpressure control. If a client consumes events slower than the agent produces them, events accumulate in memory unbounded.

**Cause:**
```python
# apps/api/routes/query.py:78-86
async def event_generator() -> AsyncGenerator[dict[str, str], None]:
    """Generate SSE events with disconnect monitoring."""
    session_id: str | None = query.session_id
    is_error = False
    num_turns = 0
    total_cost_usd: float | None = None
    try:
        async for event in agent_service.query_stream(query, api_key):
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

**Status:** Verified present in current codebase (2026-02-06)
**Tracking:** Performance report section 3.3
**Fix Timeline:** Next release

---

## Low Priority Issues

### CODE-001: metadata_ Naming Workaround

**Severity:** LOW
**Impact:** Developer confusion
**Affected Code:** `apps/api/models/session.py:67`

**Description:**
The `Session` model uses `metadata_` as the attribute name but `"metadata"` as the database column name. This workaround is necessary because SQLAlchemy's `Base` class already uses `metadata` for table metadata.

**Cause:**
```python
# apps/api/models/session.py:67
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

**Status:** Verified present in current codebase (2026-02-06)
**Tracking:** This document
**Fix Timeline:** Consider for v2.0 (breaking change)

---

### CODE-002: Protocol/Implementation Naming Collision

**Severity:** LOW
**Impact:** Type confusion, breaks typing.Protocol best practices
**Affected Code:**
- `apps/api/protocols.py:35` - Protocol `SessionRepository`
- `apps/api/adapters/session_repo.py:24` - Concrete class `SessionRepository`

**Description:**
The protocol and its implementation have the same name (`SessionRepository`). This violates typing best practices and can cause import confusion.

**Cause:**
```python
# apps/api/protocols.py:35
class SessionRepository(Protocol):  # Protocol
    ...

# apps/api/adapters/session_repo.py:24
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

**Status:** Verified present in current codebase (2026-02-06)
**Tracking:** This document
**Fix Timeline:** Consider for v2.0 (breaking change)

---

### PERF-005: Redis Connection Pool Size

**Severity:** LOW
**Impact:** Connection pool exhaustion with high concurrency
**Affected Code:** `apps/api/config.py:70-72`

**Description:**
Redis max connections (50) may be insufficient when running multiple Uvicorn workers with high concurrency.

**Cause:**
```python
# apps/api/config.py:70-72
redis_max_connections: int = Field(
    default=50, ge=5, le=200, description="Redis max connections"
)

# With 10 workers × 5 concurrent requests = 50 connections (at limit)
```

**Workaround:** Increase `REDIS_MAX_CONNECTIONS` env var

**Fix:**
```python
# Scale with expected concurrency
redis_max_connections = max(db_pool_size + db_max_overflow, 50)
# Example: 30 DB connections → 50 Redis connections (adequate)
```

**Status:** Verified present in current codebase (2026-02-06)
**Tracking:** Performance report section 2.5
**Fix Timeline:** Monitor in production, adjust if needed

---

### CONFIG-001: Proxy Header Trust Configuration

**Severity:** LOW
**Impact:** IP-based features fail behind proxy
**Affected Code:** `apps/api/config.py:101-103`

**Description:**
`trust_proxy_headers` defaults to `False`, which means the API doesn't trust `X-Forwarded-For` headers. This is secure but breaks IP-based features (like IP rate limiting) when deployed behind a reverse proxy.

**Cause:**
```python
# apps/api/config.py:101-103
trust_proxy_headers: bool = Field(
    default=False,  # ⚠️ Secure default but breaks proxy deployments
    description="Trust X-Forwarded-For header (only enable behind trusted proxy)",
)
```

**Workaround:**
- Set `TRUST_PROXY_HEADERS=true` in production behind trusted proxy
- Document proxy IP whitelist

**Fix:**
1. Document proxy deployment requirements in README
2. Add validation that proxy headers are ONLY trusted behind known proxies
3. Consider environment-specific defaults (false for dev, true for prod)

**Status:** Verified present in current codebase (2026-02-06)
**Tracking:** Security audit section A07
**Fix Timeline:** Document in deployment guide

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

### PERF-001: N+1 Query Problem in Session Loading (FIXED)

**Status:** ✅ FIXED
**Fix Date:** 2026-02-06 (verification date)
**Severity:** HIGH (when unfixed)

**Description:** Eager loading with `selectin` strategy caused multiple database queries per session retrieval.

**Fix Applied:** Changed to `lazy="raise"` strategy to prevent accidental N+1 queries and force explicit loading.

**Verification:** `apps/api/models/session.py:80,86,91` - all relationships now use `lazy="raise"`

**Related:** Performance report section 1.1

---

### PERF-002: Missing Index on owner_api_key (FIXED)

**Status:** ✅ FIXED
**Fix Date:** 2026-01-10 (migration date)
**Severity:** HIGH (when unfixed)

**Description:** Session ownership filtering was performed in application code because `owner_api_key` column lacked an index.

**Fix Applied:** 
1. Added migration `20260110_000004_add_sessions_owner_api_key_index.py`
2. Added index `idx_sessions_owner_api_key_hash` on `owner_api_key_hash` column
3. Column migrated to `owner_api_key_hash` (SHA-256) as part of Phase 3 security migration

**Verification:** `apps/api/models/session.py:102` - index definition present

**Related:** Performance report section 1.2, API key hashing migration

---

### PERF-003: Application-Level Filtering Instead of Database Queries (FIXED)

**Status:** ✅ FIXED  
**Fix Date:** 2026-02-06 (verification date)
**Severity:** MEDIUM (when unfixed)

**Description:** Session listing loaded ALL sessions from cache/database, then filtered in Python.

**Fix Applied:** Service now uses database queries with indexed filtering via `SessionRepository.list_sessions()`

**Verification:** 
- `apps/api/services/session.py:389-404` - uses DB repo for owner-filtered queries
- `apps/api/adapters/session_repo.py:163-218` - implements proper WHERE clause filtering

**Related:** Performance report section 1.1

---

### SEC-008: Webhook Fail-Open Bypass (FIXED)

**Status:** ✅ FIXED in commit 73c1f12
**Fix Date:** 2026-01-09
**Severity:** MEDIUM (when unfixed)

**Description:** Webhook hooks had fail-open behavior - if webhook timed out, tool use was auto-approved.

**Fix Applied:** Changed default to fail-closed (deny on timeout)

**Verification:** `apps/api/services/webhook.py:96` - "PreToolUse hooks fail closed (deny)"

**Related:** Security audit section A04

---

## Removed Issues (Not Actual Issues)

### SEC-001: Duplicate Authentication Logic (REMOVED)

**Status:** ❌ REMOVED - Not an actual issue
**Removal Date:** 2026-02-06
**Reason:** This was incorrectly identified as a problem. Having both middleware and dependency injection for authentication is a standard FastAPI pattern:
- **Middleware:** Global request-level auth for all routes
- **Dependency:** Route-specific injection for business logic access

This is the recommended approach in FastAPI documentation and provides both layers of security and testability.

**Note:** Authentication is NOT duplicated - they serve different architectural purposes.

---

## Workarounds Summary

| Issue ID | Workaround | Performance Impact |
|----------|------------|-------------------|
| SCALE-001 | Limit to 3-5 instances | 20% efficiency loss beyond 5 instances |
| PERF-004 | Monitor memory usage | Risk of OOM with slow clients |
| CODE-001 | Use `metadata_` attribute name | Developer confusion |
| CODE-002 | Import context determines which class | Type confusion risk |
| PERF-005 | Increase `REDIS_MAX_CONNECTIONS` env var | None if configured |
| CONFIG-001 | Set `TRUST_PROXY_HEADERS=true` in prod | None if configured |

---

## Issue Tracking

**Security Issues:** See `.docs/security-audit-owasp-2026-01-10.md`
**Performance Issues:** See `docs/performance-analysis-2026-01-10.md`
**Documentation Issues:** See `.docs/documentation-review-2026-01-10.md`

**Next Review:** 2026-03-06 (monthly)

---

## Contributing

When adding a new known issue:

1. Assign an ID: `CATEGORY-NNN` (e.g., PERF-006, SEC-009, CODE-003, CONFIG-002)
2. Set severity: LOW / MEDIUM / HIGH / CRITICAL
3. Describe impact with metrics
4. Provide affected code locations with line numbers
5. Document current workaround (if any)
6. Propose fix with code example
7. Update "Related" cross-references
8. Verify issue exists in current codebase before documenting

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

**Status:** (Verified present/fixed in current codebase - DATE)
**Tracking:** (Link to related docs)
**Fix Timeline:** (When will it be fixed?)
```

---

## Summary Statistics

- **Active Issues:** 6 (0 High, 2 Medium, 4 Low)
- **Fixed Issues:** 4 (2 High, 1 Medium, 1 Medium-Security)
- **Removed Issues:** 1 (incorrectly identified)
- **Last Verification:** 2026-02-06
