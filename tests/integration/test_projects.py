"""Integration tests for project endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
async def test_project_crud_flow(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Projects can be created, listed, updated, and deleted."""
    create_response = await async_client.post(
        "/api/v1/projects",
        json={"name": "demo-project", "metadata": {"owner": "test"}},
        headers=auth_headers,
    )

    assert create_response.status_code == 201
    created = create_response.json()
    project_id = created["id"]
    assert created["name"] == "demo-project"
    assert created["metadata"]["owner"] == "test"

    list_response = await async_client.get("/api/v1/projects", headers=auth_headers)
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert any(project["id"] == project_id for project in list_data["projects"])

    get_response = await async_client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["id"] == project_id

    patch_response = await async_client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "demo-project-updated"},
        headers=auth_headers,
    )
    assert patch_response.status_code == 200
    patch_data = patch_response.json()
    assert patch_data["name"] == "demo-project-updated"

    delete_response = await async_client.delete(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204

    missing_response = await async_client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )
    assert missing_response.status_code == 404
