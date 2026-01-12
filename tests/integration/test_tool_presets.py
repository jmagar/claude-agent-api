"""Integration tests for tool preset endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
async def test_tool_preset_crud_flow(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Tool presets can be created, listed, updated, and deleted."""
    create_response = await async_client.post(
        "/api/v1/tool-presets",
        json={
            "name": "Starter",
            "allowed_tools": ["Read", "Write"],
            "disallowed_tools": ["Bash"],
        },
        headers=auth_headers,
    )

    assert create_response.status_code == 201
    created = create_response.json()
    preset_id = created["id"]
    assert created["name"] == "Starter"
    assert created["allowed_tools"] == ["Read", "Write"]
    assert created["disallowed_tools"] == ["Bash"]

    list_response = await async_client.get(
        "/api/v1/tool-presets",
        headers=auth_headers,
    )

    assert list_response.status_code == 200
    list_data = list_response.json()
    assert any(preset["id"] == preset_id for preset in list_data["presets"])

    update_response = await async_client.put(
        f"/api/v1/tool-presets/{preset_id}",
        json={
            "name": "Updated",
            "allowed_tools": ["Read"],
            "disallowed_tools": [],
        },
        headers=auth_headers,
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "Updated"
    assert updated["allowed_tools"] == ["Read"]
    assert updated["disallowed_tools"] == []

    delete_response = await async_client.delete(
        f"/api/v1/tool-presets/{preset_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204

    get_response = await async_client.get(
        f"/api/v1/tool-presets/{preset_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404
