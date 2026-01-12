"""Integration tests for skill endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
async def test_skill_crud_flow(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Skills can be created, listed, updated, and deleted."""
    create_response = await async_client.post(
        "/api/v1/skills",
        json={"name": "Demo Skill", "description": "Desc", "content": "# Skill"},
        headers=auth_headers,
    )

    assert create_response.status_code == 201
    created = create_response.json()
    skill_id = created["id"]
    assert created["name"] == "Demo Skill"

    list_response = await async_client.get("/api/v1/skills", headers=auth_headers)
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert any(skill["id"] == skill_id for skill in list_data["skills"])

    update_response = await async_client.put(
        f"/api/v1/skills/{skill_id}",
        json={
            "id": skill_id,
            "name": "Demo Skill",
            "description": "Updated",
            "content": "# Skill",
            "enabled": True,
        },
        headers=auth_headers,
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["description"] == "Updated"

    delete_response = await async_client.delete(
        f"/api/v1/skills/{skill_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204
