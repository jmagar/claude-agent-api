# Testing Strategy Analysis - Claude Agent API

**Generated:** 07:09:15 AM | 01/10/2026 (UTC)

## Executive Summary

**Overall Coverage:** 81.64% (2409/2828 lines covered)

**Test Statistics:**
- Total Test Files: 79
- Total Test Functions: 776
- Total Assertions: 1436
- Assertions per Test: 1.85
- Skipped Tests: 5
- Test Code Lines: 16,109
- Production Code Lines: 9,792
- Test-to-Code Ratio: 1.64:1

**Verdict:** GOOD coverage with CRITICAL gaps in security and performance testing

---

## 1. Unit Test Coverage Analysis

### Coverage by Category

**Well-Tested Areas (>85% coverage):**
- Schema validation (test_security.py, test_validators.py)
- Request/response models (test_request_*.py, test_schemas.py)
- Agent service orchestrator components (test_stream_*.py, test_single_query_*.py)
- Cache operations (test_cache.py)
- Configuration (test_config.py)

**Under-Tested Areas (<80% coverage):**

| File | Coverage | Missing Lines | Risk Level |
|------|----------|---------------|------------|
| protocols.py | 0.0% | 56 | LOW (interface definitions) |
| schemas/messages.py | 51.3% | 20 | MEDIUM |
| routes/health.py | 67.3% | 14 | LOW |
| services/agent/service.py | 67.8% | 73 | **HIGH** |
| routes/query.py | 69.2% | 21 | **HIGH** |
| routes/websocket.py | 71.2% | 38 | **CRITICAL** |
| middleware/logging.py | 74.5% | 9 | MEDIUM |
| services/agent/handlers.py | 75.5% | 24 | HIGH |
| routes/session_control.py | 75.5% | 7 | MEDIUM |
| adapters/session_repo.py | 76.1% | 20 | HIGH |
| schemas/requests/sessions.py | 76.9% | 10 | MEDIUM |
| services/agent/hooks.py | 77.3% | 4 | MEDIUM |
| main.py | 78.1% | 14 | MEDIUM |
| services/webhook.py | 78.6% | 17 | HIGH |
| services/session.py | 79.2% | 34 | HIGH |

### Critical Coverage Gaps

**1. WebSocket Routes (71.2% coverage, 38 missing lines)**
- **Issue:** WebSocket authentication only partially tested
- **Risk:** Session auth bypass vulnerability (SECURITY-002 unfixed)
- **Missing Tests:**
  - Session ownership validation in WebSocket connections
  - WebSocket-specific rate limiting
  - Connection hijacking prevention
  - Error handling during mid-stream authentication failures

**2. Agent Service Core (67.8% coverage, 73 missing lines)**
- **Issue:** Core orchestration logic under-tested
- **Risk:** Critical business logic failures in production
- **Missing Tests:**
  - Concurrent session handling
  - Lock contention scenarios
  - Error recovery paths
  - Resource cleanup on abnormal termination

**3. Query Routes (69.2% coverage, 21 missing lines)**
- **Issue:** Primary API endpoint under-tested
- **Risk:** SSE streaming failures, session leaks
- **Missing Tests:**
  - SSE origin validation (SECURITY-003)
  - Slow client handling
  - Connection pool exhaustion
  - Multi-turn conversation edge cases

---

## 2. Integration Test Coverage Analysis

### Coverage Assessment

**Strong Integration Testing:**
- ✅ Session lifecycle (create, resume, fork)
- ✅ Checkpoints (create, list, rewind)
- ✅ Model selection and configuration
- ✅ Tool restrictions (allowed/disallowed tools)
- ✅ Structured output handling
- ✅ Subagent invocation
- ✅ Slash command execution
- ✅ Skills integration
- ✅ Permission modes

**Weak Integration Testing:**
- ❌ Database N+1 query prevention (PERF-001)
- ❌ Connection pool exhaustion scenarios (PERF-003)
- ❌ Distributed lock contention (PERF-004)
- ❌ Redis failover behavior
- ❌ PostgreSQL connection failures
- ❌ Cache invalidation edge cases

### Integration Test Quality

**Strengths:**
- Tests use real database and cache (PostgreSQL + Redis)
- Fixtures properly isolate test state
- Mock Claude SDK prevents real API calls
- Tests verify contract compliance (OpenAPI)

**Weaknesses:**
- No load testing for concurrent sessions
- No chaos engineering tests (service failures)
- Limited error injection testing
- No performance regression tests

---

## 3. Test Quality Metrics

### Assertion Density: 1.85 assertions/test

**Assessment:** BELOW OPTIMAL (target: 2.5-3.5)

**Analysis:**
- Some tests verify only success/failure (1 assertion)
- Contract tests often check single field
- Missing comprehensive state validation
- Insufficient boundary condition checks

**Examples of Low Assertion Density:**

```python
# tests/contract/test_sessions_contract.py
async def test_session_interrupt_returns_success(self, ...):
    response = await async_client.post(...)
    assert response.status_code == 200  # Only 1 assertion
```

**Recommended Pattern:**
```python
async def test_session_interrupt_returns_success(self, ...):
    response = await async_client.post(...)
    assert response.status_code == 200
    assert "session_id" in response.json()
    assert response.json()["status"] == "interrupted"
    # Verify side effects in database/cache
```

### Test Maintainability

**Strengths:**
- Descriptive test names following convention
- Fixtures properly scoped and reusable
- Mock infrastructure well-organized (tests/mocks/)
- Clear separation: unit/integration/contract/e2e

**Weaknesses:**
- Some tests tightly coupled to implementation
- Large fixtures (conftest.py is 335 lines)
- Mock Claude SDK complexity (multiple event builders)
- Repetitive setup code in some test classes

### Test Performance

**Test Execution:** ~777 tests run successfully

**Skipped Tests:** 5 (SDK integration tests requiring real Claude API)

**Concerns:**
- No timeout limits on individual tests
- No parallelization markers for slow tests
- Integration tests may be slower than necessary

---

## 4. Test Pyramid Assessment

### Current Distribution

```
         /\
        /E2\     E2E: ~1 test (0.1%)
       /----\
      /  I   \   Integration: ~280 tests (36%)
     /--------\
    /    U     \ Unit: ~490 tests (63%)
   /------------\
```

**Assessment:** INVERTED PYRAMID (too many integration tests)

**Recommended Distribution:**
```
         /\
        /E2\     E2E: 5-10% (40-80 tests)
       /----\
      /  I   \   Integration: 20-30% (150-230 tests)
     /--------\
    /    U     \ Unit: 60-70% (465-540 tests)
   /------------\
```

### Pyramid Violations

**Issue 1: Too Many Integration Tests (36%)**
- Many integration tests could be unit tests
- Slow test suite execution
- Harder to pinpoint failures

**Example Violation:**
```python
# tests/integration/test_permissions.py (should be unit test)
async def test_permission_mode_default_when_not_specified(self, ...):
    request = QueryRequest(prompt="Test prompt")
    assert request.permission_mode == "default"
```

**Issue 2: Insufficient E2E Tests (0.1%)**
- Only 1 E2E test (test_claude_api.py)
- No end-to-end workflow validation
- No real Claude SDK integration testing

**Recommended E2E Tests:**
- Complete query → response → checkpoint → rewind flow
- Multi-turn conversation with real SDK
- Session fork with real file modifications
- Webhook hook execution end-to-end

---

## 5. TDD Practices Analysis

### Evidence of TDD

**Positive Indicators:**
- RED-GREEN comments in some tests
- Test file creation dates precede implementation
- Contract tests drive API design

**Negative Indicators:**
- Many tests added after implementation
- Some complex logic lacks incremental tests
- Refactoring without test updates

### TDD Compliance: 65% (estimated)

**Well-TDD'd Components:**
- Security validators (test_security.py)
- Schema validation (test_validators.py)
- Cache operations (test_cache.py)

**Poorly-TDD'd Components:**
- Agent service orchestrator (added tests after)
- WebSocket routes (incomplete test coverage)
- Session repository (missing edge cases)

---

## 6. Security Testing Gaps (CRITICAL)

### Coverage by Security Issue

| Issue | Tests | Gap | Risk |
|-------|-------|-----|------|
| SECURITY-001: Duplicate auth logic | ✅ Partial | No middleware + dependency integration test | MEDIUM |
| SECURITY-002: WebSocket session auth | ❌ None | Zero tests for session ownership | **CRITICAL** |
| SECURITY-003: SSE origin validation | ❌ None | No CORS/origin tests | **HIGH** |
| SECURITY-004: Brute force protection | ✅ Good | Rate limit tests exist | LOW |
| SECURITY-005: Proxy header trust | ✅ Good | test_ratelimit.py covers this | LOW |
| SECURITY-006: Sensitive data in logs | ❌ None | No log sanitization tests | **HIGH** |

### Missing Security Tests

**1. Authentication Bypass Tests**
```python
# MISSING: tests/integration/test_auth_bypass.py
async def test_websocket_rejects_session_from_different_api_key():
    """Verify WebSocket validates session ownership."""
    pass  # NOT IMPLEMENTED

async def test_query_rejects_forged_correlation_id():
    """Verify correlation ID cannot be spoofed."""
    pass  # NOT IMPLEMENTED
```

**2. Authorization Tests (Session Ownership)**
```python
# MISSING: tests/integration/test_session_authorization.py
async def test_resume_rejects_session_from_different_owner():
    """Verify session owner_api_key is validated."""
    pass  # NOT IMPLEMENTED

async def test_list_sessions_filters_by_api_key():
    """Verify sessions are isolated by API key."""
    pass  # NOT IMPLEMENTED
```

**3. Input Validation Tests**
```python
# EXISTING but INCOMPLETE: tests/unit/test_security.py
# ✅ Path traversal: TESTED
# ✅ Null bytes: TESTED
# ✅ Environment variables: TESTED
# ❌ SQL injection: NOT TESTED
# ❌ NoSQL injection: NOT TESTED
# ❌ SSRF in webhooks: PARTIALLY TESTED
# ❌ XXE attacks: NOT TESTED
```

**4. Rate Limiting Tests**
```python
# EXISTING: tests/unit/middleware/test_ratelimit.py
# ✅ IP extraction: TESTED
# ✅ API key extraction: TESTED
# ✅ 429 responses: TESTED
# ❌ Distributed rate limiting: NOT TESTED
# ❌ Rate limit bypass attempts: NOT TESTED
# ❌ Concurrent request bursts: NOT TESTED
```

**5. CORS Configuration Tests**
```python
# MISSING: tests/integration/test_cors.py
async def test_sse_rejects_unauthorized_origin():
    """Verify SSE streams validate Origin header."""
    pass  # NOT IMPLEMENTED

async def test_cors_headers_present_on_preflight():
    """Verify CORS preflight requests."""
    pass  # NOT IMPLEMENTED
```

**6. Sensitive Data Leakage Tests**
```python
# MISSING: tests/unit/test_log_sanitization.py
async def test_logs_redact_api_keys():
    """Verify API keys are not logged."""
    pass  # NOT IMPLEMENTED

async def test_error_responses_hide_internal_paths():
    """Verify stack traces are not exposed."""
    pass  # NOT IMPLEMENTED
```

---

## 7. Performance Testing Gaps (CRITICAL)

### Coverage by Performance Issue

| Issue | Tests | Gap | Risk |
|-------|-------|-----|------|
| PERF-001: N+1 query problem | ❌ None | No query count assertions | **CRITICAL** |
| PERF-002: Missing index on owner_api_key | ❌ None | No performance benchmarks | **HIGH** |
| PERF-003: Connection pool exhaustion | ❌ None | No concurrent load tests | **CRITICAL** |
| PERF-004: Distributed lock contention | ❌ None | No contention stress tests | **HIGH** |
| PERF-005: High complexity functions | ❌ None | No complexity regression tests | MEDIUM |

### Missing Performance Tests

**1. N+1 Query Detection**
```python
# MISSING: tests/performance/test_database_queries.py
async def test_list_sessions_single_query():
    """Verify session listing executes only 1 database query."""
    # Create 100 sessions
    # Track query count (using sqlalchemy event listeners)
    # Assert query_count == 1 (no N+1)
    pass  # NOT IMPLEMENTED

async def test_session_load_with_messages_eager_loads():
    """Verify session with messages uses JOIN, not N queries."""
    pass  # NOT IMPLEMENTED
```

**2. Connection Pool Exhaustion**
```python
# MISSING: tests/performance/test_connection_pools.py
async def test_concurrent_queries_respect_pool_limits():
    """Verify 100 concurrent queries don't exhaust pool."""
    # Create 100 concurrent query tasks
    # Assert all complete successfully
    # Assert pool size stays within limits
    pass  # NOT IMPLEMENTED

async def test_abandoned_connections_are_recycled():
    """Verify crashed clients don't leak connections."""
    pass  # NOT IMPLEMENTED
```

**3. Distributed Lock Contention**
```python
# MISSING: tests/performance/test_distributed_locks.py
async def test_concurrent_session_access_serializes():
    """Verify 10 concurrent requests for same session serialize via locks."""
    # 10 tasks try to resume same session
    # Measure lock acquisition time
    # Assert reasonable throughput
    pass  # NOT IMPLEMENTED

async def test_lock_timeout_prevents_deadlocks():
    """Verify abandoned locks expire and don't block forever."""
    pass  # NOT IMPLEMENTED
```

**4. Load Testing**
```python
# MISSING: tests/performance/test_load.py
async def test_api_handles_100_concurrent_sessions():
    """Verify API can handle 100 concurrent active sessions."""
    pass  # NOT IMPLEMENTED

async def test_sse_streams_handle_slow_clients():
    """Verify slow SSE consumers don't block other clients."""
    pass  # NOT IMPLEMENTED
```

**5. Memory Leak Testing**
```python
# MISSING: tests/performance/test_memory.py
async def test_long_running_session_memory_stable():
    """Verify 1000-turn session doesn't leak memory."""
    # Start session
    # Execute 1000 query/response cycles
    # Assert memory usage stays bounded
    pass  # NOT IMPLEMENTED
```

---

## 8. Contract Testing Assessment

### OpenAPI Compliance

**Strengths:**
- tests/contract/test_openapi.py validates spec existence
- Endpoint existence verified
- Content-Type headers validated

**Weaknesses:**
- No automated schema validation against responses
- No request/response example testing
- No deprecated endpoint detection

### Contract Test Coverage

**Covered:**
- ✅ Query endpoints (POST /api/v1/query, /query/single)
- ✅ Session endpoints (GET/POST /api/v1/sessions/*)
- ✅ Checkpoint endpoints (GET/POST /api/v1/checkpoints/*)
- ✅ Skills endpoints

**Not Covered:**
- ❌ WebSocket contract validation
- ❌ Error response schemas (4xx, 5xx)
- ❌ Pagination contract (limit/offset behavior)
- ❌ Rate limit response headers

### Recommended Contract Tests

```python
# tests/contract/test_error_responses.py
async def test_404_error_matches_schema():
    """Verify 404 responses match OpenAPI error schema."""
    pass

async def test_422_validation_error_includes_field_details():
    """Verify validation errors include field-level info."""
    pass

# tests/contract/test_pagination.py
async def test_sessions_list_respects_limit_offset():
    """Verify pagination parameters work correctly."""
    pass
```

---

## 9. Test Isolation and Determinism

### Isolation Assessment: GOOD

**Strengths:**
- Function-scoped fixtures prevent state leakage
- Database/cache cleared between test runs (via migrations)
- Mock Claude SDK prevents external dependencies
- Correlation IDs isolate concurrent tests

**Weaknesses:**
- Some integration tests may share Redis state
- File system operations not fully isolated
- Time-dependent tests could be flaky

### Determinism Assessment: GOOD

**Strengths:**
- No random data in tests
- Timestamps mocked where needed
- UUIDs generated deterministically in fixtures

**Weaknesses:**
- No seed control for random operations
- Async race conditions possible in WebSocket tests
- No retry logic for transient failures

---

## 10. Test Pyramid Recommendations

### Immediate Actions (Priority 1)

**1. Add Critical Security Tests (2-3 days)**
- WebSocket session ownership validation
- Session authorization by API key
- Log sanitization tests

**2. Add N+1 Query Performance Tests (1 day)**
- Instrument database query counting
- Test session list with 100+ sessions
- Verify eager loading for related data

**3. Add Connection Pool Tests (1 day)**
- Concurrent query load testing
- Connection leak detection
- Pool exhaustion scenarios

### Short-Term Improvements (Priority 2)

**4. Increase Unit Test Coverage to 85%+ (3-4 days)**
- Focus on services/agent/service.py (67.8%)
- Focus on routes/websocket.py (71.2%)
- Focus on routes/query.py (69.2%)

**5. Add E2E Tests (2 days)**
- Complete workflow: query → checkpoint → rewind
- Multi-turn conversation with real SDK
- Session fork end-to-end

**6. Add Contract Tests (1 day)**
- Error response schemas
- Pagination behavior
- Rate limit headers

### Medium-Term Enhancements (Priority 3)

**7. Add Chaos Engineering Tests (3-5 days)**
- Redis failover during active query
- PostgreSQL connection loss
- Network partition scenarios

**8. Add Load/Stress Tests (2-3 days)**
- 100 concurrent sessions
- 1000 query/response turns
- Slow SSE client handling

**9. Refactor Test Pyramid (1 week)**
- Convert 50 integration tests to unit tests
- Add 40-80 E2E tests
- Rebalance to 60/30/10 distribution

---

## 11. Test-Driven Development Compliance

### TDD Assessment: 65% Compliance

**Evidence:**
- Security validators: RED-GREEN-REFACTOR cycle visible
- Schema validation: Tests written first
- Cache operations: Incremental test addition

**Non-Compliance:**
- Agent service: Tests added after implementation
- WebSocket routes: Implementation-first approach
- Session repository: Retroactive test addition

### TDD Improvement Plan

**1. Enforce TDD for New Features**
- Pre-commit hook: Block commits without tests
- PR review checklist: Verify tests exist
- CI pipeline: Fail if coverage decreases

**2. Retrofit TDD for Existing Code**
- Identify untested critical paths
- Write characterization tests
- Refactor with test safety net

**3. TDD Training**
- Document RED-GREEN-REFACTOR workflow
- Provide TDD examples in CLAUDE.md
- Code review focus on test-first approach

---

## 12. Specific Test Recommendations

### Priority 1: Critical Security Tests (MUST ADD)

```python
# tests/integration/test_session_authorization.py
class TestSessionAuthorization:
    async def test_resume_rejects_session_from_different_api_key(self):
        """SECURITY-002: Verify session ownership in resume."""
        # Create session with API key A
        # Attempt resume with API key B
        # Assert 403 Forbidden

    async def test_websocket_validates_session_ownership(self):
        """SECURITY-002: Verify WebSocket checks session owner."""
        # Create session with API key A
        # Connect WebSocket with API key B
        # Send resume message
        # Assert connection rejected

    async def test_list_sessions_filters_by_owner_api_key(self):
        """SECURITY-002: Verify session isolation."""
        # Create 10 sessions with API key A
        # Create 10 sessions with API key B
        # List sessions with API key A
        # Assert only 10 sessions returned (A's sessions)
```

```python
# tests/integration/test_sse_security.py
class TestSSEOriginValidation:
    async def test_sse_rejects_unauthorized_origin(self):
        """SECURITY-003: Verify Origin header validation."""
        # POST /query with Origin: https://evil.com
        # Assert 403 or connection rejected

    async def test_sse_allows_authorized_origin(self):
        """SECURITY-003: Verify whitelisted origins work."""
        # Configure allowed origins
        # POST /query with whitelisted Origin
        # Assert stream starts
```

```python
# tests/unit/test_log_sanitization.py
class TestLogSanitization:
    def test_api_key_redacted_in_logs(self):
        """SECURITY-006: Verify API keys never logged."""
        # Trigger log with API key in context
        # Assert logs contain "[REDACTED]" not actual key

    def test_sensitive_headers_excluded_from_logs(self):
        """SECURITY-006: Verify Authorization headers hidden."""
        # Log request with Authorization header
        # Assert header value redacted
```

### Priority 2: Performance Tests (MUST ADD)

```python
# tests/performance/test_n_plus_one.py
class TestDatabaseQueryOptimization:
    async def test_list_sessions_single_query(self):
        """PERF-001: Verify no N+1 queries in session list."""
        # Create 100 sessions
        # Install query counter (SQLAlchemy event listener)
        # Call list_sessions()
        # Assert query_count <= 2 (1 for sessions, 1 for count)

    async def test_session_with_messages_eager_loads(self):
        """PERF-001: Verify JOINs used for related data."""
        # Create session with 50 messages
        # Install query counter
        # Call get_session_with_messages()
        # Assert query_count == 1 (single JOIN query)
```

```python
# tests/performance/test_connection_pool.py
class TestConnectionPoolLimits:
    async def test_concurrent_queries_respect_pool_size(self):
        """PERF-003: Verify pool limits enforced."""
        # Configure pool_size=10
        # Launch 50 concurrent queries
        # Assert all complete without deadlock
        # Assert max concurrent connections <= 10

    async def test_abandoned_connections_recycled(self):
        """PERF-003: Verify connection cleanup."""
        # Start query, simulate client disconnect
        # Wait for connection timeout
        # Assert connection returned to pool
```

```python
# tests/performance/test_distributed_locks.py
class TestLockContention:
    async def test_concurrent_session_resume_serializes(self):
        """PERF-004: Verify locks prevent race conditions."""
        # Launch 10 concurrent resumes for same session
        # Assert all succeed without data corruption
        # Measure average lock wait time (<100ms)

    async def test_lock_timeout_prevents_deadlock(self):
        """PERF-004: Verify lock expiration."""
        # Acquire lock, simulate process crash
        # Attempt lock acquisition after TTL
        # Assert lock acquired successfully
```

### Priority 3: Contract and E2E Tests

```python
# tests/contract/test_error_schemas.py
class TestErrorResponseSchemas:
    async def test_404_matches_openapi_schema(self):
        """Verify 404 error responses match spec."""
        # Request nonexistent session
        # Validate response against OpenAPI schema

    async def test_422_validation_error_structure(self):
        """Verify validation errors include field details."""
        # Send invalid request (missing prompt)
        # Assert response has 'detail' array with field info
```

```python
# tests/e2e/test_complete_workflow.py
@pytest.mark.e2e
class TestCompleteWorkflow:
    async def test_query_checkpoint_rewind_workflow(self):
        """End-to-end: Query → Checkpoint → Rewind."""
        # POST /query with prompt
        # Wait for completion
        # GET /checkpoints (verify created)
        # POST /checkpoints/{id}/rewind
        # Verify file state restored

    async def test_multi_turn_conversation_with_real_sdk(self):
        """End-to-end: 10-turn conversation."""
        # Query 1: "List files"
        # Query 2: "Create test.py"
        # Query 3: "Read test.py"
        # ...
        # Verify conversation context maintained
```

---

## 13. Test Maintainability Improvements

### Reduce Fixture Complexity

**Issue:** conftest.py is 335 lines with complex fixtures

**Recommendation:**
- Split into multiple fixture files by domain
- Extract common patterns into helper functions
- Document fixture dependencies

```python
# tests/fixtures/sessions.py
from tests.fixtures.database import db_session
from tests.fixtures.cache import redis_cache

@pytest.fixture
async def mock_session_id(db_session, redis_cache):
    """Create session (moved from conftest.py)."""
    ...
```

### Reduce Test Duplication

**Issue:** Similar test patterns repeated across files

**Recommendation:**
- Extract common assertion helpers
- Create test base classes for shared setup
- Use parametrize for similar test cases

```python
# tests/helpers/assertions.py
def assert_valid_session_response(response):
    """Reusable assertion for session responses."""
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "model" in data
    assert "status" in data

# tests/integration/test_sessions.py
class TestSessionEndpoints:
    async def test_create_session(self, ...):
        response = await client.post(...)
        assert_valid_session_response(response)
```

---

## 14. Flaky Test Prevention

### Current Risk: MEDIUM

**Potential Sources of Flakiness:**
- Async race conditions in WebSocket tests
- Time-dependent assertions
- Shared Redis state between tests
- Event loop issues with fixtures

### Recommendations

**1. Add Timeout Protections**
```python
@pytest.mark.timeout(5)  # Fail after 5 seconds
async def test_slow_operation(self):
    ...
```

**2. Add Retry Logic for Transient Failures**
```python
@pytest.mark.flaky(reruns=3, reruns_delay=1)
async def test_eventually_consistent(self):
    ...
```

**3. Isolate Async Tests**
```python
@pytest.fixture
async def isolated_event_loop():
    """Dedicated event loop per test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
```

**4. Add Explicit Wait Conditions**
```python
async def wait_for_session_active(session_id):
    """Wait until session is active (no busy waiting)."""
    for _ in range(50):  # 5 second timeout
        session = await get_session(session_id)
        if session.status == "active":
            return
        await asyncio.sleep(0.1)
    raise TimeoutError("Session never became active")
```

---

## 15. Testing Tool Recommendations

### Missing Testing Tools

**1. Query Counter for N+1 Detection**
```python
# tests/utils/query_counter.py
from sqlalchemy import event

class QueryCounter:
    def __init__(self):
        self.count = 0

    def __enter__(self):
        event.listen(Engine, "before_cursor_execute", self._count)
        return self

    def __exit__(self, *args):
        event.remove(Engine, "before_cursor_execute", self._count)

    def _count(self, *args):
        self.count += 1

# Usage:
with QueryCounter() as counter:
    await session_service.list_sessions()
    assert counter.count <= 2  # No N+1
```

**2. Load Testing Framework**
```python
# tests/performance/load_test.py
import locust

class QueryLoadTest(locust.HttpUser):
    @task
    def query_endpoint(self):
        self.client.post("/api/v1/query", json={"prompt": "test"})

# Run: locust -f load_test.py --users 100 --spawn-rate 10
```

**3. Contract Validation Library**
```python
# tests/utils/contract_validator.py
from openapi_spec_validator import validate_spec
from openapi_core import validate_response

def assert_matches_openapi(response, operation_id):
    """Validate response against OpenAPI schema."""
    spec = load_openapi_spec()
    validate_response(spec, operation_id, response)
```

**4. Memory Profiler**
```python
# tests/performance/test_memory.py
from memory_profiler import profile

@profile
async def test_session_memory_usage(self):
    """Profile memory usage during 1000-turn session."""
    for i in range(1000):
        await query(f"Turn {i}")
```

---

## 16. CI/CD Integration Recommendations

### Current CI Pipeline

**Strengths:**
- Tests run on every commit (GitHub Actions)
- PostgreSQL and Redis services configured
- Parallel test execution (pytest-xdist)

**Weaknesses:**
- No coverage threshold enforcement
- No performance regression detection
- No flaky test tracking

### Recommended CI Enhancements

**1. Enforce Coverage Thresholds**
```yaml
# .github/workflows/ci.yml
- name: Check coverage
  run: |
    uv run pytest --cov=apps/api --cov-fail-under=85
```

**2. Track Coverage Trends**
```yaml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
    fail_ci_if_error: true
```

**3. Run Performance Tests Separately**
```yaml
- name: Run performance tests
  run: |
    uv run pytest tests/performance/ --benchmark-only
```

**4. Detect Flaky Tests**
```yaml
- name: Detect flaky tests
  run: |
    uv run pytest --reruns 3 --only-rerun-failed
```

---

## 17. Summary: Prioritized Test Gaps

### CRITICAL Gaps (Fix Immediately)

1. **WebSocket Session Authorization (SECURITY-002)**
   - Impact: Session hijacking possible
   - Effort: 4 hours
   - Tests Needed: 3

2. **N+1 Query Prevention (PERF-001)**
   - Impact: Database overload at scale
   - Effort: 1 day
   - Tests Needed: 5

3. **Connection Pool Exhaustion (PERF-003)**
   - Impact: Service outage under load
   - Effort: 1 day
   - Tests Needed: 4

### HIGH Gaps (Fix This Sprint)

4. **SSE Origin Validation (SECURITY-003)**
   - Impact: CORS bypass attacks
   - Effort: 2 hours
   - Tests Needed: 2

5. **Log Sanitization (SECURITY-006)**
   - Impact: API key leakage
   - Effort: 3 hours
   - Tests Needed: 3

6. **Agent Service Coverage (67.8%)**
   - Impact: Business logic failures
   - Effort: 2 days
   - Tests Needed: 15

### MEDIUM Gaps (Fix Next Sprint)

7. **Distributed Lock Contention (PERF-004)**
   - Impact: Deadlocks under load
   - Effort: 1 day
   - Tests Needed: 3

8. **Query Routes Coverage (69.2%)**
   - Impact: SSE streaming failures
   - Effort: 1 day
   - Tests Needed: 8

9. **E2E Test Suite (0.1%)**
   - Impact: Integration regressions
   - Effort: 2 days
   - Tests Needed: 5

---

## 18. Testing Metrics Dashboard (Recommended)

### Track Over Time

**Coverage Metrics:**
- Overall coverage percentage (target: 85%+)
- Coverage by module (identify trends)
- Uncovered critical paths

**Test Quality Metrics:**
- Assertions per test (target: 2.5-3.5)
- Test execution time (detect slowdowns)
- Flaky test rate (target: <1%)

**Test Distribution:**
- Unit/Integration/E2E ratio (target: 60/30/10)
- Test count by priority level
- Skipped test count (minimize)

**Performance Metrics:**
- N+1 query occurrences (target: 0)
- Database query count per endpoint
- Response time percentiles (p50, p95, p99)

---

## 19. Conclusion

### Overall Assessment: GOOD but CRITICAL GAPS

**Strengths:**
- Strong coverage (81.64%) for a pre-production API
- Well-structured test organization (unit/integration/contract)
- Good TDD practices in security-critical areas
- Comprehensive schema validation

**Critical Weaknesses:**
- WebSocket session authorization completely untested (**SECURITY RISK**)
- No N+1 query prevention tests (**PERFORMANCE RISK**)
- No connection pool exhaustion tests (**STABILITY RISK**)
- Inverted test pyramid (too many integration tests)
- Low assertion density (1.85 vs target 2.5-3.5)

### Risk Assessment

**Security Risk:** HIGH
- 3 critical security issues lack tests
- WebSocket auth bypass possible
- API key leakage in logs untested

**Performance Risk:** CRITICAL
- Database overload at scale likely
- Connection pool exhaustion possible
- Lock contention untested

**Stability Risk:** MEDIUM
- Good error handling coverage
- Missing chaos engineering tests
- Flaky test potential in WebSocket tests

### Recommended Next Steps

1. **Week 1:** Add CRITICAL security tests (WebSocket auth, log sanitization)
2. **Week 2:** Add CRITICAL performance tests (N+1 queries, connection pools)
3. **Week 3:** Increase coverage to 85%+ (agent service, query routes, websocket)
4. **Week 4:** Add E2E tests and chaos engineering scenarios
5. **Ongoing:** Rebalance test pyramid (convert integration → unit)

---

**End of Analysis**
