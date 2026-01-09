# PERF-002 Missing Redis Connection Pool Configuration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **Organization Note:** When this plan is fully implemented and verified, move this file to `docs/plans/complete/` to keep the plans folder organized.

**Goal:** Make Redis connection pool sizing and timeouts configurable to prevent exhaustion and improve reliability under load.

**Architecture:** Add Redis pool settings to `Settings`, plumb them through `RedisCache.create`, update `.env.example`, and adjust cache adapter tests to assert proper configuration usage.

**Tech Stack:** Python 3.11, redis.asyncio, pydantic-settings, pytest.

---

### Task 1: Add Redis pool settings to configuration (tests first)

**Files:**
- Modify: `apps/api/config.py`
- Modify: `tests/unit/test_config.py`

**Step 1: Write the failing test**

Extend default settings tests to cover new Redis pool configuration:

```python
with patch.dict(
    os.environ,
    {
        "API_KEY": "test-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "CORS_ORIGINS": '["http://localhost:3000"]',
    },
    clear=True,
):
    settings = Settings(_env_file=None)

    assert settings.redis_max_connections == 50
    assert settings.redis_socket_connect_timeout == 5
    assert settings.redis_socket_timeout == 5
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_config.py::TestSettings::test_default_values -v`

Expected: FAIL (new fields missing).

**Step 3: Write minimal implementation**

Add settings in `apps/api/config.py`:

```python
redis_max_connections: int = Field(
    default=50, ge=5, le=200, description="Redis max connections"
)
redis_socket_connect_timeout: int = Field(
    default=5, ge=1, le=30, description="Redis socket connect timeout (seconds)"
)
redis_socket_timeout: int = Field(
    default=5, ge=1, le=30, description="Redis socket timeout (seconds)"
)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_config.py::TestSettings::test_default_values -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add apps/api/config.py tests/unit/test_config.py
git commit -m "feat(config): add Redis pool configuration settings"
```

### Task 2: Use configurable Redis pool settings in cache adapter (tests first)

**Files:**
- Modify: `apps/api/adapters/cache.py`
- Modify: `tests/unit/adapters/test_cache.py`
- Modify: `.env.example`

**Step 1: Write the failing test**

Update existing test in `tests/unit/adapters/test_cache.py` at line 593.

REPLACE the current test body of `test_create_cache_uses_settings_when_url_not_provided` to assert settings are used:

```python
@pytest.mark.anyio
async def test_create_cache_uses_settings_when_url_not_provided(self) -> None:
    """Test cache creation uses settings for pool configuration."""
    with patch("apps.api.adapters.cache.redis.from_url") as mock_from_url:
        mock_client = Mock()
        mock_from_url.return_value = mock_client

        with patch("apps.api.adapters.cache.get_settings") as mock_settings:
            mock_settings.return_value.redis_url = "redis://localhost:53380/0"
            mock_settings.return_value.redis_max_connections = 50
            mock_settings.return_value.redis_socket_connect_timeout = 5
            mock_settings.return_value.redis_socket_timeout = 5

            cache = await RedisCache.create()

            assert cache._client == mock_client
            mock_from_url.assert_called_once_with(
                "redis://localhost:53380/0",
                encoding="utf-8",
                decode_responses=False,
                max_connections=50,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
```

Note: This replaces the existing test that currently expects hardcoded values.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/adapters/test_cache.py::test_create_cache_uses_settings_when_url_not_provided -v`

Expected: FAIL (settings not used / args mismatch).

**Step 3: Write minimal implementation**

Replace hardcoded values in `RedisCache.create` (current lines 107-114) with settings:

```python
# BEFORE (current hardcoded):
# client = redis.from_url(
#     redis_url,
#     encoding="utf-8",
#     decode_responses=False,
#     max_connections=50,
#     socket_connect_timeout=5,
#     socket_timeout=5,
# )

# AFTER (use settings):
settings = get_settings()
redis_url = url or settings.redis_url
client = redis.from_url(
    redis_url,
    encoding="utf-8",
    decode_responses=False,
    max_connections=settings.redis_max_connections,
    socket_connect_timeout=settings.redis_socket_connect_timeout,
    socket_timeout=settings.redis_socket_timeout,
)
```

Update `.env.example`:

```env
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_SOCKET_TIMEOUT=5
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/adapters/test_cache.py::test_create_cache_uses_settings_when_url_not_provided -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add apps/api/adapters/cache.py tests/unit/adapters/test_cache.py .env.example
git commit -m "perf(cache): make Redis pool settings configurable"
```

### Task 3: Update performance audit docs

**Files:**
- Modify: `.docs/audit-summary.md`
- Modify: `.docs/quick-wins-checklist.md`
- Modify: `.docs/framework-best-practices-audit.md`

**Step 1: Write the failing test**

Verify current documentation doesn't show fix as complete.

**Step 2: Run test to verify it fails**

Run: `rg -n "Status.*Fixed.*Redis|Redis pool settings are configurable" .docs/audit-summary.md .docs/quick-wins-checklist.md .docs/framework-best-practices-audit.md`

Expected: No matches (documentation not yet updated).

**Step 3: Write minimal documentation update**

Update three locations:

1. In `.docs/audit-summary.md` at line 139, ADD after "**Priority**: HIGH":
```markdown
**Status**: ✅ Fixed
**Note**: Redis pool settings are now configurable via REDIS_MAX_CONNECTIONS, REDIS_SOCKET_CONNECT_TIMEOUT, and REDIS_SOCKET_TIMEOUT environment variables.
```

2. In `.docs/quick-wins-checklist.md` at line 37, REPLACE section title:
```markdown
### 2. ✅ Add Redis Connection Pool (30 minutes) - COMPLETED
**Impact**: MEDIUM - Prevents connection exhaustion
**Status**: Fixed - Settings now configurable
```

3. In `.docs/framework-best-practices-audit.md` at line 779, ADD after "**Effort**: 30 minutes":
```markdown
**Status**: ✅ Completed
**Solution**: Configurable via REDIS_MAX_CONNECTIONS, REDIS_SOCKET_CONNECT_TIMEOUT, REDIS_SOCKET_TIMEOUT
```

**Step 4: Run test to verify it passes**

Run: `rg -n "Redis pool settings are" .docs/audit-summary.md`

Expected: Match found at updated line.

**Step 5: Commit**

```bash
git add .docs/audit-summary.md .docs/quick-wins-checklist.md .docs/framework-best-practices-audit.md
git commit -m "docs: mark PERF-002 Redis connection pool as fixed"
```

---

**Notes:** Follow @test-driven-development and @verification-before-completion for each task.
