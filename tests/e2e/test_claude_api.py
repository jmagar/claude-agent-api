"""End-to-end tests that actually call Claude API."""

import asyncio
import json
from collections.abc import Awaitable, Callable

import pytest
from httpx import ASGITransport, AsyncClient, Response

SseEventHandler = Callable[[str, dict[str, object]], Awaitable[None]]


async def _collect_sse_events(
    response: Response,
    on_event: SseEventHandler | None = None,
) -> list[dict[str, object]]:
    """Collect SSE events from a streaming response."""
    events: list[dict[str, object]] = []
    event_type: str | None = None
    data_lines: list[str] = []

    async for line in response.aiter_lines():
        if line.startswith("event:"):
            event_type = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").strip())
        elif line == "":
            if event_type is None:
                data_lines = []
                continue

            data_str = "\n".join(data_lines)
            try:
                parsed_data: dict[str, object] = json.loads(data_str)
            except json.JSONDecodeError:
                parsed_data = {"raw": data_str}

            events.append({"event": event_type, "data": parsed_data})
            if on_event is not None:
                await on_event(event_type, parsed_data)

            if event_type == "done":
                break

            event_type = None
            data_lines = []

    return events


@pytest.mark.e2e
@pytest.mark.anyio
async def test_real_claude_query(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test real Claude API calls (no mocking).

    Makes 4 total API calls:
    1) /query (streaming)
    2) /sessions/{id}/interrupt
    3) /query/single
    4) /sessions/{id}/resume
    """
    session_id: str | None = None
    interrupt_sent = False
    saw_message = False
    saw_done = False
    transport = async_client._transport
    base_url = str(async_client.base_url)
    if isinstance(transport, ASGITransport):
        interrupt_client = AsyncClient(
            transport=transport,
            base_url=base_url,
        )
    else:
        interrupt_client = AsyncClient(base_url=base_url)

    async def interrupt_with_retry() -> None:
        """Retry interrupt until it succeeds or timeout expires."""
        nonlocal interrupt_sent
        assert session_id is not None
        deadline = asyncio.get_running_loop().time() + 3.0
        while not interrupt_sent and asyncio.get_running_loop().time() < deadline:
            interrupt_response = await interrupt_client.post(
                f"/api/v1/sessions/{session_id}/interrupt",
                headers=auth_headers,
            )
            if interrupt_response.status_code == 200:
                interrupt_sent = True
                return
            await asyncio.sleep(0.05)
        if not interrupt_sent:
            raise AssertionError("Interrupt did not succeed before timeout")

    async def on_stream_event(event: str, data: dict[str, object]) -> None:
        nonlocal session_id, saw_message, saw_done
        if event == "error":
            raise AssertionError(f"Streaming query failed: {data!r}")

        if event == "init" and session_id is None:
            session_id_value = data.get("session_id")
            if isinstance(session_id_value, str):
                session_id = session_id_value
                await interrupt_with_retry()
            return

        if event == "message":
            saw_message = True
        if event == "done":
            saw_done = True

    try:
        async with async_client.stream(
            "POST",
            "/api/v1/query",
            json={"prompt": "Write 50 words about the word hello."},
            headers=auth_headers,
        ) as response:
            assert response.status_code == 200
            events = await _collect_sse_events(response, on_event=on_stream_event)
    finally:
        await interrupt_client.aclose()

    assert interrupt_sent
    assert session_id is not None
    assert saw_message
    assert any(event["event"] == "init" for event in events)
    assert any(event["event"] == "message" for event in events)
    assert any(event["event"] == "result" for event in events)
    assert any(event["event"] == "done" for event in events)
    done_event = next(event for event in events if event["event"] == "done")
    done_data = done_event["data"]
    assert isinstance(done_data, dict) and done_data.get("reason") == "interrupted"

    single_response = await async_client.post(
        "/api/v1/query/single",
        json={"prompt": "Say hello"},
        headers=auth_headers,
    )
    assert single_response.status_code == 200
    single_data = single_response.json()
    assert "session_id" in single_data
    assert "model" in single_data
    assert "content" in single_data
    assert "duration_ms" in single_data
    assert "num_turns" in single_data

    async with async_client.stream(
        "POST",
        f"/api/v1/sessions/{session_id}/resume",
        json={"prompt": "Continue"},
        headers=auth_headers,
    ) as response:
        assert response.status_code == 200
        resume_events = await _collect_sse_events(response)

    assert any(event["event"] == "init" for event in resume_events)
    assert any(event["event"] == "done" for event in resume_events)
    error_events = [event for event in resume_events if event["event"] == "error"]
    assert not error_events, f"Resume error events: {error_events!r}"
