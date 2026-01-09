"""Integration tests for session management (T041)."""

import json

import pytest
from httpx import AsyncClient
from httpx_sse import aconnect_sse


class TestSessionResumeIntegration:
    """Integration tests for session resume flow."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_creates_session_that_can_be_resumed(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that a query creates a session that can be resumed."""
        # First query to create a session using SSE
        request_data = {"prompt": "Say hello"}

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

        # Extract session ID from the init event
        init_events = [e for e in events if e["event"] == "init"]
        assert len(init_events) == 1
        init_data = json.loads(init_events[0]["data"])
        session_id = init_data["session_id"]
        assert session_id is not None

        # Resume the session
        resume_response = await async_client.post(
            f"/api/v1/sessions/{session_id}/resume",
            json={"prompt": "Continue the conversation"},
            headers=auth_headers,
        )
        assert resume_response.status_code == 200
        assert "text/event-stream" in resume_response.headers.get("content-type", "")

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_session_fork_creates_new_session(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that forking creates a new session ID."""
        # First query to create a session using SSE
        request_data = {"prompt": "Count to 3"}

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

        # Extract original session_id
        init_events = [e for e in events if e["event"] == "init"]
        assert len(init_events) == 1
        original_session_id = json.loads(init_events[0]["data"])["session_id"]

        # Fork the session using SSE
        fork_events: list[dict[str, str]] = []
        async with aconnect_sse(
            async_client,
            "POST",
            f"/api/v1/sessions/{original_session_id}/fork",
            headers={**auth_headers, "Accept": "text/event-stream"},
            json={"prompt": "Now count backwards from 3"},
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.event:
                    fork_events.append({"event": sse.event, "data": sse.data})

        # The forked session should have a different session_id
        fork_init_events = [e for e in fork_events if e["event"] == "init"]
        assert len(fork_init_events) == 1
        forked_session_id = json.loads(fork_init_events[0]["data"])["session_id"]

        assert forked_session_id != original_session_id

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_session_list_shows_created_sessions(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that session list shows recently created sessions."""
        # Create a session using SSE
        request_data = {"prompt": "Test session listing"}

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

        # Extract session ID
        init_events = [e for e in events if e["event"] == "init"]
        assert len(init_events) == 1
        session_id = json.loads(init_events[0]["data"])["session_id"]

        # List sessions
        list_response = await async_client.get(
            "/api/v1/sessions",
            headers=auth_headers,
        )
        assert list_response.status_code == 200
        data = list_response.json()

        # Session should appear in the list
        session_ids = [s["id"] for s in data["sessions"]]
        assert session_id in session_ids

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_session_detail_returns_session_info(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that session detail returns session information."""
        # Create a session using SSE
        request_data = {"prompt": "Test session detail"}

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

        # Extract session ID
        init_events = [e for e in events if e["event"] == "init"]
        assert len(init_events) == 1
        session_id = json.loads(init_events[0]["data"])["session_id"]

        # Get session detail
        detail_response = await async_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers,
        )
        assert detail_response.status_code == 200
        data = detail_response.json()

        assert data["id"] == session_id
        assert "status" in data
        assert "created_at" in data

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_single_query_session_is_persisted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that sessions from /query/single are persisted and retrievable."""
        # Create a session via single query endpoint
        query_response = await async_client.post(
            "/api/v1/query/single",
            json={"prompt": "Test single query session persistence"},
            headers=auth_headers,
        )
        assert query_response.status_code == 200
        query_data = query_response.json()

        # Extract session_id from response
        session_id = query_data["session_id"]
        assert session_id is not None

        # Verify session can be retrieved
        detail_response = await async_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers,
        )
        assert detail_response.status_code == 200
        session_data = detail_response.json()

        # Verify session details
        assert session_data["id"] == session_id
        assert session_data["status"] in ["active", "completed", "error"]
        assert "created_at" in session_data
        assert "model" in session_data
