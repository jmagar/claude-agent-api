# PERF-001 N+1 Query Pattern in Session Listing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **Organization Note:** When this plan is fully implemented and verified, move this file to `docs/plans/complete/` to keep the plans folder organized.

**Goal:** Replace per-session cache lookups in session listing with a single bulk cache fetch to remove N+1 latency.

**Architecture:** Extend the Cache protocol with `get_many_json`, implement it in `RedisCache` using `mget`, then update `SessionService.list_sessions` to fetch and parse all sessions in one roundtrip. Add unit tests for the cache adapter and the session service call path.

**Tech Stack:** Python 3.11, redis.asyncio, pytest.

---

### Task 1: Add bulk cache read API (tests first)

**Files:**
- Modify: `apps/api/protocols.py`
- Modify: `apps/api/adapters/cache.py`
- Modify: `tests/unit/adapters/test_cache.py`

**Step 1: Write the failing test**

Add a unit test to a new test class in `tests/unit/adapters/test_cache.py` asserting that `RedisCache.get_many_json` calls `mget` once and parses JSON safely:

```python
# Add to tests/unit/adapters/test_cache.py after TestCacheBasicOperations

class TestCacheBulkOperations:
    """Tests for bulk cache operations (get_many_json)."""

    @pytest.mark.anyio
    async def test_get_many_json_uses_mget_and_parses() -> None:
        """Test that get_many_json uses mget and parses JSON values safely."""
        mock_client = AsyncMock()
        mock_client.mget.return_value = [
            b"{\"id\": \"s1\"}",
            None,
            b"{\"id\": \"s2\"}",
        ]

        cache = RedisCache(mock_client)

        result = await cache.get_many_json(["session:s1", "session:missing", "session:s2"])

        mock_client.mget.assert_called_once_with(
            "session:s1",
            "session:missing",
            "session:s2",
        )
        assert result == [
            {"id": "s1"},
            None,
            {"id": "s2"},
        ]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/adapters/test_cache.py::TestCacheBulkOperations::test_get_many_json_uses_mget_and_parses -v`

Expected: FAIL (method does not exist).

**Step 3: Write minimal implementation**

Add method to the `Cache` protocol and implement in `RedisCache` (note: `json` module is already imported at line 5 of cache.py):

```python
# apps/api/protocols.py (add after get_json method around line 296)
async def get_many_json(self, keys: list[str]) -> list[dict[str, object] | None]:
    """Get multiple JSON values from cache.

    Args:
        keys: List of cache keys.

    Returns:
        List of parsed JSON dicts (None for missing/invalid keys).
    """
    ...

# apps/api/adapters/cache.py (add after get_json method around line 157)
async def get_many_json(self, keys: list[str]) -> list[dict[str, object] | None]:
    """Get multiple JSON values from cache using Redis mget.

    Args:
        keys: List of cache keys to fetch.

    Returns:
        List of parsed JSON dicts in same order as keys.
        None for missing keys or JSON decode errors.
    """
    if not keys:
        return []

    values = await self._client.mget(*keys)
    results: list[dict[str, object] | None] = []

    for raw in values:
        if raw is None:
            results.append(None)
            continue
        try:
            decoded = raw.decode("utf-8")
            results.append(json.loads(decoded))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            results.append(None)

    return results
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/adapters/test_cache.py::TestCacheBulkOperations::test_get_many_json_uses_mget_and_parses -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add apps/api/protocols.py apps/api/adapters/cache.py tests/unit/adapters/test_cache.py
git commit -m "feat(cache): add bulk JSON fetch API"
```

### Task 2: Use bulk cache reads in session listing (tests first)

**Files:**
- Modify: `apps/api/services/session.py`
- Modify: `tests/unit/test_session_service.py`

**Step 1: Write the failing test**

Extend the existing `MockCache` class (in `tests/unit/test_session_service.py` starting at line 9) to add bulk read tracking:

```python
# Modify existing MockCache class in tests/unit/test_session_service.py

class MockCache:
    """Mock cache that stores data in memory.

    Implements the Cache protocol for testing purposes.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, object]] = {}
        self.get_many_calls = 0  # ← ADD THIS LINE

    # ... existing methods ...

    async def get_many_json(self, keys: list[str]) -> list[dict[str, object] | None]:
        """Get multiple JSON values (tracks call count)."""
        self.get_many_calls += 1
        return [self._store.get(key) for key in keys]
```

Then add a new test to the `TestSessionServiceEdgeCases` class (add after line 545):

```python
# Add to TestSessionServiceEdgeCases class in tests/unit/test_session_service.py

@pytest.mark.anyio
async def test_list_sessions_uses_bulk_cache_reads(
    session_service: SessionService,
    mock_cache: MockCache,
) -> None:
    """Test that list_sessions uses bulk cache read instead of N individual reads."""
    # Create 3 sessions
    for i in range(3):
        await session_service.create_session(
            model="sonnet",
            session_id=f"session-{i}",
        )

    # Reset counter after creation
    mock_cache.get_many_calls = 0

    # List sessions
    result = await session_service.list_sessions(page=1, page_size=10)

    # Should make exactly 1 bulk cache call (not 3 individual calls)
    assert result.total == 3
    assert mock_cache.get_many_calls == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_session_service.py::TestSessionServiceEdgeCases::test_list_sessions_uses_bulk_cache_reads -v`

Expected: FAIL (`get_many_json` not called).

**Step 3: Write minimal implementation**

Refactor `list_sessions` to use bulk fetch (replace method starting at line 353):

```python
# apps/api/services/session.py (replace list_sessions method around line 353)
async def list_sessions(
    self,
    page: int = 1,
    page_size: int = 20,
) -> SessionListResult:
    """List sessions with pagination using bulk cache reads.

    Args:
        page: Page number (1-indexed).
        page_size: Number of sessions per page.

    Returns:
        Paginated session list.
    """
    sessions: list[Session] = []

    if self._cache:
        pattern = "session:*"
        all_keys = await self._cache.scan_keys(pattern)

        # Bulk fetch all session data in one Redis roundtrip
        cached_rows = await self._cache.get_many_json(all_keys)

        # Parse each cached session
        for key, parsed in zip(all_keys, cached_rows, strict=True):
            if not parsed:
                continue
            session = self._parse_cached_session(parsed)
            if session:
                sessions.append(session)

    # Sort by created_at descending
    sessions.sort(key=lambda s: s.created_at, reverse=True)

    # Calculate pagination
    total = len(sessions)
    start = (page - 1) * page_size
    end = start + page_size
    page_sessions = sessions[start:end]

    return SessionListResult(
        sessions=page_sessions,
        total=total,
        page=page,
        page_size=page_size,
    )
```

Extract parsing logic into reusable helper (add new method after `_get_cached_session` around line 612):

```python
# apps/api/services/session.py (add new helper method)
def _parse_cached_session(
    self,
    parsed: dict[str, object],
) -> Session | None:
    """Parse cached session data into Session object.

    Args:
        parsed: Parsed JSON dict from cache.

    Returns:
        Session object or None if parsing fails.

    Note:
        This extracts the parsing logic from _get_cached_session
        for reuse in list_sessions bulk operations.
    """
    try:
        # Extract values with proper type casting
        session_id_val = str(parsed["id"])
        model_val = str(parsed["model"])
        status_raw = str(parsed["status"])
        created_at_val = str(parsed["created_at"])
        updated_at_val = str(parsed["updated_at"])

        # Validate status is one of the allowed values
        status_val: Literal["active", "completed", "error"]
        if status_raw == "active":
            status_val = "active"
        elif status_raw == "completed":
            status_val = "completed"
        elif status_raw == "error":
            status_val = "error"
        else:
            status_val = "active"  # Default to active for invalid values

        # Get optional values with proper type handling
        total_turns_raw = parsed.get("total_turns", 0)
        if isinstance(total_turns_raw, int):
            total_turns_val = total_turns_raw
        elif isinstance(total_turns_raw, (str, float)):
            total_turns_val = int(total_turns_raw)
        else:
            total_turns_val = 0

        total_cost_raw = parsed.get("total_cost_usd")
        if total_cost_raw is None:
            total_cost_val = None
        elif isinstance(total_cost_raw, (int, float, str)):
            total_cost_val = float(total_cost_raw)
        else:
            total_cost_val = None

        parent_id_raw = parsed.get("parent_session_id")
        parent_id_val = str(parent_id_raw) if parent_id_raw is not None else None
        owner_raw = parsed.get("owner_api_key")
        owner_val = str(owner_raw) if owner_raw is not None else None

        # Parse datetimes and normalize to naive (remove timezone info)
        created_dt = datetime.fromisoformat(created_at_val)
        updated_dt = datetime.fromisoformat(updated_at_val)

        # Convert to naive if timezone-aware
        if created_dt.tzinfo is not None:
            created_dt = created_dt.replace(tzinfo=None)
        if updated_dt.tzinfo is not None:
            updated_dt = updated_dt.replace(tzinfo=None)

        return Session(
            id=session_id_val,
            model=model_val,
            status=status_val,
            created_at=created_dt,
            updated_at=updated_dt,
            total_turns=total_turns_val,
            total_cost_usd=total_cost_val,
            parent_session_id=parent_id_val,
            owner_api_key=owner_val,
        )
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(
            "Failed to parse cached session",
            error=str(e),
        )
        return None
```

Then refactor `_get_cached_session` to use the helper (update method around line 525):

```python
# apps/api/services/session.py (simplify _get_cached_session to use helper)
async def _get_cached_session(self, session_id: str) -> Session | None:
    """Get a session from cache.

    Args:
        session_id: Session ID to retrieve.

    Returns:
        Session if found in cache.
    """
    if not self._cache:
        return None

    key = self._cache_key(session_id)
    parsed = await self._cache.get_json(key)

    if not parsed:
        return None

    return self._parse_cached_session(parsed)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_session_service.py::TestSessionServiceEdgeCases::test_list_sessions_uses_bulk_cache_reads -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add apps/api/services/session.py tests/unit/test_session_service.py
git commit -m "perf(session): avoid N+1 cache reads in list_sessions"
```

### Task 3: Update performance audit docs

**Files:**
- Modify: `.docs/audit-summary.md`
- Modify: `.docs/quick-wins-checklist.md`

**Step 1: Write the failing test**

Add a short note under PERF-001 to mark the fix and the new bulk cache approach.

**Step 2: Run test to verify it fails**

Run: `rg -n "PERF-001.*Fixed" .docs/audit-summary.md .docs/quick-wins-checklist.md`

Expected: FAIL to find "Fixed" status for PERF-001.

**Step 3: Write minimal documentation update**

Update both audit docs to mark PERF-001 as fixed:

In `.docs/audit-summary.md` (around line 130-137), update the N+1 section:

```markdown
### 4. N+1 Query Performance 🐌
**Status**: ✅ FIXED
**Impact**: Performance degrades with session count
**Effort**: 1 hour
**Priority**: HIGH

**Fix**: Session listing now uses Redis `mget` via `get_many_json` to fetch all sessions in one roundtrip instead of N individual cache reads.
```

In `.docs/quick-wins-checklist.md` (around line 88-108), update the index section:

```markdown
### 4. Add Database Index (1 hour)
**Status**: N/A (PERF-001 fixed via Redis bulk fetch instead)
**Impact**: HIGH - N+1 cache reads eliminated

**Note**: Session listing performance issue was resolved by implementing bulk cache reads using Redis `mget` command. Database index not needed for this specific issue.
```

**Step 4: Run test to verify it passes**

Run: `rg -n "PERF-001.*Fixed|mget.*bulk" .docs/audit-summary.md .docs/quick-wins-checklist.md`

Expected: Match found in both files.

**Step 5: Commit**

```bash
git add .docs/audit-summary.md .docs/quick-wins-checklist.md
git commit -m "docs: mark PERF-001 session listing fix"
```

---

**Notes:** Follow @test-driven-development and @verification-before-completion for each task.
