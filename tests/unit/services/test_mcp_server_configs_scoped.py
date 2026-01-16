"""Unit tests for API-key scoped MCP server configuration service."""

from unittest.mock import AsyncMock

import pytest

from apps.api.services.mcp_server_configs import McpServerConfigService


@pytest.fixture
def mock_cache() -> AsyncMock:
    """Mock cache for testing."""
    cache = AsyncMock()
    cache.set_members = AsyncMock(return_value=set())
    cache.get_many_json = AsyncMock(return_value=[])
    cache.get_json = AsyncMock(return_value=None)
    cache.set_json = AsyncMock()
    cache.add_to_set = AsyncMock()
    cache.remove_from_set = AsyncMock()
    cache.delete = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def service(mock_cache: AsyncMock) -> McpServerConfigService:
    """Create service instance with mock cache."""
    return McpServerConfigService(cache=mock_cache)


def test_server_key_includes_api_key(service: McpServerConfigService) -> None:
    """Test that server key pattern includes API key for isolation."""
    # GIVEN
    api_key = "test-key-123"
    server_name = "my-server"

    # WHEN
    key = service._server_key(api_key, server_name)

    # THEN
    # Expect format: mcp_server:{api_key}:{name}
    assert key == "mcp_server:test-key-123:my-server"
    assert api_key in key
    assert server_name in key


def test_index_key_scoped(service: McpServerConfigService) -> None:
    """Test that index key pattern is scoped to API key."""
    # GIVEN
    api_key = "test-key-456"

    # WHEN
    key = service._index_key(api_key)

    # THEN
    # Expect format: mcp_servers:index:{api_key}
    assert key == "mcp_servers:index:test-key-456"
    assert api_key in key


@pytest.mark.anyio
async def test_list_servers_for_api_key_isolation(
    service: McpServerConfigService, mock_cache: AsyncMock
) -> None:
    """Test that listing servers for one API key doesn't return another's servers."""
    # GIVEN an API key with servers
    api_key_1 = "tenant-1"

    # Mock cache returns for api_key_1
    mock_cache.set_members = AsyncMock(return_value={"server-a"})
    mock_cache.get_many_json = AsyncMock(
        return_value=[
            {
                "id": "id-a",
                "name": "server-a",
                "transport_type": "stdio",
                "command": "cmd-a",
                "args": None,
                "url": None,
                "headers": None,
                "env": None,
                "enabled": True,
                "status": "active",
                "error": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": None,
                "metadata": None,
                "resources": [],
            }
        ]
    )

    # WHEN listing servers for api_key_1
    servers = await service.list_servers_for_api_key(api_key_1)

    # THEN only api_key_1's servers returned
    assert len(servers) == 1
    assert servers[0].name == "server-a"

    # AND cache was queried with api_key_1's index
    mock_cache.set_members.assert_called_once_with("mcp_servers:index:tenant-1")

    # AND cache was queried with api_key_1's server key
    mock_cache.get_many_json.assert_called_once_with(["mcp_server:tenant-1:server-a"])


@pytest.mark.anyio
async def test_create_server_for_api_key(
    service: McpServerConfigService, mock_cache: AsyncMock
) -> None:
    """Test that creating server for API key uses scoped keys."""
    # GIVEN
    api_key = "tenant-xyz"
    server_name = "new-server"
    config = {
        "command": "python",
        "args": ["-m", "server"],
        "enabled": True,
    }

    # Mock no existing server
    mock_cache.get_json = AsyncMock(return_value=None)

    # WHEN creating server for API key
    result = await service.create_server_for_api_key(
        api_key=api_key,
        name=server_name,
        transport_type="stdio",
        config=config,
    )

    # THEN server created successfully
    assert result is not None
    assert result.name == server_name
    assert result.command == "python"

    # AND cache set with scoped key
    expected_key = "mcp_server:tenant-xyz:new-server"
    mock_cache.set_json.assert_called_once()
    actual_key = mock_cache.set_json.call_args[0][0]
    assert actual_key == expected_key

    # AND index updated with scoped key
    expected_index = "mcp_servers:index:tenant-xyz"
    mock_cache.add_to_set.assert_called_once_with(expected_index, server_name)
