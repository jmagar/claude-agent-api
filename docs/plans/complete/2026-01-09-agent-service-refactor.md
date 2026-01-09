# AgentService Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split `AgentService` into smaller, focused modules without changing public behavior or API surface.

**Architecture:** Extract cohesive responsibilities into new helpers (session tracking, SDK execution, stream orchestration, single-query aggregation, hook forwarding) while keeping `AgentService` as a façade. Preserve existing methods used by tests (`_execute_query`, `_mock_response`, `_register_active_session`, `_is_session_active`, `_unregister_active_session`, `_check_interrupt`, `_build_options`, `_map_sdk_message`, `_track_file_modifications`) by delegating to the new helpers rather than removing them.

**Tech Stack:** FastAPI, asyncio, claude_agent_sdk, Redis cache protocol, pytest, mypy, ruff.

---

## Plan Validation Notes (Based on Current Code/Test Suite)

- Tests in `tests/integration/test_sdk_errors.py` call `AgentService._execute_query()` directly; this method must remain and keep its current error handling behavior. Extract logic into a helper but keep `_execute_query` as a wrapper.
- Tests in `tests/unit/test_agent_service.py` call private methods `_register_active_session`, `_is_session_active`, `_unregister_active_session`, `_check_interrupt`; these must remain and delegate to the tracker.
- There are no existing fixtures named `mock_cache` or `agent_service` in `tests/unit/test_agent_service.py`; new tests must use local `MagicMock/AsyncMock` like the existing tests.
- Keep `apps/api/services/agent/__init__.py` exports stable; add new classes only if they need to be importable by external modules/tests.

---

### Task 1: Add session-tracking helper (Redis-backed active sessions)

**Files:**
- Create: `apps/api/services/agent/session_tracker.py`
- Modify: `apps/api/services/agent/service.py`
- Test: `tests/unit/test_agent_service.py`

**Step 1: Write the failing test**

Add a local test (no fixtures) in `tests/unit/test_agent_service.py` to assert that a custom tracker is accepted and used for delegation.

```python
def test_agent_service_accepts_session_tracker_dependency() -> None:
    from unittest.mock import MagicMock

    from apps.api.services.agent.session_tracker import AgentSessionTracker

    tracker = MagicMock(spec=AgentSessionTracker)
    service = AgentService(session_tracker=tracker)

    assert service._session_tracker is tracker
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_agent_service.py::test_agent_service_accepts_session_tracker_dependency -v`
Expected: FAIL (AgentSessionTracker not defined / AgentService init missing).

**Step 3: Write minimal implementation**

Create `apps/api/services/agent/session_tracker.py` with XML-style docstrings:

```python
"""<summary>Redis-backed session tracking for AgentService.</summary>"""

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from apps.api.protocols import Cache

logger = structlog.get_logger(__name__)


class AgentSessionTracker:
    """<summary>Tracks active sessions and interrupts in Redis.</summary>"""

    def __init__(self, cache: "Cache | None") -> None:
        """<summary>Initialize tracker.</summary>"""
        self._cache = cache

    async def register(self, session_id: str) -> None:
        """<summary>Register session as active.</summary>"""
        ...

    async def is_active(self, session_id: str) -> bool:
        """<summary>Return True if session is active.</summary>"""
        ...

    async def unregister(self, session_id: str) -> None:
        """<summary>Unregister session.</summary>"""
        ...

    async def is_interrupted(self, session_id: str) -> bool:
        """<summary>Return True if interrupt marker exists.</summary>"""
        ...

    async def mark_interrupted(self, session_id: str) -> None:
        """<summary>Mark session as interrupted.</summary>"""
        ...
```

Modify `apps/api/services/agent/service.py`:
- Add `session_tracker: AgentSessionTracker | None = None` to `AgentService.__init__`.
- Assign `self._session_tracker = session_tracker or AgentSessionTracker(cache=cache)`.
- Update `_register_active_session`, `_is_session_active`, `_unregister_active_session`, `_check_interrupt` to delegate to `self._session_tracker` (keep method names and signatures intact).

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_agent_service.py::test_agent_service_accepts_session_tracker_dependency -v`
Expected: PASS.

**Step 5: Commit (if desired)**

```bash
git add apps/api/services/agent/session_tracker.py apps/api/services/agent/service.py tests/unit/test_agent_service.py
git commit -m "refactor: extract agent session tracking helper"
```

---

### Task 2: Extract SDK execution into QueryExecutor (keep _execute_query wrapper)

**Files:**
- Create: `apps/api/services/agent/query_executor.py`
- Modify: `apps/api/services/agent/service.py`
- Test: `tests/integration/test_sdk_errors.py`

**Step 1: Write the failing test**

Add a unit test that verifies `AgentService._execute_query` delegates to a stub executor, while keeping the integration tests intact.

```python
@pytest.mark.anyio
async def test_execute_query_delegates_to_executor() -> None:
    from apps.api.services.agent.query_executor import QueryExecutor
    from apps.api.services.agent.types import StreamContext
    from apps.api.services.commands import CommandsService

    class StubExecutor(QueryExecutor):
        def __init__(self) -> None:
            self.called = False

        async def execute(self, request, ctx, commands_service):
            self.called = True
            if False:
                yield {"event": "noop", "data": "{}"}

    service = AgentService(query_executor=StubExecutor())
    ctx = StreamContext(session_id="sid", model="sonnet", start_time=0.0)
    commands_service = CommandsService(project_path=Path.cwd())
    request = QueryRequest(prompt="test")

    async for _ in service._execute_query(request, ctx, commands_service):
        pass

    assert service._query_executor.called is True
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_agent_service.py::test_execute_query_delegates_to_executor -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

Create `apps/api/services/agent/query_executor.py`:
- Move the full body of `_execute_query` and `_mock_response` into a new class `QueryExecutor`.
- Keep error handling and logging identical.
- Keep the claude_agent_sdk import inside the method (for patching in tests).

Modify `AgentService`:
- Add `query_executor: QueryExecutor | None = None` to `__init__`.
- Assign `self._query_executor = query_executor or QueryExecutor(self._message_handler)`.
- Replace `_execute_query` body with `async for event in self._query_executor.execute(...): yield event`.
- Replace `_mock_response` with a wrapper that calls `self._query_executor.mock_response(...)` (keep method name for compatibility).

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_agent_service.py::test_execute_query_delegates_to_executor -v`
Expected: PASS.

**Step 5: Run the integration error tests**

Run: `uv run pytest tests/integration/test_sdk_errors.py -v`
Expected: PASS (ensures `_execute_query` behavior unchanged).

**Step 6: Commit (if desired)**

```bash
git add apps/api/services/agent/query_executor.py apps/api/services/agent/service.py tests/unit/test_agent_service.py
git commit -m "refactor: extract query execution from AgentService"
```

---

### Task 3: Extract stream orchestration helpers

**Files:**
- Create: `apps/api/services/agent/stream_orchestrator.py`
- Modify: `apps/api/services/agent/service.py`
- Test: `tests/unit/services/agent/test_stream_orchestrator.py`

**Step 1: Write the failing test**

Create `tests/unit/services/agent/test_stream_orchestrator.py`:

```python
import pytest

from apps.api.services.agent.handlers import MessageHandler
from apps.api.services.agent.stream_orchestrator import StreamOrchestrator


@pytest.mark.anyio
async def test_stream_orchestrator_builds_init_and_done_events() -> None:
    orchestrator = StreamOrchestrator(message_handler=MessageHandler())
    init_event = orchestrator.build_init_event(
        session_id="sid",
        model="sonnet",
        tools=["Read"],
        plugins=[],
        commands=[],
        permission_mode="default",
    )
    done_event = orchestrator.build_done_event(reason="completed")
    assert init_event["event"] == "init"
    assert done_event["event"] == "done"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/services/agent/test_stream_orchestrator.py -v`
Expected: FAIL (StreamOrchestrator not defined).

**Step 3: Write minimal implementation**

Create `apps/api/services/agent/stream_orchestrator.py` with methods that build:
- `build_init_event` (InitEvent)
- `build_result_event` (ResultEvent, including UsageSchema conversion)
- `build_done_event` (DoneEvent)

Then update `AgentService.query_stream` to call these helper methods instead of inline event construction.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/services/agent/test_stream_orchestrator.py -v`
Expected: PASS.

**Step 5: Commit (if desired)**

```bash
git add apps/api/services/agent/stream_orchestrator.py apps/api/services/agent/service.py tests/unit/services/agent/test_stream_orchestrator.py
git commit -m "refactor: extract stream orchestration helpers"
```

---

### Task 4: Extract single-query aggregation

**Files:**
- Create: `apps/api/services/agent/single_query_aggregator.py`
- Modify: `apps/api/services/agent/service.py`
- Test: `tests/unit/services/agent/test_single_query_aggregator.py`

**Step 1: Write the failing test**

Create `tests/unit/services/agent/test_single_query_aggregator.py`:

```python
from apps.api.services.agent.single_query_aggregator import SingleQueryAggregator
from apps.api.services.agent.types import StreamContext


def test_single_query_aggregator_finalizes_result() -> None:
    agg = SingleQueryAggregator()
    ctx = StreamContext(session_id="sid", model="sonnet", start_time=0.0)
    result = agg.finalize(session_id="sid", model="sonnet", ctx=ctx, duration_ms=10)
    assert result["session_id"] == "sid"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/services/agent/test_single_query_aggregator.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

Create `apps/api/services/agent/single_query_aggregator.py`:

```python
class SingleQueryAggregator:
    def __init__(self) -> None:
        self._content_blocks: list[dict[str, object]] = []
        self._usage_data: dict[str, int] | None = None
        self._is_error = False

    def handle_event(self, event: dict[str, str]) -> None:
        # Move per-event parsing from AgentService.query_single
        ...

    def finalize(self, session_id: str, model: str, ctx: StreamContext, duration_ms: int) -> QueryResponseDict:
        # Build the response dict
        ...
```

Update `AgentService.query_single` to use this aggregator, keeping output structure unchanged.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/services/agent/test_single_query_aggregator.py -v`
Expected: PASS.

**Step 5: Commit (if desired)**

```bash
git add apps/api/services/agent/single_query_aggregator.py apps/api/services/agent/service.py tests/unit/services/agent/test_single_query_aggregator.py
git commit -m "refactor: extract single-query aggregation"
```

---

### Task 5: Move hook forwarding into a thin facade

**Files:**
- Create: `apps/api/services/agent/hook_facade.py`
- Modify: `apps/api/services/agent/service.py`
- Test: `tests/unit/services/agent/test_hook_facade.py`

**Step 1: Write the failing test**

Create `tests/unit/services/agent/test_hook_facade.py`:

```python
import pytest

from apps.api.services.agent.hook_facade import HookFacade
from apps.api.services.agent.hooks import HookExecutor
from apps.api.services.webhook import WebhookService


@pytest.mark.anyio
async def test_hook_facade_forwards_pre_tool_use() -> None:
    facade = HookFacade(executor=HookExecutor(WebhookService()))
    result = await facade.execute_pre_tool_use(None, "sid", "Tool")
    assert isinstance(result, dict)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/services/agent/test_hook_facade.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

Create `apps/api/services/agent/hook_facade.py` with forwarding methods for all hook types:
- `execute_pre_tool_use`
- `execute_post_tool_use`
- `execute_stop`
- `execute_subagent_stop`
- `execute_user_prompt_submit`

Modify `AgentService` to build `HookFacade` and delegate its hook methods.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/services/agent/test_hook_facade.py -v`
Expected: PASS.

**Step 5: Commit (if desired)**

```bash
git add apps/api/services/agent/hook_facade.py apps/api/services/agent/service.py tests/unit/services/agent/test_hook_facade.py
git commit -m "refactor: extract hook facade"
```

---

### Task 6: Public API stability check

**Files:**
- Modify: `apps/api/services/agent/service.py`
- Test: `tests/unit/test_agent_service.py`

**Step 1: Write the failing test**

Add a minimal test to ensure public methods still exist:

```python
def test_agent_service_public_api_stable() -> None:
    service = AgentService(cache=None)
    assert hasattr(service, "query_stream")
    assert hasattr(service, "query_single")
    assert hasattr(service, "interrupt")
    assert hasattr(service, "submit_answer")
    assert hasattr(service, "update_permission_mode")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_agent_service.py::test_agent_service_public_api_stable -v`
Expected: FAIL if refactor breaks method exposure.

**Step 3: Write minimal implementation**

Ensure `AgentService` remains a façade; keep public and private method names intact and delegate to helpers.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_agent_service.py::test_agent_service_public_api_stable -v`
Expected: PASS.

**Step 5: Commit (if desired)**

```bash
git add apps/api/services/agent/service.py tests/unit/test_agent_service.py
git commit -m "refactor: verify agent public api stability"
```

---

### Task 7: Full validation

**Files:**
- None

**Step 1: Run type checks**

Run: `uv run mypy apps/api --strict`
Expected: Success.

**Step 2: Run lints**

Run: `uv run ruff check apps/api`
Expected: All checks passed.

**Step 3: Run formatting**

Run: `uv run ruff format apps/api`
Expected: No changes or minimal formatting.

**Step 4: Run tests**

Run: `uv run pytest`
Expected: PASS (with existing skip markers).

**Step 5: Commit (if desired)**

```bash
git commit -am "chore: validate agent refactor"
```

---

**Notes for engineers with zero context**
- Keep the public methods in `AgentService` unchanged; only move internal logic.
- Preserve existing response schemas and error handling; do not change payloads.
- Do not remove `_execute_query` or `_mock_response`; wrap them.
- Keep `MessageHandler`, `OptionsBuilder`, and `HookExecutor` behavior unchanged; only rewire.
- Any new classes must be in `apps/api/services/agent/` (no `src/` directories).
