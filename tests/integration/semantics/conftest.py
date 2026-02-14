"""Shared fixtures for Phase 2 semantic tests.

SSE Event Types Reference
--------------------------
The query streaming endpoints emit the following SSE event types:

- ``init``    - Session initialization (session_id, model, tools, mcp_servers, plugins, commands, permission_mode)
- ``message`` - Agent message (type: user/assistant/system, content blocks, model, usage)
- ``question``- AskUserQuestion tool use (tool_use_id, question, session_id)
- ``partial`` - Streaming content deltas (content_block_start/delta/stop with index)
- ``todo``    - TodoWrite tracking (todos list)
- ``result``  - Final result (session_id, is_error, duration_ms, num_turns, cost, usage)
- ``error``   - Mid-stream error (code, message, optional details)
- ``done``    - Stream completion (reason: completed/interrupted/error)

Typical happy-path sequence::

    init -> [partial...] -> [message...] -> result -> done
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, TypedDict
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from httpx import AsyncClient, Response

# Required fields per SSE event type, used by validate_sse_event_data fixture.
# Maps event name -> set of required top-level keys in event.data.
SSE_EVENT_REQUIRED_FIELDS: dict[str, set[str]] = {
    "init": {"session_id", "model"},
    "message": {"type", "content"},
    "question": {"tool_use_id", "question", "session_id"},
    "partial": {"type", "index"},
    "todo": {"todos"},
    "result": {"session_id", "is_error", "duration_ms", "num_turns"},
    "error": {"code", "message"},
    "done": {"reason"},
}

# Valid values for enum-like fields within SSE events.
SSE_EVENT_VALID_VALUES: dict[str, dict[str, set[str]]] = {
    "message": {"type": {"user", "assistant", "system"}},
    "partial": {
        "type": {"content_block_start", "content_block_delta", "content_block_stop"}
    },
    "done": {"reason": {"completed", "interrupted", "error"}},
    "result": {
        "stop_reason": {"completed", "max_turns_reached", "interrupted", "error"},
    },
}


class SseEvent(TypedDict):
    """SSE event structure.

    Attributes:
        event: The event type name (init, message, partial, result, error, done, etc.).
        data: Parsed JSON data payload for the event.
    """

    event: str
    data: dict[str, object]


@pytest.fixture
def second_api_key() -> str:
    """Second API key for cross-tenant isolation tests."""
    return f"test-api-key-{uuid4().hex[:8]}"


@pytest.fixture
def second_auth_headers(second_api_key: str) -> dict[str, str]:
    """Auth headers for second tenant."""
    return {"X-API-Key": second_api_key}


@pytest.fixture
def sse_event_collector() -> Callable[[Response], Awaitable[list[SseEvent]]]:
    """Helper to collect and validate SSE events from streaming responses."""

    async def collect_events(response: Response) -> list[SseEvent]:
        """Parse SSE stream and return list of events.

        Args:
            response: HTTP response with SSE stream

        Returns:
            List of SseEvent dicts
        """
        events: list[SseEvent] = []
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


@pytest.fixture
def validate_sse_sequence() -> Callable[[list[SseEvent], list[str]], None]:
    """Validate SSE event sequence matches expected pattern."""

    def validate(events: list[SseEvent], expected_sequence: list[str]) -> None:
        """Assert events follow expected order.

        Args:
            events: List of SseEvent dicts
            expected_sequence: List of event names in order
        """
        actual_sequence = [e["event"] for e in events]
        assert actual_sequence == expected_sequence, (
            f"Event sequence mismatch.\n"
            f"Expected: {expected_sequence}\n"
            f"Actual: {actual_sequence}"
        )

    return validate


@pytest.fixture
def validate_sse_event_data() -> Callable[[SseEvent], None]:
    """Validate that an SSE event's data contains the required fields for its type.

    Checks both required fields and enum value constraints. Unknown event types
    are silently accepted (forward-compatible).

    Usage::

        def test_init_event(validate_sse_event_data):
            event: SseEvent = {"event": "init", "data": {"session_id": "abc", "model": "sonnet"}}
            validate_sse_event_data(event)  # passes

            bad: SseEvent = {"event": "init", "data": {"model": "sonnet"}}
            validate_sse_event_data(bad)  # fails: missing session_id
    """

    def validate(event: SseEvent) -> None:
        """Assert event data has required fields and valid enum values.

        Args:
            event: Single SSE event to validate.
        """
        event_type = event["event"]
        data = event["data"]

        # Check required fields
        required = SSE_EVENT_REQUIRED_FIELDS.get(event_type)
        if required is not None:
            missing = required - set(data.keys())
            assert not missing, (
                f"Event '{event_type}' missing required fields: {missing}\n"
                f"Got keys: {set(data.keys())}"
            )

        # Check enum constraints on present fields
        valid_values = SSE_EVENT_VALID_VALUES.get(event_type, {})
        for field_name, allowed in valid_values.items():
            value = data.get(field_name)
            if value is not None:
                assert value in allowed, (
                    f"Event '{event_type}' field '{field_name}' has invalid value: {value!r}\n"
                    f"Allowed: {allowed}"
                )

    return validate


@pytest.fixture
def validate_all_sse_events() -> Callable[[list[SseEvent]], None]:
    """Validate data structures for every event in a list.

    Convenience wrapper that calls validate_sse_event_data on each event.

    Usage::

        def test_stream(sse_event_collector, validate_all_sse_events):
            events = await sse_event_collector(response)
            validate_all_sse_events(events)
    """

    def validate(events: list[SseEvent]) -> None:
        """Assert all events have valid data structures.

        Args:
            events: List of SSE events to validate.
        """
        for i, event in enumerate(events):
            event_type = event["event"]
            data = event["data"]

            required = SSE_EVENT_REQUIRED_FIELDS.get(event_type)
            if required is not None:
                missing = required - set(data.keys())
                assert not missing, (
                    f"Event #{i} '{event_type}' missing required fields: {missing}\n"
                    f"Got keys: {set(data.keys())}"
                )

            valid_values = SSE_EVENT_VALID_VALUES.get(event_type, {})
            for field_name, allowed in valid_values.items():
                value = data.get(field_name)
                if value is not None:
                    assert value in allowed, (
                        f"Event #{i} '{event_type}' field '{field_name}' "
                        f"has invalid value: {value!r}\n"
                        f"Allowed: {allowed}"
                    )

    return validate


@pytest.fixture
def sse_event_collector_with_timeout() -> Callable[
    [AsyncClient, str, dict[str, str], dict[str, object], float],
    Awaitable[list[SseEvent]],
]:
    """Collect SSE events from a streaming POST request with timeout protection.

    Prevents tests from hanging indefinitely on slow or stuck SSE streams.
    Uses httpx's async streaming context manager for proper resource cleanup.

    Usage::

        async def test_query_stream(sse_event_collector_with_timeout, auth_headers):
            events = await sse_event_collector_with_timeout(
                async_client, "/api/v1/query", auth_headers,
                {"prompt": "hello"}, timeout=10.0,
            )
            assert len(events) > 0
    """

    async def collect(
        client: AsyncClient,
        url: str,
        headers: dict[str, str],
        json_body: dict[str, object],
        timeout: float = 30.0,
    ) -> list[SseEvent]:
        """Stream a POST request and collect SSE events with timeout.

        Args:
            client: Async HTTP client.
            url: Endpoint URL.
            headers: Request headers (must include auth).
            json_body: JSON request body.
            timeout: Maximum seconds to wait for stream completion.

        Returns:
            List of parsed SSE events.

        Raises:
            TimeoutError: If stream does not complete within timeout.
        """
        events: list[SseEvent] = []
        event_type: str | None = None

        async def _stream() -> None:
            nonlocal event_type
            async with client.stream(
                "POST", url, json=json_body, headers=headers
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("event:"):
                        event_type = line.split(":", 1)[1].strip()
                    elif line.startswith("data:"):
                        raw = line.split(":", 1)[1].strip()
                        try:
                            data = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        if event_type:
                            events.append({"event": event_type, "data": data})
                            event_type = None

        try:
            await asyncio.wait_for(_stream(), timeout=timeout)
        except TimeoutError:
            raise TimeoutError(
                f"SSE stream did not complete within {timeout}s. "
                f"Collected {len(events)} events so far: "
                f"{[e['event'] for e in events]}"
            ) from None

        return events

    return collect


@pytest.fixture
def aggregate_partial_text() -> Callable[[list[SseEvent]], str]:
    """Aggregate text from partial SSE events into a single string.

    Extracts text deltas from ``partial`` events with type ``content_block_delta``
    and concatenates them in order.

    Usage::

        def test_streaming_text(aggregate_partial_text):
            events = [...]  # collected SSE events
            full_text = aggregate_partial_text(events)
            assert "expected content" in full_text
    """

    def aggregate(events: list[SseEvent]) -> str:
        """Concatenate text deltas from partial events.

        Args:
            events: List of SSE events (filters to partial events internally).

        Returns:
            Concatenated text from all content_block_delta events.
        """
        parts: list[str] = []
        for event in events:
            if event["event"] != "partial":
                continue
            data = event["data"]
            if data.get("type") != "content_block_delta":
                continue
            delta = data.get("delta")
            if isinstance(delta, dict):
                text = delta.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)

    return aggregate


@pytest.fixture
def find_sse_event() -> Callable[[list[SseEvent], str], SseEvent | None]:
    """Find the first SSE event matching a given event type.

    Usage::

        def test_has_init(find_sse_event):
            init = find_sse_event(events, "init")
            assert init is not None
            assert init["data"]["session_id"]
    """

    def find(events: list[SseEvent], event_type: str) -> SseEvent | None:
        """Return first event matching type, or None.

        Args:
            events: List of SSE events to search.
            event_type: Event type name to find.

        Returns:
            First matching event or None.
        """
        for event in events:
            if event["event"] == event_type:
                return event
        return None

    return find


@pytest.fixture
def filter_sse_events() -> Callable[[list[SseEvent], str], list[SseEvent]]:
    """Filter SSE events by event type.

    Usage::

        def test_message_count(filter_sse_events):
            messages = filter_sse_events(events, "message")
            assert len(messages) >= 1
    """

    def _filter(events: list[SseEvent], event_type: str) -> list[SseEvent]:
        """Return all events matching the given type.

        Args:
            events: List of SSE events to filter.
            event_type: Event type name to match.

        Returns:
            Filtered list of matching events.
        """
        return [e for e in events if e["event"] == event_type]

    return _filter


@pytest.fixture
def validate_sse_sequence_contains() -> Callable[[list[SseEvent], list[str]], None]:
    """Validate SSE event sequence contains required events in order (non-strict).

    Unlike ``validate_sse_sequence`` which requires exact match, this validates
    that the required events appear in the correct relative order, allowing
    other events between them.

    Usage::

        def test_stream_has_bookends(validate_sse_sequence_contains):
            # Validates init comes before result, result before done
            # Allows any events between them (partial, message, etc.)
            validate_sse_sequence_contains(events, ["init", "result", "done"])
    """

    def validate(events: list[SseEvent], required_sequence: list[str]) -> None:
        """Assert required events appear in order within the event list.

        Args:
            events: List of SSE events.
            required_sequence: Event types that must appear in this order.
        """
        actual_types = [e["event"] for e in events]
        search_from = 0
        for required_type in required_sequence:
            found = False
            for i in range(search_from, len(actual_types)):
                if actual_types[i] == required_type:
                    search_from = i + 1
                    found = True
                    break
            assert found, (
                f"Required event '{required_type}' not found in expected order.\n"
                f"Required sequence: {required_sequence}\n"
                f"Actual sequence: {actual_types}"
            )

    return validate


@pytest.fixture
async def mock_session_other_tenant(
    async_client: AsyncClient,
    second_auth_headers: dict[str, str],
) -> str:
    """Create session owned by second tenant for isolation tests."""
    from fastapi import Request

    from apps.api.adapters.session_repo import SessionRepository
    from apps.api.dependencies import get_app_state
    from apps.api.services.session import SessionService

    # Get app state from test client
    request = Request(scope={"type": "http", "app": async_client._transport.app})  # type: ignore[arg-type]
    app_state = get_app_state(request)

    assert app_state.cache is not None, "Cache must be initialized"
    assert app_state.session_maker is not None, "Session maker must be initialized"

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


@pytest.fixture
async def mock_project_other_tenant(
    async_client: AsyncClient,
    second_auth_headers: dict[str, str],
) -> dict[str, object]:
    """Create project owned by second tenant for isolation tests.

    NOTE: Projects do not yet support multi-tenant isolation (no owner_api_key).
    This fixture creates a project via service layer to prepare for future isolation.
    When multi-tenant support is added, the test will validate 404 behavior.
    """
    from fastapi import Request

    from apps.api.dependencies import get_app_state
    from apps.api.services.projects import ProjectService

    # Get app state from test client
    request = Request(scope={"type": "http", "app": async_client._transport.app})  # type: ignore[arg-type]
    app_state = get_app_state(request)

    assert app_state.cache is not None, "Cache must be initialized"

    # Create project for second tenant
    suffix = uuid4().hex[:8]
    name = f"isolation-project-{suffix}"
    path = f"/tmp/isolation-project-{suffix}"

    service = ProjectService(cache=app_state.cache)
    project = await service.create_project(name=name, path=path, metadata=None)

    assert project is not None, "Project creation failed"

    return {
        "id": project.id,
        "name": project.name,
        "path": project.path,
        "created_at": project.created_at,
        "last_accessed_at": project.last_accessed_at,
        "session_count": project.session_count,
        "metadata": project.metadata,
    }


@pytest.fixture
async def mock_memory_other_tenant(
    async_client: AsyncClient,
    second_auth_headers: dict[str, str],
) -> dict[str, str]:
    """Create memory owned by second tenant for isolation tests.

    Single attempt with immediate skip on external service failure.
    This prevents test timeouts from retry+backoff loops.
    """
    from fastapi import Request

    from apps.api.dependencies import get_app_state, get_memory_service
    from apps.api.utils.crypto import hash_api_key

    # Get app state from test client
    request = Request(scope={"type": "http", "app": async_client._transport.app})  # type: ignore[arg-type]
    app_state = get_app_state(request)

    # Get memory service from DI (singleton pattern)
    service = await get_memory_service(app_state)

    # Create memory for second tenant (single attempt, skip on failure)
    memory_content = f"Isolation test memory {uuid4().hex[:8]}"
    user_id = hash_api_key(second_auth_headers["X-API-Key"])

    try:
        results = await service.add_memory(
            messages=memory_content,
            user_id=user_id,
            metadata=None,
            enable_graph=False,
        )
    except Exception as exc:
        error_msg = str(exc)
        if "429" in error_msg or "rate" in error_msg.lower():
            pytest.skip(f"External LLM rate-limited: {exc}")
        if "Collection" in error_msg and "already exists" in error_msg:
            pytest.skip(f"Qdrant collection conflict: {exc}")
        raise

    if len(results) == 0:
        pytest.skip("Mem0 returned empty result (LLM likely rate-limited)")

    # Type narrowing: validate fields before accessing
    first_result = results[0]
    memory_id = first_result["id"]
    memory_text = first_result["memory"]

    assert isinstance(memory_id, str), "Memory ID must be a string"
    assert isinstance(memory_text, str), "Memory text must be a string"

    return {"id": memory_id, "content": memory_text}


@pytest.fixture
async def mock_session(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> str:
    """Create a session for the primary tenant for CRUD tests.

    Args:
        async_client: HTTP client for API requests.
        auth_headers: Auth headers with API key.

    Returns:
        Session ID string.
    """
    from fastapi import Request

    from apps.api.adapters.session_repo import SessionRepository
    from apps.api.dependencies import get_app_state
    from apps.api.services.session import SessionService

    # Get app state from test client
    request = Request(scope={"type": "http", "app": async_client._transport.app})  # type: ignore[arg-type]
    app_state = get_app_state(request)

    assert app_state.cache is not None, "Cache must be initialized"
    assert app_state.session_maker is not None, "Session maker must be initialized"

    # Create session for primary tenant
    async with app_state.session_maker() as db_session:
        repo = SessionRepository(db_session)
        service = SessionService(cache=app_state.cache, db_repo=repo)
        session = await service.create_session(
            model="sonnet",
            session_id=str(uuid4()),
            owner_api_key=auth_headers["X-API-Key"],
        )
        return session.id


@pytest.fixture
async def mock_memory(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> dict[str, str]:
    """Create a memory via API for CRUD tests.

    Single attempt with immediate skip on external service failure.
    This prevents test timeouts from retry+backoff loops.

    Args:
        async_client: HTTP client for API requests.
        auth_headers: Auth headers with API key.

    Returns:
        Dict with 'id' and 'content' of the created memory.
    """
    suffix = uuid4().hex[:8]
    memory_content = f"Test memory for semantics testing {suffix}"

    try:
        response = await async_client.post(
            "/api/v1/memories",
            json={
                "messages": memory_content,
                "enable_graph": False,
            },
            headers=auth_headers,
        )
    except Exception as exc:
        error_msg = str(exc)
        if "429" in error_msg or "rate" in error_msg.lower():
            pytest.skip(f"External LLM rate-limited: {exc}")
        raise

    # Skip on external service failures
    if response.status_code == 500:
        body = response.text
        if "429" in body or "rate" in body.lower():
            pytest.skip("External LLM rate-limited (429)")
        if "Collection" in body and "already exists" in body:
            pytest.skip("Qdrant collection conflict (concurrent Mem0 init)")
        # Re-raise unexpected 500s
        pytest.fail(f"Unexpected 500 from memory API: {body[:200]}")

    assert response.status_code == 201, f"Memory creation failed: {response.text}"

    data = response.json()
    # Type narrowing: validate structure before accessing
    assert isinstance(data, dict), "Response data must be a dict"
    count = data.get("count", 0)
    assert isinstance(count, int), "count must be an int"

    if count == 0:
        pytest.skip("Mem0 returned empty result (LLM likely rate-limited)")

    memories = data.get("memories")
    assert isinstance(memories, list), "memories must be a list"
    assert len(memories) > 0, "memories list must not be empty"

    first_memory = memories[0]
    assert isinstance(first_memory, dict), "memory must be a dict"

    memory_id = first_memory.get("id")
    memory_text = first_memory.get("memory")
    assert isinstance(memory_id, str), "id must be a string"
    assert isinstance(memory_text, str), "memory must be a string"

    return {"id": memory_id, "content": memory_text}


@pytest.fixture
async def mock_project(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> dict[str, object]:
    """Create a test project via API for CRUD tests.

    Args:
        async_client: HTTP client for API requests
        auth_headers: Auth headers with API key

    Returns:
        Project data dict containing id, name, metadata, etc.
    """
    suffix = uuid4().hex[:8]
    response = await async_client.post(
        "/api/v1/projects",
        json={
            "name": f"test-project-{suffix}",
            "metadata": {"purpose": "semantics-testing"},
        },
        headers=auth_headers,
    )

    assert response.status_code == 201, f"Project creation failed: {response.text}"
    return response.json()


@pytest.fixture
async def mock_mcp_server(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> dict[str, object]:
    """Create a test MCP server config via API for CRUD tests.

    Args:
        async_client: HTTP client for API requests.
        auth_headers: Auth headers with API key.

    Returns:
        MCP server data dict containing id, name, transport_type, etc.
    """
    suffix = uuid4().hex[:8]
    response = await async_client.post(
        "/api/v1/mcp-servers",
        json={
            "name": f"test-mcp-{suffix}",
            "type": "stdio",
            "config": {
                "command": "echo",
                "args": ["hello"],
            },
        },
        headers=auth_headers,
    )

    assert response.status_code == 201, f"MCP server creation failed: {response.text}"
    return response.json()
