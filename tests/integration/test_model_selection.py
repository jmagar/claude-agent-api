"""Integration tests for model selection (T105)."""

import json

import pytest
from httpx import AsyncClient
from httpx_sse import aconnect_sse


class TestModelSelection:
    """Integration tests for model selection parameter."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_default_model_uses_sonnet(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that queries without model parameter default to sonnet."""
        request_data = {
            "prompt": "Hello",
            "allowed_tools": [],
        }

        # Collect events from SSE stream
        events: list[dict[str, str]] = []
        async with aconnect_sse(
            async_client,
            "POST",
            "/api/v1/query",
            headers={**auth_headers, "Accept": "text/event-stream"},
            json=request_data,
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.event:
                    events.append({"event": sse.event, "data": sse.data})

        # Parse init event to check model
        init_events = [e for e in events if e["event"] == "init"]
        assert len(init_events) == 1
        init_data = json.loads(init_events[0]["data"])
        assert init_data["model"] == "sonnet"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_explicit_sonnet_model(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that queries with model=sonnet use sonnet."""
        request_data = {
            "prompt": "Hello",
            "model": "sonnet",
            "allowed_tools": [],
        }

        # Collect events from SSE stream
        events: list[dict[str, str]] = []
        async with aconnect_sse(
            async_client,
            "POST",
            "/api/v1/query",
            headers={**auth_headers, "Accept": "text/event-stream"},
            json=request_data,
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.event:
                    events.append({"event": sse.event, "data": sse.data})

        # Parse init event to check model
        init_events = [e for e in events if e["event"] == "init"]
        assert len(init_events) == 1
        init_data = json.loads(init_events[0]["data"])
        assert init_data["model"] == "sonnet"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_opus_model(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that queries with model=opus use opus."""
        request_data = {
            "prompt": "Hello",
            "model": "opus",
            "allowed_tools": [],
        }

        # Collect events from SSE stream
        events: list[dict[str, str]] = []
        async with aconnect_sse(
            async_client,
            "POST",
            "/api/v1/query",
            headers={**auth_headers, "Accept": "text/event-stream"},
            json=request_data,
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.event:
                    events.append({"event": sse.event, "data": sse.data})

        # Parse init event to check model
        init_events = [e for e in events if e["event"] == "init"]
        assert len(init_events) == 1
        init_data = json.loads(init_events[0]["data"])
        assert init_data["model"] == "opus"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_haiku_model(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that queries with model=haiku use haiku."""
        request_data = {
            "prompt": "Hello",
            "model": "haiku",
            "allowed_tools": [],
        }

        # Collect events from SSE stream
        events: list[dict[str, str]] = []
        async with aconnect_sse(
            async_client,
            "POST",
            "/api/v1/query",
            headers={**auth_headers, "Accept": "text/event-stream"},
            json=request_data,
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.event:
                    events.append({"event": sse.event, "data": sse.data})

        # Parse init event to check model
        init_events = [e for e in events if e["event"] == "init"]
        assert len(init_events) == 1
        init_data = json.loads(init_events[0]["data"])
        assert init_data["model"] == "haiku"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_invalid_model_returns_422(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that queries with invalid model return validation error."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "model": "invalid-model",
                "allowed_tools": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        # Verify error mentions valid model options
        error_str = str(data["detail"])
        assert "sonnet" in error_str or "model" in error_str.lower()

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_full_model_id_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that queries with full model ID are accepted."""
        request_data = {
            "prompt": "Hello",
            "model": "claude-sonnet-4-20250514",
            "allowed_tools": [],
        }

        # Collect events from SSE stream
        events: list[dict[str, str]] = []
        async with aconnect_sse(
            async_client,
            "POST",
            "/api/v1/query",
            headers={**auth_headers, "Accept": "text/event-stream"},
            json=request_data,
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.event:
                    events.append({"event": sse.event, "data": sse.data})

        # Parse init event to check model
        init_events = [e for e in events if e["event"] == "init"]
        assert len(init_events) == 1
        init_data = json.loads(init_events[0]["data"])
        assert init_data["model"] == "claude-sonnet-4-20250514"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_result_event_contains_model_usage(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that result event contains model_usage breakdown."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "model": "sonnet",
                "allowed_tools": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        content = response.text
        # Find result event - parse line by line to find result event JSON
        # SSE format: "event: result\ndata: {...json...}"
        result_data = None
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "event: result" in line:
                # Find the next line containing JSON data
                for next_line in lines[i + 1 :]:
                    if next_line.startswith("data: {") or ": {" in next_line:
                        # Extract JSON from the line
                        json_start = next_line.find("{")
                        if json_start >= 0:
                            result_data = json.loads(next_line[json_start:])
                            break
                break

        assert result_data is not None, f"No result event found in: {content}"
        # model_usage should be present (may be None if single model)
        assert "model_usage" in result_data

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_single_query_with_model_parameter(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that /query/single endpoint respects model parameter."""
        response = await async_client.post(
            "/api/v1/query/single",
            json={
                "prompt": "Hello",
                "model": "haiku",
                "allowed_tools": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["model"] == "haiku"
