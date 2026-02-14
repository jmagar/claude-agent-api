"""Exhaustive semantic tests for Tool Presets endpoints.

Tests full CRUD operations, validation, edge cases, and error handling.
Covers Task 4 from Phase 3 semantic tests plan.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# =============================================================================
# Create Tool Preset Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_tool_preset_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a tool preset returns 201 with all fields populated.

    Validates that the response includes a generated ID, the provided
    name, description, tool lists, is_system default, and a created_at timestamp.
    """
    suffix = uuid4().hex[:8]
    payload = {
        "name": f"preset-{suffix}",
        "description": "A test preset for semantic validation",
        "allowed_tools": ["Read", "Write"],
        "disallowed_tools": ["Bash"],
    }

    response = await async_client.post(
        "/api/v1/tool-presets",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert data["allowed_tools"] == ["Read", "Write"]
    assert data["disallowed_tools"] == ["Bash"]
    assert data["is_system"] is False
    assert "created_at" in data


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_tool_preset_minimal_payload(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a tool preset with only the required name field succeeds.

    Optional fields (description, allowed_tools, disallowed_tools) should
    default to None and empty lists respectively.
    """
    suffix = uuid4().hex[:8]
    payload = {"name": f"minimal-{suffix}"}

    response = await async_client.post(
        "/api/v1/tool-presets",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] is None
    assert data["allowed_tools"] == []
    assert data["disallowed_tools"] == []


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_tool_preset_with_empty_tool_lists(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a tool preset with explicit empty tool lists succeeds.

    Both allowed_tools and disallowed_tools can be empty arrays,
    which means no tool restrictions are applied.
    """
    suffix = uuid4().hex[:8]
    payload = {
        "name": f"empty-tools-{suffix}",
        "allowed_tools": [],
        "disallowed_tools": [],
    }

    response = await async_client.post(
        "/api/v1/tool-presets",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["allowed_tools"] == []
    assert data["disallowed_tools"] == []


# =============================================================================
# List Tool Presets Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_tool_presets_returns_created_preset(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing tool presets includes a previously created preset.

    After creating a preset, the list endpoint should return it
    with all fields intact and correct structure.
    """
    suffix = uuid4().hex[:8]
    create_response = await async_client.post(
        "/api/v1/tool-presets",
        json={"name": f"listed-{suffix}", "allowed_tools": ["Glob"]},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()

    response = await async_client.get(
        "/api/v1/tool-presets",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "presets" in data
    assert isinstance(data["presets"], list)

    preset_ids = [p["id"] for p in data["presets"]]
    assert created["id"] in preset_ids

    matched = next(p for p in data["presets"] if p["id"] == created["id"])
    assert matched["name"] == f"listed-{suffix}"
    assert matched["allowed_tools"] == ["Glob"]


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_tool_presets_structure(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing tool presets returns valid response structure.

    Each preset in the list must contain id, name, allowed_tools,
    disallowed_tools, is_system, and created_at fields.
    """
    response = await async_client.get(
        "/api/v1/tool-presets",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "presets" in data
    assert isinstance(data["presets"], list)

    for preset in data["presets"]:
        assert "id" in preset
        assert "name" in preset
        assert "allowed_tools" in preset
        assert "disallowed_tools" in preset
        assert "is_system" in preset
        assert "created_at" in preset


# =============================================================================
# Get Tool Preset Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_tool_preset_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a tool preset by ID returns the full preset data.

    Validates that the returned preset matches the originally created
    data including all fields.
    """
    suffix = uuid4().hex[:8]
    create_response = await async_client.post(
        "/api/v1/tool-presets",
        json={
            "name": f"fetchable-{suffix}",
            "description": "For get test",
            "allowed_tools": ["Read"],
            "disallowed_tools": ["Write"],
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()

    response = await async_client.get(
        f"/api/v1/tool-presets/{created['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["name"] == f"fetchable-{suffix}"
    assert data["description"] == "For get test"
    assert data["allowed_tools"] == ["Read"]
    assert data["disallowed_tools"] == ["Write"]
    assert data["is_system"] is False
    assert data["created_at"] == created["created_at"]


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_tool_preset_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a nonexistent tool preset returns 404 with TOOL_PRESET_NOT_FOUND code.

    Validates error response structure with the correct error code
    for consistent client-side error handling.
    """
    fake_id = str(uuid4())

    response = await async_client.get(
        f"/api/v1/tool-presets/{fake_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "TOOL_PRESET_NOT_FOUND"


# =============================================================================
# Update Tool Preset Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_tool_preset_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Updating a tool preset replaces name, description, and tool lists.

    PUT semantics require all fields to be provided. Validates that
    the updated preset reflects new values and persists correctly.
    """
    suffix = uuid4().hex[:8]
    create_response = await async_client.post(
        "/api/v1/tool-presets",
        json={
            "name": f"original-{suffix}",
            "description": "Original description",
            "allowed_tools": ["Read"],
            "disallowed_tools": [],
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    preset_id = create_response.json()["id"]

    update_payload = {
        "name": f"updated-{suffix}",
        "description": "Updated description",
        "allowed_tools": ["Read", "Write", "Glob"],
        "disallowed_tools": ["Bash"],
    }

    response = await async_client.put(
        f"/api/v1/tool-presets/{preset_id}",
        json=update_payload,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == preset_id
    assert data["name"] == f"updated-{suffix}"
    assert data["description"] == "Updated description"
    assert data["allowed_tools"] == ["Read", "Write", "Glob"]
    assert data["disallowed_tools"] == ["Bash"]

    # Verify persistence via GET
    get_response = await async_client.get(
        f"/api/v1/tool-presets/{preset_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["name"] == f"updated-{suffix}"
    assert fetched["allowed_tools"] == ["Read", "Write", "Glob"]


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_tool_preset_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Updating a nonexistent tool preset returns 404 with TOOL_PRESET_NOT_FOUND code.

    Validates that the API does not silently create a new preset
    when updating a non-existent ID.
    """
    fake_id = str(uuid4())

    response = await async_client.put(
        f"/api/v1/tool-presets/{fake_id}",
        json={
            "name": "ghost-preset",
            "allowed_tools": [],
            "disallowed_tools": [],
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "TOOL_PRESET_NOT_FOUND"


# =============================================================================
# Delete Tool Preset Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_tool_preset_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a tool preset returns 204 and subsequent GET returns 404.

    Creates a dedicated preset for deletion, deletes it, then
    verifies it is no longer retrievable.
    """
    suffix = uuid4().hex[:8]
    create_response = await async_client.post(
        "/api/v1/tool-presets",
        json={"name": f"delete-me-{suffix}", "allowed_tools": ["Read"]},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    preset_id = create_response.json()["id"]

    delete_response = await async_client.delete(
        f"/api/v1/tool-presets/{preset_id}",
        headers=auth_headers,
    )

    assert delete_response.status_code == 204

    # Verify preset is gone
    get_response = await async_client.get(
        f"/api/v1/tool-presets/{preset_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404
    data = get_response.json()
    assert data["error"]["code"] == "TOOL_PRESET_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_tool_preset_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a nonexistent tool preset returns 404 with TOOL_PRESET_NOT_FOUND code.

    Validates consistent error handling for delete operations on
    resources that do not exist.
    """
    fake_id = str(uuid4())

    response = await async_client.delete(
        f"/api/v1/tool-presets/{fake_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "TOOL_PRESET_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_tool_preset_removed_from_list(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleted tool preset no longer appears in the list endpoint.

    After deletion, the preset should not be returned by the list
    endpoint, verifying index cleanup in the cache.
    """
    suffix = uuid4().hex[:8]
    create_response = await async_client.post(
        "/api/v1/tool-presets",
        json={"name": f"list-removal-{suffix}"},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    preset_id = create_response.json()["id"]

    # Verify it appears in list
    list_before = await async_client.get(
        "/api/v1/tool-presets",
        headers=auth_headers,
    )
    assert list_before.status_code == 200
    ids_before = [p["id"] for p in list_before.json()["presets"]]
    assert preset_id in ids_before

    # Delete
    delete_response = await async_client.delete(
        f"/api/v1/tool-presets/{preset_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204

    # Verify it is gone from list
    list_after = await async_client.get(
        "/api/v1/tool-presets",
        headers=auth_headers,
    )
    assert list_after.status_code == 200
    ids_after = [p["id"] for p in list_after.json()["presets"]]
    assert preset_id not in ids_after


# =============================================================================
# Validation Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_tool_preset_validates_name_required(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a tool preset without a name returns 422 validation error.

    The name field is required with min_length=1. Omitting it triggers
    Pydantic validation and returns 422 Unprocessable Entity.
    """
    response = await async_client.post(
        "/api/v1/tool-presets",
        json={"allowed_tools": ["Read"]},
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_tool_preset_validates_name_constraints(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a tool preset with empty or oversized name returns 422.

    Validates both min_length=1 and max_length=100 constraints
    on the name field defined in ToolPresetCreateRequest schema.
    """
    # Empty name (violates min_length=1)
    empty_response = await async_client.post(
        "/api/v1/tool-presets",
        json={"name": ""},
        headers=auth_headers,
    )
    assert empty_response.status_code == 422

    # Name exceeding max_length=100
    long_name = "x" * 101
    long_response = await async_client.post(
        "/api/v1/tool-presets",
        json={"name": long_name},
        headers=auth_headers,
    )
    assert long_response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_tool_preset_validates_description_max_length(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a tool preset with description exceeding 500 chars returns 422.

    Validates the max_length=500 constraint on the description field.
    """
    suffix = uuid4().hex[:8]
    long_description = "d" * 501

    response = await async_client.post(
        "/api/v1/tool-presets",
        json={
            "name": f"desc-too-long-{suffix}",
            "description": long_description,
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_tool_preset_preserves_is_system_and_created_at(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Updating a tool preset preserves read-only fields is_system and created_at.

    The update endpoint should not allow overriding system metadata fields.
    Only name, description, allowed_tools, and disallowed_tools are mutable.
    """
    suffix = uuid4().hex[:8]
    create_response = await async_client.post(
        "/api/v1/tool-presets",
        json={
            "name": f"immutable-fields-{suffix}",
            "allowed_tools": ["Read"],
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    original_created_at = created["created_at"]
    original_is_system = created["is_system"]

    # Update with new values
    response = await async_client.put(
        f"/api/v1/tool-presets/{created['id']}",
        json={
            "name": f"changed-{suffix}",
            "allowed_tools": ["Write"],
            "disallowed_tools": [],
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["created_at"] == original_created_at
    assert data["is_system"] == original_is_system
