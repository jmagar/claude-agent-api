"""Exhaustive semantic tests for MCP Discovery endpoints.

Tests filesystem-based MCP server discovery, source filtering,
filesystem server access patterns, and readonly enforcement.
Covers Task 2 from Phase 3 semantic tests plan.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# =============================================================================
# MCP Discovery: List Servers with Source Filtering
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_mcp_servers_returns_valid_structure(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing MCP servers returns response with servers array.

    Validates the base response shape: a dict with a 'servers' key
    containing a list, regardless of how many servers are discovered.
    """
    # ACT
    response = await async_client.get(
        "/api/v1/mcp-servers",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert "servers" in data
    assert isinstance(data["servers"], list)


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_mcp_servers_filesystem_source_filter(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Filtering by source=filesystem returns only filesystem-discovered servers.

    All returned servers must have source='filesystem' and IDs
    prefixed with 'fs:'.
    """
    # ACT
    response = await async_client.get(
        "/api/v1/mcp-servers",
        params={"source": "filesystem"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["servers"], list)

    for server in data["servers"]:
        assert server["source"] == "filesystem"
        assert server["id"].startswith("fs:")
        assert server["enabled"] is True
        assert server["status"] == "active"


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_mcp_servers_database_source_filter(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Filtering by source=database returns only database-stored servers.

    All returned servers must have source='database' and should not
    have 'fs:' prefixed IDs.
    """
    # ACT
    response = await async_client.get(
        "/api/v1/mcp-servers",
        params={"source": "database"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["servers"], list)

    for server in data["servers"]:
        assert server["source"] == "database"
        assert not server["id"].startswith("fs:")


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_mcp_servers_no_filter_includes_both_sources(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing without source filter returns servers from all sources.

    Creates a database server to ensure both sources are represented,
    then verifies the unfiltered list can contain both filesystem
    and database servers.
    """
    # ARRANGE - Create a database server so we know at least one exists
    suffix = uuid4().hex[:8]
    server_name = f"discovery-test-{suffix}"
    create_response = await async_client.post(
        "/api/v1/mcp-servers",
        json={
            "name": server_name,
            "type": "stdio",
            "config": {"command": "echo", "args": ["hello"]},
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201

    try:
        # ACT
        response = await async_client.get(
            "/api/v1/mcp-servers",
            headers=auth_headers,
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        sources = {s["source"] for s in data["servers"]}
        # At minimum, database source should be present
        assert "database" in sources

        # Verify the created server appears
        names = [s["name"] for s in data["servers"]]
        assert server_name in names
    finally:
        # Cleanup
        await async_client.delete(
            f"/api/v1/mcp-servers/{server_name}",
            headers=auth_headers,
        )


# =============================================================================
# MCP Discovery: Filesystem Server Field Validation
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_filesystem_server_has_required_fields(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Filesystem-discovered servers include all required response fields.

    Each filesystem server must have id, name, transport_type, enabled,
    status, and source fields properly populated.
    """
    # ACT
    response = await async_client.get(
        "/api/v1/mcp-servers",
        params={"source": "filesystem"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()

    for server in data["servers"]:
        assert "id" in server
        assert "name" in server
        assert "transport_type" in server
        assert "enabled" in server
        assert "status" in server
        assert "source" in server
        assert server["transport_type"] in ("stdio", "sse", "http")


# =============================================================================
# MCP Discovery: Get Server by Name
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_filesystem_server_by_fs_prefix(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a filesystem server by fs:-prefixed name returns it.

    First discovers available filesystem servers, then fetches one
    by its fs:-prefixed name to validate the lookup path.
    """
    # ARRANGE - Get list of filesystem servers first
    list_response = await async_client.get(
        "/api/v1/mcp-servers",
        params={"source": "filesystem"},
        headers=auth_headers,
    )
    assert list_response.status_code == 200
    fs_servers = list_response.json()["servers"]

    if not fs_servers:
        pytest.skip("No filesystem MCP servers discovered")

    # Use the first discovered filesystem server
    server_name = fs_servers[0]["name"]

    # ACT
    response = await async_client.get(
        f"/api/v1/mcp-servers/fs:{server_name}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == server_name
    assert data["source"] == "filesystem"
    assert data["id"].startswith("fs:")


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_nonexistent_filesystem_server_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a nonexistent filesystem server returns 404 with MCP_SERVER_NOT_FOUND.

    Validates that the fs: prefix lookup path returns a proper error
    when the server name does not match any discovered config.
    """
    # ARRANGE
    fake_name = f"nonexistent-fs-server-{uuid4().hex[:8]}"

    # ACT
    response = await async_client.get(
        f"/api/v1/mcp-servers/fs:{fake_name}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MCP_SERVER_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_nonexistent_database_server_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a nonexistent database server returns 404 with MCP_SERVER_NOT_FOUND.

    Validates the database lookup path when no fs: prefix is used
    and the server name does not exist in the database.
    """
    # ARRANGE
    fake_name = f"nonexistent-db-server-{uuid4().hex[:8]}"

    # ACT
    response = await async_client.get(
        f"/api/v1/mcp-servers/{fake_name}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MCP_SERVER_NOT_FOUND"


# =============================================================================
# MCP Discovery: Filesystem Server Readonly Enforcement
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_filesystem_server_rejected(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Updating a filesystem server via API returns 400 MCP_SERVER_READONLY.

    Filesystem servers are discovered from config files and cannot
    be modified through the API. The fs: prefix triggers a readonly check.
    """
    # ARRANGE
    fake_fs_name = f"fs:some-server-{uuid4().hex[:8]}"

    # ACT
    response = await async_client.put(
        f"/api/v1/mcp-servers/{fake_fs_name}",
        json={"type": "stdio", "config": {"command": "echo"}},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MCP_SERVER_READONLY"


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_filesystem_server_rejected(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a filesystem server via API returns 400 MCP_SERVER_READONLY.

    Filesystem servers cannot be removed through the API. Users must
    edit the config file directly to remove them.
    """
    # ARRANGE
    fake_fs_name = f"fs:some-server-{uuid4().hex[:8]}"

    # ACT
    response = await async_client.delete(
        f"/api/v1/mcp-servers/{fake_fs_name}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MCP_SERVER_READONLY"


# =============================================================================
# MCP Discovery: Credential Sanitization
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_filesystem_servers_redact_sensitive_env_vars(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Filesystem server env vars with sensitive keys are redacted in responses.

    Servers discovered from config files that have environment variables
    matching sensitive patterns (api_key, token, secret, password, etc.)
    must have their values replaced with '***REDACTED***'.
    """
    # ACT
    response = await async_client.get(
        "/api/v1/mcp-servers",
        params={"source": "filesystem"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()

    for server in data["servers"]:
        env = server.get("env", {})
        if env:
            for key, value in env.items():
                lower_key = key.lower()
                if any(
                    pattern in lower_key
                    for pattern in [
                        "api_key",
                        "apikey",
                        "secret",
                        "password",
                        "token",
                        "auth",
                        "credential",
                    ]
                ):
                    assert value == "***REDACTED***", (
                        f"Sensitive env var '{key}' on server "
                        f"'{server['name']}' was not redacted"
                    )
