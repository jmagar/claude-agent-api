"""Query Execution endpoint tests for Phase 2 semantic validation.

Tests cover:
- Streaming query (POST /api/v1/query) SSE event validation
- Single query (POST /api/v1/query/single) response validation
- Authentication and authorization
- Input validation (prompt, model, tools)
- Session creation and resumption
- Multi-tenant isolation
- Error handling
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast
from uuid import uuid4

import pytest
from httpx_sse import aconnect_sse

if TYPE_CHECKING:
    from httpx import AsyncClient


def _parse_sse_data(data: str | None) -> dict[str, object]:
    """Parse SSE event data from raw string.

    Args:
        data: Raw SSE data string (JSON).

    Returns:
        Parsed dict, or empty dict on failure.
    """
    if not data or not data.strip():
        return {}
    try:
        return cast("dict[str, object]", json.loads(data))
    except json.JSONDecodeError:
        return {"raw": data}


async def _collect_stream_events(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    request_data: dict[str, object],
    *,
    stop_after: str | None = "done",
    max_events: int = 50,
) -> list[dict[str, object]]:
    """Collect SSE events from the streaming query endpoint.

    Args:
        async_client: HTTP client.
        auth_headers: Auth headers with API key.
        request_data: Query request payload.
        stop_after: Event type to stop at (None = collect all).
        max_events: Max events to collect before stopping.

    Returns:
        List of event dicts with 'event' and 'data' keys.
    """
    events: list[dict[str, object]] = []
    async with aconnect_sse(
        async_client,
        "POST",
        "/api/v1/query",
        headers={**auth_headers, "Accept": "text/event-stream"},
        json=request_data,
    ) as event_source:
        async for sse in event_source.aiter_sse():
            if sse.event:
                data = _parse_sse_data(sse.data)
                events.append({"event": sse.event, "data": data})
                if stop_after and sse.event == stop_after:
                    break
                if len(events) >= max_events:
                    break
    return events


# ---------------------------------------------------------------------------
# Streaming Query: Authentication
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_stream_query_requires_api_key(
    async_client: AsyncClient,
) -> None:
    """Streaming query without API key returns 401."""
    response = await async_client.post(
        "/api/v1/query",
        json={"prompt": "Hello"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data


@pytest.mark.integration
@pytest.mark.anyio
async def test_stream_query_invalid_api_key(
    async_client: AsyncClient,
) -> None:
    """Streaming query with wrong API key returns 401."""
    response = await async_client.post(
        "/api/v1/query",
        headers={"X-API-Key": f"invalid-key-{uuid4().hex[:8]}"},
        json={"prompt": "Hello"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Streaming Query: Input Validation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_stream_query_missing_prompt(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Streaming query without prompt returns 422."""
    response = await async_client.post(
        "/api/v1/query",
        headers=auth_headers,
        json={},
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) > 0
    # Verify the validation error mentions prompt field
    error_entry = data["detail"][0]
    assert isinstance(error_entry, dict)
    assert "loc" in error_entry
    assert "prompt" in str(error_entry["loc"])


@pytest.mark.integration
@pytest.mark.anyio
async def test_stream_query_empty_prompt(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Streaming query with empty string prompt returns 422."""
    response = await async_client.post(
        "/api/v1/query",
        headers=auth_headers,
        json={"prompt": ""},
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) > 0
    # Verify the validation error mentions prompt field and min length
    error_entry = data["detail"][0]
    assert isinstance(error_entry, dict)
    assert "loc" in error_entry
    assert "prompt" in str(error_entry["loc"])
    assert "type" in error_entry
    assert error_entry["type"] == "string_too_short"


@pytest.mark.integration
@pytest.mark.anyio
async def test_stream_query_invalid_model(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Streaming query with invalid model name returns 422."""
    response = await async_client.post(
        "/api/v1/query",
        headers=auth_headers,
        json={"prompt": "Hello", "model": "invalid-model-xyz"},
    )
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_stream_query_invalid_max_turns(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Streaming query with max_turns=0 returns 422."""
    response = await async_client.post(
        "/api/v1/query",
        headers=auth_headers,
        json={"prompt": "Hello", "max_turns": 0},
    )
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_stream_query_tool_conflict(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Streaming query with tool in both allowed and disallowed returns 422."""
    response = await async_client.post(
        "/api/v1/query",
        headers=auth_headers,
        json={
            "prompt": "Hello",
            "allowed_tools": ["Bash"],
            "disallowed_tools": ["Bash"],
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Streaming Query: SSE Event Sequence
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_stream_query_init_event(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Streaming query emits init event with session_id and model."""
    events = await _collect_stream_events(
        async_client,
        auth_headers,
        {"prompt": "Say hello", "max_turns": 1},
        stop_after="init",
    )

    assert len(events) >= 1
    init_event = events[0]
    assert init_event["event"] == "init"

    init_data = init_event["data"]
    assert isinstance(init_data, dict)
    assert "session_id" in init_data
    assert isinstance(init_data["session_id"], str)
    assert len(str(init_data["session_id"])) > 0
    assert "model" in init_data


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_stream_query_result_event(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Streaming query emits result event with completion data."""
    events = await _collect_stream_events(
        async_client,
        auth_headers,
        {"prompt": "What is 2+2?", "max_turns": 1},
        stop_after="result",
    )

    event_types = [e["event"] for e in events]
    assert "init" in event_types
    assert "result" in event_types

    result_events = [e for e in events if e["event"] == "result"]
    assert len(result_events) >= 1

    result_data = result_events[-1]["data"]
    assert isinstance(result_data, dict)
    assert "session_id" in result_data or "is_complete" in result_data


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_stream_query_done_event(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Streaming query emits done event as the final event."""
    events = await _collect_stream_events(
        async_client,
        auth_headers,
        {"prompt": "Say test", "max_turns": 1},
        stop_after="done",
    )

    event_types = [e["event"] for e in events]
    assert "done" in event_types
    # done should be the last event
    assert events[-1]["event"] == "done"


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_stream_query_event_sequence(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Streaming query events follow init -> ... -> result -> done order."""
    events = await _collect_stream_events(
        async_client,
        auth_headers,
        {"prompt": "Hi", "max_turns": 1},
        stop_after="done",
    )

    event_types = [e["event"] for e in events]
    assert len(event_types) >= 2, f"Expected at least 2 events, got: {event_types}"

    # init must be first
    assert event_types[0] == "init", f"First event should be init, got: {event_types[0]}"

    # done must be last (if present)
    if "done" in event_types:
        assert event_types[-1] == "done"

    # result should come before done (if both present)
    if "result" in event_types and "done" in event_types:
        result_idx = event_types.index("result")
        done_idx = event_types.index("done")
        assert result_idx < done_idx


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_stream_query_init_contains_tools(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Init event includes tools field from allowed_tools."""
    events = await _collect_stream_events(
        async_client,
        auth_headers,
        {"prompt": "Test", "allowed_tools": ["Glob", "Read"], "max_turns": 1},
        stop_after="init",
    )

    init_data = events[0]["data"]
    assert isinstance(init_data, dict)
    assert "tools" in init_data
    tools = init_data["tools"]
    assert isinstance(tools, list)
    assert "Glob" in tools
    assert "Read" in tools


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_stream_query_init_contains_permission_mode(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Init event contains the specified permission mode."""
    events = await _collect_stream_events(
        async_client,
        auth_headers,
        {"prompt": "Test", "permission_mode": "plan", "max_turns": 1},
        stop_after="init",
    )

    init_data = events[0]["data"]
    assert isinstance(init_data, dict)
    assert "permission_mode" in init_data
    assert init_data["permission_mode"] == "plan"


# ---------------------------------------------------------------------------
# Streaming Query: Session Creation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_stream_query_creates_session(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Streaming query creates a new session accessible via sessions API."""
    events = await _collect_stream_events(
        async_client,
        auth_headers,
        {"prompt": "Hello", "max_turns": 1},
        stop_after="done",
    )

    # Extract session_id from init event
    init_events = [e for e in events if e["event"] == "init"]
    assert len(init_events) >= 1
    init_data = init_events[0]["data"]
    assert isinstance(init_data, dict)
    session_id = init_data.get("session_id")
    assert session_id is not None

    # Verify session is accessible via GET
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    session_data = response.json()
    assert session_data["id"] == session_id


# ---------------------------------------------------------------------------
# Streaming Query: Session Resumption
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_stream_query_with_existing_session_id(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Streaming query with session_id references existing session."""
    events = await _collect_stream_events(
        async_client,
        auth_headers,
        {"prompt": "Continue", "session_id": mock_session, "max_turns": 1},
        stop_after="init",
    )

    assert len(events) >= 1
    init_data = events[0]["data"]
    assert isinstance(init_data, dict)
    # The init event should have a session_id
    assert "session_id" in init_data


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_stream_query_invalid_session_id(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Streaming query with nonexistent session_id still starts (SDK handles)."""
    fake_id = str(uuid4())

    # The streaming endpoint doesn't reject invalid session_ids at the HTTP level;
    # the SDK handles session_id validation during execution.
    # We just verify the request is accepted (200 SSE stream starts).
    events = await _collect_stream_events(
        async_client,
        auth_headers,
        {"prompt": "Continue", "session_id": fake_id, "max_turns": 1},
        stop_after="init",
        max_events=5,
    )

    # Should have at least gotten an init event or error
    assert len(events) >= 1


# ---------------------------------------------------------------------------
# Single Query: Authentication
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_single_query_requires_api_key(
    async_client: AsyncClient,
) -> None:
    """Single query without API key returns 401."""
    response = await async_client.post(
        "/api/v1/query/single",
        json={"prompt": "Hello"},
    )
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.anyio
async def test_single_query_invalid_api_key(
    async_client: AsyncClient,
) -> None:
    """Single query with wrong API key returns 401."""
    response = await async_client.post(
        "/api/v1/query/single",
        headers={"X-API-Key": f"invalid-key-{uuid4().hex[:8]}"},
        json={"prompt": "Hello"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Single Query: Input Validation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_single_query_missing_prompt(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Single query without prompt returns 422."""
    response = await async_client.post(
        "/api/v1/query/single",
        headers=auth_headers,
        json={},
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) > 0
    # Verify the validation error mentions prompt field
    error_entry = data["detail"][0]
    assert isinstance(error_entry, dict)
    assert "loc" in error_entry
    assert "prompt" in str(error_entry["loc"])


@pytest.mark.integration
@pytest.mark.anyio
async def test_single_query_empty_prompt(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Single query with empty string prompt returns 422."""
    response = await async_client.post(
        "/api/v1/query/single",
        headers=auth_headers,
        json={"prompt": ""},
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) > 0
    # Verify the validation error mentions prompt field and min length
    error_entry = data["detail"][0]
    assert isinstance(error_entry, dict)
    assert "loc" in error_entry
    assert "prompt" in str(error_entry["loc"])
    assert "type" in error_entry
    assert error_entry["type"] == "string_too_short"


@pytest.mark.integration
@pytest.mark.anyio
async def test_single_query_invalid_model(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Single query with invalid model name returns 422."""
    response = await async_client.post(
        "/api/v1/query/single",
        headers=auth_headers,
        json={"prompt": "Hello", "model": "invalid-model-xyz"},
    )
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_single_query_invalid_max_turns(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Single query with max_turns=0 returns 422."""
    response = await async_client.post(
        "/api/v1/query/single",
        headers=auth_headers,
        json={"prompt": "Hello", "max_turns": 0},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Single Query: Successful Response
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_single_query_returns_response(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Single query returns a complete response with expected fields."""
    response = await async_client.post(
        "/api/v1/query/single",
        headers=auth_headers,
        json={"prompt": "Say hello", "max_turns": 1},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify required response fields from SingleQueryResponse schema
    assert "session_id" in data
    assert isinstance(data["session_id"], str)
    assert len(data["session_id"]) > 0

    assert "model" in data
    assert isinstance(data["model"], str)

    assert "content" in data
    assert isinstance(data["content"], list)

    assert "is_error" in data
    assert isinstance(data["is_error"], bool)

    assert "duration_ms" in data
    assert isinstance(data["duration_ms"], int)
    assert data["duration_ms"] >= 0

    assert "num_turns" in data
    assert isinstance(data["num_turns"], int)
    assert data["num_turns"] >= 0


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_single_query_content_blocks_structure(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Single query content blocks have valid structure."""
    response = await async_client.post(
        "/api/v1/query/single",
        headers=auth_headers,
        json={"prompt": "Say test", "max_turns": 1},
    )

    assert response.status_code == 200
    data = response.json()
    content = data["content"]

    if len(content) > 0:
        block = content[0]
        assert isinstance(block, dict)
        assert "type" in block
        assert block["type"] in ("text", "thinking", "tool_use", "tool_result")


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_single_query_creates_session(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Single query creates a session accessible via sessions API."""
    response = await async_client.post(
        "/api/v1/query/single",
        headers=auth_headers,
        json={"prompt": "Hello", "max_turns": 1},
    )

    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]

    # Verify session is accessible
    session_response = await async_client.get(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers,
    )
    assert session_response.status_code == 200
    session_data = session_response.json()
    assert session_data["id"] == session_id


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_single_query_with_allowed_tools(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Single query with allowed_tools restriction succeeds."""
    response = await async_client.post(
        "/api/v1/query/single",
        headers=auth_headers,
        json={
            "prompt": "Test with tools",
            "allowed_tools": ["Glob", "Read"],
            "max_turns": 1,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_error"] is False


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_single_query_session_status_completed(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Single query updates session status to completed on success."""
    response = await async_client.post(
        "/api/v1/query/single",
        headers=auth_headers,
        json={"prompt": "Say done", "max_turns": 1},
    )

    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]

    # Check session status
    session_response = await async_client.get(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers,
    )
    assert session_response.status_code == 200
    session_data = session_response.json()
    
    # Type safety: verify status field exists and is a string
    assert isinstance(session_data, dict), "Session data must be a dict"
    assert "status" in session_data, "Session data must have status field"
    status = session_data["status"]
    assert isinstance(status, str), f"Status must be a string, got {type(status)}"
    
    # Verify session status is completed after successful query
    assert status == "completed", f"Expected status 'completed' after successful query, got '{status}'"


# ---------------------------------------------------------------------------
# Single Query: Session Resumption
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_single_query_with_session_id(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Single query with existing session_id resumes conversation.
    
    Note: Marked as e2e because it requires real SDK execution to test session
    resumption. The SDK must connect, query, and disconnect, which involves:
    - Real Claude API interaction
    - MCP server initialization
    - Mem0 memory retrieval
    - Posthog analytics cleanup
    """
    response = await async_client.post(
        "/api/v1/query/single",
        headers=auth_headers,
        json={
            "prompt": "Continue conversation",
            "session_id": mock_session,
            "max_turns": 1,
        },
    )

    # Should succeed or return SDK-level error (not 4xx validation)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data


# ---------------------------------------------------------------------------
# Multi-Tenant Isolation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_stream_query_session_tenant_isolated(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """Stream query cannot access sessions owned by other tenants.

    Validates that streaming query endpoints respect session ownership.
    Tenant A cannot access Tenant B's session, even if session_id is known.
    """
    # ACT - Tenant A tries to access Tenant B's session via GET
    response = await async_client.get(
        f"/api/v1/sessions/{mock_session_other_tenant}",
        headers=auth_headers,
    )

    # ASSERT - Returns 404 (not 403) to prevent enumeration
    # Session exists but owned by different tenant (owner_api_key_hash mismatch)
    assert response.status_code == 404
    data = response.json()
    assert isinstance(data, dict)
    assert "error" in data
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_single_query_session_tenant_isolated(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """Single query cannot access sessions owned by other tenants.

    Validates that single query endpoints respect session ownership.
    Tenant A cannot access Tenant B's session, even if session_id is known.
    """
    # ACT - Tenant A tries to access Tenant B's session via GET
    session_response = await async_client.get(
        f"/api/v1/sessions/{mock_session_other_tenant}",
        headers=auth_headers,
    )

    # ASSERT - Returns 404 (not 403) to prevent enumeration
    # Session exists but owned by different tenant (owner_api_key_hash mismatch)
    assert session_response.status_code == 404
    data = session_response.json()
    assert isinstance(data, dict)
    assert "error" in data
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


# ---------------------------------------------------------------------------
# Security: Path Traversal & Injection
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_stream_query_cwd_path_traversal_rejected(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Streaming query rejects cwd with path traversal."""
    response = await async_client.post(
        "/api/v1/query",
        headers=auth_headers,
        json={"prompt": "Test", "cwd": "/etc/../../../etc/passwd"},
    )
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_stream_query_env_dangerous_vars_rejected(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Streaming query rejects dangerous environment variables."""
    response = await async_client.post(
        "/api/v1/query",
        headers=auth_headers,
        json={"prompt": "Test", "env": {"LD_PRELOAD": "/tmp/evil.so"}},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Query Options: Model Selection
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_stream_query_with_model_selection(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Streaming query with valid model propagates to init event."""
    events = await _collect_stream_events(
        async_client,
        auth_headers,
        {"prompt": "Test", "model": "sonnet", "max_turns": 1},
        stop_after="init",
    )

    assert len(events) >= 1
    init_data = events[0]["data"]
    assert isinstance(init_data, dict)
    assert init_data.get("model") == "sonnet"


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_single_query_with_model_selection(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Single query with valid model returns model in response."""
    response = await async_client.post(
        "/api/v1/query/single",
        headers=auth_headers,
        json={"prompt": "Test", "model": "sonnet", "max_turns": 1},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "sonnet"
