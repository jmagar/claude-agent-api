"""Integration tests for validation error handling (Phase 2 fixes)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import OperationalError
from unittest.mock import AsyncMock, patch


class TestSessionUUIDValidation:
    """Test UUID validation in session endpoints."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_get_session_rejects_invalid_uuid(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that get_session returns 422 for malformed UUID."""
        # Malformed UUID should return 422, not 500
        response = await async_client.get(
            "/api/v1/sessions/not-a-uuid",
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "Invalid session ID format" in data["error"]["message"]
        assert data["error"]["details"]["field"] == "session_id"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_promote_session_rejects_invalid_uuid(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that promote_session returns 422 for malformed UUID."""
        response = await async_client.post(
            "/api/v1/sessions/bad-uuid/promote",
            json={"project_id": "test-project"},
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "Invalid session ID format" in data["error"]["message"]
        assert data["error"]["details"]["field"] == "session_id"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_update_tags_rejects_invalid_uuid(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that update_tags returns 422 for malformed UUID."""
        response = await async_client.patch(
            "/api/v1/sessions/invalid-uuid/tags",
            json={"tags": ["test"]},
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "Invalid session ID format" in data["error"]["message"]
        assert data["error"]["details"]["field"] == "session_id"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_partial_uuid_rejected(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that partial UUIDs are rejected."""
        response = await async_client.get(
            "/api/v1/sessions/123e4567-e89b-12d3",
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_valid_uuid_passes_validation(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that valid UUIDs pass validation (may return 404)."""
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        response = await async_client.get(
            f"/api/v1/sessions/{valid_uuid}",
            headers=auth_headers,
        )

        # Should get 404 (not found), not 422 (validation error)
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "SESSION_NOT_FOUND"


class TestDateTimeParsingValidation:
    """Test datetime parsing error handling in MCP servers."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_corrupted_timestamp_raises_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that corrupted timestamps in database raise validation error."""
        from apps.api.routes.mcp_servers import _parse_datetime
        from apps.api.exceptions import ValidationError

        # Invalid ISO format should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            _parse_datetime("2024-13-45T99:99:99")

        assert exc_info.value.code == "VALIDATION_ERROR"
        assert "Invalid timestamp format" in exc_info.value.message
        assert exc_info.value.details["field"] == "timestamp"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_none_timestamp_returns_now(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that None timestamp returns current time."""
        from apps.api.routes.mcp_servers import _parse_datetime
        from datetime import datetime, UTC

        result = _parse_datetime(None)

        assert isinstance(result, datetime)
        # Should be recent (within last 5 seconds)
        now = datetime.now(UTC)
        assert (now - result).total_seconds() < 5

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_valid_iso_timestamp_parsed(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that valid ISO timestamps are parsed correctly."""
        from apps.api.routes.mcp_servers import _parse_datetime
        from datetime import datetime

        result = _parse_datetime("2024-01-15T10:30:00")

        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30


class TestMcpServerDatabaseErrorHandling:
    """Test database error handling in MCP server endpoints."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_list_servers_handles_operational_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that database unavailability returns 503."""
        with patch(
            "apps.api.services.mcp_server_configs.McpServerConfigService.list_servers_for_api_key",
            side_effect=OperationalError("connection failed", None, None),
        ):
            response = await async_client.get(
                "/api/v1/mcp-servers",
                headers=auth_headers,
            )

            assert response.status_code == 503
            data = response.json()
            assert data["error"]["code"] == "DATABASE_UNAVAILABLE"
            assert "temporarily unavailable" in data["error"]["message"].lower()

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_create_server_handles_operational_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that create_server returns 503 on database failure."""
        with patch(
            "apps.api.services.mcp_server_configs.McpServerConfigService.create_server_for_api_key",
            side_effect=OperationalError("connection timeout", None, None),
        ):
            response = await async_client.post(
                "/api/v1/mcp-servers",
                json={
                    "name": "test-server",
                    "type": "stdio",
                    "config": {"command": "test"},
                },
                headers=auth_headers,
            )

            assert response.status_code == 503
            data = response.json()
            assert data["error"]["code"] == "DATABASE_UNAVAILABLE"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_get_server_handles_operational_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that get_server returns 503 on database failure."""
        with patch(
            "apps.api.services.mcp_server_configs.McpServerConfigService.get_server_for_api_key",
            side_effect=OperationalError("database locked", None, None),
        ):
            response = await async_client.get(
                "/api/v1/mcp-servers/test-server",
                headers=auth_headers,
            )

            assert response.status_code == 503
            data = response.json()
            assert data["error"]["code"] == "DATABASE_UNAVAILABLE"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_update_server_handles_operational_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that update_server returns 503 on database failure."""
        with patch(
            "apps.api.services.mcp_server_configs.McpServerConfigService.update_server_for_api_key",
            side_effect=OperationalError("connection lost", None, None),
        ):
            response = await async_client.put(
                "/api/v1/mcp-servers/test-server",
                json={
                    "type": "stdio",
                    "config": {"command": "updated"},
                },
                headers=auth_headers,
            )

            assert response.status_code == 503
            data = response.json()
            assert data["error"]["code"] == "DATABASE_UNAVAILABLE"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_delete_server_handles_operational_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that delete_server returns 503 on database failure."""
        with patch(
            "apps.api.services.mcp_server_configs.McpServerConfigService.delete_server_for_api_key",
            side_effect=OperationalError("transaction failed", None, None),
        ):
            response = await async_client.delete(
                "/api/v1/mcp-servers/test-server",
                headers=auth_headers,
            )

            assert response.status_code == 503
            data = response.json()
            assert data["error"]["code"] == "DATABASE_UNAVAILABLE"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_list_resources_handles_operational_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that list_resources returns 503 on database failure."""
        with patch(
            "apps.api.services.mcp_server_configs.McpServerConfigService.get_server_for_api_key",
            side_effect=OperationalError("database error", None, None),
        ):
            response = await async_client.get(
                "/api/v1/mcp-servers/test-server/resources",
                headers=auth_headers,
            )

            assert response.status_code == 503
            data = response.json()
            assert data["error"]["code"] == "DATABASE_UNAVAILABLE"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_get_resource_handles_operational_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that get_resource returns 503 on database failure."""
        with patch(
            "apps.api.services.mcp_server_configs.McpServerConfigService.get_server_for_api_key",
            side_effect=OperationalError("query timeout", None, None),
        ):
            response = await async_client.get(
                "/api/v1/mcp-servers/test-server/resources/test-uri",
                headers=auth_headers,
            )

            assert response.status_code == 503
            data = response.json()
            assert data["error"]["code"] == "DATABASE_UNAVAILABLE"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_unexpected_database_error_returns_500(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that unexpected database errors return 500."""
        with patch(
            "apps.api.services.mcp_server_configs.McpServerConfigService.list_servers_for_api_key",
            side_effect=RuntimeError("Unexpected database error"),
        ):
            response = await async_client.get(
                "/api/v1/mcp-servers",
                headers=auth_headers,
            )

            assert response.status_code == 500
            data = response.json()
            assert data["error"]["code"] == "INTERNAL_ERROR"
            # Should not leak internal error details
            assert "RuntimeError" not in data["error"]["message"]
