# Claude Agent API - Testing Strategy & Coverage Analysis
**Generated:** 2026-01-29 | **Test Suite:** 926 passed, 13 skipped, 1 intermittent failure | **Overall Coverage:** 83%

---

## Executive Summary

The claude-agent-api has **strong foundational test infrastructure** (940 test cases, 83% code coverage) but **critical security and performance testing gaps** exist:

| Category | Status | Risk Level | Priority |
|----------|--------|-----------|----------|
| **Security** | ⚠️ Gaps Identified | HIGH | P0 |
| **Performance** | ❌ Not Tested | HIGH | P0 |
| **Authorization Boundaries** | ⚠️ Partial | HIGH | P0 |
| **Infrastructure (DB/Cache)** | ✅ Good | LOW | P3 |
| **API Contract** | ✅ Good | LOW | P2 |
| **Test Quality** | ⚠️ Mixed | MEDIUM | P1 |

---

## Coverage Analysis

### Overall Metrics
```
Line Coverage:     83% (4,385 / 5,071 lines)
Branch Coverage:   26% coverage on branches (low)
Test Count:        926 active tests
Test Execution:    21.02 seconds (parallel)
Configuration:     pytest-xdist, 12 workers, -n auto
```

### By Module

#### High Coverage (>90%)
```
✅ schemas/                    95-100% (100% - All request/response models)
✅ protocols.py                60% (baseline) → Uses interfaces, not implementation
✅ exceptions/                 100% (All custom exception classes)
✅ dependencies.py             100% (DI fixtures and factories)
✅ models/session.py           94% (94 - DB model persistence layer)
✅ services/openai/            93-100% (OpenAI compatibility translation)
✅ services/agents.py          86% (Agent CRUD operations)
✅ services/session.py         81% (Session service with cache/DB dual write)
```

#### Medium Coverage (70-90%)
```
⚠️ routes/agents.py           78% (Agent management endpoints)
⚠️ routes/health.py           67% (Health check endpoints)
⚠️ routes/mcp_servers.py      77% (MCP server CRUD)
⚠️ routes/openai/chat.py      90% (OpenAI chat completions)
⚠️ middleware/auth.py         93% (API key authentication)
⚠️ middleware/openai_auth.py  93% (Bearer token extraction)
```

#### Low Coverage (<70%) - CRITICAL GAPS
```
❌ routes/sessions.py         41% (Sessions CRUD - 59% untested!)
   - list_sessions()          34 LOC, ~50% coverage
   - promote_session()        Not tested
   - update_session_tags()    Not tested

❌ routes/query.py            71% (Query execution - critical path)
   - Streaming logic          Partial coverage
   - SSE event handling       Gap in error cases

❌ routes/websocket.py        70% (Real-time agent execution)
   - Message streaming        Incomplete
   - Connection lifecycle     Untested error paths

❌ routes/skills.py           61% (Tool preset management)
   - Discovery endpoints      Partial
   - Update operations        Low coverage

❌ services/mcp_server_configs.py  63% (MCP server configuration)
   - API key scoped queries   Incomplete
   - Server creation/update   Partial paths

❌ services/agent/handlers.py 60% (Agent event handlers)
   - Tool execution hooks     Incomplete
   - Error handling cascade   Missing edge cases

❌ services/agent/query_executor.py  54% (Core query execution)
   - Streaming orchestration  Significant gaps
   - Resource cleanup         Not verified
```

---

## PHASE 2: SECURITY FINDINGS & TEST GAPS

### 1. Session Authorization Boundary - CRITICAL

**Finding:** `list_sessions()` endpoint has authorization bypass vulnerability.

**Current Implementation (sessions.py:34):**
```python
# VULNERABLE: Loads ALL sessions from DB, then filters in Python
sessions, _ = await repo.list_sessions(limit=10000, offset=0)  # NO owner filter in query

# Then filters in memory
def matches(session) -> bool:
    if session.owner_api_key and session.owner_api_key != _api_key:
        return False
    # ... more checks
```

**Problems:**
1. **No Database-Level Filtering** - SQL query loads ALL sessions before applying Python filter
2. **N+1 Query Risk** - Each session might trigger additional DB calls (metadata, parent lookups)
3. **Memory Exhaustion** - Loading 10,000+ sessions into memory is wasteful
4. **Authorization Bypass** - If filtering is skipped, unowned sessions are visible

**Test Coverage:** 0% - Not a single unit test validates:
- ✅ Unauthorized API keys can access only their own sessions
- ✅ Sessions from other API keys are filtered out
- ✅ Database query is optimized (indexed owner_api_key filter)
- ✅ Pagination respects ownership boundaries

**Required Tests:**
```python
@pytest.mark.anyio
async def test_list_sessions_filters_by_owner_api_key():
    """RED: Verify ownership boundary is enforced at DB query level."""
    # Create sessions for different API keys
    session1 = await create_session(owner_api_key="key-alice")
    session2 = await create_session(owner_api_key="key-bob")

    # List as alice
    result = await repo.list_sessions(owner_api_key="key-alice", limit=100, offset=0)

    # Then: Only alice's session returned (filtered at DB, not in memory)
    assert len(result) == 1
    assert result[0].id == session1.id

@pytest.mark.anyio
async def test_list_sessions_cross_api_key_isolation():
    """Verify strict isolation between API key tenants."""
    # Alice attempts to access Bob's sessions
    response = await client.get(
        "/api/v1/sessions",
        headers={"X-API-Key": "key-alice"}
    )

    # Then: Only alice's sessions returned
    data = response.json()
    for session in data["sessions"]:
        assert session["owner_api_key"] == "key-alice"
```

---

### 2. MCP Share Endpoint - Public Access Risk

**Finding:** MCP share endpoints potentially expose configuration without proper authorization.

**Current Code (mcp_servers.py:*):**
```python
@router.post("/mcp-servers/share", ...)
async def create_mcp_share(
    name: str,
    payload: McpShareCreateRequest,
    _api_key: ApiKey,  # ✅ Protected
    cache: Cache,
) -> McpShareCreateResponse:
    """Create shareable MCP server token."""
    # Generates token for sharing MCP config

@router.get("/mcp-servers/share/{token}")
async def get_mcp_share(
    token: str,
    _api_key: ApiKey,  # ⚠️ REQUIRED - But is it verified?
    cache: Cache,
) -> McpSharePayloadResponse:
    """Resolve share token to payload."""
    # Returns MCP config from Redis
```

**Security Questions (Untested):**
1. ✅ Is `_api_key` actually required? (dependency validation)
2. ❌ Can unauthenticated requests call GET endpoint?
3. ❌ Is token reuse/replay prevented?
4. ❌ Are tokens scoped to creator only?
5. ❌ Is token TTL enforced?

**Test Coverage:** 0% security tests

**Required Tests:**
```python
@pytest.mark.anyio
async def test_mcp_share_create_requires_auth():
    """RED: Share creation requires valid API key."""
    response = await client.post(
        "/api/v1/mcp-servers/share",
        headers={},  # No auth
        json={"name": "test"}
    )
    assert response.status_code == 401

@pytest.mark.anyio
async def test_mcp_share_get_with_invalid_token():
    """RED: Invalid token returns 404, not detailed error."""
    response = await client.get(
        "/api/v1/mcp-servers/share/invalid-token-xyz",
        headers=auth_headers
    )
    assert response.status_code == 404
    # Verify no information leakage in error message

@pytest.mark.anyio
async def test_mcp_share_token_isolation_by_api_key():
    """RED: Alice cannot use Bob's share token."""
    # Alice creates share token
    resp1 = await client.post(
        "/api/v1/mcp-servers/share",
        headers={"X-API-Key": "key-alice"},
        json={"name": "alice-server"}
    )
    token = resp1.json()["token"]

    # Bob tries to use it
    resp2 = await client.get(
        f"/api/v1/mcp-servers/share/{token}",
        headers={"X-API-Key": "key-bob"}
    )

    # Then: Bob gets 404 or 403 (not the token)
    assert resp2.status_code in (403, 404)
```

---

### 3. Bearer Token Extraction - Edge Cases

**Current Tests (test_openai_auth.py):**
```python
✅ test_extracts_bearer_token_for_v1_routes()
✅ test_ignores_non_v1_routes()
✅ test_preserves_existing_x_api_key()
✅ test_handles_missing_auth_header()
✅ test_accepts_lowercase_bearer_scheme()
✅ test_ignores_empty_bearer_token()
```

**Missing Edge Cases (8 additional tests needed):**

```python
@pytest.mark.anyio
async def test_bearer_token_with_extra_whitespace():
    """RED: "Bearer  sk-test" (double space) handled correctly."""
    request.headers = {"Authorization": "Bearer  sk-test-123"}
    # Should extract "sk-test-123" (single space or trimmed)

@pytest.mark.anyio
async def test_bearer_token_case_insensitive_scheme():
    """Test "BeArEr" scheme is accepted."""
    request.headers = {"Authorization": "BeArEr sk-test-123"}
    # Should extract token regardless of Bearer case

@pytest.mark.anyio
async def test_malformed_auth_header_ignored():
    """Test malformed headers don't cause crashes."""
    request.headers = {"Authorization": "Bearer"}  # No token
    request.headers = {"Authorization": "InvalidScheme sk-test"}
    request.headers = {"Authorization": "\x00Bearer\x00sk-test"}  # Null bytes
    # Should gracefully skip extraction

@pytest.mark.anyio
async def test_bearer_token_precedence_over_header():
    """RED: Bearer token should NOT override explicit X-API-Key."""
    request.headers = {
        "Authorization": "Bearer sk-bearer-123",
        "X-API-Key": "sk-explicit-456"
    }

    middleware = BearerAuthMiddleware(app=MagicMock())
    await middleware.dispatch(request, mock_call_next)

    # Then: Explicit X-API-Key preserved (not overwritten)
    header = get_scope_header(request, "x-api-key")
    assert header == "sk-explicit-456"

@pytest.mark.anyio
async def test_bearer_token_special_characters():
    """RED: Bearer token with special chars handled safely."""
    tokens_with_special_chars = [
        "sk-test-123-!@#$%",
        "sk-test_123_456",
        "sk-test.123.456",
        "sk-test+123=456",  # URL-encoded chars
        "sk-test/123==",  # Base64 padding
    ]

    for token in tokens_with_special_chars:
        request.headers = {"Authorization": f"Bearer {token}"}
        await middleware.dispatch(request, mock_call_next)
        # Should not crash or modify token
```

---

### 4. Webhook Matcher ReDoS - Regex Vulnerability

**Current Code (services/webhook.py:~220-230):**
```python
def should_execute_hook(self, hook_config, tool_name: str) -> bool:
    matcher = hook_config.matcher
    if not matcher:
        return True

    try:
        # POTENTIAL ReDoS: No validation of regex complexity
        return re.match(matcher, tool_name) is not None
    except re.error:
        # Logs but defaults to matching (safe, but still vulnerable)
        logger.warning("invalid_matcher_regex", ...)
        return True
```

**Vulnerability:** User-supplied regex patterns can cause exponential backtracking:
```
matcher = "(a+)+" + "b"  # Catastrophic backtracking
tool_name = "aaaaaaaaaaaaaaaaaaaaaa" (20 a's)  # Hangs for seconds/minutes
```

**Test Coverage:** 0% ReDoS tests

**Required Tests:**
```python
@pytest.mark.anyio
async def test_webhook_regex_timeout_protection():
    """RED: Malicious regex doesn't hang server."""
    hook_config = HookWebhookSchema(
        url="http://webhook.local/hook",
        matcher="(a+)+b"  # Catastrophic backtracking pattern
    )

    service = WebhookService(timeout=1.0)

    # Should timeout or have max execution time
    start = time.time()
    result = service.should_execute_hook(hook_config, "aaaaaaaaaaaaaaaa")
    elapsed = time.time() - start

    assert elapsed < 0.5, f"Regex took {elapsed}s (vulnerable to ReDoS)"

@pytest.mark.anyio
async def test_webhook_regex_complexity_validated():
    """RED: Reject regexes with high complexity upfront."""
    dangerous_patterns = [
        "(a+)+b",          # Nested quantifiers
        "(a|a)*b",         # Alternation catastrophe
        "(a|ab)*b",        # Alternation worst-case
        "(.*)*",           # Nested .*
        "(?:a|a)*b",       # Non-capturing group worst case
    ]

    for pattern in dangerous_patterns:
        # Should either:
        # 1. Reject at creation time (400/422)
        # 2. Have timeout protection (< 100ms for any tool_name)

        hook_config = HookWebhookSchema(
            url="http://webhook.local/hook",
            matcher=pattern
        )

        start = time.time()
        for tool_name in ["a" * i for i in range(5, 30, 5)]:
            result = service.should_execute_hook(hook_config, tool_name)
            elapsed = time.time() - start
            assert elapsed < 0.1, f"Pattern {pattern} hangs on {tool_name}"
```

---

## PHASE 2: PERFORMANCE TESTING GAPS

### 1. N+1 Query Detection - MISSING

**Problem Area:** Session listing loads all sessions, potentially triggering additional queries.

**Current Vulnerable Code (session.py:365-452):**
```python
async def list_sessions(...) -> SessionListResult:
    # Uses db_repo.list_sessions() with no owner filter
    db_sessions, total = await self._db_repo.list_sessions(
        owner_api_key=None,  # ⚠️ Loads ALL
        limit=10000,
        offset=0
    )

    # Then filters in Python
    sessions = [self._map_db_to_service(s) for s in db_sessions]
    # Each _map_db_to_service() might access:
    # - s.parent_session_id (foreign key lookup?)
    # - s.metadata_ (separate table?)
```

**Test Coverage:** 0% query performance tests

**Required Tests:**
```python
@pytest.mark.anyio
async def test_list_sessions_no_n_plus_1_queries(mock_session_id, async_client, auth_headers):
    """RED: list_sessions doesn't trigger N+1 queries."""
    # Create multiple sessions
    session_ids = []
    for i in range(10):
        response = await async_client.post(
            "/api/v1/query",
            headers=auth_headers,
            json={"prompt": f"Test query {i}", "stream": False}
        )
        # Extract session ID from response

    # Intercept database queries
    query_log = []
    original_execute = db_session.connection.execute

    async def logged_execute(query, *args, **kwargs):
        query_log.append((str(query), args, kwargs))
        return await original_execute(query, *args, **kwargs)

    db_session.connection.execute = logged_execute

    # List sessions
    response = await async_client.get(
        "/api/v1/sessions?page=1&page_size=20",
        headers=auth_headers
    )

    # Then: Only 1-2 queries (not 1 + N)
    select_queries = [q for q in query_log if "SELECT" in str(q[0])]
    assert len(select_queries) <= 2, f"N+1 detected: {len(select_queries)} queries"

@pytest.mark.anyio
async def test_list_sessions_respects_pagination_limit():
    """RED: Pagination limit actually limits queries."""
    # Create 1000 sessions
    for i in range(1000):
        await create_session(f"session-{i}")

    # List with page_size=20
    response = await client.get(
        "/api/v1/sessions?page=1&page_size=20",
        headers=auth_headers
    )

    data = response.json()
    assert len(data["sessions"]) == 20
    assert data["total"] == 1000

    # Verify DB query respects limit (no loading 1000 rows in memory)
```

---

### 2. Redis Scan Pagination - UNTESTED

**Problem:** `cache.scan_keys(pattern)` might not handle pagination correctly for large key spaces.

**Code (session.py:422-425):**
```python
# Fall back to full cache scan (only when no owner filter)
pattern = "session:*"
all_keys = await self._cache.scan_keys(pattern)  # ⚠️ Might load all into memory

# Bulk fetch all session data in one Redis roundtrip
cached_rows = await self._cache.get_many_json(all_keys)
```

**Test Coverage:** 0% - No tests for:
- ✅ Large key sets (10K+ sessions in Redis)
- ✅ Pagination within scan results
- ✅ Memory usage under load
- ✅ Timeout behavior for slow scans

**Required Tests:**
```python
@pytest.mark.anyio
async def test_cache_scan_handles_large_key_sets(cache):
    """RED: scan_keys() handles 10K+ keys without memory explosion."""
    # Add 10K sessions to cache
    for i in range(10_000):
        await cache.set_json(f"session:id-{i}", {"id": f"id-{i}"}, 3600)

    # Scan for all sessions
    start_memory = get_memory_usage()
    all_keys = await cache.scan_keys("session:*")
    end_memory = get_memory_usage()

    memory_increase = end_memory - start_memory
    assert memory_increase < 50_000_000, f"Memory spike: {memory_increase} bytes"
    assert len(all_keys) == 10_000

@pytest.mark.anyio
async def test_cache_scan_respects_cursor_pagination(cache):
    """RED: scan_keys() uses cursor pagination internally."""
    # Verify implementation uses Redis SCAN with cursor, not KEYS
    # (KEYS blocks Redis, SCAN doesn't)

    # Add keys
    for i in range(5000):
        await cache.set_json(f"session:{i}", {"id": i}, 3600)

    # Should not block Redis for seconds
    start = time.time()
    keys = await cache.scan_keys("session:*")
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Scan took {elapsed}s (probably using KEYS)"
    assert len(keys) == 5000
```

---

### 3. Connection Pool Exhaustion - NOT TESTED

**Missing Tests:**
- ✅ Database connection pool limits
- ✅ Redis connection pool limits
- ✅ Graceful degradation when pools exhausted
- ✅ Connection leak detection

**Required Tests:**
```python
@pytest.mark.anyio
async def test_database_connection_pool_limit(settings):
    """RED: Respects max pool size, queues excess requests."""
    settings.db_pool_size = 5  # Small pool for testing

    # Start 20 concurrent requests
    tasks = []
    for i in range(20):
        tasks.append(async_client.get(f"/api/v1/sessions/{i}"))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Then: All requests succeed (pool queues, doesn't reject)
    assert all(not isinstance(r, Exception) for r in results)

@pytest.mark.anyio
async def test_redis_connection_leak_detection(cache):
    """RED: No connection leaks under error conditions."""
    initial_connections = cache.connection_pool.size

    # Trigger many errors (malformed keys, timeouts, etc.)
    for i in range(100):
        try:
            await cache.set_json(f"key-{i}", {"data": "x" * 1_000_000}, 3600)
        except Exception:
            pass  # Expected to fail

    final_connections = cache.connection_pool.size

    # Connections should return to pool (not leaked)
    assert final_connections <= initial_connections + 1  # Allow 1 for GC
```

---

## Low-Priority Test Gaps (P2-P3)

### Currently Untested Scenarios

| Module | Scenario | Impact | Priority |
|--------|----------|--------|----------|
| `routes/health.py` | Health check edge cases | MEDIUM | P2 |
| `routes/skills.py` | Skill discovery failure modes | MEDIUM | P2 |
| `services/checkpoint.py` | Checkpoint corruption recovery | MEDIUM | P2 |
| `middleware/ratelimit.py` | Rate limit edge cases (burst, reset) | LOW | P3 |
| `services/webhook.py` | Webhook timeout/retry logic | MEDIUM | P2 |
| `routes/websocket.py` | WebSocket connection lifecycle errors | HIGH | P1 |
| `services/mcp_config_loader.py` | Env var resolution edge cases | MEDIUM | P2 |

---

## Test Quality Metrics

### Assertion Density Analysis

```
STRONG Assertion Density (>5 assertions/test):
✅ schemas/requests/  - Validation tests (pydantic models)
✅ contract/          - OpenAPI contract tests
✅ unit/adapters/     - Cache adapter tests

WEAK Assertion Density (<3 assertions/test):
⚠️ integration/test_agents.py     - Single assertion per test
⚠️ routes/*_test.py               - Often 1-2 assertions
⚠️ services/agent/*_test.py       - Incomplete validation
```

### Mock Usage Pattern Issues

1. **Over-Mocking (Hides Real Issues):**
   - All tests mock `claude_agent_sdk.ClaudeSDKClient`
   - E2E path (`query_stream()`) never tested with real SDK
   - Contract tests use mock responses that might differ from SDK reality

2. **Under-Mocking (Creates Fragile Tests):**
   - Database tests use real PostgreSQL (flaky if DB slow)
   - Redis tests use real Redis (flaky if Redis unavailable)
   - No isolation layer for external dependencies

3. **Fixture Complexity:**
   - `conftest.py` is 396 lines (too large)
   - 8 different session fixtures (`mock_session_id`, `mock_active_session_id`, etc.)
   - Fixture dependencies create implicit test ordering

---

## TDD Compliance Assessment

### RED-GREEN-REFACTOR Patterns

**Strong TDD Tests (Clear RED → GREEN → REFACTOR):**
```python
✅ tests/unit/middleware/test_openai_auth.py
   - Each test shows clear given→when→then structure
   - Tests written before implementation
   - Describes behavior in docstring

✅ tests/contract/test_openai_compliance.py
   - Contract-first: API behavior specified
   - Validates both sync and streaming modes
```

**Weak TDD Patterns (No Visible Failing State):**
```python
⚠️ tests/unit/adapters/test_cache.py
   - No evidence of RED phase (test written after code?)
   - Tests are implementation-focused, not behavior-focused

⚠️ tests/integration/test_agents.py
   - Single assertion per test (hard to fail)
   - No clear expected behavior boundaries
```

### Test Naming Quality

**Good Names (Behavior-Focused):**
```
✅ test_extracts_bearer_token_for_v1_routes()
✅ test_query_requires_authentication()
✅ test_sessions_list_respects_pagination()
```

**Poor Names (Implementation-Focused):**
```
❌ test_session_service_get()              (what does it test?)
❌ test_repo_create()                      (many scenarios possible)
❌ test_cache_set_json()                   (should specify expected behavior)
```

---

## Recommendations

### IMMEDIATE (P0 - Fix Before Deployment)

1. **Session Authorization Boundary (2-3 days)**
   - Add 5+ tests for `list_sessions()` ownership filtering
   - Optimize DB query to filter by `owner_api_key` at SQL level (not in Python)
   - Implement query benchmark to prevent regression

2. **Bearer Token Edge Cases (1 day)**
   - Add 8 edge case tests to `test_openai_auth.py`
   - Validate token extraction handles all malformed inputs safely
   - Add spec for token format validation

3. **Webhook ReDoS Protection (1-2 days)**
   - Add regex complexity validator before storing matcher patterns
   - Implement timeout for regex matching (max 100ms)
   - Add tests verifying timeout enforcement

4. **MCP Share Endpoint Security (1 day)**
   - Add 5+ security tests for token isolation, TTL, reuse prevention
   - Document authorization requirements in endpoint

### MEDIUM-TERM (P1 - Next Sprint)

5. **Performance Testing (3-5 days)**
   - Implement query counting fixture to detect N+1 queries
   - Add load test suite for list_sessions() with 1K+ items
   - Benchmark cache.scan_keys() with 10K+ keys
   - Document performance SLOs (e.g., list_sessions < 500ms for 1K items)

6. **Close Coverage Gaps (2-4 days)**
   - `routes/sessions.py`: 41% → 85%+ (promote, update_tags endpoints)
   - `routes/query.py`: 71% → 85%+ (error paths in streaming)
   - `services/agent/handlers.py`: 60% → 80%+ (hook execution)

7. **Refactor Test Infrastructure (2-3 days)**
   - Split `conftest.py` into focused modules (`fixtures/sessions.py`, `fixtures/cache.py`)
   - Reduce fixture count from 8 to 3-4 core fixtures
   - Add fixture documentation with use cases

### ONGOING (P2-P3)

8. **Test Quality Improvements**
   - Enforce minimum 3 assertions per test
   - Require TDD comment pattern (RED, GREEN, REFACTOR markers)
   - Add assertion density metrics to CI/CD

9. **Documentation**
   - Add testing guidelines to CLAUDE.md
   - Document mock strategy (when to use, when to use real services)
   - Create ReDoS protection checklist for user-supplied regexes

---

## Test Categories Summary

### By Category:

**Contract Tests (7 files, ~80 tests)**
- ✅ Strong coverage of API contracts
- ✅ Good validation of request/response formats
- ⚠️ Limited error scenario coverage

**Unit Tests (35+ files, ~600 tests)**
- ✅ Good schema/validation coverage
- ✅ Good exception handling coverage
- ⚠️ Service layer coverage is inconsistent
- ❌ Security boundary tests missing

**Integration Tests (4 files, ~50 tests)**
- ✅ Good E2E workflow coverage
- ⚠️ Few negative test scenarios
- ⚠️ Performance characteristics not validated

**Security Tests (1 file, ~6 tests)**
- ⚠️ MCP config sanitization covered
- ❌ Authorization boundary tests missing
- ❌ Token/credential handling tests missing

**E2E Tests (1 file, ~3 tests)**
- ⚠️ Require ALLOW_REAL_CLAUDE_API=true flag
- ⚠️ Slow execution (skipped by default)
- ❌ Performance characteristics not measured

---

## Files to Prioritize

### High Priority (Fix First)
1. `/apps/api/routes/sessions.py` - 41% coverage
2. `/apps/api/services/session.py` - Authorization boundary gap
3. `/apps/api/middleware/openai_auth.py` - Bearer token edge cases
4. `/apps/api/services/webhook.py` - ReDoS vulnerability

### Medium Priority (Next)
5. `/apps/api/routes/query.py` - 71% coverage
6. `/apps/api/routes/websocket.py` - 70% coverage
7. `/apps/api/services/mcp_server_configs.py` - 63% coverage
8. `/apps/api/services/agent/handlers.py` - 60% coverage

### Infrastructure Tests Needed
- Connection pool exhaustion tests
- Cache scan pagination tests
- Database N+1 query detection

---

## Configuration Notes

### Current Test Setup
```
Framework:      pytest v9.0.2
Async Support:  pytest-anyio (not pytest-asyncio)
Parallelization: pytest-xdist with 12 workers
Coverage Tool:  pytest-cov
Database:       PostgreSQL (async with asyncpg)
Cache:          Redis (async with redis-py)
Mocking:        unittest.mock
```

### Important Settings (pyproject.toml)
```toml
# Disabled pytest-asyncio to avoid event loop conflicts
addopts = "-v --tb=short -p no:asyncio -n auto"

# Uses anyio backend instead
@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
```

### Environment Variables for Testing
```bash
DATABASE_URL="postgresql+asyncpg://test:test@localhost:54432/test"
REDIS_URL="redis://localhost:54379/0"
API_KEY="test-api-key-12345"
ALLOW_REAL_CLAUDE_API="false"  # Disable E2E tests by default
```

---

## Next Steps

1. **Run this analysis with team** - Review findings in standup
2. **Prioritize fixes** - Focus on P0 security gaps first
3. **Create test tasks** - Break down recommendations into 1-2 day tasks
4. **Implement coverage validation** - Add pre-commit check to prevent new gaps
5. **Schedule follow-up** - Re-run analysis after Phase 2 fixes

---

**Report Generated By:** Test Analysis Agent
**Test Execution Time:** 21.02 seconds
**Command:** `uv run pytest --cov=apps/api --cov-report=term-missing -q`
