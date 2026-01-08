"""Integration tests for permission mode functionality (User Story 6)."""

import pytest
from httpx import AsyncClient

from apps.api.schemas.requests.query import QueryRequest


class TestPermissionModeValidation:
    """Tests for permission mode request validation."""

    @pytest.mark.anyio
    async def test_default_permission_mode_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that default permission mode is accepted in query request."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "permission_mode": "default",
            },
            headers=auth_headers,
        )
        # Should accept the request (stream starts) - status 200 for SSE
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_accept_edits_permission_mode_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that acceptEdits permission mode is accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "permission_mode": "acceptEdits",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_plan_permission_mode_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that plan permission mode is accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "permission_mode": "plan",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_bypass_permissions_mode_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that bypassPermissions mode is accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "permission_mode": "bypassPermissions",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_invalid_permission_mode_rejected(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that invalid permission modes are rejected with 422."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "permission_mode": "invalid_mode",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data


class TestPermissionModeInInit:
    """Tests for permission mode in SSE init events."""

    @pytest.mark.anyio
    async def test_permission_mode_included_in_init_event(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that permission_mode is included in init event data.

        The init event should contain the configured permission mode
        so clients know what mode is active for the session.
        """
        # This test requires SDK integration and SSE parsing
        pytest.skip("Requires SDK integration for full init event verification")

    @pytest.mark.anyio
    async def test_permission_mode_default_when_not_specified(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that permission_mode defaults to 'default' when not specified."""
        # Verify request without permission_mode uses default
        request = QueryRequest(prompt="Test prompt")
        assert request.permission_mode == "default"


class TestPermissionModeWithResume:
    """Tests for permission mode in session resume scenarios."""

    @pytest.mark.anyio
    async def test_resume_with_permission_mode_override(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
    ) -> None:
        """Test that permission_mode can be overridden when resuming session."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/resume",
            json={
                "prompt": "Continue with different permissions",
                "permission_mode": "acceptEdits",
            },
            headers=auth_headers,
        )
        # Should accept the resume request with overridden permission mode
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_resume_inherits_permission_mode_when_not_specified(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
    ) -> None:
        """Test that permission mode is inherited when not specified in resume."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/resume",
            json={
                "prompt": "Continue without specifying permission mode",
            },
            headers=auth_headers,
        )
        # Should accept the resume request (inheriting permission mode)
        assert response.status_code == 200


class TestPermissionModeWithFork:
    """Tests for permission mode in session fork scenarios."""

    @pytest.mark.anyio
    async def test_fork_with_permission_mode_override(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
    ) -> None:
        """Test that permission_mode can be overridden when forking session."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/fork",
            json={
                "prompt": "Fork with different permissions",
                "permission_mode": "plan",
            },
            headers=auth_headers,
        )
        # Should accept the fork request with overridden permission mode
        assert response.status_code == 200


class TestPermissionPromptToolName:
    """Tests for permission_prompt_tool_name parameter."""

    @pytest.mark.anyio
    async def test_permission_prompt_tool_name_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that permission_prompt_tool_name parameter is accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "permission_mode": "default",
                "permission_prompt_tool_name": "custom_prompt_tool",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_permission_prompt_tool_name_in_request_schema(self) -> None:
        """Test that permission_prompt_tool_name is part of QueryRequest schema."""
        request = QueryRequest(
            prompt="Test prompt",
            permission_prompt_tool_name="my_custom_tool",
        )
        assert request.permission_prompt_tool_name == "my_custom_tool"

    @pytest.mark.anyio
    async def test_permission_prompt_tool_name_defaults_to_none(self) -> None:
        """Test that permission_prompt_tool_name defaults to None."""
        request = QueryRequest(prompt="Test prompt")
        assert request.permission_prompt_tool_name is None


class TestPermissionModeSingleQuery:
    """Tests for permission mode in non-streaming (single) query."""

    @pytest.mark.anyio
    async def test_single_query_with_permission_mode(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that permission_mode works with single (non-streaming) query."""
        response = await async_client.post(
            "/api/v1/query/single",
            json={
                "prompt": "List files",
                "permission_mode": "acceptEdits",
            },
            headers=auth_headers,
        )
        # Single query endpoint should accept permission mode
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_single_query_invalid_permission_mode_rejected(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that invalid permission mode is rejected in single query."""
        response = await async_client.post(
            "/api/v1/query/single",
            json={
                "prompt": "List files",
                "permission_mode": "not_a_valid_mode",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestDynamicPermissionModeChanges:
    """Tests for dynamic permission mode changes during streaming (FR-015, T080a)."""

    @pytest.mark.anyio
    async def test_control_endpoint_exists(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_active_session_id: str,
    ) -> None:
        """Test that the control endpoint exists for active sessions."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_active_session_id}/control",
            json={
                "type": "permission_mode_change",
                "permission_mode": "acceptEdits",
            },
            headers=auth_headers,
        )
        # Should accept the control event (even if session is not running query)
        assert response.status_code in (200, 202, 404)

    @pytest.mark.anyio
    async def test_control_endpoint_validates_permission_mode(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_active_session_id: str,
    ) -> None:
        """Test that invalid permission mode in control event is rejected."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_active_session_id}/control",
            json={
                "type": "permission_mode_change",
                "permission_mode": "invalid_mode",
            },
            headers=auth_headers,
        )
        # Should reject invalid permission mode
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_control_endpoint_requires_type(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_active_session_id: str,
    ) -> None:
        """Test that control event requires 'type' field."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_active_session_id}/control",
            json={
                "permission_mode": "acceptEdits",
            },
            headers=auth_headers,
        )
        # Should reject missing type
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_control_request_schema_validation(self) -> None:
        """Test ControlRequest schema validation."""
        from apps.api.schemas.requests.control import ControlRequest

        # Valid permission_mode_change request
        request = ControlRequest(
            type="permission_mode_change",
            permission_mode="acceptEdits",
        )
        assert request.type == "permission_mode_change"
        assert request.permission_mode == "acceptEdits"

    @pytest.mark.anyio
    async def test_control_request_requires_permission_mode_for_change(self) -> None:
        """Test that permission_mode_change type requires permission_mode field."""
        from apps.api.schemas.requests.control import ControlRequest

        with pytest.raises(ValueError):
            ControlRequest(
                type="permission_mode_change",
                # missing permission_mode
            )
