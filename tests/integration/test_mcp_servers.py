"""Integration tests for MCP server endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
async def test_mcp_server_crud_flow(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """MCP servers can be created, listed, updated, and deleted."""
    server_name = f"demo-{uuid4().hex[:8]}"

    create_response = await async_client.post(
        "/api/v1/mcp-servers",
        json={
            "name": server_name,
            "type": "sse",
            "config": {
                "url": "https://example.com",
                "headers": {"Authorization": "Bearer token"},
                "env": {"API_KEY": "secret"},
                "resources": [
                    {
                        "uri": "resource://demo",
                        "name": "Demo",
                        "description": "Demo resource",
                        "mimeType": "text/plain",
                        "text": "Hello",
                    }
                ],
            },
        },
        headers=auth_headers,
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == server_name

    list_response = await async_client.get(
        "/api/v1/mcp-servers", headers=auth_headers
    )
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert any(server["name"] == server_name for server in list_data["servers"])

    get_response = await async_client.get(
        f"/api/v1/mcp-servers/{server_name}", headers=auth_headers
    )
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["name"] == server_name

    resources_response = await async_client.get(
        f"/api/v1/mcp-servers/{server_name}/resources", headers=auth_headers
    )
    assert resources_response.status_code == 200
    resources_data = resources_response.json()
    assert resources_data["resources"]

    resource_response = await async_client.get(
        f"/api/v1/mcp-servers/{server_name}/resources/resource://demo",
        headers=auth_headers,
    )
    assert resource_response.status_code == 200
    resource_data = resource_response.json()
    assert resource_data["text"] == "Hello"

    update_response = await async_client.put(
        f"/api/v1/mcp-servers/{server_name}",
        json={
            "type": "sse",
            "config": {
                "url": "https://example.com",
                "headers": {"Authorization": "Bearer token"},
                "env": {"API_KEY": "secret"},
            },
        },
        headers=auth_headers,
    )
    assert update_response.status_code == 200

    delete_response = await async_client.delete(
        f"/api/v1/mcp-servers/{server_name}", headers=auth_headers
    )
    assert delete_response.status_code == 204
