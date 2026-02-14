"""Integration tests for MCP servers route dependency injection."""

import inspect

from apps.api.routes import mcp_servers


def test_list_mcp_servers_uses_di_signature() -> None:
    """Verify list_mcp_servers uses DI for mcp services."""
    sig = inspect.signature(mcp_servers.list_mcp_servers)
    params = list(sig.parameters.keys())
    assert "mcp_discovery" in params
    assert "mcp_config" in params
    assert "cache" not in params


def test_create_mcp_server_uses_di_signature() -> None:
    """Verify create_mcp_server uses DI for mcp_config."""
    sig = inspect.signature(mcp_servers.create_mcp_server)
    params = list(sig.parameters.keys())
    assert "mcp_config" in params
    assert "cache" not in params


def test_get_mcp_server_uses_di_signature() -> None:
    """Verify get_mcp_server uses DI for mcp services."""
    sig = inspect.signature(mcp_servers.get_mcp_server)
    params = list(sig.parameters.keys())
    assert "mcp_discovery" in params
    assert "mcp_config" in params
    assert "cache" not in params


def test_update_mcp_server_uses_di_signature() -> None:
    """Verify update_mcp_server uses DI for mcp_config."""
    sig = inspect.signature(mcp_servers.update_mcp_server)
    params = list(sig.parameters.keys())
    assert "mcp_config" in params
    assert "cache" not in params


def test_delete_mcp_server_uses_di_signature() -> None:
    """Verify delete_mcp_server uses DI for mcp_config."""
    sig = inspect.signature(mcp_servers.delete_mcp_server)
    params = list(sig.parameters.keys())
    assert "mcp_config" in params
    assert "cache" not in params


def test_list_mcp_resources_uses_di_signature() -> None:
    """Verify list_mcp_resources uses DI for mcp_config."""
    sig = inspect.signature(mcp_servers.list_mcp_resources)
    params = list(sig.parameters.keys())
    assert "mcp_config" in params
    assert "cache" not in params


def test_get_mcp_resource_uses_di_signature() -> None:
    """Verify get_mcp_resource uses DI for mcp_config."""
    sig = inspect.signature(mcp_servers.get_mcp_resource)
    params = list(sig.parameters.keys())
    assert "mcp_config" in params
    assert "cache" not in params


def test_create_mcp_share_uses_di_signature() -> None:
    """Verify create_mcp_share uses DI for mcp_share."""
    sig = inspect.signature(mcp_servers.create_mcp_share)
    params = list(sig.parameters.keys())
    assert "mcp_share" in params
    assert "cache" not in params


def test_get_mcp_share_uses_di_signature() -> None:
    """Verify get_mcp_share uses DI for mcp_share."""
    sig = inspect.signature(mcp_servers.get_mcp_share)
    params = list(sig.parameters.keys())
    assert "mcp_share" in params
    assert "cache" not in params


def test_no_helper_functions_exist() -> None:
    """Verify helper functions have been removed."""
    assert not hasattr(mcp_servers, "_get_mcp_discovery_service")
