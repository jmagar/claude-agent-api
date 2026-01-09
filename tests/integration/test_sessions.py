"""Integration tests for session management (T041)."""

import pytest
from httpx import AsyncClient


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
        # First query to create a session
        response = await async_client.post(
            "/api/v1/query",
            json={"prompt": "Say hello"},
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Extract session ID from the init event
        # The response is SSE - we need to parse it
        content = response.text
        assert "session_id" in content

        # For now, we'll parse the session_id from the SSE response
        # In a real test, we'd use an SSE client
        import json
        import re

        # Find init event data
        init_match = re.search(r'data: (\{"session_id".*?\})', content)
        assert init_match is not None, f"No init event found in: {content[:500]}"

        init_data = json.loads(init_match.group(1))
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
        # First query to create a session
        response = await async_client.post(
            "/api/v1/query",
            json={"prompt": "Count to 3"},
            headers=auth_headers,
        )
        assert response.status_code == 200

        import json
        import re

        # Extract original session_id
        init_match = re.search(r'data: (\{"session_id".*?\})', response.text)
        assert init_match is not None
        original_session_id = json.loads(init_match.group(1))["session_id"]

        # Fork the session
        fork_response = await async_client.post(
            f"/api/v1/sessions/{original_session_id}/fork",
            json={"prompt": "Now count backwards from 3"},
            headers=auth_headers,
        )
        assert fork_response.status_code == 200

        # The forked session should have a different session_id
        fork_init_match = re.search(r'data: (\{"session_id".*?\})', fork_response.text)
        assert fork_init_match is not None
        forked_session_id = json.loads(fork_init_match.group(1))["session_id"]

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
        # Create a session
        query_response = await async_client.post(
            "/api/v1/query",
            json={"prompt": "Test session listing"},
            headers=auth_headers,
        )
        assert query_response.status_code == 200

        import json
        import re

        init_match = re.search(r'data: (\{"session_id".*?\})', query_response.text)
        assert init_match is not None
        session_id = json.loads(init_match.group(1))["session_id"]

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
        # Create a session
        query_response = await async_client.post(
            "/api/v1/query",
            json={"prompt": "Test session detail"},
            headers=auth_headers,
        )
        assert query_response.status_code == 200

        import json
        import re

        init_match = re.search(r'data: (\{"session_id".*?\})', query_response.text)
        assert init_match is not None
        session_id = json.loads(init_match.group(1))["session_id"]

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
