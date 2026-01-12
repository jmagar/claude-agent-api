"""Integration tests for slash command endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
async def test_slash_command_crud_flow(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Slash commands can be created, listed, updated, and deleted."""
    create_response = await async_client.post(
        "/api/v1/slash-commands",
        json={
            "name": "hello",
            "description": "Say hello",
            "content": "# Command",
        },
        headers=auth_headers,
    )

    assert create_response.status_code == 201
    created = create_response.json()
    command_id = created["id"]
    assert created["name"] == "hello"

    list_response = await async_client.get(
        "/api/v1/slash-commands", headers=auth_headers
    )
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert any(cmd["id"] == command_id for cmd in list_data["commands"])

    update_response = await async_client.put(
        f"/api/v1/slash-commands/{command_id}",
        json={
            "id": command_id,
            "name": "hello",
            "description": "Updated",
            "content": "# Command",
            "enabled": True,
        },
        headers=auth_headers,
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["description"] == "Updated"

    delete_response = await async_client.delete(
        f"/api/v1/slash-commands/{command_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204
