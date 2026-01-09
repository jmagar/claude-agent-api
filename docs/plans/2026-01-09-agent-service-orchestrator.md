# AgentService Orchestrator Slimdown Implementation Plan

> **📁 Organization Note:** When this plan is fully implemented and verified, move this file to `docs/plans/complete/` to keep the plans folder organized.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `AgentService` a thin orchestrator by moving remaining business logic into focused helpers while preserving public and test-facing methods.

**Architecture:** Extract the remaining flow logic (command discovery, streaming lifecycle, single-query flow, session control actions, checkpoint creation, and file modification tracking) into dedicated modules under `apps/api/services/agent/`. Keep `AgentService` as a façade that wires dependencies and delegates, with existing method names preserved for tests.

**Tech Stack:** FastAPI, asyncio, pytest, mypy, ruff, structlog, claude_agent_sdk.

---

## Plan Validation Notes (Based on Current Code/Test Suite)

- `tests/unit/test_agent_service.py` calls `_track_file_modifications` and `_map_sdk_message` directly; these methods must remain on `AgentService` and delegate without changing signatures.
- `tests/integration/test_sdk_errors.py` calls `AgentService._execute_query()` directly; do not remove it—keep it as a wrapper.
- `query_stream` and `query_single` are part of public API; preserve signatures and return shapes.
- New helper classes should use XML-style docstrings for module/class/function consistency.
- Keep `apps/api/services/agent/__init__.py` exports stable unless a helper must be imported externally.

---

### Task 1: Extract command discovery into a helper

**Files:**
- Create: `apps/api/services/agent/command_discovery.py`
- Test: `tests/unit/services/agent/test_command_discovery.py`

**Step 1: Write the failing test**

Create `tests/unit/services/agent/test_command_discovery.py`:

```python
"""Unit tests for CommandDiscovery."""

from pathlib import Path

from apps.api.services.agent.command_discovery import CommandDiscovery


def test_command_discovery_returns_schema_objects(tmp_path: Path) -> None:
    discovery = CommandDiscovery(project_path=tmp_path)
    commands_service = discovery.commands_service
    assert commands_service.project_path == tmp_path
    assert discovery.discover_commands() == []
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/services/agent/test_command_discovery.py -v`
Expected: FAIL (module not found).

**Step 3: Write minimal implementation**

Create `apps/api/services/agent/command_discovery.py`:

```python
"""<summary>Discover slash commands for agent sessions.</summary>"""

from pathlib import Path
from typing import TYPE_CHECKING

from apps.api.schemas.responses import CommandInfoSchema
from apps.api.services.commands import CommandsService

if TYPE_CHECKING:
    from apps.api.services.commands import CommandsService


class CommandDiscovery:
    """<summary>Discovers slash commands and exposes the CommandsService.</summary>"""

    def __init__(self, project_path: Path) -> None:
        """<summary>Initialize with a project path.</summary>"""
        self._commands_service = CommandsService(project_path=project_path)

    @property
    def commands_service(self) -> CommandsService:
        """<summary>Return the commands service instance.</summary>"""
        return self._commands_service

    def discover_commands(self) -> list[CommandInfoSchema]:
        """<summary>Return discovered commands as schema objects.</summary>"""
        discovered = self._commands_service.discover_commands()
        return [
            CommandInfoSchema(name=cmd["name"], path=cmd["path"])
            for cmd in discovered
        ]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/services/agent/test_command_discovery.py -v`
Expected: PASS.

**Step 5: Commit (if desired)**

```bash
git add apps/api/services/agent/command_discovery.py tests/unit/services/agent/test_command_discovery.py
git commit -m "refactor: add command discovery helper"
```

---

### Task 2: Move streaming lifecycle logic into StreamQueryRunner

**Files:**
- Create: `apps/api/services/agent/stream_query_runner.py`
- Modify: `apps/api/services/agent/service.py`
- Test: `tests/unit/services/agent/test_stream_query_runner.py`

**Step 1: Write the failing test**

Create `tests/unit/services/agent/test_stream_query_runner.py`:

```python
"""Unit tests for StreamQueryRunner delegation."""

import pytest

from apps.api.schemas.requests.query import QueryRequest
from apps.api.services.agent.stream_query_runner import StreamQueryRunner


@pytest.mark.anyio
async def test_stream_query_runner_yields_init_event() -> None:
    runner = StreamQueryRunner()
    request = QueryRequest(prompt="test")

    events = []
    async for event in runner.run(request):
        events.append(event)
        break

    assert events
    assert events[0]["event"] == "init"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/services/agent/test_stream_query_runner.py -v`
Expected: FAIL (module not found).

**Step 3: Write minimal implementation**

Create `apps/api/services/agent/stream_query_runner.py`:

```python
"""<summary>Run streaming queries for AgentService.</summary>"""

import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

import structlog

from apps.api.schemas.responses import ErrorEvent, ErrorEventData
from apps.api.services.agent.command_discovery import CommandDiscovery
from apps.api.services.agent.stream_orchestrator import StreamOrchestrator
from apps.api.services.agent.types import StreamContext
from apps.api.services.agent.query_executor import QueryExecutor
from apps.api.services.agent.session_tracker import AgentSessionTracker

if TYPE_CHECKING:
    from apps.api.schemas.requests.query import QueryRequest

logger = structlog.get_logger(__name__)


class StreamQueryRunner:
    """<summary>Handles the streaming query flow.</summary>"""

    def __init__(
        self,
        session_tracker: AgentSessionTracker | None = None,
        query_executor: QueryExecutor | None = None,
        stream_orchestrator: StreamOrchestrator | None = None,
    ) -> None:
        """<summary>Initialize dependencies.</summary>"""
        self._session_tracker = session_tracker
        self._query_executor = query_executor
        self._stream_orchestrator = stream_orchestrator

    async def run(
        self, request: "QueryRequest"
    ) -> AsyncGenerator[dict[str, str], None]:
        """<summary>Execute the streaming query flow.</summary>"""
        if not self._session_tracker or not self._query_executor or not self._stream_orchestrator:
            raise RuntimeError("StreamQueryRunner dependencies not configured")

        session_id = request.session_id or str(uuid4())
        model = request.model or "sonnet"
        ctx = StreamContext(
            session_id=session_id,
            model=model,
            start_time=time.perf_counter(),
            enable_file_checkpointing=request.enable_file_checkpointing,
            include_partial_messages=request.include_partial_messages,
        )

        await self._session_tracker.register(session_id)

        try:
            project_path = Path(request.cwd) if request.cwd else Path.cwd()
            discovery = CommandDiscovery(project_path)
            command_schemas = discovery.discover_commands()

            init_event = self._stream_orchestrator.build_init_event(
                session_id=session_id,
                model=model,
                tools=request.allowed_tools or [],
                plugins=[p.name for p in request.plugins or [] if p.enabled],
                commands=command_schemas,
                permission_mode=request.permission_mode,
                mcp_servers=[],
            )
            yield init_event

            async for event in self._query_executor.execute(
                request, ctx, discovery.commands_service
            ):
                yield event
                if await self._session_tracker.is_interrupted(session_id):
                    logger.info("Session interrupted", session_id=session_id)
                    ctx.is_error = False
                    break

            duration_ms = int((time.perf_counter() - ctx.start_time) * 1000)
            yield self._stream_orchestrator.build_result_event(
                ctx=ctx,
                duration_ms=duration_ms,
            )

            reason: Literal["completed", "interrupted", "error"]
            if await self._session_tracker.is_interrupted(session_id):
                reason = "interrupted"
            elif ctx.is_error:
                reason = "error"
            else:
                reason = "completed"
            yield self._stream_orchestrator.build_done_event(reason=reason)

        except Exception as exc:
            logger.exception("Query stream error", session_id=session_id, error=str(exc))
            error_event = ErrorEvent(
                data=ErrorEventData(
                    code="AGENT_ERROR",
                    message=str(exc),
                )
            )
            yield self._stream_orchestrator._message_handler.format_sse(
                error_event.event, error_event.data.model_dump()
            )
            yield self._stream_orchestrator.build_done_event(reason="error")

        finally:
            await self._session_tracker.unregister(session_id)
```

Modify `apps/api/services/agent/service.py`:
- Add `stream_runner: StreamQueryRunner | None = None` to `__init__`.
- Instantiate `self._stream_runner = stream_runner or StreamQueryRunner(...)` with existing deps.
- Replace `query_stream` body with `async for event in self._stream_runner.run(request): yield event`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/services/agent/test_stream_query_runner.py -v`
Expected: PASS.

**Step 5: Commit (if desired)**

```bash
git add apps/api/services/agent/stream_query_runner.py apps/api/services/agent/service.py tests/unit/services/agent/test_stream_query_runner.py
git commit -m "refactor: extract stream query runner"
```

---

### Task 3: Move single-query flow into SingleQueryRunner

**Files:**
- Create: `apps/api/services/agent/single_query_runner.py`
- Modify: `apps/api/services/agent/service.py`
- Test: `tests/unit/services/agent/test_single_query_runner.py`

**Step 1: Write the failing test**

Create `tests/unit/services/agent/test_single_query_runner.py`:

```python
"""Unit tests for SingleQueryRunner delegation."""

import pytest

from apps.api.schemas.requests.query import QueryRequest
from apps.api.services.agent.single_query_runner import SingleQueryRunner


@pytest.mark.anyio
async def test_single_query_runner_returns_response_dict() -> None:
    runner = SingleQueryRunner()
    request = QueryRequest(prompt="test")

    result = await runner.run(request)

    assert result["session_id"]
    assert result["model"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/services/agent/test_single_query_runner.py -v`
Expected: FAIL (module not found).

**Step 3: Write minimal implementation**

Create `apps/api/services/agent/single_query_runner.py`:

```python
"""<summary>Run single-shot queries for AgentService.</summary>"""

import time
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from apps.api.services.agent.command_discovery import CommandDiscovery
from apps.api.services.agent.query_executor import QueryExecutor
from apps.api.services.agent.single_query_aggregator import SingleQueryAggregator
from apps.api.services.agent.types import StreamContext

if TYPE_CHECKING:
    from apps.api.schemas.requests.query import QueryRequest
    from apps.api.services.agent.types import QueryResponseDict


class SingleQueryRunner:
    """<summary>Handles the single query flow.</summary>"""

    def __init__(self, query_executor: QueryExecutor | None = None) -> None:
        """<summary>Initialize dependencies.</summary>"""
        self._query_executor = query_executor

    async def run(self, request: "QueryRequest") -> "QueryResponseDict":
        """<summary>Execute a single query and aggregate results.</summary>"""
        if not self._query_executor:
            raise RuntimeError("SingleQueryRunner dependency not configured")

        session_id = request.session_id or str(uuid4())
        model = request.model or "sonnet"
        start_time = time.perf_counter()
        aggregator = SingleQueryAggregator()

        ctx = StreamContext(
            session_id=session_id,
            model=model,
            start_time=start_time,
            enable_file_checkpointing=request.enable_file_checkpointing,
            include_partial_messages=request.include_partial_messages,
        )

        project_path = Path(request.cwd) if request.cwd else Path.cwd()
        discovery = CommandDiscovery(project_path)

        try:
            async for event in self._query_executor.execute(
                request, ctx, discovery.commands_service
            ):
                aggregator.handle_event(event)
        except Exception as exc:
            ctx.is_error = True
            aggregator.content_blocks.clear()
            aggregator.content_blocks.append({"type": "text", "text": f"Error: {exc}"})

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        return aggregator.finalize(
            session_id=session_id,
            model=model,
            ctx=ctx,
            duration_ms=duration_ms,
        )
```

Modify `apps/api/services/agent/service.py`:
- Add `single_query_runner: SingleQueryRunner | None = None` to `__init__`.
- Instantiate `self._single_query_runner = single_query_runner or SingleQueryRunner(self._query_executor)`.
- Replace `query_single` body with `return await self._single_query_runner.run(request)`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/services/agent/test_single_query_runner.py -v`
Expected: PASS.

**Step 5: Commit (if desired)**

```bash
git add apps/api/services/agent/single_query_runner.py apps/api/services/agent/service.py tests/unit/services/agent/test_single_query_runner.py
git commit -m "refactor: extract single query runner"
```

---

### Task 4: Move session control methods into SessionControl

**Files:**
- Create: `apps/api/services/agent/session_control.py`
- Modify: `apps/api/services/agent/service.py`
- Test: `tests/unit/services/agent/test_session_control.py`

**Step 1: Write the failing test**

Create `tests/unit/services/agent/test_session_control.py`:

```python
"""Unit tests for SessionControl."""

import pytest
from unittest.mock import AsyncMock

from apps.api.services.agent.session_control import SessionControl
from apps.api.services.agent.session_tracker import AgentSessionTracker


@pytest.mark.anyio
async def test_session_control_interrupt_requires_active_session() -> None:
    tracker = AsyncMock(spec=AgentSessionTracker)
    tracker.is_active.return_value = False
    control = SessionControl(session_tracker=tracker)

    result = await control.interrupt("sid")

    assert result is False
    tracker.is_active.assert_called_once_with("sid")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/services/agent/test_session_control.py -v`
Expected: FAIL (module not found).

**Step 3: Write minimal implementation**

Create `apps/api/services/agent/session_control.py`:

```python
"""<summary>Session control actions for AgentService.</summary>"""

from typing import Literal

import structlog

from apps.api.services.agent.session_tracker import AgentSessionTracker

logger = structlog.get_logger(__name__)


class SessionControl:
    """<summary>Controls session-level operations.</summary>"""

    def __init__(self, session_tracker: AgentSessionTracker) -> None:
        """<summary>Initialize with a session tracker.</summary>"""
        self._session_tracker = session_tracker

    async def interrupt(self, session_id: str) -> bool:
        """<summary>Interrupt a running session.</summary>"""
        is_active = await self._session_tracker.is_active(session_id)
        if not is_active:
            logger.info("Cannot interrupt inactive session", session_id=session_id)
            return False

        await self._session_tracker.mark_interrupted(session_id)
        logger.info("Interrupt signal sent", session_id=session_id)
        return True

    async def submit_answer(self, session_id: str, answer: str) -> bool:
        """<summary>Submit an answer to a pending question.</summary>"""
        is_active = await self._session_tracker.is_active(session_id)
        if not is_active:
            return False

        logger.info(
            "Answer submitted for session",
            session_id=session_id,
            answer_length=len(answer),
        )
        return True

    async def update_permission_mode(
        self,
        session_id: str,
        permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"],
    ) -> bool:
        """<summary>Update permission mode for an active session.</summary>"""
        is_active = await self._session_tracker.is_active(session_id)
        if not is_active:
            return False

        logger.info(
            "Permission mode updated for session",
            session_id=session_id,
            new_permission_mode=permission_mode,
        )
        return True
```

Modify `apps/api/services/agent/service.py`:
- Add `session_control: SessionControl | None = None` to `__init__`.
- Instantiate `self._session_control = session_control or SessionControl(self._session_tracker)`.
- Replace `interrupt`, `submit_answer`, `update_permission_mode` bodies with delegation to `self._session_control`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/services/agent/test_session_control.py -v`
Expected: PASS.

**Step 5: Commit (if desired)**

```bash
git add apps/api/services/agent/session_control.py apps/api/services/agent/service.py tests/unit/services/agent/test_session_control.py
git commit -m "refactor: extract session control"
```

---

### Task 5: Move checkpoint creation into CheckpointManager

**Files:**
- Create: `apps/api/services/agent/checkpoint_manager.py`
- Modify: `apps/api/services/agent/service.py`
- Test: `tests/unit/services/agent/test_checkpoint_manager.py`

**Step 1: Write the failing test**

Create `tests/unit/services/agent/test_checkpoint_manager.py`:

```python
"""Unit tests for CheckpointManager."""

import pytest
from unittest.mock import AsyncMock

from apps.api.services.agent.checkpoint_manager import CheckpointManager
from apps.api.services.agent.types import StreamContext


@pytest.mark.anyio
async def test_checkpoint_manager_skips_when_disabled() -> None:
    checkpoint_service = AsyncMock()
    manager = CheckpointManager(checkpoint_service=checkpoint_service)
    ctx = StreamContext(session_id="sid", model="sonnet", start_time=0.0)

    result = await manager.create_from_context(ctx)

    assert result is None
    checkpoint_service.create_checkpoint.assert_not_called()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/services/agent/test_checkpoint_manager.py -v`
Expected: FAIL (module not found).

**Step 3: Write minimal implementation**

Create `apps/api/services/agent/checkpoint_manager.py`:

```python
"""<summary>Create checkpoints from stream context data.</summary>"""

from typing import TYPE_CHECKING

import structlog

from apps.api.services.agent.types import StreamContext

if TYPE_CHECKING:
    from apps.api.services.checkpoint import Checkpoint, CheckpointService

logger = structlog.get_logger(__name__)


class CheckpointManager:
    """<summary>Manages checkpoint creation from a stream context.</summary>"""

    def __init__(self, checkpoint_service: "CheckpointService | None") -> None:
        """<summary>Initialize with a checkpoint service.</summary>"""
        self._checkpoint_service = checkpoint_service

    async def create_from_context(self, ctx: StreamContext) -> "Checkpoint | None":
        """<summary>Create a checkpoint using stream context data.</summary>"""
        if not ctx.enable_file_checkpointing:
            return None
        if not ctx.last_user_message_uuid:
            return None
        if not self._checkpoint_service:
            logger.warning(
                "Cannot create checkpoint: checkpoint_service not configured",
                session_id=ctx.session_id,
            )
            return None

        try:
            checkpoint = await self._checkpoint_service.create_checkpoint(
                session_id=ctx.session_id,
                user_message_uuid=ctx.last_user_message_uuid,
                files_modified=ctx.files_modified.copy(),
            )
            logger.info(
                "Created checkpoint from context",
                checkpoint_id=checkpoint.id,
                session_id=ctx.session_id,
                user_message_uuid=ctx.last_user_message_uuid,
                files_count=len(ctx.files_modified),
            )
            return checkpoint
        except Exception as exc:
            logger.error(
                "Failed to create checkpoint from context",
                session_id=ctx.session_id,
                error=str(exc),
            )
            return None
```

Modify `apps/api/services/agent/service.py`:
- Add `checkpoint_manager: CheckpointManager | None = None` to `__init__`.
- Instantiate `self._checkpoint_manager = checkpoint_manager or CheckpointManager(self._checkpoint_service)`.
- Replace `create_checkpoint_from_context` body with `return await self._checkpoint_manager.create_from_context(ctx)`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/services/agent/test_checkpoint_manager.py -v`
Expected: PASS.

**Step 5: Commit (if desired)**

```bash
git add apps/api/services/agent/checkpoint_manager.py apps/api/services/agent/service.py tests/unit/services/agent/test_checkpoint_manager.py
git commit -m "refactor: extract checkpoint manager"
```

---

### Task 6: Move file modification tracking into FileModificationTracker

**Files:**
- Create: `apps/api/services/agent/file_modification_tracker.py`
- Modify: `apps/api/services/agent/service.py`
- Test: `tests/unit/services/agent/test_file_modification_tracker.py`

**Step 1: Write the failing test**

Create `tests/unit/services/agent/test_file_modification_tracker.py`:

```python
"""Unit tests for FileModificationTracker."""

from unittest.mock import MagicMock

from apps.api.schemas.responses import ContentBlockSchema
from apps.api.services.agent.file_modification_tracker import FileModificationTracker
from apps.api.services.agent.types import StreamContext


def test_file_modification_tracker_converts_dicts() -> None:
    handler = MagicMock()
    tracker = FileModificationTracker(handler)
    ctx = StreamContext(session_id="sid", model="sonnet", start_time=0.0)

    tracker.track([{ "type": "text", "text": "hi" }], ctx)

    handler.track_file_modifications.assert_called_once()
    args, _ = handler.track_file_modifications.call_args
    assert isinstance(args[0][0], ContentBlockSchema)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/services/agent/test_file_modification_tracker.py -v`
Expected: FAIL (module not found).

**Step 3: Write minimal implementation**

Create `apps/api/services/agent/file_modification_tracker.py`:

```python
"""<summary>Track file modifications from content blocks.</summary>"""

from apps.api.schemas.responses import ContentBlockSchema
from apps.api.services.agent.types import StreamContext


class FileModificationTracker:
    """<summary>Converts blocks and forwards to MessageHandler.</summary>"""

    def __init__(self, message_handler: object) -> None:
        """<summary>Initialize with a message handler.</summary>"""
        self._message_handler = message_handler

    def track(self, content_blocks: list[object], ctx: StreamContext) -> None:
        """<summary>Convert blocks and forward tracking.</summary>"""
        typed_blocks: list[ContentBlockSchema] = []
        for block in content_blocks:
            if isinstance(block, ContentBlockSchema):
                typed_blocks.append(block)
            elif isinstance(block, dict):
                typed_blocks.append(ContentBlockSchema(**block))

        self._message_handler.track_file_modifications(typed_blocks, ctx)
```

Modify `apps/api/services/agent/service.py`:
- Add `file_modification_tracker: FileModificationTracker | None = None` to `__init__`.
- Instantiate `self._file_modification_tracker = file_modification_tracker or FileModificationTracker(self._message_handler)`.
- Replace `_track_file_modifications` body with `self._file_modification_tracker.track(content_blocks, ctx)`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/services/agent/test_file_modification_tracker.py -v`
Expected: PASS.

**Step 5: Commit (if desired)**

```bash
git add apps/api/services/agent/file_modification_tracker.py apps/api/services/agent/service.py tests/unit/services/agent/test_file_modification_tracker.py
git commit -m "refactor: extract file modification tracker"
```

---

### Task 7: Public API stability test (keep façade intact)

**Files:**
- Modify: `tests/unit/test_agent_service.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_agent_service.py` (if not already present):

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
Expected: FAIL if any refactor breaks method exposure.

**Step 3: Write minimal implementation**

Ensure `AgentService` keeps the public methods and delegates to helpers.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_agent_service.py::test_agent_service_public_api_stable -v`
Expected: PASS.

**Step 5: Commit (if desired)**

```bash
git add tests/unit/test_agent_service.py apps/api/services/agent/service.py
git commit -m "test: guard agent service public api"
```

---

### Task 8: Full validation

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
git status --short
```

---

## Notes for Implementation

- Keep `AgentService._execute_query`, `_mock_response`, `_map_sdk_message`, and `_track_file_modifications` methods as wrappers for compatibility.
- Do not remove `AgentService.query_stream` or `AgentService.query_single`; they should become delegates to the new runners.
- Prefer injecting helpers via `__init__` with defaults, mirroring current patterns (e.g., `session_tracker`, `query_executor`).

---

Plan complete and saved to `docs/plans/2026-01-09-agent-service-orchestrator.md`. Two execution options:

1. Subagent-Driven (this session) - I dispatch fresh subagent per task, review between tasks, fast iteration
2. Parallel Session (separate) - Open new session with executing-plans, batch execution with checkpoints

Which approach?
