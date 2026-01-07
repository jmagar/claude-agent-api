"""Contract tests for checkpoint endpoints (T095, T096)."""

import pytest
from httpx import AsyncClient


class TestCheckpointsListContractGET:
    """Contract tests for GET /api/v1/sessions/{id}/checkpoints endpoint (T095)."""

    @pytest.mark.anyio
    async def test_checkpoints_list_requires_authentication(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that checkpoints list requires API key."""
        response = await async_client.get(
            "/api/v1/sessions/test-session-id/checkpoints"
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    @pytest.mark.anyio
    async def test_checkpoints_list_returns_404_for_unknown_session(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that checkpoints list returns 404 for unknown session."""
        response = await async_client.get(
            "/api/v1/sessions/nonexistent-session/checkpoints",
            headers=auth_headers,
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "SESSION_NOT_FOUND"

    @pytest.mark.anyio
    async def test_checkpoints_list_returns_empty_list_for_session_without_checkpoints(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
    ) -> None:
        """Test that checkpoints list returns empty list for session without checkpoints."""
        response = await async_client.get(
            f"/api/v1/sessions/{mock_session_id}/checkpoints",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "checkpoints" in data
        assert isinstance(data["checkpoints"], list)
        assert len(data["checkpoints"]) == 0

    @pytest.mark.anyio
    async def test_checkpoints_list_response_format(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_with_checkpoints: str,
    ) -> None:
        """Test checkpoint list response format matches OpenAPI schema."""
        response = await async_client.get(
            f"/api/v1/sessions/{mock_session_with_checkpoints}/checkpoints",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "checkpoints" in data
        assert isinstance(data["checkpoints"], list)
        assert len(data["checkpoints"]) > 0

        # Verify checkpoint response format per OpenAPI spec
        checkpoint = data["checkpoints"][0]
        assert "id" in checkpoint
        assert "session_id" in checkpoint
        assert "user_message_uuid" in checkpoint
        assert "created_at" in checkpoint
        assert "files_modified" in checkpoint
        assert isinstance(checkpoint["files_modified"], list)


class TestRewindToCheckpointContractPOST:
    """Contract tests for POST /api/v1/sessions/{id}/rewind endpoint (T096)."""

    @pytest.mark.anyio
    async def test_rewind_requires_authentication(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that rewind endpoint requires API key."""
        response = await async_client.post(
            "/api/v1/sessions/test-session-id/rewind",
            json={"checkpoint_id": "test-checkpoint-id"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    @pytest.mark.anyio
    async def test_rewind_validates_checkpoint_id_required(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that checkpoint_id is required for rewind."""
        response = await async_client.post(
            "/api/v1/sessions/test-session-id/rewind",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_rewind_returns_404_for_unknown_session(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that rewind returns 404 for unknown session."""
        response = await async_client.post(
            "/api/v1/sessions/nonexistent-session/rewind",
            json={"checkpoint_id": "test-checkpoint-id"},
            headers=auth_headers,
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "SESSION_NOT_FOUND"

    @pytest.mark.anyio
    async def test_rewind_returns_400_for_invalid_checkpoint(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
    ) -> None:
        """Test that rewind returns 400 for invalid checkpoint_id."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/rewind",
            json={"checkpoint_id": "nonexistent-checkpoint"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_CHECKPOINT"

    @pytest.mark.anyio
    async def test_rewind_returns_success_response(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_with_checkpoints: str,
        mock_checkpoint_id: str,
    ) -> None:
        """Test that rewind returns success response with checkpoint_id."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_with_checkpoints}/rewind",
            json={"checkpoint_id": mock_checkpoint_id},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rewound"
        assert data["checkpoint_id"] == mock_checkpoint_id

    @pytest.mark.anyio
    async def test_rewind_validates_checkpoint_belongs_to_session(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
        mock_checkpoint_from_other_session: str,
    ) -> None:
        """Test that rewind rejects checkpoint from different session."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/rewind",
            json={"checkpoint_id": mock_checkpoint_from_other_session},
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_CHECKPOINT"
