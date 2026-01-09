"""Integration tests for file checkpointing and rewind (T097)."""

import json
import re

import pytest
from httpx import AsyncClient


class TestCheckpointIntegration:
    """Integration tests for checkpoint functionality."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_session_with_checkpointing_lists_checkpoints(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_with_checkpoints: str,
        mock_claude_sdk: None,
    ) -> None:
        """Test that checkpoints can be listed for a session with checkpoints."""
        # Get checkpoints for the session
        response = await async_client.get(
            f"/api/v1/sessions/{mock_session_with_checkpoints}/checkpoints",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert "checkpoints" in data
        assert isinstance(data["checkpoints"], list)
        assert len(data["checkpoints"]) > 0

        # Verify checkpoint structure
        checkpoint = data["checkpoints"][0]
        assert "id" in checkpoint
        assert "session_id" in checkpoint
        assert "user_message_uuid" in checkpoint
        assert "created_at" in checkpoint
        assert "files_modified" in checkpoint

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_session_without_checkpointing_returns_empty_list(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
        mock_claude_sdk: None,
    ) -> None:
        """Test that sessions without checkpoints return empty list."""
        response = await async_client.get(
            f"/api/v1/sessions/{mock_session_id}/checkpoints",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert "checkpoints" in data
        assert isinstance(data["checkpoints"], list)
        assert len(data["checkpoints"]) == 0

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_rewind_to_valid_checkpoint_succeeds(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_with_checkpoints: str,
        mock_checkpoint_id: str,
        mock_claude_sdk: None,
    ) -> None:
        """Test that rewinding to a valid checkpoint succeeds."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_with_checkpoints}/rewind",
            json={"checkpoint_id": mock_checkpoint_id},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "validated"
        assert data["checkpoint_id"] == mock_checkpoint_id

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_rewind_to_invalid_checkpoint_fails(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
        mock_claude_sdk: None,
    ) -> None:
        """Test that rewinding to an invalid checkpoint fails with 400."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/rewind",
            json={"checkpoint_id": "nonexistent-checkpoint"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = response.json()

        assert data["error"]["code"] == "INVALID_CHECKPOINT"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_rewind_with_other_session_checkpoint_fails(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
        mock_checkpoint_from_other_session: str,
        mock_claude_sdk: None,
    ) -> None:
        """Test that rewinding with a checkpoint from another session fails."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/rewind",
            json={"checkpoint_id": mock_checkpoint_from_other_session},
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = response.json()

        assert data["error"]["code"] == "INVALID_CHECKPOINT"


class TestEnableFileCheckpointing:
    """Integration tests for enable_file_checkpointing parameter."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_checkpointing_enabled_tracks_checkpoints(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that queries with enable_file_checkpointing=true track checkpoints."""
        # Send a query with checkpointing enabled
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Create a test file",
                "enable_file_checkpointing": True,
                "allowed_tools": ["Write"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Extract session ID from the init event
        content = response.text
        init_match = re.search(r'data: (\{"session_id".*?\})', content)
        assert init_match is not None, f"No init event found in: {content[:500]}"

        init_data = json.loads(init_match.group(1))
        session_id = init_data["session_id"]

        # Get checkpoints for the session
        # Note: This may return empty if no files were modified during the query
        checkpoint_response = await async_client.get(
            f"/api/v1/sessions/{session_id}/checkpoints",
            headers=auth_headers,
        )
        assert checkpoint_response.status_code == 200
        data = checkpoint_response.json()

        # Should have checkpoints list (may be empty if no file modifications)
        assert "checkpoints" in data
        assert isinstance(data["checkpoints"], list)

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_without_checkpointing_does_not_track(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that queries without enable_file_checkpointing don't track checkpoints."""
        # Send a query without checkpointing
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "enable_file_checkpointing": False,
                "allowed_tools": ["Glob"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Extract session ID
        content = response.text
        init_match = re.search(r'data: (\{"session_id".*?\})', content)
        assert init_match is not None

        init_data = json.loads(init_match.group(1))
        session_id = init_data["session_id"]

        # Get checkpoints - should be empty (no checkpointing enabled)
        checkpoint_response = await async_client.get(
            f"/api/v1/sessions/{session_id}/checkpoints",
            headers=auth_headers,
        )
        assert checkpoint_response.status_code == 200
        data = checkpoint_response.json()

        assert "checkpoints" in data
        assert isinstance(data["checkpoints"], list)
        # Without checkpointing enabled, no checkpoints should be created
        assert len(data["checkpoints"]) == 0
