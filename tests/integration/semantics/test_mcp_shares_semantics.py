"""Exhaustive semantic tests for MCP Share Token endpoints.

Tests share token creation, credential sanitization, token uniqueness,
validation, authentication, and the GET share routing behavior.

Endpoints under test:
  POST /api/v1/mcp-servers/{name}/share  - create share token
  GET  /api/v1/mcp-servers/share         - resolve share token

Note: The GET /share endpoint is shadowed by the config router's
GET /{name} route because config_router is registered before share_router.
FastAPI matches /{name} with name="share" before the literal /share route.
Tests document this routing behavior explicitly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# =============================================================================
# Helper: Create a share token via API
# =============================================================================


async def _create_share(
    client: AsyncClient,
    headers: dict[str, str],
    name: str = "test-server",
    config: dict[str, object] | None = None,
) -> dict[str, object]:
    """Create a share token and return the response JSON.

    Args:
        client: Async HTTP client.
        headers: Auth headers with API key.
        name: MCP server name.
        config: MCP server configuration to share.

    Returns:
        Response JSON dict with share_token, name, config, created_at.
    """
    if config is None:
        config = {"type": "stdio", "command": "echo", "args": ["hello"]}

    response = await client.post(
        f"/api/v1/mcp-servers/{name}/share",
        json={"config": config},
        headers=headers,
    )
    assert response.status_code == 200, f"Share creation failed: {response.text}"
    return response.json()


# =============================================================================
# Create Share Token Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_share_token_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a share token returns token, server name, config, and timestamp.

    Validates that the response contains all required fields with correct
    types and that the server name matches the path parameter.
    """
    # ARRANGE
    server_name = f"share-server-{uuid4().hex[:8]}"
    config: dict[str, object] = {
        "type": "stdio",
        "command": "mcp-test",
        "args": ["--verbose"],
    }

    # ACT
    response = await async_client.post(
        f"/api/v1/mcp-servers/{server_name}/share",
        json={"config": config},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()

    assert "share_token" in data
    assert isinstance(data["share_token"], str)
    assert len(data["share_token"]) > 0

    assert data["name"] == server_name
    assert data["config"] == config
    assert "created_at" in data
    assert isinstance(data["created_at"], str)


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_share_token_sanitizes_env_credentials(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a share token redacts sensitive env vars like API keys and tokens.

    Validates that environment variables matching sensitive patterns
    (api_key, token, password, secret, auth, credential) are replaced
    with '***REDACTED***' in the response config.
    """
    # ARRANGE
    server_name = f"secret-server-{uuid4().hex[:8]}"
    config: dict[str, object] = {
        "type": "stdio",
        "command": "mcp-secret",
        "env": {
            "GITHUB_API_KEY": "ghp_super_secret_123",
            "AUTH_TOKEN": "tok_secret_456",
            "DATABASE_PASSWORD": "p@ssw0rd",
            "NORMAL_VAR": "safe-value",
        },
    }

    # ACT
    response = await async_client.post(
        f"/api/v1/mcp-servers/{server_name}/share",
        json={"config": config},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    env = data["config"]["env"]

    # Sensitive keys should be redacted
    assert env["GITHUB_API_KEY"] == "***REDACTED***"
    assert env["AUTH_TOKEN"] == "***REDACTED***"
    assert env["DATABASE_PASSWORD"] == "***REDACTED***"

    # Non-sensitive keys should be preserved
    assert env["NORMAL_VAR"] == "safe-value"


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_share_token_sanitizes_headers(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a share token redacts sensitive HTTP headers like Authorization.

    Validates that headers matching sensitive patterns (auth, token,
    authorization) are replaced with '***REDACTED***'.
    """
    # ARRANGE
    server_name = f"header-server-{uuid4().hex[:8]}"
    config: dict[str, object] = {
        "type": "sse",
        "url": "https://example.com/mcp",
        "headers": {
            "Authorization": "Bearer sk-secret-key",
            "X-Auth-Token": "secret-token",
            "Content-Type": "application/json",
        },
    }

    # ACT
    response = await async_client.post(
        f"/api/v1/mcp-servers/{server_name}/share",
        json={"config": config},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    headers = data["config"]["headers"]

    # Sensitive headers should be redacted
    assert headers["Authorization"] == "***REDACTED***"
    assert headers["X-Auth-Token"] == "***REDACTED***"

    # Non-sensitive headers should be preserved
    assert headers["Content-Type"] == "application/json"


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_share_token_unique_per_call(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Each share token creation returns a unique token even for identical config.

    Validates that the service generates cryptographically unique tokens
    and does not deduplicate based on config content.
    """
    # ARRANGE
    server_name = f"unique-server-{uuid4().hex[:8]}"
    config: dict[str, object] = {"type": "stdio", "command": "echo"}

    # ACT - Create two shares with identical config
    data1 = await _create_share(async_client, auth_headers, server_name, config)
    data2 = await _create_share(async_client, auth_headers, server_name, config)

    # ASSERT - Tokens must be different
    assert data1["share_token"] != data2["share_token"]

    # Both should have valid structure
    assert data1["name"] == server_name
    assert data2["name"] == server_name


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_share_token_missing_config_returns_422(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a share token without the required config field returns 422.

    The McpShareCreateRequest schema requires a 'config' field.
    Omitting it triggers Pydantic validation error.
    """
    # ACT
    response = await async_client.post(
        "/api/v1/mcp-servers/test-server/share",
        json={},
        headers=auth_headers,
    )

    # ASSERT - config is required (Field(...)), so omitting it triggers 422
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_share_token_requires_auth(
    async_client: AsyncClient,
) -> None:
    """Creating a share token without authentication returns 401.

    Validates that the API key middleware rejects unauthenticated requests.
    """
    # ACT - No auth headers
    response = await async_client.post(
        "/api/v1/mcp-servers/test-server/share",
        json={"config": {"type": "stdio", "command": "echo"}},
    )

    # ASSERT
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_share_token_with_empty_config(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a share token with an empty config dict succeeds.

    An empty config is a valid dict value for the config field.
    The endpoint should accept it without error.
    """
    # ARRANGE
    server_name = f"empty-config-{uuid4().hex[:8]}"

    # ACT
    response = await async_client.post(
        f"/api/v1/mcp-servers/{server_name}/share",
        json={"config": {}},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == server_name
    assert data["config"] == {}
    assert "share_token" in data


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_share_token_preserves_non_sensitive_env(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Non-sensitive env vars are preserved as strings through sanitization.

    Validates that environment variables NOT matching sensitive patterns
    are converted to strings and returned unchanged.
    """
    # ARRANGE
    server_name = f"safe-env-{uuid4().hex[:8]}"
    config: dict[str, object] = {
        "type": "stdio",
        "command": "mcp-safe",
        "env": {
            "HOME": "/home/user",
            "PATH": "/usr/bin:/usr/local/bin",
            "NODE_ENV": "production",
            "LOG_LEVEL": "debug",
        },
    }

    # ACT
    response = await async_client.post(
        f"/api/v1/mcp-servers/{server_name}/share",
        json={"config": config},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    env = data["config"]["env"]

    assert env["HOME"] == "/home/user"
    assert env["PATH"] == "/usr/bin:/usr/local/bin"
    assert env["NODE_ENV"] == "production"
    assert env["LOG_LEVEL"] == "debug"


# =============================================================================
# Resolve Share Token Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_resolve_share_route_shadowed_by_config_route(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /mcp-servers/share is shadowed by config router's GET /{name} route.

    The config_router registers GET /{name} before share_router registers
    GET /share. FastAPI matches the parameterized route first, so
    name="share" is treated as a config server lookup, returning 404
    because no MCP server named "share" exists.

    This documents a routing conflict where the share resolution endpoint
    is unreachable via GET /api/v1/mcp-servers/share.
    """
    # ARRANGE - Create a valid share token
    create_data = await _create_share(async_client, auth_headers)
    token = str(create_data["share_token"])

    # ACT - Attempt to resolve via GET /mcp-servers/share
    response = await async_client.get(
        "/api/v1/mcp-servers/share",
        headers={**auth_headers, "X-Share-Token": token},
    )

    # ASSERT - Route is shadowed, returns 404 from config endpoint
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    # Error comes from config endpoint (get_mcp_server), not share endpoint
    assert data["error"]["code"] == "MCP_SERVER_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_resolve_share_token_without_header_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /mcp-servers/share without X-Share-Token returns 404.

    Due to the routing conflict, the request hits the config endpoint's
    GET /{name} with name="share" which looks for an MCP server config
    named "share" and returns 404 when not found.
    """
    # ACT - No X-Share-Token header
    response = await async_client.get(
        "/api/v1/mcp-servers/share",
        headers=auth_headers,
    )

    # ASSERT - Hits config endpoint, not share endpoint
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "MCP_SERVER_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_resolve_share_requires_auth(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Resolving a share token without authentication returns 401.

    Even with a valid share token, the request must be authenticated.
    Both the config and share routes require API key auth.
    """
    # ARRANGE - Create a share token first
    create_data = await _create_share(async_client, auth_headers)
    token = str(create_data["share_token"])

    # ACT - Use token but no auth headers
    response = await async_client.get(
        "/api/v1/mcp-servers/share",
        headers={"X-Share-Token": token},
    )

    # ASSERT
    assert response.status_code == 401
