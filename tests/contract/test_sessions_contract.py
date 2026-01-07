"""Contract tests for session endpoints."""

import pytest
from httpx import AsyncClient


class TestSessionAnswerContractPOST:
    """Contract tests for POST /api/v1/sessions/{id}/answer endpoint."""

    @pytest.mark.anyio
    async def test_answer_requires_authentication(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that answer endpoint requires API key."""
        response = await async_client.post(
            "/api/v1/sessions/test-session-123/answer",
            json={"answer": "Yes, please continue"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    @pytest.mark.anyio
    async def test_answer_validates_answer_required(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that answer field is required."""
        response = await async_client.post(
            "/api/v1/sessions/test-session-123/answer",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_answer_validates_answer_not_empty(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that answer cannot be empty."""
        response = await async_client.post(
            "/api/v1/sessions/test-session-123/answer",
            json={"answer": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_answer_returns_404_for_unknown_session(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that answer returns 404 for unknown session."""
        response = await async_client.post(
            "/api/v1/sessions/nonexistent-session/answer",
            json={"answer": "Test answer"},
            headers=auth_headers,
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "SESSION_NOT_FOUND"


class TestSessionListContractGET:
    """Contract tests for GET /api/v1/sessions endpoint (T037)."""

    @pytest.mark.anyio
    async def test_sessions_list_requires_authentication(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that sessions list requires API key."""
        response = await async_client.get("/api/v1/sessions")
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    @pytest.mark.anyio
    async def test_sessions_list_returns_paginated_results(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that sessions list returns paginated results."""
        response = await async_client.get(
            "/api/v1/sessions",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["sessions"], list)

    @pytest.mark.anyio
    async def test_sessions_list_pagination_params(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test sessions list with pagination parameters."""
        response = await async_client.get(
            "/api/v1/sessions?page=1&page_size=10",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    @pytest.mark.anyio
    async def test_sessions_list_validates_page_size(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that page_size is validated (max 100)."""
        response = await async_client.get(
            "/api/v1/sessions?page_size=200",
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestSessionDetailContractGET:
    """Contract tests for GET /api/v1/sessions/{id} endpoint (T038)."""

    @pytest.mark.anyio
    async def test_session_detail_requires_authentication(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that session detail requires API key."""
        response = await async_client.get("/api/v1/sessions/test-session-id")
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    @pytest.mark.anyio
    async def test_session_detail_returns_404_for_unknown(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that unknown session returns 404."""
        response = await async_client.get(
            "/api/v1/sessions/nonexistent-session",
            headers=auth_headers,
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "SESSION_NOT_FOUND"

    @pytest.mark.anyio
    async def test_session_detail_response_format(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
    ) -> None:
        """Test session detail response format."""
        response = await async_client.get(
            f"/api/v1/sessions/{mock_session_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["id"] == mock_session_id


class TestSessionResumeContractPOST:
    """Contract tests for POST /api/v1/sessions/{id}/resume endpoint (T039)."""

    @pytest.mark.anyio
    async def test_session_resume_requires_authentication(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that session resume requires API key."""
        response = await async_client.post(
            "/api/v1/sessions/test-session-id/resume",
            json={"prompt": "Continue the conversation"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    @pytest.mark.anyio
    async def test_session_resume_validates_prompt_required(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that prompt is required for resume."""
        response = await async_client.post(
            "/api/v1/sessions/test-session-id/resume",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_session_resume_returns_404_for_unknown(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that resume returns 404 for unknown session."""
        response = await async_client.post(
            "/api/v1/sessions/nonexistent-session/resume",
            json={"prompt": "Continue"},
            headers=auth_headers,
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "SESSION_NOT_FOUND"

    @pytest.mark.anyio
    async def test_session_resume_returns_sse_stream(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
    ) -> None:
        """Test that resume returns SSE stream."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/resume",
            json={"prompt": "Continue"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")


class TestSessionForkContractPOST:
    """Contract tests for POST /api/v1/sessions/{id}/fork endpoint (T040)."""

    @pytest.mark.anyio
    async def test_session_fork_requires_authentication(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that session fork requires API key."""
        response = await async_client.post(
            "/api/v1/sessions/test-session-id/fork",
            json={"prompt": "New branch conversation"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    @pytest.mark.anyio
    async def test_session_fork_validates_prompt_required(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that prompt is required for fork."""
        response = await async_client.post(
            "/api/v1/sessions/test-session-id/fork",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_session_fork_returns_404_for_unknown(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that fork returns 404 for unknown session."""
        response = await async_client.post(
            "/api/v1/sessions/nonexistent-session/fork",
            json={"prompt": "Fork this"},
            headers=auth_headers,
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "SESSION_NOT_FOUND"

    @pytest.mark.anyio
    async def test_session_fork_returns_new_session_id(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
    ) -> None:
        """Test that fork returns a new session ID."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/fork",
            json={"prompt": "Fork this conversation"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")


class TestSessionInterruptContractPOST:
    """Contract tests for POST /api/v1/sessions/{id}/interrupt endpoint."""

    @pytest.mark.anyio
    async def test_session_interrupt_requires_authentication(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that session interrupt requires API key."""
        response = await async_client.post(
            "/api/v1/sessions/test-session-id/interrupt",
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    @pytest.mark.anyio
    async def test_session_interrupt_returns_404_for_unknown(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that interrupt returns 404 for unknown session."""
        response = await async_client.post(
            "/api/v1/sessions/nonexistent-session/interrupt",
            headers=auth_headers,
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "SESSION_NOT_FOUND"

    @pytest.mark.anyio
    async def test_session_interrupt_returns_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_active_session_id: str,
    ) -> None:
        """Test that interrupt returns success for active session."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_active_session_id}/interrupt",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "interrupted"
