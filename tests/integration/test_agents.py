"""Integration tests for agent endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
async def test_agent_crud_and_share(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Agents can be created, listed, updated, shared, and deleted."""
    create_response = await async_client.post(
        "/api/v1/agents",
        json={
            "name": "demo-agent",
            "description": "Demo",
            "prompt": "Say hi",
            "tools": ["Read"],
            "model": "sonnet",
        },
        headers=auth_headers,
    )

    assert create_response.status_code == 201
    created = create_response.json()
    agent_id = created["id"]
    assert created["name"] == "demo-agent"

    list_response = await async_client.get("/api/v1/agents", headers=auth_headers)
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert any(agent["id"] == agent_id for agent in list_data["agents"])

    update_response = await async_client.put(
        f"/api/v1/agents/{agent_id}",
        json={
            "id": agent_id,
            "name": "demo-agent",
            "description": "Updated",
            "prompt": "Say hi",
            "tools": ["Read"],
            "model": "sonnet",
        },
        headers=auth_headers,
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["description"] == "Updated"

    share_response = await async_client.post(
        f"/api/v1/agents/{agent_id}/share",
        headers=auth_headers,
    )
    assert share_response.status_code == 200
    share_data = share_response.json()
    assert share_data["share_url"]
    assert share_data["share_token"]

    delete_response = await async_client.delete(
        f"/api/v1/agents/{agent_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204
