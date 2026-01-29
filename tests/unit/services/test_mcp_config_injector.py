"""Unit tests for MCP config injector service.

Tests the McpConfigInjector which coordinates config loading, merging,
validation, and injection into QueryRequest objects.

TDD Phase: RED - Tests written first, expected to fail.
"""

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock

import pytest

from apps.api.schemas.requests.query import QueryRequest
from apps.api.services.mcp_config_injector import McpConfigInjector


@pytest.fixture
def mock_loader() -> Generator[Mock, None, None]:
    """Mock config loader dependency."""
    loader = Mock()
    loader.load_application_config.return_value = {
        "app-server": {"command": "app-cmd", "type": "stdio"}
    }
    loader.resolve_env_vars.return_value = {
        "app-server": {"command": "app-cmd", "type": "stdio"}
    }
    loader.merge_configs.return_value = {
        "merged-server": {"command": "merged-cmd", "type": "stdio"}
    }
    yield loader


@pytest.fixture
def mock_validator() -> Generator[Mock, None, None]:
    """Mock config validator dependency."""
    validator = Mock()
    validator.sanitize_credentials.return_value = {
        "server": {"command": "***REDACTED***", "type": "stdio"}
    }
    validator.validate_config.return_value = None  # No-op, validation passes
    yield validator


@pytest.fixture
def mock_config_service() -> Generator[Mock, None, None]:
    """Mock database service dependency."""
    service = Mock()
    service.list_servers_for_api_key = AsyncMock(
        return_value=[
            Mock(
                name="db-server",
                command="db-cmd",
                args=None,
                env=None,
                url=None,
                headers=None,
                enabled=True,
                transport_type="stdio",
            )
        ]
    )
    yield service


@pytest.fixture
def injector(mock_loader: Mock, mock_config_service: Mock) -> McpConfigInjector:
    """Create injector with mocked dependencies."""
    return McpConfigInjector(
        config_loader=mock_loader,
        config_service=mock_config_service,
    )


@pytest.mark.anyio
async def test_inject_with_null_request_mcp_servers(
    injector: McpConfigInjector, mock_loader: Mock
) -> None:
    """Test injection uses server-side configs when request mcp_servers is null."""
    request = QueryRequest(
        prompt="test query",
        mcp_servers=None,  # null = use server-side
    )

    result = await injector.inject(request, api_key="test-api-key")

    # Should have merged configs from application + api-key tiers
    assert result.mcp_servers is not None
    assert "merged-server" in result.mcp_servers
    mock_loader.merge_configs.assert_called_once()


@pytest.mark.anyio
async def test_inject_with_empty_dict_opts_out(
    injector: McpConfigInjector, mock_loader: Mock
) -> None:
    """Test injection preserves empty dict (opt-out mechanism)."""
    request = QueryRequest(
        prompt="test query",
        mcp_servers={},  # empty dict = opt-out
    )

    result = await injector.inject(request, api_key="test-api-key")

    # Should return unchanged (opt-out)
    assert result.mcp_servers == {}
    mock_loader.merge_configs.assert_not_called()


@pytest.mark.anyio
async def test_inject_logs_sanitized_config(
    injector: McpConfigInjector,
    mock_validator: Mock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test injection logs sanitized config (not raw credentials).

    This test expects validator integration which will be added in GREEN phase.
    Currently expected to fail as validator is not yet integrated.
    """
    # Add validator to injector (simulating GREEN phase implementation)
    injector.validator = mock_validator

    request = QueryRequest(prompt="test query", mcp_servers=None)

    await injector.inject(request, api_key="test-api-key")

    # Should have called sanitizer before logging (GREEN phase will implement)
    # For now, this will fail since validator is not integrated
    mock_validator.sanitize_credentials.assert_called()


@pytest.mark.anyio
async def test_inject_with_request_override(
    injector: McpConfigInjector, mock_loader: Mock
) -> None:
    """Test injection preserves request config when provided."""
    from apps.api.schemas.requests.config import McpServerConfigSchema

    request = QueryRequest(
        prompt="test query",
        mcp_servers={
            "request-server": McpServerConfigSchema(command="request-cmd", type="stdio")
        },
    )

    result = await injector.inject(request, api_key="test-api-key")

    # Should merge with request tier having highest priority
    assert result.mcp_servers is not None
    mock_loader.merge_configs.assert_called_once()
    # Verify merge_configs received request mcp_servers as third argument
    call_args = mock_loader.merge_configs.call_args
    # Should have dict with server config
    assert call_args[1]["request_config"] is not None
    assert "request-server" in call_args[1]["request_config"]
