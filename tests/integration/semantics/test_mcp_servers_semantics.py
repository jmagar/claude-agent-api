"""Exhaustive semantic tests for MCP Server Configuration endpoints.

Tests full CRUD operations, validation, multi-tenant isolation, edge cases,
and error handling for the /api/v1/mcp-servers endpoint group.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# =============================================================================
# Helper: Create MCP server via API
# =============================================================================


async def _create_mcp_server(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    name: str | None = None,
    transport_type: str = "stdio",
    config: dict[str, object] | None = None,
) -> dict[str, object]:
    """Create an MCP server and return the response JSON.

    Args:
        client: HTTP test client.
        headers: Auth headers with API key.
        name: Server name (auto-generated if None).
        transport_type: Transport type (default "stdio").
        config: Server config dict (default empty).

    Returns:
        Parsed JSON response body.
    """
    if name is None:
        name = f"test-mcp-{uuid4().hex[:8]}"
    if config is None:
        config = {"command": "echo", "args": ["hello"]}

    response = await client.post(
        "/api/v1/mcp-servers",
        json={"name": name, "type": transport_type, "config": config},
        headers=headers,
    )
    assert response.status_code == 201, f"MCP server creation failed: {response.text}"
    return response.json()


# =============================================================================
# List MCP Servers Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_mcp_servers_returns_servers_array(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing MCP servers returns a response with servers array.

    Validates the list endpoint returns proper structure with a
    servers array, even when no database servers exist.
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
async def test_list_mcp_servers_includes_created_server(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing MCP servers after creation includes the newly created server.

    Validates that a server created via POST appears in the subsequent
    GET list filtered to database source only.
    """
    # ARRANGE
    server = await _create_mcp_server(async_client, auth_headers)
    server_name = server["name"]

    # ACT
    response = await async_client.get(
        "/api/v1/mcp-servers",
        params={"source": "database"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    names = [s["name"] for s in data["servers"]]
    assert server_name in names


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_mcp_servers_filter_by_source_database(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Filtering by source=database returns only database-sourced servers.

    Validates that source query parameter correctly filters results
    to only database-backed servers (not filesystem).
    """
    # ARRANGE
    await _create_mcp_server(async_client, auth_headers)

    # ACT
    response = await async_client.get(
        "/api/v1/mcp-servers",
        params={"source": "database"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    for server in data["servers"]:
        assert server["source"] == "database"


# =============================================================================
# Create MCP Server Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_mcp_server_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an MCP server returns 201 with full server configuration.

    Validates that the response includes all expected fields: id, name,
    transport_type, command, enabled, status, source, and timestamps.
    """
    # ARRANGE
    name = f"create-test-{uuid4().hex[:8]}"

    # ACT
    response = await async_client.post(
        "/api/v1/mcp-servers",
        json={
            "name": name,
            "type": "stdio",
            "config": {
                "command": "python",
                "args": ["-m", "my_mcp_server"],
                "env": {"LOG_LEVEL": "debug"},
            },
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == name
    assert data["transport_type"] == "stdio"
    assert data["command"] == "python"
    assert data["args"] == ["-m", "my_mcp_server"]
    assert data["enabled"] is True
    assert data["status"] == "active"
    assert data["source"] == "database"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_mcp_server_duplicate_name_returns_409(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an MCP server with a duplicate name returns 409 conflict.

    The service layer checks for existing servers with the same name
    scoped to the API key and returns MCP_SERVER_EXISTS error.
    """
    # ARRANGE
    name = f"dup-test-{uuid4().hex[:8]}"
    await _create_mcp_server(async_client, auth_headers, name=name)

    # ACT - Create another server with the same name
    response = await async_client.post(
        "/api/v1/mcp-servers",
        json={"name": name, "type": "stdio", "config": {}},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 409
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MCP_SERVER_EXISTS"


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_mcp_server_validates_name_required(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an MCP server without a name returns 422 validation error.

    The name field is required with min_length=1. Omitting it should
    trigger Pydantic validation and return 422 Unprocessable Entity.
    """
    # ACT
    response = await async_client.post(
        "/api/v1/mcp-servers",
        json={"type": "stdio", "config": {}},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_mcp_server_validates_empty_name(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an MCP server with empty name returns 422 validation error.

    Validates the min_length=1 constraint on the name field.
    """
    # ACT
    response = await async_client.post(
        "/api/v1/mcp-servers",
        json={"name": "", "type": "stdio", "config": {}},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_mcp_server_validates_name_max_length(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an MCP server with name exceeding 100 chars returns 422.

    Validates the max_length=100 constraint on the name field.
    """
    # ACT
    long_name = "x" * 101
    response = await async_client.post(
        "/api/v1/mcp-servers",
        json={"name": long_name, "type": "stdio", "config": {}},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_mcp_server_validates_type_required(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an MCP server without type field returns 422 validation error.

    The type field is required in McpServerCreateRequest.
    """
    # ACT
    response = await async_client.post(
        "/api/v1/mcp-servers",
        json={"name": f"no-type-{uuid4().hex[:8]}"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


# =============================================================================
# Get MCP Server Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_mcp_server_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting an MCP server by name returns full server data.

    Validates that the returned server matches the originally created
    data including name, transport_type, command, and configuration.
    """
    # ARRANGE
    created = await _create_mcp_server(
        async_client,
        auth_headers,
        config={"command": "node", "args": ["server.js"]},
    )
    server_name = created["name"]

    # ACT
    response = await async_client.get(
        f"/api/v1/mcp-servers/{server_name}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == server_name
    assert data["id"] == created["id"]
    assert data["command"] == "node"
    assert data["args"] == ["server.js"]
    assert data["source"] == "database"


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_mcp_server_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a nonexistent MCP server returns 404 with MCP_SERVER_NOT_FOUND.

    Validates error response structure with correct error code for
    consistent client-side error handling.
    """
    # ACT
    response = await async_client.get(
        f"/api/v1/mcp-servers/nonexistent-{uuid4().hex[:8]}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MCP_SERVER_NOT_FOUND"


# =============================================================================
# Update MCP Server Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_mcp_server_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Updating an MCP server persists changes correctly.

    Validates that PUT updates the transport_type and config fields
    while preserving the server name and id.
    """
    # ARRANGE
    created = await _create_mcp_server(async_client, auth_headers)
    server_name = created["name"]

    # ACT
    response = await async_client.put(
        f"/api/v1/mcp-servers/{server_name}",
        json={
            "type": "sse",
            "config": {"url": "http://example.com/mcp"},
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == server_name
    assert data["id"] == created["id"]
    assert data["transport_type"] == "sse"
    assert data["url"] == "http://example.com/mcp"
    assert data["updated_at"] is not None

    # Verify persistence by re-fetching
    get_response = await async_client.get(
        f"/api/v1/mcp-servers/{server_name}",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["transport_type"] == "sse"
    assert fetched["url"] == "http://example.com/mcp"


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_mcp_server_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Updating a nonexistent MCP server returns 404 with MCP_SERVER_NOT_FOUND.

    Validates that attempting to update a server that does not exist
    returns a proper error response rather than silently creating.
    """
    # ACT
    response = await async_client.put(
        f"/api/v1/mcp-servers/nonexistent-{uuid4().hex[:8]}",
        json={"type": "stdio", "config": {}},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MCP_SERVER_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_filesystem_server_returns_400(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Updating a filesystem MCP server returns 400 MCP_SERVER_READONLY.

    Filesystem servers (prefixed with fs:) are read-only and cannot
    be modified via the API. Users must edit the config file directly.
    """
    # ACT
    response = await async_client.put(
        "/api/v1/mcp-servers/fs:some-server",
        json={"type": "stdio", "config": {}},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MCP_SERVER_READONLY"


# =============================================================================
# Delete MCP Server Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_mcp_server_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting an MCP server returns 204 and subsequent GET returns 404.

    Creates a dedicated server, deletes it, and verifies it is gone.
    """
    # ARRANGE
    created = await _create_mcp_server(async_client, auth_headers)
    server_name = created["name"]

    # ACT
    delete_response = await async_client.delete(
        f"/api/v1/mcp-servers/{server_name}",
        headers=auth_headers,
    )

    # ASSERT - Deletion returns 204 No Content
    assert delete_response.status_code == 204

    # Verify server is gone
    get_response = await async_client.get(
        f"/api/v1/mcp-servers/{server_name}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404
    data = get_response.json()
    assert data["error"]["code"] == "MCP_SERVER_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_mcp_server_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a nonexistent MCP server returns 404 with MCP_SERVER_NOT_FOUND.

    Validates proper error handling for delete operations on
    servers that do not exist.
    """
    # ACT
    response = await async_client.delete(
        f"/api/v1/mcp-servers/nonexistent-{uuid4().hex[:8]}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MCP_SERVER_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_filesystem_server_returns_400(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a filesystem MCP server returns 400 MCP_SERVER_READONLY.

    Filesystem servers are read-only and cannot be deleted via API.
    """
    # ACT
    response = await async_client.delete(
        "/api/v1/mcp-servers/fs:some-server",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MCP_SERVER_READONLY"


# =============================================================================
# Multi-Tenant Isolation Tests (Service Layer)
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_mcp_server_tenant_isolation_list(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Servers created by one API key are not visible to another via service layer.

    Validates that the API-key scoped Redis keys ensure complete isolation
    between tenants at the service level. Uses service layer directly because
    the auth middleware validates a single configured API key.
    """
    from fastapi import Request

    from apps.api.dependencies import get_app_state
    from apps.api.services.mcp_server_configs import McpServerConfigService

    # ARRANGE - Create server for primary tenant via API
    server = await _create_mcp_server(async_client, auth_headers)
    server_name = server["name"]
    assert isinstance(server_name, str)

    # Get service from app state
    request = Request(scope={"type": "http", "app": async_client._transport.app})  # type: ignore[arg-type]
    app_state = get_app_state(request)
    assert app_state.cache is not None
    service = McpServerConfigService(cache=app_state.cache)

    # ACT - List servers for a different API key (simulated second tenant)
    second_api_key = f"tenant-{uuid4().hex[:8]}"
    second_tenant_servers = await service.list_servers_for_api_key(second_api_key)

    # ASSERT - Second tenant should not see primary tenant's server
    names = [s.name for s in second_tenant_servers]
    assert server_name not in names


@pytest.mark.integration
@pytest.mark.anyio
async def test_mcp_server_tenant_isolation_get(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting another tenant's server by name returns None at service layer.

    Validates that API-key scoping prevents cross-tenant access
    to individual server configurations.
    """
    from fastapi import Request

    from apps.api.dependencies import get_app_state
    from apps.api.services.mcp_server_configs import McpServerConfigService

    # ARRANGE - Create server for primary tenant via API
    server = await _create_mcp_server(async_client, auth_headers)
    server_name = server["name"]
    assert isinstance(server_name, str)

    # Get service from app state
    request = Request(scope={"type": "http", "app": async_client._transport.app})  # type: ignore[arg-type]
    app_state = get_app_state(request)
    assert app_state.cache is not None
    service = McpServerConfigService(cache=app_state.cache)

    # ACT - Try to access as second tenant
    second_api_key = f"tenant-{uuid4().hex[:8]}"
    result = await service.get_server_for_api_key(second_api_key, server_name)

    # ASSERT - Should be None (not visible to other tenant)
    assert result is None


@pytest.mark.integration
@pytest.mark.anyio
async def test_mcp_server_tenant_isolation_same_name_different_tenants(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Two tenants can create servers with the same name independently.

    Validates that API-key scoped namespacing allows identical names
    across different tenants without conflict at the service layer.
    """
    from fastapi import Request

    from apps.api.dependencies import get_app_state
    from apps.api.services.mcp_server_configs import McpServerConfigService

    # ARRANGE
    shared_name = f"shared-name-{uuid4().hex[:8]}"

    # Create server for primary tenant via API
    response_1 = await async_client.post(
        "/api/v1/mcp-servers",
        json={"name": shared_name, "type": "stdio", "config": {"command": "a"}},
        headers=auth_headers,
    )
    assert response_1.status_code == 201

    # Get service from app state for second tenant
    request = Request(scope={"type": "http", "app": async_client._transport.app})  # type: ignore[arg-type]
    app_state = get_app_state(request)
    assert app_state.cache is not None
    service = McpServerConfigService(cache=app_state.cache)

    # ACT - Second tenant creates server with the same name via service layer
    second_api_key = f"tenant-{uuid4().hex[:8]}"
    result = await service.create_server_for_api_key(
        api_key=second_api_key,
        name=shared_name,
        transport_type="sse",
        config={"url": "http://example.com/b"},
    )

    # ASSERT - Both succeed with different configs
    assert result is not None
    assert result.transport_type == "sse"
    assert response_1.json()["transport_type"] == "stdio"


# =============================================================================
# Sensitive Data Sanitization Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_mcp_server_redacts_sensitive_env_vars(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an MCP server with sensitive env vars redacts them in response.

    Validates that environment variables with names matching sensitive
    patterns (api_key, token, password, etc.) are redacted to prevent
    credential leakage in API responses.
    """
    # ARRANGE
    name = f"redact-test-{uuid4().hex[:8]}"

    # ACT
    response = await async_client.post(
        "/api/v1/mcp-servers",
        json={
            "name": name,
            "type": "stdio",
            "config": {
                "command": "python",
                "env": {
                    "API_KEY": "super-secret-key",
                    "DATABASE_PASSWORD": "db-pass-123",
                    "LOG_LEVEL": "debug",
                },
            },
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 201
    data = response.json()
    env = data.get("env", {})
    # Sensitive keys should be redacted
    assert env.get("API_KEY") == "***REDACTED***"
    assert env.get("DATABASE_PASSWORD") == "***REDACTED***"
    # Non-sensitive keys should be preserved
    assert env.get("LOG_LEVEL") == "debug"


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_mcp_server_redacts_sensitive_headers(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an MCP server with sensitive headers redacts them in response.

    Validates that headers matching sensitive patterns (authorization,
    token, auth) are redacted to prevent credential leakage.
    """
    # ARRANGE
    name = f"header-redact-{uuid4().hex[:8]}"

    # ACT
    response = await async_client.post(
        "/api/v1/mcp-servers",
        json={
            "name": name,
            "type": "sse",
            "config": {
                "url": "http://example.com/mcp",
                "headers": {
                    "Authorization": "Bearer secret-token",
                    "X-Custom-Token": "another-secret",
                    "Content-Type": "application/json",
                },
            },
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 201
    data = response.json()
    headers = data.get("headers", {})
    # Sensitive headers should be redacted
    assert headers.get("Authorization") == "***REDACTED***"
    assert headers.get("X-Custom-Token") == "***REDACTED***"
    # Non-sensitive headers should be preserved
    assert headers.get("Content-Type") == "application/json"


# =============================================================================
# Edge Cases & Configuration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_mcp_server_with_empty_config(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an MCP server with empty config defaults correctly.

    Validates that a server can be created with minimal config and
    that default values are applied (enabled=True, status=active).
    """
    # ARRANGE
    name = f"empty-config-{uuid4().hex[:8]}"

    # ACT
    response = await async_client.post(
        "/api/v1/mcp-servers",
        json={"name": name, "type": "stdio", "config": {}},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == name
    assert data["enabled"] is True
    assert data["status"] == "active"
    assert data["command"] is None
    assert data["source"] == "database"


@pytest.mark.integration
@pytest.mark.anyio
async def test_full_crud_lifecycle(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Full CRUD lifecycle: create, get, update, delete.

    End-to-end test that validates the complete lifecycle of an MCP
    server configuration through all CRUD operations.
    """
    name = f"lifecycle-{uuid4().hex[:8]}"

    # CREATE
    create_resp = await async_client.post(
        "/api/v1/mcp-servers",
        json={
            "name": name,
            "type": "stdio",
            "config": {"command": "python", "args": ["-m", "server"]},
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["name"] == name
    server_id = created["id"]

    # GET
    get_resp = await async_client.get(
        f"/api/v1/mcp-servers/{name}",
        headers=auth_headers,
    )
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == server_id
    assert fetched["command"] == "python"

    # UPDATE
    update_resp = await async_client.put(
        f"/api/v1/mcp-servers/{name}",
        json={
            "type": "sse",
            "config": {"url": "http://localhost:9000/mcp"},
        },
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["id"] == server_id
    assert updated["transport_type"] == "sse"
    assert updated["url"] == "http://localhost:9000/mcp"

    # DELETE
    delete_resp = await async_client.delete(
        f"/api/v1/mcp-servers/{name}",
        headers=auth_headers,
    )
    assert delete_resp.status_code == 204

    # VERIFY DELETED
    verify_resp = await async_client.get(
        f"/api/v1/mcp-servers/{name}",
        headers=auth_headers,
    )
    assert verify_resp.status_code == 404
