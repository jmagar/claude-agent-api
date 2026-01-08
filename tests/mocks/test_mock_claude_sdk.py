"""Tests for Claude SDK mocking infrastructure."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_mock_claude_sdk_returns_init_event(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_claude_sdk: None,
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
            # Strip whitespace and newlines from event type
            event_type = line.split("event: ")[1].split("\n")[0].strip()
            events.append(event_type)

    assert "init" in events


@pytest.mark.anyio
async def test_mock_claude_sdk_returns_complete_event_sequence(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_claude_sdk: None,
) -> None:
    """Test that mocked SDK returns all expected events in sequence."""
    from httpx_sse import aconnect_sse

    events: list[str] = []
    async with aconnect_sse(
        async_client,
        "POST",
        "/api/v1/query",
        headers={**auth_headers, "Accept": "text/event-stream"},
        json={"prompt": "test"},
    ) as event_source:
        async for sse in event_source.aiter_sse():
            if sse.event:
                events.append(sse.event)

    # Verify standard event sequence: init, message, result, done
    assert "init" in events
    assert "message" in events
    assert "result" in events
    assert "done" in events

    # Verify order (init should be first, done should be last)
    assert events[0] == "init"
    assert events[-1] == "done"
