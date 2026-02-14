"""Exhaustive semantic tests for Skills endpoints.

Tests full CRUD operations, validation, edge cases, and error handling
for database-backed skills and filesystem skill read-only guards.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def mock_skill(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> dict[str, object]:
    """Create a test skill via API for CRUD tests.

    Returns:
        Skill data dict from the creation response.
    """
    suffix = uuid4().hex[:8]
    response = await async_client.post(
        "/api/v1/skills",
        json={
            "name": f"test-skill-{suffix}",
            "description": f"A test skill for semantics testing {suffix}",
            "content": f"# Test Skill {suffix}\n\nDo the thing.",
            "enabled": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201, f"Skill creation failed: {response.text}"
    return response.json()


# =============================================================================
# List Skills Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_skills_returns_valid_structure(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing skills returns response with skills array.

    Validates the response has the expected top-level structure
    regardless of how many skills exist.
    """
    response = await async_client.get(
        "/api/v1/skills",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert isinstance(data["skills"], list)


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_skills_includes_created_skill(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_skill: dict[str, object],
) -> None:
    """Listing skills after creation includes the newly created skill.

    Validates the created skill appears in the list with matching fields.
    """
    response = await async_client.get(
        "/api/v1/skills",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    skill_ids = [s["id"] for s in data["skills"]]
    assert mock_skill["id"] in skill_ids

    # Verify the skill has required fields
    for skill in data["skills"]:
        assert "id" in skill
        assert "name" in skill
        assert "description" in skill
        assert "content" in skill
        assert "source" in skill


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_skills_filter_by_database_source(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_skill: dict[str, object],
) -> None:
    """Filtering skills by source=database returns only database skills.

    Validates the source query parameter correctly filters results.
    """
    response = await async_client.get(
        "/api/v1/skills",
        params={"source": "database"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    for skill in data["skills"]:
        assert skill["source"] == "database"


# =============================================================================
# Create Skill Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_skill_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a skill returns 201 with full skill data including timestamps.

    Validates the response contains all expected fields and the source
    is set to 'database'.
    """
    suffix = uuid4().hex[:8]
    payload = {
        "name": f"create-test-{suffix}",
        "description": "A skill created via test",
        "content": "# Skill\n\nInstructions here.",
        "enabled": True,
    }

    response = await async_client.post(
        "/api/v1/skills",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert data["content"] == payload["content"]
    assert data["enabled"] is True
    assert data["source"] == "database"
    assert "id" in data
    assert data["created_at"] is not None


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_skill_disabled(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a skill with enabled=false persists the disabled state.

    Validates the enabled flag is respected and stored correctly.
    """
    suffix = uuid4().hex[:8]
    response = await async_client.post(
        "/api/v1/skills",
        json={
            "name": f"disabled-skill-{suffix}",
            "description": "A disabled skill",
            "content": "# Disabled\n\nThis skill is off.",
            "enabled": False,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["enabled"] is False


# =============================================================================
# Get Skill Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_skill_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_skill: dict[str, object],
) -> None:
    """Getting a skill by ID returns full skill data matching creation.

    Validates all fields match the originally created skill.
    """
    skill_id = mock_skill["id"]

    response = await async_client.get(
        f"/api/v1/skills/{skill_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == mock_skill["id"]
    assert data["name"] == mock_skill["name"]
    assert data["description"] == mock_skill["description"]
    assert data["content"] == mock_skill["content"]
    assert data["source"] == "database"


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_skill_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a nonexistent skill returns 404 with SKILL_NOT_FOUND code.

    Validates error response structure for missing database skills.
    """
    fake_id = str(uuid4())

    response = await async_client.get(
        f"/api/v1/skills/{fake_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SKILL_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_filesystem_skill_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a nonexistent filesystem skill returns 404.

    Validates the fs: prefix routing correctly returns SKILL_NOT_FOUND
    when the named filesystem skill does not exist.
    """
    response = await async_client.get(
        "/api/v1/skills/fs:nonexistent-skill-xyz",
        headers=auth_headers,
    )

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SKILL_NOT_FOUND"


# =============================================================================
# Update Skill Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_skill_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_skill: dict[str, object],
) -> None:
    """Updating a skill persists all changed fields correctly.

    Validates that PUT replaces name, description, content, and enabled,
    and that updated_at is set after the update.
    """
    skill_id = mock_skill["id"]
    updated_payload = {
        "id": skill_id,
        "name": f"updated-skill-{uuid4().hex[:8]}",
        "description": "Updated description",
        "content": "# Updated\n\nNew instructions.",
        "enabled": False,
    }

    response = await async_client.put(
        f"/api/v1/skills/{skill_id}",
        json=updated_payload,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == updated_payload["name"]
    assert data["description"] == updated_payload["description"]
    assert data["content"] == updated_payload["content"]
    assert data["enabled"] is False
    assert data["updated_at"] is not None

    # Verify persistence by re-fetching
    get_response = await async_client.get(
        f"/api/v1/skills/{skill_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["name"] == updated_payload["name"]
    assert fetched["content"] == updated_payload["content"]


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_skill_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Updating a nonexistent skill returns 404 with SKILL_NOT_FOUND code.

    Validates that attempting to update a skill that does not exist
    returns a proper error response.
    """
    fake_id = str(uuid4())

    response = await async_client.put(
        f"/api/v1/skills/{fake_id}",
        json={
            "id": fake_id,
            "name": "ghost-skill",
            "description": "Does not exist",
            "content": "# Ghost",
            "enabled": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SKILL_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_filesystem_skill_returns_400(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Updating a filesystem skill returns 400 SKILL_READONLY.

    Filesystem skills are read-only via the API; users must edit
    the .md file directly.
    """
    response = await async_client.put(
        "/api/v1/skills/fs:some-skill",
        json={
            "id": "fs:some-skill",
            "name": "some-skill",
            "description": "Attempt to update filesystem skill",
            "content": "# Updated",
            "enabled": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SKILL_READONLY"


# =============================================================================
# Delete Skill Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_skill_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a skill returns 204 and subsequent GET returns 404.

    Creates a dedicated skill for deletion, deletes it, then verifies
    it is gone.
    """
    # Create a skill specifically for deletion
    suffix = uuid4().hex[:8]
    create_response = await async_client.post(
        "/api/v1/skills",
        json={
            "name": f"delete-me-{suffix}",
            "description": "Skill to be deleted",
            "content": "# Delete Me",
            "enabled": True,
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    skill_id = create_response.json()["id"]

    # Delete
    delete_response = await async_client.delete(
        f"/api/v1/skills/{skill_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204

    # Verify skill is gone
    get_response = await async_client.get(
        f"/api/v1/skills/{skill_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404
    data = get_response.json()
    assert data["error"]["code"] == "SKILL_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_skill_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a nonexistent skill returns 404 with SKILL_NOT_FOUND code.

    Validates error handling for delete operations on missing resources.
    """
    fake_id = str(uuid4())

    response = await async_client.delete(
        f"/api/v1/skills/{fake_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SKILL_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_filesystem_skill_returns_400(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a filesystem skill returns 400 SKILL_READONLY.

    Filesystem skills cannot be deleted via API; users must remove
    the .md file directly.
    """
    response = await async_client.delete(
        "/api/v1/skills/fs:some-skill",
        headers=auth_headers,
    )

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SKILL_READONLY"


# =============================================================================
# Validation Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_skill_validates_name_required(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a skill without a name returns 422 validation error.

    The name field is required with min_length=1.
    """
    response = await async_client.post(
        "/api/v1/skills",
        json={
            "description": "Missing name",
            "content": "# No Name",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_skill_validates_empty_name(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a skill with an empty name returns 422.

    Validates min_length=1 constraint on the name field.
    """
    response = await async_client.post(
        "/api/v1/skills",
        json={
            "name": "",
            "description": "Empty name skill",
            "content": "# Empty Name",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_skill_validates_name_max_length(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a skill with name exceeding 100 chars returns 422.

    Validates max_length=100 constraint on the name field.
    """
    long_name = "x" * 101

    response = await async_client.post(
        "/api/v1/skills",
        json={
            "name": long_name,
            "description": "Long name skill",
            "content": "# Long Name",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_skill_validates_description_required(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a skill without a description returns 422.

    The description field is required with min_length=1.
    """
    response = await async_client.post(
        "/api/v1/skills",
        json={
            "name": "no-description",
            "content": "# No Description",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_skill_validates_content_required(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a skill without content returns 422.

    The content field is required with min_length=1.
    """
    response = await async_client.post(
        "/api/v1/skills",
        json={
            "name": "no-content",
            "description": "Skill missing content",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_skill_validates_empty_content(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a skill with empty content returns 422.

    Validates min_length=1 constraint on the content field.
    """
    response = await async_client.post(
        "/api/v1/skills",
        json={
            "name": "empty-content",
            "description": "Skill with empty content",
            "content": "",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422
