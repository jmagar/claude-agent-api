"""Shared fixtures for Phase 2 semantic tests."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, TypedDict
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from httpx import AsyncClient, Response


class SseEvent(TypedDict):
    """SSE event structure."""

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
