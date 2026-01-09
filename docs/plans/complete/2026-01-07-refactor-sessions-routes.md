# Refactor Sessions Routes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the monolithic `routes/sessions.py` (429 lines, 8 endpoints) into 4 focused route modules following single responsibility principle.

**Architecture:** Extract routes by domain concern: CRUD stays in sessions.py, checkpoint operations move to checkpoints.py, session control (resume/fork/interrupt) moves to session_control.py, and user interaction (answer) moves to interactions.py. All routers use `/sessions` prefix and are mounted in main.py.

**Tech Stack:** FastAPI routers, SSE streaming, Pydantic schemas, pytest

---

## Task 1: Create Checkpoints Routes Module

**Files:**
- Create: `apps/api/routes/checkpoints.py`
- Test: `tests/unit/test_checkpoints_routes.py`

**Step 1: Write failing test for checkpoints router existence**

Create `tests/unit/test_checkpoints_routes.py`:

```python
"""Unit tests for checkpoint routes module."""

import pytest


class TestCheckpointsRouterStructure:
    """Tests for checkpoints router structure."""

    def test_checkpoints_router_exists(self) -> None:
        """Test that checkpoints router can be imported."""
        from apps.api.routes.checkpoints import router

        assert router is not None
        assert router.prefix == "/sessions"

    def test_checkpoints_router_has_list_endpoint(self) -> None:
        """Test that router has list checkpoints endpoint."""
        from apps.api.routes.checkpoints import router

        routes = [r.path for r in router.routes]
        assert "/{session_id}/checkpoints" in routes

    def test_checkpoints_router_has_rewind_endpoint(self) -> None:
        """Test that router has rewind endpoint."""
        from apps.api.routes.checkpoints import router

        routes = [r.path for r in router.routes]
        assert "/{session_id}/rewind" in routes
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_checkpoints_routes.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'apps.api.routes.checkpoints'"

**Step 3: Create checkpoints.py with routes extracted from sessions.py**

Create `apps/api/routes/checkpoints.py`:

```python
"""Checkpoint management endpoints."""

from fastapi import APIRouter

from apps.api.dependencies import (
    ApiKey,
    CheckpointSvc,
    SessionSvc,
)
from apps.api.exceptions import InvalidCheckpointError, SessionNotFoundError
from apps.api.schemas.requests import RewindRequest
from apps.api.schemas.responses import (
    CheckpointListResponse,
    CheckpointResponse,
)

router = APIRouter(prefix="/sessions", tags=["Checkpoints"])


@router.get("/{session_id}/checkpoints")
async def list_session_checkpoints(
    session_id: str,
    _api_key: ApiKey,
    session_service: SessionSvc,
    checkpoint_service: CheckpointSvc,
) -> CheckpointListResponse:
    """List all checkpoints for a session (T102).

    Returns all file checkpoints created during the session, which can be
    used to rewind the session to a previous state.

    Args:
        session_id: Session ID to get checkpoints for.
        _api_key: Validated API key (via dependency).
        session_service: Session service instance.
        checkpoint_service: Checkpoint service instance.

    Returns:
        List of checkpoints for the session.

    Raises:
        SessionNotFoundError: If session doesn't exist.
    """
    session = await session_service.get_session(session_id)
    if not session:
        raise SessionNotFoundError(session_id)

    checkpoints = await checkpoint_service.list_checkpoints(session_id)

    return CheckpointListResponse(
        checkpoints=[
            CheckpointResponse(
                id=cp.id,
                session_id=cp.session_id,
                user_message_uuid=cp.user_message_uuid,
                created_at=cp.created_at,
                files_modified=cp.files_modified,
            )
            for cp in checkpoints
        ]
    )


@router.post("/{session_id}/rewind")
async def rewind_to_checkpoint(
    session_id: str,
    request: RewindRequest,
    _api_key: ApiKey,
    session_service: SessionSvc,
    checkpoint_service: CheckpointSvc,
) -> dict[str, str]:
    """Rewind session files to a checkpoint state (T103).

    Restores files to their state at the specified checkpoint. This allows
    reverting changes made by the agent during the session.

    Args:
        session_id: Session ID to rewind.
        request: Rewind request with checkpoint_id.
        _api_key: Validated API key (via dependency).
        session_service: Session service instance.
        checkpoint_service: Checkpoint service instance.

    Returns:
        Status response with checkpoint_id that was rewound to.

    Raises:
        SessionNotFoundError: If session doesn't exist.
        InvalidCheckpointError: If checkpoint is invalid or doesn't belong to session.
    """
    session = await session_service.get_session(session_id)
    if not session:
        raise SessionNotFoundError(session_id)

    is_valid = await checkpoint_service.validate_checkpoint(
        session_id=session_id,
        checkpoint_id=request.checkpoint_id,
    )

    if not is_valid:
        raise InvalidCheckpointError(
            checkpoint_id=request.checkpoint_id,
            session_id=session_id,
        )

    return {
        "status": "validated",
        "checkpoint_id": request.checkpoint_id,
        "message": "Checkpoint validated. File restoration pending SDK support.",
    }
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_checkpoints_routes.py -v`

Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add apps/api/routes/checkpoints.py tests/unit/test_checkpoints_routes.py
git commit -m "feat: extract checkpoint routes from sessions.py"
```

---

## Task 2: Create Session Control Routes Module

**Files:**
- Create: `apps/api/routes/session_control.py`
- Test: `tests/unit/test_session_control_routes.py`

**Step 1: Write failing test for session_control router**

Create `tests/unit/test_session_control_routes.py`:

```python
"""Unit tests for session control routes module."""

import pytest


class TestSessionControlRouterStructure:
    """Tests for session control router structure."""

    def test_session_control_router_exists(self) -> None:
        """Test that session control router can be imported."""
        from apps.api.routes.session_control import router

        assert router is not None
        assert router.prefix == "/sessions"

    def test_session_control_router_has_resume_endpoint(self) -> None:
        """Test that router has resume endpoint."""
        from apps.api.routes.session_control import router

        routes = [r.path for r in router.routes]
        assert "/{session_id}/resume" in routes

    def test_session_control_router_has_fork_endpoint(self) -> None:
        """Test that router has fork endpoint."""
        from apps.api.routes.session_control import router

        routes = [r.path for r in router.routes]
        assert "/{session_id}/fork" in routes

    def test_session_control_router_has_interrupt_endpoint(self) -> None:
        """Test that router has interrupt endpoint."""
        from apps.api.routes.session_control import router

        routes = [r.path for r in router.routes]
        assert "/{session_id}/interrupt" in routes

    def test_session_control_router_has_control_endpoint(self) -> None:
        """Test that router has control endpoint."""
        from apps.api.routes.session_control import router

        routes = [r.path for r in router.routes]
        assert "/{session_id}/control" in routes
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_session_control_routes.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'apps.api.routes.session_control'"

**Step 3: Create session_control.py with routes extracted from sessions.py**

Create `apps/api/routes/session_control.py`:

```python
"""Session control endpoints (resume, fork, interrupt, control)."""

from fastapi import APIRouter
from sse_starlette import EventSourceResponse

from apps.api.dependencies import (
    AgentSvc,
    ApiKey,
    SessionSvc,
    ShutdownState,
)
from apps.api.exceptions import SessionNotFoundError
from apps.api.schemas.requests import (
    ControlRequest,
    ForkRequest,
    QueryRequest,
    ResumeRequest,
)

router = APIRouter(prefix="/sessions", tags=["Session Control"])


@router.post("/{session_id}/resume")
async def resume_session(
    session_id: str,
    request: ResumeRequest,
    _api_key: ApiKey,
    agent_service: AgentSvc,
    session_service: SessionSvc,
    _shutdown: ShutdownState,
) -> EventSourceResponse:
    """Resume an existing session with a new prompt.

    Args:
        session_id: Session ID to resume.
        request: Resume request with prompt.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.
        session_service: Session service instance.
        _shutdown: Shutdown state check (via dependency, rejects if shutting down).

    Returns:
        SSE stream of agent events.

    Raises:
        SessionNotFoundError: If session doesn't exist.
    """
    session = await session_service.get_session(session_id)
    if not session:
        raise SessionNotFoundError(session_id)

    query_request = QueryRequest(
        prompt=request.prompt,
        images=request.images,
        session_id=session_id,
        fork_session=False,
        allowed_tools=request.allowed_tools or [],
        disallowed_tools=request.disallowed_tools or [],
        permission_mode=request.permission_mode or "default",
        max_turns=request.max_turns,
        hooks=request.hooks,
    )

    return EventSourceResponse(
        agent_service.query_stream(query_request),
        ping=15,
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/fork")
async def fork_session(
    session_id: str,
    request: ForkRequest,
    _api_key: ApiKey,
    agent_service: AgentSvc,
    session_service: SessionSvc,
    _shutdown: ShutdownState,
) -> EventSourceResponse:
    """Fork an existing session into a new branch.

    Creates a new session that inherits the conversation history
    from the parent session up to the fork point.

    Args:
        session_id: Parent session ID to fork from.
        request: Fork request with prompt and optional overrides.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.
        session_service: Session service instance.
        _shutdown: Shutdown state check (via dependency, rejects if shutting down).

    Returns:
        SSE stream of agent events for the new session.

    Raises:
        SessionNotFoundError: If parent session doesn't exist.
    """
    parent_session = await session_service.get_session(session_id)
    if not parent_session:
        raise SessionNotFoundError(session_id)

    model = request.model or parent_session.model
    forked_session = await session_service.create_session(
        model=model,
        parent_session_id=session_id,
    )

    query_request = QueryRequest(
        prompt=request.prompt,
        images=request.images,
        session_id=forked_session.id,
        fork_session=True,
        allowed_tools=request.allowed_tools or [],
        disallowed_tools=request.disallowed_tools or [],
        permission_mode=request.permission_mode or "default",
        max_turns=request.max_turns,
        model=model,
        hooks=request.hooks,
    )

    return EventSourceResponse(
        agent_service.query_stream(query_request),
        ping=15,
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/interrupt")
async def interrupt_session(
    session_id: str,
    _api_key: ApiKey,
    agent_service: AgentSvc,
) -> dict[str, str]:
    """Interrupt a running session.

    Signals the agent to stop processing and return control
    to the user. The session remains valid and can be resumed.

    Args:
        session_id: Session ID to interrupt.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.

    Returns:
        Status response indicating interrupt was sent.

    Raises:
        SessionNotFoundError: If session doesn't exist or isn't active.
    """
    success = await agent_service.interrupt(session_id)

    if not success:
        raise SessionNotFoundError(session_id)

    return {"status": "interrupted", "session_id": session_id}


@router.post("/{session_id}/control")
async def send_control_event(
    session_id: str,
    request: ControlRequest,
    _api_key: ApiKey,
    agent_service: AgentSvc,
) -> dict[str, str]:
    """Send a control event to an active session (FR-015).

    Control events allow dynamic changes during streaming, such as
    changing the permission mode mid-session.

    Args:
        session_id: Session ID to send control event to.
        request: Control request with event type and data.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.

    Returns:
        Status response indicating control event was processed.

    Raises:
        SessionNotFoundError: If session doesn't exist or isn't active.
    """
    if request.type == "permission_mode_change":
        assert request.permission_mode is not None
        success = await agent_service.update_permission_mode(
            session_id, request.permission_mode
        )

        if not success:
            raise SessionNotFoundError(session_id)

        return {
            "status": "accepted",
            "session_id": session_id,
            "permission_mode": request.permission_mode,
        }

    return {"status": "unknown_type", "session_id": session_id}
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_session_control_routes.py -v`

Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add apps/api/routes/session_control.py tests/unit/test_session_control_routes.py
git commit -m "feat: extract session control routes from sessions.py"
```

---

## Task 3: Create Interactions Routes Module

**Files:**
- Create: `apps/api/routes/interactions.py`
- Test: `tests/unit/test_interactions_routes.py`

**Step 1: Write failing test for interactions router**

Create `tests/unit/test_interactions_routes.py`:

```python
"""Unit tests for interactions routes module."""

import pytest


class TestInteractionsRouterStructure:
    """Tests for interactions router structure."""

    def test_interactions_router_exists(self) -> None:
        """Test that interactions router can be imported."""
        from apps.api.routes.interactions import router

        assert router is not None
        assert router.prefix == "/sessions"

    def test_interactions_router_has_answer_endpoint(self) -> None:
        """Test that router has answer endpoint."""
        from apps.api.routes.interactions import router

        routes = [r.path for r in router.routes]
        assert "/{session_id}/answer" in routes
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_interactions_routes.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'apps.api.routes.interactions'"

**Step 3: Create interactions.py with answer route extracted from sessions.py**

Create `apps/api/routes/interactions.py`:

```python
"""User interaction endpoints (answer questions from agent)."""

from fastapi import APIRouter

from apps.api.dependencies import AgentSvc, ApiKey
from apps.api.exceptions import SessionNotFoundError
from apps.api.schemas.requests import AnswerRequest

router = APIRouter(prefix="/sessions", tags=["Interactions"])


@router.post("/{session_id}/answer")
async def answer_question(
    session_id: str,
    answer: AnswerRequest,
    _api_key: ApiKey,
    agent_service: AgentSvc,
) -> dict[str, str]:
    """Answer an AskUserQuestion from the agent.

    This endpoint is used to respond to questions posed by the agent
    during a streaming session via the AskUserQuestion tool.

    Args:
        session_id: Session ID that posed the question.
        answer: The user's answer to the question.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.

    Returns:
        Status response indicating the answer was received.

    Raises:
        SessionNotFoundError: If the session is not active or doesn't exist.
    """
    success = await agent_service.submit_answer(session_id, answer.answer)

    if not success:
        raise SessionNotFoundError(session_id)

    return {"status": "accepted", "session_id": session_id}
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_interactions_routes.py -v`

Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add apps/api/routes/interactions.py tests/unit/test_interactions_routes.py
git commit -m "feat: extract interactions route from sessions.py"
```

---

## Task 4: Slim Down sessions.py to CRUD Only

**Files:**
- Modify: `apps/api/routes/sessions.py`
- Test: `tests/unit/test_sessions_routes.py`

**Step 1: Write test for slimmed sessions router**

Create `tests/unit/test_sessions_routes.py`:

```python
"""Unit tests for sessions routes module (CRUD only)."""

import pytest


class TestSessionsRouterStructure:
    """Tests for sessions router structure after refactor."""

    def test_sessions_router_exists(self) -> None:
        """Test that sessions router can be imported."""
        from apps.api.routes.sessions import router

        assert router is not None
        assert router.prefix == "/sessions"

    def test_sessions_router_has_list_endpoint(self) -> None:
        """Test that router has list endpoint."""
        from apps.api.routes.sessions import router

        routes = [r.path for r in router.routes]
        assert "" in routes  # GET /sessions

    def test_sessions_router_has_get_endpoint(self) -> None:
        """Test that router has get endpoint."""
        from apps.api.routes.sessions import router

        routes = [r.path for r in router.routes]
        assert "/{session_id}" in routes

    def test_sessions_router_does_not_have_checkpoint_endpoints(self) -> None:
        """Test that checkpoint endpoints were extracted."""
        from apps.api.routes.sessions import router

        routes = [r.path for r in router.routes]
        assert "/{session_id}/checkpoints" not in routes
        assert "/{session_id}/rewind" not in routes

    def test_sessions_router_does_not_have_control_endpoints(self) -> None:
        """Test that control endpoints were extracted."""
        from apps.api.routes.sessions import router

        routes = [r.path for r in router.routes]
        assert "/{session_id}/resume" not in routes
        assert "/{session_id}/fork" not in routes
        assert "/{session_id}/interrupt" not in routes
        assert "/{session_id}/control" not in routes

    def test_sessions_router_does_not_have_answer_endpoint(self) -> None:
        """Test that answer endpoint was extracted."""
        from apps.api.routes.sessions import router

        routes = [r.path for r in router.routes]
        assert "/{session_id}/answer" not in routes
```

**Step 2: Run test to verify it fails (endpoints still exist)**

Run: `uv run pytest tests/unit/test_sessions_routes.py -v`

Expected: FAIL on tests checking endpoints don't exist

**Step 3: Replace sessions.py with CRUD-only version**

Replace `apps/api/routes/sessions.py` with:

```python
"""Session CRUD endpoints."""

from fastapi import APIRouter, Query

from apps.api.dependencies import ApiKey, SessionSvc
from apps.api.exceptions import SessionNotFoundError
from apps.api.schemas.responses import SessionListResponse, SessionResponse

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("")
async def list_sessions(
    _api_key: ApiKey,
    session_service: SessionSvc,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
) -> SessionListResponse:
    """List all sessions with pagination.

    Args:
        _api_key: Validated API key (via dependency).
        session_service: Session service instance.
        page: Page number (1-indexed).
        page_size: Number of sessions per page (max 100).

    Returns:
        Paginated list of sessions.
    """
    result = await session_service.list_sessions(page=page, page_size=page_size)

    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s.id,
                status=s.status,
                model=s.model,
                created_at=s.created_at,
                updated_at=s.updated_at,
                total_turns=s.total_turns,
                total_cost_usd=s.total_cost_usd,
                parent_session_id=s.parent_session_id,
            )
            for s in result.sessions
        ],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    _api_key: ApiKey,
    session_service: SessionSvc,
) -> SessionResponse:
    """Get session details by ID.

    Args:
        session_id: Session ID to retrieve.
        _api_key: Validated API key (via dependency).
        session_service: Session service instance.

    Returns:
        Session details.

    Raises:
        SessionNotFoundError: If session doesn't exist.
    """
    session = await session_service.get_session(session_id)
    if not session:
        raise SessionNotFoundError(session_id)

    return SessionResponse(
        id=session.id,
        status=session.status,
        model=session.model,
        created_at=session.created_at,
        updated_at=session.updated_at,
        total_turns=session.total_turns,
        total_cost_usd=session.total_cost_usd,
        parent_session_id=session.parent_session_id,
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_sessions_routes.py -v`

Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add apps/api/routes/sessions.py tests/unit/test_sessions_routes.py
git commit -m "refactor: slim sessions.py to CRUD-only endpoints"
```

---

## Task 5: Update main.py to Include New Routers

**Files:**
- Modify: `apps/api/main.py:19,142-146`
- Test: `tests/unit/test_main_routes.py`

**Step 1: Write test for all routers being registered**

Create `tests/unit/test_main_routes.py`:

```python
"""Unit tests for main app router registration."""

import pytest


class TestMainRouterRegistration:
    """Tests for router registration in main.py."""

    def test_all_session_routers_registered(self) -> None:
        """Test that all session-related routers are registered."""
        from apps.api.main import app

        routes = [r.path for r in app.routes]

        # Sessions CRUD
        assert "/api/v1/sessions" in routes
        assert "/api/v1/sessions/{session_id}" in routes

        # Session control
        assert "/api/v1/sessions/{session_id}/resume" in routes
        assert "/api/v1/sessions/{session_id}/fork" in routes
        assert "/api/v1/sessions/{session_id}/interrupt" in routes
        assert "/api/v1/sessions/{session_id}/control" in routes

        # Checkpoints
        assert "/api/v1/sessions/{session_id}/checkpoints" in routes
        assert "/api/v1/sessions/{session_id}/rewind" in routes

        # Interactions
        assert "/api/v1/sessions/{session_id}/answer" in routes
```

**Step 2: Run test to verify it fails (new routers not imported yet)**

Run: `uv run pytest tests/unit/test_main_routes.py -v`

Expected: FAIL - routes missing (checkpoints, control, interactions not registered)

**Step 3: Update main.py imports and router registration**

Edit `apps/api/main.py` line 19 to add imports:

```python
from apps.api.routes import (
    checkpoints,
    health,
    interactions,
    query,
    session_control,
    sessions,
    skills,
    websocket,
)
```

Edit `apps/api/main.py` lines 142-146 to register new routers:

```python
    # Include routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(query.router, prefix="/api/v1")
    app.include_router(sessions.router, prefix="/api/v1")
    app.include_router(session_control.router, prefix="/api/v1")
    app.include_router(checkpoints.router, prefix="/api/v1")
    app.include_router(interactions.router, prefix="/api/v1")
    app.include_router(skills.router, prefix="/api/v1")
    app.include_router(websocket.router, prefix="/api/v1")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_main_routes.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add apps/api/main.py tests/unit/test_main_routes.py
git commit -m "feat: register new route modules in main.py"
```

---

## Task 6: Update routes/__init__.py Exports

**Files:**
- Modify: `apps/api/routes/__init__.py`

**Step 1: Update __init__.py with new module exports**

Replace `apps/api/routes/__init__.py` with:

```python
"""API route handlers."""

from apps.api.routes import (
    checkpoints,
    health,
    interactions,
    query,
    session_control,
    sessions,
    skills,
    websocket,
)

__all__ = [
    "checkpoints",
    "health",
    "interactions",
    "query",
    "session_control",
    "sessions",
    "skills",
    "websocket",
]
```

**Step 2: Run full test suite to verify everything works**

Run: `uv run pytest tests/ -v --ignore=tests/contract`

Expected: All tests PASS

**Step 3: Commit**

```bash
git add apps/api/routes/__init__.py
git commit -m "chore: update routes __init__.py with new module exports"
```

---

## Task 7: Run Integration Tests and Full Verification

**Step 1: Run linter**

Run: `uv run ruff check apps/api/routes/`

Expected: No errors

**Step 2: Run formatter**

Run: `uv run ruff format apps/api/routes/`

Expected: Files formatted or already formatted

**Step 3: Run type checker**

Run: `uv run mypy apps/api/routes/`

Expected: No type errors

**Step 4: Run integration tests**

Run: `uv run pytest tests/integration/test_sessions.py -v`

Expected: All integration tests PASS (endpoints still work via new routers)

**Step 5: Final commit**

```bash
git add -A
git commit -m "chore: complete sessions routes refactor - lint and type check"
```

---

## Summary

| File | Before | After |
|------|--------|-------|
| `routes/sessions.py` | 429 lines | ~70 lines |
| `routes/session_control.py` | - | ~140 lines |
| `routes/checkpoints.py` | - | ~90 lines |
| `routes/interactions.py` | - | ~45 lines |

**Total:** 429 lines split into 4 focused modules (~345 lines total, reduction from removing duplication).
