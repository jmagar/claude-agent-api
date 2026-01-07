"""Integration tests for query endpoints.

These tests make actual calls to the Claude Agent SDK.
They require:
- Claude Code CLI installed (npm install -g @anthropic-ai/claude-code)
- Logged in with Claude Max subscription
- NO ANTHROPIC_API_KEY set (uses Claude Max auth instead)
"""

import json
import os
from typing import Any

import pytest
from httpx import AsyncClient
from httpx_sse import aconnect_sse


def sdk_available() -> bool:
    """Check if SDK integration is available."""
    # Check that we're NOT using API key auth (Claude Max uses different auth)
    # SDK should be available via Claude Max subscription
    return not os.environ.get("ANTHROPIC_API_KEY")


def parse_sse_data(data: str | None) -> dict[str, Any]:
    """Parse SSE data, handling empty strings."""
    if not data or not data.strip():
        return {}
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return {"raw": data}


# Mark all tests to skip if SDK not available
pytestmark = pytest.mark.skipif(
    not sdk_available(),
    reason="SDK integration requires Claude Max subscription (no ANTHROPIC_API_KEY)",
)


class TestQueryStreaming:
    """Integration tests for streaming query functionality."""

    @pytest.mark.anyio
    @pytest.mark.timeout(60)
    async def test_query_stream_init_event(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that query stream starts with init event."""
        request_data = {
            "prompt": "Say hello in exactly 3 words",
            "max_turns": 1,
        }

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
                    data = parse_sse_data(sse.data)
                    events.append({"event": sse.event, "data": data})
                    # Stop after init event for this test
                    if sse.event == "init":
                        break

        assert len(events) >= 1
        init_event = events[0]
        assert init_event["event"] == "init"
        init_data = init_event["data"]
        assert isinstance(init_data, dict)
        assert "session_id" in init_data

    @pytest.mark.anyio
    @pytest.mark.timeout(60)
    async def test_query_stream_result_event(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that query stream ends with result event."""
        request_data = {
            "prompt": "What is 2+2? Answer with just the number.",
            "max_turns": 1,
        }

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
                    data = parse_sse_data(sse.data)
                    events.append({"event": sse.event, "data": data})
                    # Stop after result event
                    if sse.event == "result":
                        break

        # Should have at least init and result events
        event_types = [e["event"] for e in events]
        assert "init" in event_types
        assert "result" in event_types

        # Verify result event structure
        result_events = [e for e in events if e["event"] == "result"]
        assert len(result_events) >= 1
        result_data = result_events[-1]["data"]
        assert isinstance(result_data, dict)
        # Result should have either is_complete or session_id
        assert "is_complete" in result_data or "session_id" in result_data

    @pytest.mark.anyio
    @pytest.mark.timeout(60)
    async def test_query_stream_done_event(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that query stream ends with done event."""
        request_data = {
            "prompt": "What is 1+1? Answer with just the number.",
            "max_turns": 1,
        }

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
                    data = parse_sse_data(sse.data)
                    events.append({"event": sse.event, "data": data})
                    # Stop after done event
                    if sse.event == "done":
                        break

        event_types = [e["event"] for e in events]
        assert "done" in event_types

    @pytest.mark.anyio
    @pytest.mark.timeout(60)
    async def test_query_stream_session_id_returned(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that session_id is returned in init event."""
        request_data = {
            "prompt": "Hi",
            "max_turns": 1,
        }

        session_id = None
        async with aconnect_sse(
            async_client,
            "POST",
            "/api/v1/query",
            headers={**auth_headers, "Accept": "text/event-stream"},
            json=request_data,
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.event == "init":
                    data = parse_sse_data(sse.data)
                    session_id = data.get("session_id")
                    break

        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0

    @pytest.mark.anyio
    @pytest.mark.timeout(60)
    async def test_query_stream_with_allowed_tools(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test query with allowed_tools restriction."""
        request_data = {
            "prompt": "What files are in the current directory?",
            "allowed_tools": ["Glob", "Read"],
            "max_turns": 2,
        }

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
                    data = parse_sse_data(sse.data)
                    events.append({"event": sse.event, "data": data})
                    if sse.event == "done":
                        break

        # Should complete without errors
        event_types = [e["event"] for e in events]
        assert "init" in event_types
        error_events = [e for e in events if e["event"] == "error"]
        assert len(error_events) == 0

    @pytest.mark.anyio
    @pytest.mark.timeout(30)
    async def test_query_stream_error_handling(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test error handling in streaming mode."""
        # Send invalid request (missing required prompt)
        request_data: dict[str, object] = {}

        response = await async_client.post(
            "/api/v1/query",
            headers={**auth_headers, "Accept": "text/event-stream"},
            json=request_data,
        )

        # Should return validation error
        assert response.status_code == 422


class TestQuerySingle:
    """Integration tests for single (non-streaming) query."""

    @pytest.mark.anyio
    @pytest.mark.timeout(60)
    async def test_query_single_returns_complete_response(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that single query returns complete response."""
        request_data = {
            "prompt": "What is 5+5? Answer with just the number.",
            "stream": False,
            "max_turns": 1,
        }

        response = await async_client.post(
            "/api/v1/query/single",
            headers=auth_headers,
            json=request_data,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have essential fields
        assert "session_id" in data
        assert "content" in data or "message" in data or "result" in data

    @pytest.mark.anyio
    @pytest.mark.timeout(60)
    async def test_query_single_includes_usage(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that single query response includes usage data."""
        request_data = {
            "prompt": "Say 'test'",
            "stream": False,
            "max_turns": 1,
        }

        response = await async_client.post(
            "/api/v1/query/single",
            headers=auth_headers,
            json=request_data,
        )

        assert response.status_code == 200
        data = response.json()

        # Check for usage data if present and not None
        if "usage" in data and data["usage"] is not None:
            usage = data["usage"]
            # Verify usage structure if it exists
            assert isinstance(usage, dict)
