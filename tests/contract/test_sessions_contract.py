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
    """Contract tests for GET /api/v1/sessions endpoint."""

    @pytest.mark.anyio
    async def test_sessions_list_requires_authentication(
        self,
        _async_client: AsyncClient,
    ) -> None:
        """Test that sessions list requires API key."""
        pytest.skip("Requires session service implementation")

    @pytest.mark.anyio
    async def test_sessions_list_returns_paginated_results(
        self,
        _async_client: AsyncClient,
        _auth_headers: dict[str, str],
    ) -> None:
        """Test that sessions list returns paginated results."""
        pytest.skip("Requires session service implementation")


class TestSessionDetailContractGET:
    """Contract tests for GET /api/v1/sessions/{id} endpoint."""

    @pytest.mark.anyio
    async def test_session_detail_requires_authentication(
        self,
        _async_client: AsyncClient,
    ) -> None:
        """Test that session detail requires API key."""
        pytest.skip("Requires session service implementation")


class TestSessionResumeContractPOST:
    """Contract tests for POST /api/v1/sessions/{id}/resume endpoint."""

    @pytest.mark.anyio
    async def test_session_resume_requires_authentication(
        self,
        _async_client: AsyncClient,
    ) -> None:
        """Test that session resume requires API key."""
        pytest.skip("Requires session service implementation")


class TestSessionForkContractPOST:
    """Contract tests for POST /api/v1/sessions/{id}/fork endpoint."""

    @pytest.mark.anyio
    async def test_session_fork_requires_authentication(
        self,
        _async_client: AsyncClient,
    ) -> None:
        """Test that session fork requires API key."""
        pytest.skip("Requires session service implementation")
