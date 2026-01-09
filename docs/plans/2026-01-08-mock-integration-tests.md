# Mock Integration Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace real Claude API calls in integration tests with mocks to improve test speed, reduce costs, and eliminate network dependencies.

**Architecture:** Create pytest fixtures that mock the ClaudeSDKClient from claude_agent_sdk. Mock fixtures will return realistic SSE events matching the API's event schema. Keep a small E2E test suite (~5-10 tests) that actually calls Claude for smoke testing.

**Tech Stack:** pytest, pytest-mock, unittest.mock.AsyncMock, pytest markers for test categorization

**Current State:**
- 10 integration test files with ~85 API calls
- Each test takes ~17-18 seconds (actual Claude API calls)
- Tests are expensive and can fail due to network issues
- Tests already use parallel execution (pytest-xdist)

---

## Task 1: Create Mock Infrastructure

**Files:**
- Create: `tests/mocks/__init__.py`
- Create: `tests/mocks/claude_sdk.py`
- Create: `tests/mocks/event_builders.py`
- Modify: `tests/conftest.py`

### Step 1: Write failing test for mock fixture

Create test to verify mock fixture returns expected events:

```python
# tests/mocks/test_mock_claude_sdk.py
"""Tests for Claude SDK mocking infrastructure."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_mock_claude_sdk_returns_init_event(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_claude_sdk: None,  # This fixture doesn't exist yet
) -> None:
    """Test that mocked SDK returns init event."""
    response = await async_client.post(
        "/api/v1/query",
        json={"prompt": "test"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    # Parse SSE events
    events = []
    for line in response.text.strip().split("\n\n"):
        if line.startswith("event: "):
            event_type = line.split("event: ")[1].split("\n")[0]
            events.append(event_type)

    assert "init" in events
```

### Step 2: Run test to verify it fails

```bash
uv run pytest tests/mocks/test_mock_claude_sdk.py::test_mock_claude_sdk_returns_init_event -v
```

Expected: FAIL with "fixture 'mock_claude_sdk' not found"

### Step 3: Create mock event builders

```python
# tests/mocks/event_builders.py
"""Builders for mock SSE events."""

from typing import Any


def build_init_event(
    session_id: str = "test-session-001",
    model: str = "sonnet",
    tools: list[str] | None = None,
    mcp_servers: list[dict[str, Any]] | None = None,
    plugins: list[str] | None = None,
    commands: list[str] | None = None,
    permission_mode: str = "default",
) -> dict[str, str]:
    """Build init SSE event.

    Args:
        session_id: Session ID
        model: Model name
        tools: List of allowed tools
        mcp_servers: List of MCP server status
        plugins: List of plugin names
        commands: List of available commands
        permission_mode: Permission mode

    Returns:
        SSE event dict with 'event' and 'data' keys
    """
    import json

    data = {
        "session_id": session_id,
        "model": model,
        "tools": tools or [],
        "mcp_servers": mcp_servers or [],
        "plugins": plugins or [],
        "commands": commands or [],
        "permission_mode": permission_mode,
    }

    return {
        "event": "init",
        "data": json.dumps(data),
    }


def build_message_event(
    message_type: str = "assistant",
    content: list[dict[str, Any]] | None = None,
    model: str = "sonnet",
    uuid: str | None = None,
    usage: dict[str, int] | None = None,
) -> dict[str, str]:
    """Build message SSE event.

    Args:
        message_type: Type of message (user/assistant/system)
        content: List of content blocks
        model: Model name
        uuid: Message UUID
        usage: Token usage info

    Returns:
        SSE event dict
    """
    import json

    if content is None:
        content = [{"type": "text", "text": "Mocked response"}]

    data: dict[str, Any] = {
        "type": message_type,
        "content": content,
        "model": model,
    }

    if uuid:
        data["uuid"] = uuid
    if usage:
        data["usage"] = usage

    return {
        "event": "message",
        "data": json.dumps(data),
    }


def build_result_event(
    model: str = "sonnet",
    usage: dict[str, int] | None = None,
    duration: float = 1.5,
) -> dict[str, str]:
    """Build result SSE event.

    Args:
        model: Model name
        usage: Token usage
        duration: Request duration in seconds

    Returns:
        SSE event dict
    """
    import json

    if usage is None:
        usage = {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        }

    data = {
        "model": model,
        "usage": usage,
        "duration": duration,
    }

    return {
        "event": "result",
        "data": json.dumps(data),
    }


def build_done_event() -> dict[str, str]:
    """Build done SSE event.

    Returns:
        SSE event dict
    """
    return {
        "event": "done",
        "data": "{}",
    }


def build_error_event(
    code: str = "INTERNAL_ERROR",
    message: str = "An error occurred",
    details: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Build error SSE event.

    Args:
        code: Error code
        message: Error message
        details: Additional error details

    Returns:
        SSE event dict
    """
    import json

    data = {
        "code": code,
        "message": message,
        "details": details or {},
    }

    return {
        "event": "error",
        "data": json.dumps(data),
    }


def build_standard_response(
    session_id: str = "test-session-001",
    model: str = "sonnet",
    response_text: str = "Mocked response",
) -> list[dict[str, str]]:
    """Build standard mock response with init, message, result, done events.

    Args:
        session_id: Session ID
        model: Model name
        response_text: Response text content

    Returns:
        List of SSE events
    """
    return [
        build_init_event(session_id=session_id, model=model),
        build_message_event(
            content=[{"type": "text", "text": response_text}],
            model=model,
        ),
        build_result_event(model=model),
        build_done_event(),
    ]
```

### Step 4: Create mock Claude SDK fixture

```python
# tests/mocks/claude_sdk.py
"""Mock Claude SDK client for testing."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.mocks.event_builders import build_standard_response


class MockClaudeSDKClient:
    """Mock implementation of ClaudeSDKClient."""

    def __init__(self, options: Any) -> None:
        """Initialize mock client.

        Args:
            options: Agent options (ignored in mock)
        """
        self.options = options
        self._events: list[dict[str, str]] = []

    async def __aenter__(self) -> "MockClaudeSDKClient":
        """Context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager exit."""
        pass

    def set_events(self, events: list[dict[str, str]]) -> None:
        """Set events to return from query.

        Args:
            events: List of SSE events to return
        """
        self._events = events

    async def query(self, prompt: str | list[dict[str, Any]]) -> AsyncGenerator[dict[str, str], None]:
        """Mock query method.

        Args:
            prompt: Query prompt (text or multimodal)

        Yields:
            SSE events
        """
        # If no events set, return standard response
        if not self._events:
            self._events = build_standard_response()

        for event in self._events:
            yield event


@pytest.fixture
def mock_claude_sdk() -> AsyncGenerator[MagicMock, None]:
    """Mock the ClaudeSDKClient for testing.

    Yields:
        Mock client that returns standard response events
    """
    with patch("apps.api.services.agent.service.ClaudeSDKClient") as mock:
        # Create mock instance
        mock_instance = MockClaudeSDKClient(options=None)

        # Make the mock return our mock instance
        mock.return_value.__aenter__.return_value = mock_instance

        yield mock
```

### Step 5: Add mock fixture to conftest

```python
# tests/conftest.py (add at end of file)

# Import mock fixtures
from tests.mocks.claude_sdk import mock_claude_sdk  # noqa: F401
```

### Step 6: Run test to verify it passes

```bash
uv run pytest tests/mocks/test_mock_claude_sdk.py::test_mock_claude_sdk_returns_init_event -v
```

Expected: PASS

### Step 7: Commit

```bash
git add tests/mocks/ tests/conftest.py
git commit -m "feat: add mock Claude SDK infrastructure for testing"
```

---

## Task 2: Add Pytest Markers for Test Categories

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/e2e/__init__.py`

### Step 1: Write test using e2e marker

```python
# tests/e2e/test_claude_api.py
"""End-to-end tests that actually call Claude API."""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.anyio
async def test_real_claude_query(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test real Claude API call (no mocking).

    This test actually calls Claude and should be run sparingly.
    """
    response = await async_client.post(
        "/api/v1/query",
        json={"prompt": "Say hello"},
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Verify we get real events from Claude
    events = []
    for line in response.text.strip().split("\n\n"):
        if line.startswith("event: "):
            event_type = line.split("event: ")[1].split("\n")[0]
            events.append(event_type)

    assert "init" in events
    assert "message" in events
    assert "result" in events
    assert "done" in events
```

### Step 2: Run test to verify it fails

```bash
uv run pytest tests/e2e/test_claude_api.py::test_real_claude_query -v -m e2e
```

Expected: FAIL with "Unknown pytest.mark.e2e"

### Step 3: Add pytest markers to pyproject.toml

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short -p no:asyncio -n auto"
filterwarnings = [
    "ignore::DeprecationWarning",
]
markers = [
    "e2e: End-to-end tests that call real Claude API (slow, expensive)",
    "unit: Unit tests (fast, no external dependencies)",
    "integration: Integration tests with mocked Claude API",
]
```

### Step 4: Run test to verify it passes

```bash
uv run pytest tests/e2e/test_claude_api.py::test_real_claude_query -v -m e2e
```

Expected: PASS (but slow ~17s)

### Step 5: Verify marker filtering works

```bash
# Run only unit tests (fast)
uv run pytest -m unit

# Skip E2E tests (default for fast testing)
uv run pytest -m "not e2e"

# Run only E2E tests (slow, for smoke testing)
uv run pytest -m e2e
```

### Step 6: Commit

```bash
git add pyproject.toml tests/e2e/
git commit -m "feat: add pytest markers for test categorization"
```

---

## Task 3: Mock test_permissions.py Integration Tests

**Files:**
- Modify: `tests/integration/test_permissions.py`

### Step 1: Add mock_claude_sdk fixture to first test

```python
# tests/integration/test_permissions.py

@pytest.mark.integration
@pytest.mark.anyio
async def test_default_permission_mode_accepted(
    self,
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_claude_sdk: None,  # ADD THIS
) -> None:
    """Test that default permission mode is accepted in query request."""
    response = await async_client.post(
        "/api/v1/query",
        json={
            "prompt": "List files",
            "permission_mode": "default",
        },
        headers=auth_headers,
    )
    # Should accept the request (stream starts) - status 200 for SSE
    assert response.status_code == 200
```

### Step 2: Run test to verify it passes quickly

```bash
uv run pytest tests/integration/test_permissions.py::TestPermissionModeValidation::test_default_permission_mode_accepted -v
```

Expected: PASS in < 2 seconds (vs ~17s before)

### Step 3: Add mock fixture to all tests in TestPermissionModeValidation

Update each test method in the class to include `mock_claude_sdk: None` parameter.

### Step 4: Run all tests in TestPermissionModeValidation

```bash
uv run pytest tests/integration/test_permissions.py::TestPermissionModeValidation -v
```

Expected: ALL PASS in < 5 seconds total

### Step 5: Add mock fixture to remaining test classes

Update all test classes in test_permissions.py:
- TestPermissionModeValidation
- TestPermissionModeSingleQuery
- TestPermissionModeWithResume
- TestPermissionModeWithFork
- TestPermissionPromptToolName
- TestDynamicPermissionModeChanges

### Step 6: Run all tests in file

```bash
uv run pytest tests/integration/test_permissions.py -v
```

Expected: ALL PASS in < 10 seconds total

### Step 7: Commit

```bash
git add tests/integration/test_permissions.py
git commit -m "test: mock Claude SDK in permission integration tests"
```

---

## Task 4: Mock test_model_selection.py Integration Tests

**Files:**
- Modify: `tests/integration/test_model_selection.py`

### Step 1: Add integration marker and mock to first test

```python
# tests/integration/test_model_selection.py

@pytest.mark.integration
@pytest.mark.anyio
async def test_query_with_default_model_uses_sonnet(
    self,
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_claude_sdk: None,  # ADD THIS
) -> None:
    """Test that queries without model parameter default to sonnet."""
    # Test implementation...
```

### Step 2: Run test to verify it passes

```bash
uv run pytest tests/integration/test_model_selection.py::TestModelSelection::test_query_with_default_model_uses_sonnet -v
```

Expected: PASS in < 2 seconds

### Step 3: Add mock fixture to all tests in TestModelSelection

Update all test methods to include `mock_claude_sdk: None`.

### Step 4: Run all tests in file

```bash
uv run pytest tests/integration/test_model_selection.py -v
```

Expected: ALL PASS in < 5 seconds

### Step 5: Commit

```bash
git add tests/integration/test_model_selection.py
git commit -m "test: mock Claude SDK in model selection integration tests"
```

---

## Task 5: Mock test_hooks.py Integration Tests

**Files:**
- Modify: `tests/integration/test_hooks.py`

### Step 1: Add integration marker and mock to all test classes

```python
# tests/integration/test_hooks.py

class TestHooksConfigValidation:
    """Tests for hooks configuration validation."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_pre_tool_use_hook_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,  # ADD THIS
    ) -> None:
        # Test implementation...
```

### Step 2: Run first test to verify

```bash
uv run pytest tests/integration/test_hooks.py::TestHooksConfigValidation::test_query_with_pre_tool_use_hook_accepted -v
```

Expected: PASS in < 2 seconds

### Step 3: Add mock to all tests in file

Update all test classes:
- TestHooksConfigValidation
- TestHookInvalidConfigurations
- TestResumeWithHooks
- TestForkWithHooks

### Step 4: Run all tests

```bash
uv run pytest tests/integration/test_hooks.py -v
```

Expected: ALL PASS in < 15 seconds

### Step 5: Commit

```bash
git add tests/integration/test_hooks.py
git commit -m "test: mock Claude SDK in hooks integration tests"
```

---

## Task 6: Mock test_structured_output.py Integration Tests

**Files:**
- Modify: `tests/integration/test_structured_output.py`

### Step 1: Add mock to all tests

```python
# tests/integration/test_structured_output.py

@pytest.mark.integration
@pytest.mark.anyio
async def test_json_output_format_accepted(
    self,
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_claude_sdk: None,  # ADD THIS
) -> None:
    # Test implementation...
```

### Step 2: Run tests

```bash
uv run pytest tests/integration/test_structured_output.py -v
```

Expected: ALL PASS in < 10 seconds

### Step 3: Commit

```bash
git add tests/integration/test_structured_output.py
git commit -m "test: mock Claude SDK in structured output integration tests"
```

---

## Task 7: Mock test_tools.py Integration Tests

**Files:**
- Modify: `tests/integration/test_tools.py`

### Step 1: Add mock to all tests

```python
# tests/integration/test_tools.py

@pytest.mark.integration
@pytest.mark.anyio
async def test_allowed_tools_parameter_accepted(
    self,
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_claude_sdk: None,  # ADD THIS
) -> None:
    # Test implementation...
```

### Step 2: Run tests

```bash
uv run pytest tests/integration/test_tools.py -v
```

Expected: ALL PASS in < 10 seconds

### Step 3: Commit

```bash
git add tests/integration/test_tools.py
git commit -m "test: mock Claude SDK in tools integration tests"
```

---

## Task 8: Mock test_subagents.py Integration Tests

**Files:**
- Modify: `tests/integration/test_subagents.py`

### Step 1: Add mock to all tests

```python
# tests/integration/test_subagents.py

@pytest.mark.integration
@pytest.mark.anyio
async def test_agents_parameter_accepted(
    self,
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_claude_sdk: None,  # ADD THIS
) -> None:
    # Test implementation...
```

### Step 2: Run tests

```bash
uv run pytest tests/integration/test_subagents.py -v
```

Expected: ALL PASS in < 10 seconds

### Step 3: Commit

```bash
git add tests/integration/test_subagents.py
git commit -m "test: mock Claude SDK in subagents integration tests"
```

---

## Task 9: Mock test_mcp.py Integration Tests

**Files:**
- Modify: `tests/integration/test_mcp.py`

### Step 1: Add mock to all tests

```python
# tests/integration/test_mcp.py

@pytest.mark.integration
@pytest.mark.anyio
async def test_query_with_mcp_server_config_accepted(
    self,
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_claude_sdk: None,  # ADD THIS
) -> None:
    # Test implementation...
```

### Step 2: Run tests

```bash
uv run pytest tests/integration/test_mcp.py -v
```

Expected: ALL PASS in < 5 seconds

### Step 3: Commit

```bash
git add tests/integration/test_mcp.py
git commit -m "test: mock Claude SDK in MCP integration tests"
```

---

## Task 10: Mock test_query.py Integration Tests

**Files:**
- Modify: `tests/integration/test_query.py`

### Step 1: Add mock to all tests

```python
# tests/integration/test_query.py

@pytest.mark.integration
@pytest.mark.anyio
async def test_query_endpoint_exists(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_claude_sdk: None,  # ADD THIS
) -> None:
    # Test implementation...
```

### Step 2: Run tests

```bash
uv run pytest tests/integration/test_query.py -v
```

Expected: ALL PASS in < 8 seconds

### Step 3: Commit

```bash
git add tests/integration/test_query.py
git commit -m "test: mock Claude SDK in query integration tests"
```

---

## Task 11: Mock test_checkpoints.py Integration Tests

**Files:**
- Modify: `tests/integration/test_checkpoints.py`

### Step 1: Add mock to all tests

```python
# tests/integration/test_checkpoints.py

@pytest.mark.integration
@pytest.mark.anyio
async def test_session_with_checkpointing_lists_checkpoints(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_claude_sdk: None,  # ADD THIS
) -> None:
    # Test implementation...
```

### Step 2: Run tests

```bash
uv run pytest tests/integration/test_checkpoints.py -v
```

Expected: ALL PASS in < 5 seconds

### Step 3: Commit

```bash
git add tests/integration/test_checkpoints.py
git commit -m "test: mock Claude SDK in checkpoints integration tests"
```

---

## Task 12: Mock test_sessions.py Integration Tests

**Files:**
- Modify: `tests/integration/test_sessions.py`

### Step 1: Add mock to all tests

```python
# tests/integration/test_sessions.py

@pytest.mark.integration
@pytest.mark.anyio
async def test_query_creates_session_that_can_be_resumed(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_claude_sdk: None,  # ADD THIS
) -> None:
    # Test implementation...
```

### Step 2: Run tests

```bash
uv run pytest tests/integration/test_sessions.py -v
```

Expected: ALL PASS in < 5 seconds

### Step 3: Commit

```bash
git add tests/integration/test_sessions.py
git commit -m "test: mock Claude SDK in sessions integration tests"
```

---

## Task 13: Create E2E Smoke Tests

**Files:**
- Create: `tests/e2e/test_smoke.py`
- Create: `README-TESTING.md`

### Step 1: Write E2E smoke tests

```python
# tests/e2e/test_smoke.py
"""End-to-end smoke tests with real Claude API calls.

These tests actually call Claude and should be run sparingly.
Run with: uv run pytest -m e2e
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.anyio
async def test_simple_query_e2e(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """E2E test: Simple query returns valid response."""
    response = await async_client.post(
        "/api/v1/query",
        json={"prompt": "Say 'test successful'"},
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Verify event structure
    events = []
    for line in response.text.strip().split("\n\n"):
        if line.startswith("event: "):
            event_type = line.split("event: ")[1].split("\n")[0]
            events.append(event_type)

    assert "init" in events
    assert "message" in events
    assert "result" in events
    assert "done" in events


@pytest.mark.e2e
@pytest.mark.anyio
async def test_query_with_tool_e2e(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """E2E test: Query with allowed tools."""
    response = await async_client.post(
        "/api/v1/query",
        json={
            "prompt": "List files in current directory",
            "allowed_tools": ["Glob", "Read"],
        },
        headers=auth_headers,
    )

    assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.anyio
async def test_session_resume_e2e(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """E2E test: Create session and resume it."""
    # Create session
    response1 = await async_client.post(
        "/api/v1/query",
        json={
            "prompt": "Say hello",
            "session_id": "e2e-session-001",
        },
        headers=auth_headers,
    )
    assert response1.status_code == 200

    # Resume session
    response2 = await async_client.post(
        f"/api/v1/sessions/e2e-session-001/resume",
        json={"prompt": "Say goodbye"},
        headers=auth_headers,
    )
    assert response2.status_code == 200


@pytest.mark.e2e
@pytest.mark.anyio
async def test_model_selection_e2e(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """E2E test: Query with different models."""
    for model in ["sonnet", "opus", "haiku"]:
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Say hello",
                "model": model,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.anyio
async def test_permission_mode_e2e(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """E2E test: Query with permission mode."""
    response = await async_client.post(
        "/api/v1/query",
        json={
            "prompt": "List files",
            "permission_mode": "plan",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
```

### Step 2: Run E2E tests to verify

```bash
uv run pytest -m e2e -v
```

Expected: ALL PASS (but slow, ~90 seconds total for 5 tests)

### Step 3: Create testing documentation

```markdown
# README-TESTING.md
# Testing Guide

## Test Categories

### Unit Tests (`-m unit`)
- **Speed**: Fast (< 5 seconds total)
- **Dependencies**: None (pure logic tests)
- **Run frequently**: After every code change

```bash
uv run pytest -m unit
```

### Integration Tests (`-m integration`)
- **Speed**: Fast (< 30 seconds total with mocking)
- **Dependencies**: Mocked Claude SDK, real database/Redis
- **Run frequently**: Before committing

```bash
uv run pytest -m integration
```

### E2E Tests (`-m e2e`)
- **Speed**: Slow (~90 seconds for 5 tests)
- **Dependencies**: Real Claude API, database, Redis
- **Run sparingly**: Before releases, after major changes
- **Cost**: Uses Claude API credits

```bash
uv run pytest -m e2e
```

## Default Test Run

By default, run all tests except E2E:

```bash
# Fast test run (unit + integration with mocks)
uv run pytest -m "not e2e"
```

## Test Coverage

```bash
# With coverage report
uv run pytest --cov=apps/api --cov-report=term-missing -m "not e2e"
```

## Parallel Execution

Tests use pytest-xdist for parallel execution (24 workers):

```bash
# Run with specific worker count
uv run pytest -n 8
```

## Test Performance

| Category | Count | Time | Cost |
|----------|-------|------|------|
| Unit | 354 | 4s | Free |
| Integration | 85 | 25s | Free (mocked) |
| E2E | 5 | 90s | Claude API credits |

## Writing New Tests

### Unit Test Template

```python
@pytest.mark.unit
def test_function_behavior():
    result = function(input)
    assert result == expected
```

### Integration Test Template

```python
@pytest.mark.integration
@pytest.mark.anyio
async def test_endpoint_behavior(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_claude_sdk: None,  # Mocks Claude API
) -> None:
    response = await async_client.post("/api/v1/query", ...)
    assert response.status_code == 200
```

### E2E Test Template

```python
@pytest.mark.e2e
@pytest.mark.anyio
async def test_real_behavior(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    # No mock_claude_sdk - this calls real Claude API
    response = await async_client.post("/api/v1/query", ...)
    assert response.status_code == 200
```

## CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Run fast tests
  run: uv run pytest -m "not e2e" --cov

- name: Run E2E smoke tests (main branch only)
  if: github.ref == 'refs/heads/main'
  run: uv run pytest -m e2e
```
```

### Step 4: Commit

```bash
git add tests/e2e/test_smoke.py README-TESTING.md
git commit -m "test: add E2E smoke tests and testing documentation"
```

---

## Task 14: Verify All Tests Pass

**Files:**
- None (verification task)

### Step 1: Run unit tests

```bash
uv run pytest -m unit -v
```

Expected: 354 PASSED in ~4 seconds

### Step 2: Run integration tests

```bash
uv run pytest -m integration -v
```

Expected: 85 PASSED in ~25 seconds (was ~1500 seconds before mocking!)

### Step 3: Run contract tests

```bash
uv run pytest tests/contract/ -v
```

Expected: ALL PASSED in ~5 seconds

### Step 4: Run all tests except E2E

```bash
uv run pytest -m "not e2e" --tb=short
```

Expected: 439+ PASSED in ~30 seconds total

### Step 5: Run E2E smoke tests

```bash
uv run pytest -m e2e -v
```

Expected: 5 PASSED in ~90 seconds

### Step 6: Generate coverage report

```bash
uv run pytest --cov=apps/api --cov-report=term-missing -m "not e2e"
```

Expected: Coverage > 80%

### Step 7: Document results

Create summary of improvements:

```bash
echo "# Test Performance Improvements

## Before Mocking
- Integration tests: ~1500 seconds (25 minutes)
- 85 real Claude API calls
- Expensive and unreliable

## After Mocking
- Integration tests: ~25 seconds (50x faster!)
- 0 Claude API calls in normal testing
- 5 E2E tests for smoke testing (~90 seconds)
- Total savings: ~1475 seconds per test run

## Commands
\`\`\`bash
# Fast tests (daily development)
uv run pytest -m \"not e2e\"  # 30 seconds

# E2E smoke tests (before releases)
uv run pytest -m e2e  # 90 seconds
\`\`\`
" > .docs/test-performance-improvements.md
```

### Step 8: Final commit

```bash
git add .docs/test-performance-improvements.md
git commit -m "docs: document test performance improvements"
```

---

## Summary

**Total Tasks**: 14
**Estimated Time**: 3-4 hours
**Performance Gain**: 50x faster integration tests (1500s → 25s)
**Cost Savings**: 85 Claude API calls → 0 per test run
**E2E Coverage**: 5 smoke tests for critical paths

**Key Files Modified**:
- `tests/conftest.py` - Added mock fixtures
- `tests/integration/*.py` - Added mocks to all integration tests (10 files)
- `tests/e2e/test_smoke.py` - New E2E test suite
- `pyproject.toml` - Added pytest markers
- `README-TESTING.md` - Testing documentation

**Related Skills**:
- @superpowers:test-driven-development - For writing failing tests first
- @superpowers:verification-before-completion - For verifying tests pass
