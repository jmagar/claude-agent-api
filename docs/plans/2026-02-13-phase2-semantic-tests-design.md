# Phase 2 Semantic Tests - Design Document

**Created:** 2026-02-13
**Status:** Approved
**Scope:** Sessions, Projects, Memories (3 resources)
**Approach:** Depth-first exhaustive coverage (~65-70 tests)

## Overview

Phase 2 expands semantic test coverage with exhaustive validation of Sessions, Projects, and Memories endpoints. This builds on Phase 1's foundation (8 tests) by adding ~65-70 tests organized into resource-based modules with full CRUD, edge cases, SSE streaming, and multi-tenancy isolation.

**Key Decisions:**
- **Depth-first:** 2-3 resources with exhaustive coverage (vs. breadth-first all resources)
- **Resource-based modules:** One file per resource (vs. monolithic or feature-based)
- **Exhaustive edge cases:** ~20+ tests per resource (vs. happy path only)
- **SSE validation:** Full event sequence testing (vs. mocked streaming)
- **Explicit isolation tests:** Dedicated cross-tenant tests (vs. implicit)

## File Structure

```
tests/integration/
├── test_non_openapi_semantics.py        # Phase 1 (existing, 8 tests)
└── semantics/                            # Phase 2 (NEW)
    ├── __init__.py                       # Empty (pytest discovery)
    ├── conftest.py                       # Shared fixtures
    ├── test_sessions_semantics.py        # 20-25 tests
    ├── test_projects_semantics.py        # 15-20 tests
    ├── test_memories_semantics.py        # 20-25 tests
    └── test_isolation_semantics.py       # 6 tests
```

**Rationale:**
- **Separate directory:** Organizes Phase 2 tests without polluting `integration/` root
- **Dedicated conftest:** Phase 2-specific fixtures (SSE helpers, multi-tenant)
- **Resource-based modules:** 4 files (~200-600 lines each) - balanced granularity
- **pytest discovery:** Standard structure, works with `pytest tests/integration/semantics/`

## Test Categories & Coverage

### `test_sessions_semantics.py` (20-25 tests)

**CRUD Operations (5 tests):**
- `test_list_sessions_pagination` - Page size, offset, total count
- `test_list_sessions_empty` - No sessions returns empty list
- `test_get_session_succeeds` - Retrieve session by ID
- `test_get_session_not_found` - 404 with SESSION_NOT_FOUND error
- `test_get_session_wrong_owner` - 404 for cross-tenant access

**Session Operations - Resume (5 tests):**
- `test_resume_session_succeeds` - Basic resume with SSE events
- `test_resume_with_model_override` - Change model mid-session
- `test_resume_with_permission_mode_change` - Override permission mode
- `test_resume_nonexistent_session` - 404 error
- `test_resume_validates_max_turns` - Rejects invalid max_turns (422)

**Session Operations - Fork (5 tests):**
- `test_fork_session_succeeds` - Creates new session with parent link
- `test_fork_with_model_override` - Fork with different model
- `test_fork_nonexistent_session` - 404 error
- `test_fork_validates_prompt_required` - Rejects empty prompt (422)
- `test_fork_preserves_parent_history` - Verify history copying

**Session State Management (5 tests):**
- `test_promote_session_succeeds` - Mark session as template
- `test_promote_nonexistent_session` - 404 error
- `test_update_session_tags_succeeds` - Add/remove tags
- `test_update_tags_validates_tag_format` - Rejects invalid tag format (422)
- `test_session_state_transitions` - Verify status field updates

**SSE Streaming (3 tests):**
- `test_resume_sse_event_sequence` - Validate init → message → result → done
- `test_fork_sse_partial_deltas` - Verify partial content deltas
- `test_interrupt_during_streaming` - Interrupt mid-stream returns interrupted status

### `test_projects_semantics.py` (15-20 tests)

**CRUD Operations (8 tests):**
- `test_list_projects_succeeds` - List all projects
- `test_list_projects_empty` - No projects returns empty list
- `test_get_project_succeeds` - Retrieve by ID
- `test_get_project_not_found` - 404 with PROJECT_NOT_FOUND
- `test_create_project_succeeds` - Verify response structure
- `test_create_project_duplicate_name` - 409 conflict (Phase 1 coverage)
- `test_update_project_succeeds` - Update name/path
- `test_delete_project_succeeds` - Soft/hard delete

**Validation & Edge Cases (7 tests):**
- `test_update_project_not_found` - 404 error
- `test_update_project_duplicate_name` - 409 conflict on name collision
- `test_delete_project_not_found` - 404 error
- `test_create_project_invalid_path` - Rejects non-existent/invalid paths (422)
- `test_update_project_validates_name_length` - Min/max length enforcement
- `test_project_path_normalization` - Verify trailing slashes handled
- `test_project_created_updated_timestamps` - Verify timezone-aware timestamps

### `test_memories_semantics.py` (20-25 tests)

**CRUD Operations (8 tests):**
- `test_search_memories_succeeds` - Semantic search returns results
- `test_search_memories_no_results` - Empty result set
- `test_add_memory_succeeds` - Add single memory
- `test_add_memory_with_metadata` - Include custom metadata
- `test_list_memories_succeeds` - List all memories for API key
- `test_list_memories_empty` - No memories returns empty list
- `test_delete_memory_succeeds` - Delete by ID
- `test_delete_all_memories_succeeds` - Bulk delete

**Multi-Tenancy & Isolation (6 tests):**
- `test_search_scoped_to_api_key` - API key A doesn't see API key B's memories
- `test_add_memory_scoped_to_api_key` - Memories tagged with owner
- `test_list_scoped_to_api_key` - List only returns owned memories
- `test_delete_memory_wrong_owner` - 404 when deleting other tenant's memory
- `test_memory_graph_isolation` - Neo4j entities scoped by user_id
- `test_memory_vector_isolation` - Qdrant filtering by API key

**Edge Cases & Validation (6 tests):**
- `test_delete_memory_not_found` - 404 error
- `test_search_validates_query_required` - Rejects empty query (422)
- `test_add_memory_validates_content_required` - Rejects empty content (422)
- `test_search_with_enable_graph_false` - Verify graph operations disabled
- `test_memory_embedding_dimensions` - Verify 1024-dim embeddings (Qwen model)
- `test_memory_timestamps_timezone_aware` - UTC timestamps enforced

### `test_isolation_semantics.py` (6 tests)

**Cross-Tenant Access Protection (6 tests):**
- `test_sessions_cross_tenant_isolation` - API key A cannot GET API key B's session
- `test_projects_cross_tenant_isolation` - API key A cannot GET API key B's project
- `test_memories_cross_tenant_isolation` - API key A cannot access API key B's memories
- `test_session_operations_cross_tenant` - Cannot resume/fork/interrupt other tenant's session
- `test_project_operations_cross_tenant` - Cannot update/delete other tenant's project
- `test_memory_operations_cross_tenant` - Cannot delete other tenant's memory

**Isolation behavior:** All cross-tenant access returns **404** (not 403) to prevent resource enumeration.

## Fixtures & Test Helpers

**Location:** `tests/integration/semantics/conftest.py`

### Multi-Tenant Fixtures

```python
@pytest.fixture
def second_api_key() -> str:
    """Second API key for cross-tenant isolation tests."""
    return f"test-api-key-{uuid4().hex[:8]}"

@pytest.fixture
def second_auth_headers(second_api_key: str) -> dict[str, str]:
    """Auth headers for second tenant."""
    return {"X-API-Key": second_api_key}
```

### Resource Fixtures

**Pattern:** Every resource has `mock_{resource}` and `mock_{resource}_other_tenant`

```python
@pytest.fixture
async def mock_session(async_client, auth_headers) -> str:
    """Create completed session, return session ID."""
    pass

@pytest.fixture
async def mock_session_other_tenant(async_client, second_auth_headers) -> str:
    """Create session owned by second tenant."""
    pass

@pytest.fixture
async def mock_project(async_client, auth_headers) -> dict[str, str]:
    """Create project, return {"id": "...", "name": "...", "path": "..."}."""
    pass

@pytest.fixture
async def mock_project_other_tenant(async_client, second_auth_headers) -> dict[str, str]:
    """Create project owned by second tenant."""
    pass

@pytest.fixture
async def mock_memory(async_client, auth_headers) -> dict[str, str]:
    """Create memory, return {"id": "...", "content": "..."}."""
    pass

@pytest.fixture
async def mock_memory_other_tenant(async_client, second_auth_headers) -> dict[str, str]:
    """Create memory owned by second tenant."""
    pass
```

### SSE Streaming Helpers

```python
@pytest.fixture
def sse_event_collector():
    """Helper to collect and validate SSE events from streaming responses."""
    async def collect_events(response):
        events = []
        async for line in response.aiter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = json.loads(line.split(":", 1)[1].strip())
                events.append({"event": event_type, "data": data})
        return events
    return collect_events

@pytest.fixture
def validate_sse_sequence():
    """Validate SSE event sequence matches expected pattern."""
    def validate(events, expected_sequence):
        actual_sequence = [e["event"] for e in events]
        assert actual_sequence == expected_sequence
    return validate
```

## Test Patterns & Conventions

### Naming Convention

```python
# Pattern: test_{operation}_{condition}_{expected_outcome}

# Good examples:
test_list_sessions_pagination               # Operation + behavior
test_get_session_not_found                  # Operation + error condition
test_resume_with_model_override             # Operation + config variant
test_sessions_cross_tenant_isolation        # Security boundary test
```

### Test Structure (AAA Pattern)

```python
async def test_get_project_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_project: dict[str, str],
) -> None:
    """Retrieve project by ID returns full project data."""
    # ARRANGE - Setup done by fixtures
    project_id = mock_project["id"]

    # ACT - Execute the operation
    response = await async_client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )

    # ASSERT - Verify behavior
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == mock_project["name"]
    assert data["path"] == mock_project["path"]
    assert "created_at" in data
    assert "updated_at" in data
```

### Error Response Validation

```python
async def test_get_session_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET non-existent session returns 404 with domain error."""
    missing_id = str(uuid4())

    response = await async_client.get(
        f"/api/v1/sessions/{missing_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404

    # Validate domain error structure
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SESSION_NOT_FOUND"
    assert data["error"]["message"]
    assert data["error"]["details"]["session_id"] == missing_id
```

### SSE Streaming Validation

```python
async def test_resume_sse_event_sequence(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
    sse_event_collector,
    validate_sse_sequence,
) -> None:
    """Resume session emits SSE events in correct order."""
    response = await async_client.post(
        f"/api/v1/sessions/{mock_session}/resume",
        json={"prompt": "Continue"},
        headers=auth_headers,
    )

    events = await sse_event_collector(response)
    validate_sse_sequence(events, ["init", "message", "result", "done"])

    # Validate event structures
    init_event = events[0]
    assert init_event["data"]["session_id"] == mock_session
    assert init_event["data"]["model"]

    result_event = [e for e in events if e["event"] == "result"][0]
    assert "total_turns" in result_event["data"]
    assert "total_cost_usd" in result_event["data"]
```

### Multi-Tenancy Isolation Pattern

```python
async def test_sessions_cross_tenant_isolation(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    second_auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """API key A cannot access API key B's session (returns 404)."""
    session_id = mock_session_other_tenant

    # Tenant A tries to access Tenant B's session
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers,  # Tenant A
    )

    # Returns 404 (not 403) to prevent enumeration
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"
```

### Key Conventions

- **Docstrings:** Every test has clear one-line description
- **Explicit assertions:** Check specific fields, not just `assert data`
- **Domain errors:** Validate `error.code` field, not just status codes
- **Isolation via 404:** Cross-tenant access returns 404 (not 403)
- **AAA separation:** Blank lines between Arrange/Act/Assert

## Implementation Order & Execution Strategy

### Build Incrementally

**Phase 2.1: Foundation (Week 1)**
1. Create directory: `tests/integration/semantics/`
2. Create `conftest.py` with fixtures
3. Implement `test_isolation_semantics.py` (6 tests)

**Phase 2.2: Projects (Week 1-2)**
4. Implement `test_projects_semantics.py` (15-20 tests)

**Phase 2.3: Memories (Week 2-3)**
5. Implement `test_memories_semantics.py` (20-25 tests)

**Phase 2.4: Sessions (Week 3-4)**
6. Implement `test_sessions_semantics.py` (20-25 tests)

### TDD Workflow

```bash
# For each test:
1. Write failing test (RED)
2. Run: pytest tests/integration/semantics/test_projects_semantics.py::test_name -v
3. Verify test fails with expected error
4. Fix implementation (if needed) or verify route works (GREEN)
5. Refactor test assertions
6. Move to next test
```

### Continuous Validation

```bash
# After each file complete:
make test-fast                              # All tests
pytest tests/integration/semantics/ -v      # Phase 2 only
pytest --cov=apps/api --cov-report=term     # Coverage check
```

### Checkpoint Strategy

- Commit after each complete test file
- Tag completion: `git tag phase-2-{resource}-complete`
- Push frequently to avoid losing work

## Success Criteria

**Phase 2 is complete when:**

### Test Coverage
- [ ] 65-70 tests implemented across 4 files
- [ ] All tests passing in CI
- [ ] No regressions in Phase 1 tests (8 tests still passing)
- [ ] Zero skipped/xfail tests

### Resource Coverage
- [ ] Sessions: 20-25 tests
- [ ] Projects: 15-20 tests
- [ ] Memories: 20-25 tests
- [ ] Isolation: 6 tests

### Quality Metrics
- [ ] All tests follow AAA pattern
- [ ] Every test has clear docstring
- [ ] All error responses validate `error.code` field
- [ ] All SSE tests validate event sequences
- [ ] All multi-tenancy tests return 404

### Documentation
- [ ] README updated with Phase 2 test count
- [ ] CLAUDE.md updated (if needed)
- [ ] Commit messages: `test(semantics): add {resource} exhaustive tests`

### CI/CD Validation

```bash
make test-fast                                    # Fast tests pass
pytest tests/integration/semantics/ -v            # All Phase 2 pass
pytest tests/integration/semantics/ -n auto -v    # Parallel execution works
uv run ruff check tests/integration/semantics/    # Linting passes
uv run ty check tests/integration/semantics/      # Type checking passes
```

### Final Checklist

```bash
1. pytest tests/integration/semantics/ -v --tb=short
   → All tests GREEN

2. pytest tests/integration/ -v
   → Phase 1 tests still GREEN

3. grep -r "xfail\|skip" tests/integration/semantics/
   → No output

4. wc -l tests/integration/semantics/*.py
   → ~1700 total lines

5. pytest tests/integration/semantics/ --cov=apps/api/routes --cov-report=term
   → Route coverage increases
```

## Definition of Done

- All checkboxes above are checked
- Code reviewed and approved
- Merged to `main` branch
- Tagged: `git tag phase-2-semantic-tests-complete`
