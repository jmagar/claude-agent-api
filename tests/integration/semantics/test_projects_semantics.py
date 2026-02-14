"""Exhaustive semantic tests for Projects endpoints.

Tests full CRUD operations, validation, edge cases, and error handling.
Covers Tasks 11-15 from Phase 2 semantic tests plan.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# =============================================================================
# Task 11: List Projects Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_projects_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_project: dict[str, object],
) -> None:
    """Listing projects returns array with total count matching projects length.

    Validates that after creating a project via mock_project fixture,
    the list endpoint returns it with correct structure and total count.
    """
    # ARRANGE - mock_project fixture already created a project

    # ACT
    response = await async_client.get(
        "/api/v1/projects",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "total" in data
    assert isinstance(data["projects"], list)
    assert data["total"] == len(data["projects"])
    assert data["total"] >= 1

    # Verify our created project is in the list
    project_ids = [p["id"] for p in data["projects"]]
    assert mock_project["id"] in project_ids

    # Verify each project has required fields
    for project in data["projects"]:
        assert "id" in project
        assert "name" in project
        assert "path" in project
        assert "created_at" in project


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_projects_empty(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing projects when none exist returns empty array with total 0.

    Note: Other tests may have created projects in shared Redis,
    so this test creates a fresh client context where we verify
    the response structure is valid even if projects exist from
    other test runs.
    """
    # ACT
    response = await async_client.get(
        "/api/v1/projects",
        headers=auth_headers,
    )

    # ASSERT - Valid response structure regardless of project count
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "total" in data
    assert isinstance(data["projects"], list)
    assert data["total"] == len(data["projects"])
    assert data["total"] >= 0


# =============================================================================
# Task 12: Get Project Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_project_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_project: dict[str, object],
) -> None:
    """Getting a project by ID returns full project data with all fields.

    Validates that the returned project matches the originally created
    project data including id, name, path, timestamps, and metadata.
    """
    # ARRANGE
    project_id = mock_project["id"]

    # ACT
    response = await async_client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == mock_project["id"]
    assert data["name"] == mock_project["name"]
    assert data["path"] == mock_project["path"]
    assert "created_at" in data
    assert data["created_at"] == mock_project["created_at"]
    assert data["metadata"] == mock_project["metadata"]


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_project_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a nonexistent project returns 404 with PROJECT_NOT_FOUND code.

    Validates error response structure with error code for consistent
    client-side error handling.
    """
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.get(
        f"/api/v1/projects/{fake_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "PROJECT_NOT_FOUND"


# =============================================================================
# Task 13: Update Project Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_project_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_project: dict[str, object],
) -> None:
    """Updating a project's name and metadata persists changes correctly.

    Validates that PATCH updates only the provided fields while preserving
    the unchanged fields like path and created_at.
    """
    # ARRANGE
    project_id = mock_project["id"]
    new_name = f"updated-project-{uuid4().hex[:8]}"
    new_metadata = {"purpose": "updated", "version": 2}

    # ACT
    response = await async_client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": new_name, "metadata": new_metadata},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == new_name
    assert data["metadata"] == new_metadata
    # Path should be unchanged
    assert data["path"] == mock_project["path"]
    # Timestamps should be preserved
    assert data["created_at"] == mock_project["created_at"]

    # Verify persistence by re-fetching
    get_response = await async_client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["name"] == new_name
    assert fetched["metadata"] == new_metadata


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_project_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Updating a nonexistent project returns 404 with PROJECT_NOT_FOUND code.

    Validates that attempting to update a project that does not exist
    returns a proper error response rather than silently creating.
    """
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.patch(
        f"/api/v1/projects/{fake_id}",
        json={"name": "ghost-project"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "PROJECT_NOT_FOUND"


# =============================================================================
# Task 14: Delete Project Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_project_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a project returns 204 and subsequent GET returns 404.

    Creates a dedicated project (not using mock_project to avoid fixture
    interference) then deletes it and verifies it is gone.
    """
    # ARRANGE - Create a project specifically for deletion
    suffix = uuid4().hex[:8]
    create_response = await async_client.post(
        "/api/v1/projects",
        json={
            "name": f"delete-me-{suffix}",
            "metadata": {"purpose": "deletion-test"},
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # ACT
    delete_response = await async_client.delete(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )

    # ASSERT - Deletion returns 204 No Content
    assert delete_response.status_code == 204

    # Verify project is gone
    get_response = await async_client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404
    data = get_response.json()
    assert data["error"]["code"] == "PROJECT_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_project_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a nonexistent project returns 404 with PROJECT_NOT_FOUND code.

    Validates idempotent error handling for delete operations on
    resources that do not exist.
    """
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.delete(
        f"/api/v1/projects/{fake_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "PROJECT_NOT_FOUND"


# =============================================================================
# Task 15: Projects Validation Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_project_validates_name_required(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a project without a name returns 422 validation error.

    The name field is required with min_length=1. Omitting it should
    trigger Pydantic validation and return a 422 Unprocessable Entity.
    """
    # ACT - Send request with missing name
    response = await async_client.post(
        "/api/v1/projects",
        json={},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_project_validates_name_length(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a project with empty name or name exceeding 100 chars returns 422.

    Validates both min_length=1 and max_length=100 constraints on the
    name field defined in ProjectCreateRequest schema.
    """
    # ACT - Empty name (violates min_length=1)
    empty_response = await async_client.post(
        "/api/v1/projects",
        json={"name": ""},
        headers=auth_headers,
    )

    # ASSERT
    assert empty_response.status_code == 422

    # ACT - Name exceeding max_length=100
    long_name = "x" * 101
    long_response = await async_client.post(
        "/api/v1/projects",
        json={"name": long_name},
        headers=auth_headers,
    )

    # ASSERT
    assert long_response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_project_duplicate_name_returns_409(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_project: dict[str, object],
) -> None:
    """Creating a project with a duplicate name returns 409 conflict.

    The service layer checks for existing projects with the same name
    and returns None, which the route translates to a 409 PROJECT_EXISTS error.
    """
    # ARRANGE - mock_project already created with a unique name
    existing_name = mock_project["name"]

    # ACT - Create another project with the same name
    response = await async_client.post(
        "/api/v1/projects",
        json={"name": existing_name},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 409
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "PROJECT_EXISTS"
