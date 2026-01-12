"""Integration tests for MCP share endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
async def test_mcp_share_roundtrip(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Create a share token and resolve it from cache."""
    payload = {
        "config": {
            "type": "sse",
            "url": "https://example.com",
            "headers": {"Authorization": "Bearer secret", "X-Trace": "ok"},
            "env": {"API_KEY": "secret", "LOG_LEVEL": "debug"},
        }
    }

    create_response = await async_client.post(
        "/api/v1/mcp-servers/postgres/share",
        json=payload,
        headers=auth_headers,
    )

    assert create_response.status_code == 200
    create_data = create_response.json()
    assert create_data["share_token"]
    assert create_data["name"] == "postgres"
    assert create_data["config"]["env"]["API_KEY"] == "***REDACTED***"
    assert create_data["config"]["headers"]["Authorization"] == "***REDACTED***"
    assert create_data["config"]["env"]["LOG_LEVEL"] == "debug"

    token = create_data["share_token"]

    get_response = await async_client.get(
        f"/api/v1/mcp-servers/share/{token}",
        headers=auth_headers,
    )

    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["name"] == "postgres"
    assert get_data["config"]["env"]["API_KEY"] == "***REDACTED***"
    assert get_data["config"]["headers"]["Authorization"] == "***REDACTED***"
    assert get_data["config"]["env"]["LOG_LEVEL"] == "debug"


@pytest.mark.integration
@pytest.mark.anyio
async def test_mcp_share_missing_token(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Unknown tokens return a 404 error."""
    response = await async_client.get(
        "/api/v1/mcp-servers/share/not-found",
        headers=auth_headers,
    )

    assert response.status_code == 404
