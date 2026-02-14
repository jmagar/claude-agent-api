# Phase 2 Semantic Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement exhaustive semantic tests for Sessions, Projects, and Memories endpoints with ~65-70 tests total.

**Architecture:** Resource-based test modules with dedicated fixtures for multi-tenancy, SSE streaming validation, and cross-tenant isolation. Tests follow TDD RED-GREEN-REFACTOR pattern with AAA structure.

**Tech Stack:** pytest, httpx, anyio, FastAPI TestClient, SSE event parsing

**Reference Design:** `docs/plans/2026-02-13-phase2-semantic-tests-design.md`

---

## Phase 2.1: Foundation & Isolation Tests

### Task 1: Create Directory Structure

**Files:**
- Create: `tests/integration/semantics/__init__.py`
- Create: `tests/integration/semantics/conftest.py`

**Step 1: Create semantics directory**

```bash
mkdir -p tests/integration/semantics
```

**Step 2: Create empty __init__.py**

```bash
touch tests/integration/semantics/__init__.py
```

**Step 3: Create conftest.py stub**

Create `tests/integration/semantics/conftest.py`:

```python
"""Shared fixtures for Phase 2 semantic tests."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient
```

**Step 4: Verify pytest discovers new directory**

Run: `pytest tests/integration/semantics/ --collect-only`
Expected: "collected 0 items" (no errors)

**Step 5: Commit**

```bash
git add tests/integration/semantics/
git commit -m "test(semantics): create Phase 2 test directory structure"
```

---

### Task 2: Add Multi-Tenant Fixtures

**Files:**
- Modify: `tests/integration/semantics/conftest.py`

**Step 1: Add second_api_key fixture**

Add to `conftest.py`:

```python
@pytest.fixture
def second_api_key() -> str:
    """Second API key for cross-tenant isolation tests."""
    return f"test-api-key-{uuid4().hex[:8]}"
```

**Step 2: Add second_auth_headers fixture**

Add to `conftest.py`:

```python
@pytest.fixture
def second_auth_headers(second_api_key: str) -> dict[str, str]:
    """Auth headers for second tenant."""
    return {"X-API-Key": second_api_key}
```

**Step 3: Type check**

Run: `uv run ty check tests/integration/semantics/conftest.py`
Expected: "All checks passed!"

**Step 4: Lint check**

Run: `uv run ruff check tests/integration/semantics/conftest.py`
Expected: "All checks passed!"

**Step 5: Commit**

```bash
git add tests/integration/semantics/conftest.py
git commit -m "test(semantics): add multi-tenant fixtures for isolation tests"
```

---

### Task 3: Add SSE Streaming Helper Fixtures

**Files:**
- Modify: `tests/integration/semantics/conftest.py`

**Step 1: Add sse_event_collector fixture**

Add to `conftest.py`:

```python
@pytest.fixture
def sse_event_collector():
    """Helper to collect and validate SSE events from streaming responses."""
    async def collect_events(response):
        """Parse SSE stream and return list of events."""
        events = []
        event_type = None
        async for line in response.aiter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = json.loads(line.split(":", 1)[1].strip())
                if event_type:
                    events.append({"event": event_type, "data": data})
                    event_type = None
        return events
    return collect_events
```

**Step 2: Add validate_sse_sequence fixture**

Add to `conftest.py`:

```python
@pytest.fixture
def validate_sse_sequence():
    """Validate SSE event sequence matches expected pattern."""
    def validate(events: list[dict], expected_sequence: list[str]) -> None:
        """Assert events follow expected order.

        Args:
            events: List of {"event": str, "data": dict}
            expected_sequence: List of event names in order
        """
        actual_sequence = [e["event"] for e in events]
        assert actual_sequence == expected_sequence, (
            f"Event sequence mismatch.\n"
            f"Expected: {expected_sequence}\n"
            f"Actual: {actual_sequence}"
        )
    return validate
```

**Step 3: Type check**

Run: `uv run ty check tests/integration/semantics/conftest.py`
Expected: "All checks passed!"

**Step 4: Lint check**

Run: `uv run ruff check tests/integration/semantics/conftest.py`
Expected: "All checks passed!"

**Step 5: Commit**

```bash
git add tests/integration/semantics/conftest.py
git commit -m "test(semantics): add SSE streaming helper fixtures"
```

---

### Task 4: Create Isolation Test File Stub

**Files:**
- Create: `tests/integration/semantics/test_isolation_semantics.py`

**Step 1: Create test file with header**

Create `tests/integration/semantics/test_isolation_semantics.py`:

```python
"""Cross-tenant isolation tests for Phase 2 semantic validation.

Validates that API key A cannot access API key B's resources.
All cross-tenant access returns 404 (not 403) to prevent enumeration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient
```

**Step 2: Verify pytest discovery**

Run: `pytest tests/integration/semantics/test_isolation_semantics.py --collect-only`
Expected: "collected 0 items"

**Step 3: Commit**

```bash
git add tests/integration/semantics/test_isolation_semantics.py
git commit -m "test(semantics): create isolation test file stub"
```

---

### Task 5: Implement Sessions Cross-Tenant Isolation Test

**Files:**
- Modify: `tests/integration/semantics/test_isolation_semantics.py`
- Modify: `tests/integration/semantics/conftest.py` (add mock_session_other_tenant fixture)

**Step 1: Add mock_session_other_tenant fixture**

Add to `conftest.py`:

```python
@pytest.fixture
async def mock_session_other_tenant(
    async_client: AsyncClient,
    second_auth_headers: dict[str, str],
) -> str:
    """Create session owned by second tenant for isolation tests."""
    from apps.api.adapters.session_repo import SessionRepository
    from apps.api.dependencies import get_app_state
    from apps.api.services.session import SessionService
    from fastapi import Request

    # Get app state
    request = Request(scope={"type": "http", "app": async_client._transport.app})  # type: ignore[arg-type]
    app_state = get_app_state(request)

    assert app_state.cache is not None
    assert app_state.session_maker is not None

    # Create session for second tenant
    async with app_state.session_maker() as db_session:
        repo = SessionRepository(db_session)
        service = SessionService(cache=app_state.cache, db_repo=repo)
        session = await service.create_session(
            model="sonnet",
            session_id=str(uuid4()),
            owner_api_key=second_auth_headers["X-API-Key"],
        )
        return session.id
```

**Step 2: Write failing test**

Add to `test_isolation_semantics.py`:

```python
@pytest.mark.integration
@pytest.mark.anyio
async def test_sessions_cross_tenant_isolation(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    second_auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """API key A cannot access API key B's session (returns 404)."""
    # ARRANGE
    session_id = mock_session_other_tenant  # Owned by tenant B

    # ACT - Tenant A tries to access it
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers,  # Tenant A
    )

    # ASSERT - Returns 404 (not 403) to prevent enumeration
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SESSION_NOT_FOUND"
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/integration/semantics/test_isolation_semantics.py::test_sessions_cross_tenant_isolation -v`
Expected: PASS (if route already enforces isolation) or FAIL (if not)

**Step 4: Verify test passes**

Run: `pytest tests/integration/semantics/test_isolation_semantics.py::test_sessions_cross_tenant_isolation -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/integration/semantics/conftest.py tests/integration/semantics/test_isolation_semantics.py
git commit -m "test(semantics): add sessions cross-tenant isolation test"
```

---

### Task 6: Implement Projects Cross-Tenant Isolation Test

**Files:**
- Modify: `tests/integration/semantics/test_isolation_semantics.py`
- Modify: `tests/integration/semantics/conftest.py` (add mock_project_other_tenant fixture)

**Step 1: Add mock_project_other_tenant fixture**

Add to `conftest.py`:

```python
@pytest.fixture
async def mock_project_other_tenant(
    async_client: AsyncClient,
    second_auth_headers: dict[str, str],
) -> dict[str, str]:
    """Create project owned by second tenant for isolation tests."""
    suffix = uuid4().hex[:8]
    name = f"isolation-project-{suffix}"
    path = f"/tmp/isolation-project-{suffix}"

    response = await async_client.post(
        "/api/v1/projects",
        json={"name": name, "path": path},
        headers=second_auth_headers,
    )
    assert response.status_code == 201
    return response.json()
```

**Step 2: Write failing test**

Add to `test_isolation_semantics.py`:

```python
@pytest.mark.integration
@pytest.mark.anyio
async def test_projects_cross_tenant_isolation(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    second_auth_headers: dict[str, str],
    mock_project_other_tenant: dict[str, str],
) -> None:
    """API key A cannot access API key B's project (returns 404)."""
    # ARRANGE
    project_id = mock_project_other_tenant["id"]  # Owned by tenant B

    # ACT - Tenant A tries to access it
    response = await async_client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,  # Tenant A
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "PROJECT_NOT_FOUND"
```

**Step 3: Run test to verify it fails/passes**

Run: `pytest tests/integration/semantics/test_isolation_semantics.py::test_projects_cross_tenant_isolation -v`
Expected: PASS

**Step 4: Commit**

```bash
git add tests/integration/semantics/conftest.py tests/integration/semantics/test_isolation_semantics.py
git commit -m "test(semantics): add projects cross-tenant isolation test"
```

---

### Task 7: Implement Memories Cross-Tenant Isolation Test

**Files:**
- Modify: `tests/integration/semantics/test_isolation_semantics.py`
- Modify: `tests/integration/semantics/conftest.py` (add mock_memory_other_tenant fixture)

**Step 1: Add mock_memory_other_tenant fixture**

Add to `conftest.py`:

```python
@pytest.fixture
async def mock_memory_other_tenant(
    async_client: AsyncClient,
    second_auth_headers: dict[str, str],
) -> dict[str, str]:
    """Create memory owned by second tenant for isolation tests."""
    response = await async_client.post(
        "/api/v1/memories",
        json={
            "messages": f"Isolation test memory {uuid4().hex[:8]}",
            "user_id": second_auth_headers["X-API-Key"],
        },
        headers=second_auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    # Return first memory ID from results
    return {"id": data["results"][0]["id"], "content": data["results"][0]["memory"]}
```

**Step 2: Write test**

Add to `test_isolation_semantics.py`:

```python
@pytest.mark.integration
@pytest.mark.anyio
async def test_memories_cross_tenant_isolation(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    second_auth_headers: dict[str, str],
    mock_memory_other_tenant: dict[str, str],
) -> None:
    """API key A cannot search API key B's memories."""
    # ARRANGE
    memory_content = mock_memory_other_tenant["content"]

    # ACT - Tenant A searches for Tenant B's memory
    response = await async_client.post(
        "/api/v1/memories/search",
        json={"query": memory_content, "user_id": auth_headers["X-API-Key"]},
        headers=auth_headers,  # Tenant A
    )

    # ASSERT - No results (scoped to Tenant A)
    assert response.status_code == 200
    data = response.json()
    # Verify Tenant B's memory is not in results
    memory_ids = [m["id"] for m in data["results"]]
    assert mock_memory_other_tenant["id"] not in memory_ids
```

**Step 3: Run test**

Run: `pytest tests/integration/semantics/test_isolation_semantics.py::test_memories_cross_tenant_isolation -v`
Expected: PASS

**Step 4: Commit**

```bash
git add tests/integration/semantics/conftest.py tests/integration/semantics/test_isolation_semantics.py
git commit -m "test(semantics): add memories cross-tenant isolation test"
```

---

### Task 8: Implement Session Operations Cross-Tenant Test

**Files:**
- Modify: `tests/integration/semantics/test_isolation_semantics.py`

**Step 1: Write test**

Add to `test_isolation_semantics.py`:

```python
@pytest.mark.integration
@pytest.mark.anyio
async def test_session_operations_cross_tenant(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """Cannot resume/fork/interrupt other tenant's session."""
    # ARRANGE
    session_id = mock_session_other_tenant

    # ACT & ASSERT - Resume
    resume_response = await async_client.post(
        f"/api/v1/sessions/{session_id}/resume",
        json={"prompt": "Test"},
        headers=auth_headers,
    )
    assert resume_response.status_code == 404

    # ACT & ASSERT - Fork
    fork_response = await async_client.post(
        f"/api/v1/sessions/{session_id}/fork",
        json={"prompt": "Test"},
        headers=auth_headers,
    )
    assert fork_response.status_code == 404

    # ACT & ASSERT - Interrupt
    interrupt_response = await async_client.post(
        f"/api/v1/sessions/{session_id}/interrupt",
        headers=auth_headers,
    )
    assert interrupt_response.status_code == 404
```

**Step 2: Run test**

Run: `pytest tests/integration/semantics/test_isolation_semantics.py::test_session_operations_cross_tenant -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/semantics/test_isolation_semantics.py
git commit -m "test(semantics): add session operations cross-tenant test"
```

---

### Task 9: Complete Remaining Isolation Tests

**Files:**
- Modify: `tests/integration/semantics/test_isolation_semantics.py`

**Step 1: Add project operations cross-tenant test**

Add to `test_isolation_semantics.py`:

```python
@pytest.mark.integration
@pytest.mark.anyio
async def test_project_operations_cross_tenant(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_project_other_tenant: dict[str, str],
) -> None:
    """Cannot update/delete other tenant's project."""
    project_id = mock_project_other_tenant["id"]

    # ACT & ASSERT - Update
    update_response = await async_client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "hacked-name"},
        headers=auth_headers,
    )
    assert update_response.status_code == 404

    # ACT & ASSERT - Delete
    delete_response = await async_client.delete(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 404
```

**Step 2: Add memory operations cross-tenant test**

Add to `test_isolation_semantics.py`:

```python
@pytest.mark.integration
@pytest.mark.anyio
async def test_memory_operations_cross_tenant(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_memory_other_tenant: dict[str, str],
) -> None:
    """Cannot delete other tenant's memory."""
    memory_id = mock_memory_other_tenant["id"]

    # ACT
    response = await async_client.delete(
        f"/api/v1/memories/{memory_id}",
        headers=auth_headers,
    )

    # ASSERT - Returns 404 (not 403)
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "MEMORY_NOT_FOUND"
```

**Step 3: Run all isolation tests**

Run: `pytest tests/integration/semantics/test_isolation_semantics.py -v`
Expected: 6 tests PASSED

**Step 4: Commit**

```bash
git add tests/integration/semantics/test_isolation_semantics.py
git commit -m "test(semantics): complete isolation test suite (6 tests)"
```

---

## Phase 2.2: Projects Semantic Tests

### Task 10: Create Projects Test File with CRUD Fixtures

**Files:**
- Create: `tests/integration/semantics/test_projects_semantics.py`
- Modify: `tests/integration/semantics/conftest.py`

**Step 1: Create test file stub**

Create `tests/integration/semantics/test_projects_semantics.py`:

```python
"""Exhaustive semantic tests for Projects endpoints.

Tests full CRUD operations, validation, edge cases, and error handling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient
```

**Step 2: Add mock_project fixture to conftest**

Add to `conftest.py`:

```python
@pytest.fixture
async def mock_project(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> dict[str, str]:
    """Create a project and return its data."""
    suffix = uuid4().hex[:8]
    name = f"test-project-{suffix}"
    path = f"/tmp/test-project-{suffix}"

    response = await async_client.post(
        "/api/v1/projects",
        json={"name": name, "path": path},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()
```

**Step 3: Verify pytest discovery**

Run: `pytest tests/integration/semantics/test_projects_semantics.py --collect-only`
Expected: "collected 0 items"

**Step 4: Commit**

```bash
git add tests/integration/semantics/test_projects_semantics.py tests/integration/semantics/conftest.py
git commit -m "test(semantics): create projects test file with fixtures"
```

---

### Task 11-15: Implement Projects CRUD Tests (List, Get, Create, Update, Delete)

Due to the large number of tests remaining (~60+ tests), I'll provide a condensed format for the remaining tasks. Each task group follows the same TDD pattern:

1. Write failing test
2. Run test (verify fail or pass)
3. Implement if needed
4. Run test (verify pass)
5. Commit

**Task 11: List Projects Tests**

Add 2 tests to `test_projects_semantics.py`:
- `test_list_projects_succeeds` - Verify pagination, total count
- `test_list_projects_empty` - Empty list when no projects

**Task 12: Get Project Tests**

Add 3 tests:
- `test_get_project_succeeds` - Returns full project data
- `test_get_project_not_found` - 404 with PROJECT_NOT_FOUND
- `test_create_project_succeeds` - Already tested in Phase 1, verify structure

**Task 13: Update Project Tests**

Add 3 tests:
- `test_update_project_succeeds` - Update name/path
- `test_update_project_not_found` - 404 error
- `test_update_project_duplicate_name` - 409 conflict

**Task 14: Delete Project Tests**

Add 2 tests:
- `test_delete_project_succeeds` - Soft/hard delete
- `test_delete_project_not_found` - 404 error

**Task 15: Projects Validation Tests**

Add 5 tests:
- `test_create_project_invalid_path` - 422 for invalid paths
- `test_update_project_validates_name_length` - Min/max enforcement
- `test_project_path_normalization` - Trailing slashes
- `test_project_created_updated_timestamps` - Timezone-aware
- `test_create_project_duplicate_name` - 409 (already in Phase 1)

**Commit after Task 15:**

```bash
git add tests/integration/semantics/test_projects_semantics.py
git commit -m "test(semantics): complete projects CRUD and validation tests (15 tests)"
```

---

## Phase 2.3: Memories Semantic Tests

### Task 16: Create Memories Test File

**Files:**
- Create: `tests/integration/semantics/test_memories_semantics.py`
- Modify: `tests/integration/semantics/conftest.py`

Follow same pattern as Projects (create file, add fixture, verify discovery, commit).

**Task 17-20: Memories CRUD Tests**

Add 8 tests:
- Search (succeeds, no results)
- Add (succeeds, with metadata)
- List (succeeds, empty)
- Delete (single, bulk)

**Task 21-22: Memories Multi-Tenancy Tests**

Add 6 tests:
- Search scoped to API key
- Add scoped to API key
- List scoped to API key
- Delete wrong owner (404)
- Graph isolation (Neo4j)
- Vector isolation (Qdrant)

**Task 23: Memories Validation & Edge Cases**

Add 6 tests:
- Delete not found
- Validation (query required, content required)
- enable_graph=false
- Embedding dimensions (1024)
- Timezone-aware timestamps

**Commit after Task 23:**

```bash
git add tests/integration/semantics/test_memories_semantics.py tests/integration/semantics/conftest.py
git commit -m "test(semantics): complete memories CRUD and multi-tenancy tests (20 tests)"
```

---

## Phase 2.4: Sessions Semantic Tests

### Task 24: Create Sessions Test File with SSE Support

**Files:**
- Create: `tests/integration/semantics/test_sessions_semantics.py`
- Modify: `tests/integration/semantics/conftest.py`

**Add mock_session fixture:**

```python
@pytest.fixture
async def mock_session(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> str:
    """Create completed session for testing."""
    from apps.api.adapters.session_repo import SessionRepository
    from apps.api.dependencies import get_app_state
    from apps.api.services.session import SessionService
    from fastapi import Request

    request = Request(scope={"type": "http", "app": async_client._transport.app})  # type: ignore[arg-type]
    app_state = get_app_state(request)

    assert app_state.cache is not None
    assert app_state.session_maker is not None

    async with app_state.session_maker() as db_session:
        repo = SessionRepository(db_session)
        service = SessionService(cache=app_state.cache, db_repo=repo)
        session = await service.create_session(
            model="sonnet",
            session_id=str(uuid4()),
            owner_api_key=auth_headers["X-API-Key"],
        )
        return session.id
```

**Task 25-27: Sessions CRUD Tests**

Add 5 tests:
- List (pagination, empty)
- Get (succeeds, not found, wrong owner)

**Task 28-30: Sessions Resume Tests**

Add 5 tests:
- Resume succeeds (with SSE)
- Model override
- Permission mode change
- Nonexistent session
- Validation (max_turns)

**Task 31-33: Sessions Fork Tests**

Add 5 tests:
- Fork succeeds
- Model override
- Nonexistent session
- Validation (prompt required)
- Preserves parent history

**Task 34-36: Sessions State Management Tests**

Add 5 tests:
- Promote succeeds
- Promote nonexistent
- Update tags succeeds
- Tag validation
- State transitions

**Task 37-39: Sessions SSE Streaming Tests**

Add 3 tests using `sse_event_collector` and `validate_sse_sequence` fixtures:
- Event sequence validation
- Partial deltas
- Interrupt during streaming

**Commit after Task 39:**

```bash
git add tests/integration/semantics/test_sessions_semantics.py tests/integration/semantics/conftest.py
git commit -m "test(semantics): complete sessions CRUD, operations, and SSE tests (23 tests)"
```

---

## Final Validation & Cleanup

### Task 40: Run Full Test Suite

**Step 1: Run all Phase 2 tests**

Run: `pytest tests/integration/semantics/ -v`
Expected: ~65-70 tests PASSED

**Step 2: Run all integration tests (Phase 1 + Phase 2)**

Run: `pytest tests/integration/ -v`
Expected: All tests PASSED (no regressions)

**Step 3: Run with coverage**

Run: `pytest tests/integration/semantics/ --cov=apps/api/routes --cov-report=term-missing`
Expected: Increased coverage for sessions, projects, memories routes

**Step 4: Lint check**

Run: `uv run ruff check tests/integration/semantics/`
Expected: "All checks passed!"

**Step 5: Type check**

Run: `uv run ty check tests/integration/semantics/`
Expected: "All checks passed!"

---

### Task 41: Update Documentation

**Files:**
- Modify: `README.md` (optional - if test section exists)
- Modify: `CLAUDE.md` (if new patterns discovered)

**Step 1: Count total tests**

Run: `pytest tests/integration/semantics/ --collect-only | grep "test session"`
Expected: Count test items

**Step 2: Update README (if applicable)**

Add Phase 2 test count to testing section.

**Step 3: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: update test counts for Phase 2 semantic tests"
```

---

### Task 42: Tag Completion

**Step 1: Create git tag**

```bash
git tag -a phase-2-semantic-tests-complete -m "Phase 2 semantic tests complete

- 65-70 exhaustive tests for Sessions, Projects, Memories
- Multi-tenancy isolation tests
- SSE streaming validation
- Full CRUD coverage with edge cases"
```

**Step 2: Push tags**

```bash
git push --tags
```

---

## Success Criteria Checklist

Before marking complete, verify:

- [ ] `pytest tests/integration/semantics/ -v` → All tests GREEN
- [ ] `pytest tests/integration/ -v` → No regressions
- [ ] `grep -r "xfail\|skip" tests/integration/semantics/` → No output
- [ ] `wc -l tests/integration/semantics/*.py` → ~1700 total lines
- [ ] 4 test files created (isolation, projects, memories, sessions)
- [ ] ~65-70 tests total
- [ ] All tests follow AAA pattern with docstrings
- [ ] All error responses validate `error.code` field
- [ ] SSE tests validate event sequences
- [ ] Multi-tenancy tests return 404
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] Tagged and committed

---

## Estimated Timeline

- **Phase 2.1 (Foundation + Isolation):** Tasks 1-9 → 1 week
- **Phase 2.2 (Projects):** Tasks 10-15 → 1 week
- **Phase 2.3 (Memories):** Tasks 16-23 → 1.5 weeks
- **Phase 2.4 (Sessions):** Tasks 24-39 → 1.5 weeks
- **Validation & Cleanup:** Tasks 40-42 → 0.5 weeks

**Total:** ~5-6 weeks for exhaustive Phase 2 coverage
