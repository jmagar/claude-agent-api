"""Exhaustive semantic tests for Slash Commands endpoints.

Tests full CRUD operations, validation, edge cases, and error handling.
Covers Task 6 from Phase 3 semantic tests plan.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# =============================================================================
# Helpers
# =============================================================================


def _slash_command_payload(
    *,
    name: str | None = None,
    description: str = "A test slash command",
    content: str = "# Test command content",
    enabled: bool = True,
) -> dict[str, object]:
    """Build a valid slash command creation payload."""
    suffix = uuid4().hex[:8]
    return {
        "name": name or f"test-cmd-{suffix}",
        "description": description,
        "content": content,
        "enabled": enabled,
    }


async def _create_slash_command(
    client: AsyncClient,
    headers: dict[str, str],
    **overrides: object,
) -> dict[str, object]:
    """Create a slash command and return its response data."""
    payload = _slash_command_payload(**overrides)  # type: ignore[arg-type]
    response = await client.post(
        "/api/v1/slash-commands",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201, f"Slash command creation failed: {response.text}"
    return response.json()


# =============================================================================
# Create Slash Command Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_slash_command_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a slash command returns 201 with all fields populated.

    Validates that the response includes id, name, description, content,
    enabled flag, and created_at timestamp.
    """
    payload = _slash_command_payload(name="create-test")

    response = await async_client.post(
        "/api/v1/slash-commands",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "create-test"
    assert data["description"] == payload["description"]
    assert data["content"] == payload["content"]
    assert data["enabled"] is True
    assert "created_at" in data


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_slash_command_disabled(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a slash command with enabled=False persists the disabled state.

    Validates that the enabled flag is respected on creation rather than
    always defaulting to True.
    """
    payload = _slash_command_payload(enabled=False)

    response = await async_client.post(
        "/api/v1/slash-commands",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["enabled"] is False


# =============================================================================
# List Slash Commands Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_slash_commands_returns_created_command(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing slash commands includes a previously created command.

    Validates that the list endpoint returns a commands array and the
    newly created command appears in it with correct data.
    """
    created = await _create_slash_command(async_client, auth_headers)

    response = await async_client.get(
        "/api/v1/slash-commands",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "commands" in data
    assert isinstance(data["commands"], list)

    command_ids = [cmd["id"] for cmd in data["commands"]]
    assert created["id"] in command_ids


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_slash_commands_empty(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing slash commands returns valid structure even with no commands.

    Validates the response always contains the commands array key
    regardless of whether any commands exist.
    """
    response = await async_client.get(
        "/api/v1/slash-commands",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "commands" in data
    assert isinstance(data["commands"], list)


# =============================================================================
# Get Slash Command Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_slash_command_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a slash command by ID returns the full command data.

    Validates that all fields match the originally created command
    including id, name, description, content, and enabled flag.
    """
    created = await _create_slash_command(async_client, auth_headers)
    command_id = created["id"]

    response = await async_client.get(
        f"/api/v1/slash-commands/{command_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == command_id
    assert data["name"] == created["name"]
    assert data["description"] == created["description"]
    assert data["content"] == created["content"]
    assert data["enabled"] == created["enabled"]
    assert data["created_at"] == created["created_at"]


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_slash_command_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a nonexistent slash command returns 404 with SLASH_COMMAND_NOT_FOUND code.

    Validates error response structure with consistent error code for
    client-side error handling.
    """
    fake_id = str(uuid4())

    response = await async_client.get(
        f"/api/v1/slash-commands/{fake_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SLASH_COMMAND_NOT_FOUND"


# =============================================================================
# Update Slash Command Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_slash_command_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Updating a slash command persists all changed fields.

    Validates that PUT replaces the command fields and sets updated_at
    while preserving the original id and created_at.
    """
    created = await _create_slash_command(async_client, auth_headers)
    command_id = created["id"]

    update_payload = {
        "id": command_id,
        "name": "updated-cmd",
        "description": "Updated description",
        "content": "# Updated content",
        "enabled": False,
    }

    response = await async_client.put(
        f"/api/v1/slash-commands/{command_id}",
        json=update_payload,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == command_id
    assert data["name"] == "updated-cmd"
    assert data["description"] == "Updated description"
    assert data["content"] == "# Updated content"
    assert data["enabled"] is False
    assert data["updated_at"] is not None

    # Verify persistence by re-fetching
    get_response = await async_client.get(
        f"/api/v1/slash-commands/{command_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["name"] == "updated-cmd"
    assert fetched["description"] == "Updated description"


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_slash_command_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Updating a nonexistent slash command returns 404 with SLASH_COMMAND_NOT_FOUND code.

    Validates that attempting to update a command that does not exist
    returns a proper error response rather than silently creating.
    """
    fake_id = str(uuid4())

    response = await async_client.put(
        f"/api/v1/slash-commands/{fake_id}",
        json={
            "id": fake_id,
            "name": "ghost-cmd",
            "description": "Ghost",
            "content": "# Ghost",
            "enabled": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SLASH_COMMAND_NOT_FOUND"


# =============================================================================
# Delete Slash Command Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_slash_command_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a slash command returns 204 and subsequent GET returns 404.

    Creates a dedicated command then deletes it and verifies it is gone.
    """
    created = await _create_slash_command(async_client, auth_headers)
    command_id = created["id"]

    delete_response = await async_client.delete(
        f"/api/v1/slash-commands/{command_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204

    # Verify command is gone
    get_response = await async_client.get(
        f"/api/v1/slash-commands/{command_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404
    data = get_response.json()
    assert data["error"]["code"] == "SLASH_COMMAND_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_slash_command_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a nonexistent slash command returns 404 with SLASH_COMMAND_NOT_FOUND code.

    Validates idempotent error handling for delete operations on
    commands that do not exist.
    """
    fake_id = str(uuid4())

    response = await async_client.delete(
        f"/api/v1/slash-commands/{fake_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SLASH_COMMAND_NOT_FOUND"


# =============================================================================
# Validation Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_slash_command_validates_name_required(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a slash command without a name returns 422 validation error.

    The name field is required with min_length=1. Omitting it triggers
    Pydantic validation and returns 422 Unprocessable Entity.
    """
    response = await async_client.post(
        "/api/v1/slash-commands",
        json={
            "description": "Missing name",
            "content": "# Content",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_slash_command_validates_empty_name(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a slash command with empty name returns 422 validation error.

    Validates the min_length=1 constraint on the name field.
    """
    response = await async_client.post(
        "/api/v1/slash-commands",
        json={
            "name": "",
            "description": "Empty name",
            "content": "# Content",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_slash_command_validates_name_max_length(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a slash command with name exceeding 100 chars returns 422.

    Validates the max_length=100 constraint on the name field defined
    in SlashCommandCreateRequest schema.
    """
    long_name = "x" * 101

    response = await async_client.post(
        "/api/v1/slash-commands",
        json={
            "name": long_name,
            "description": "Long name",
            "content": "# Content",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_slash_command_validates_content_required(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a slash command without content returns 422 validation error.

    The content field is required with min_length=1. Omitting it triggers
    Pydantic validation.
    """
    response = await async_client.post(
        "/api/v1/slash-commands",
        json={
            "name": "no-content-cmd",
            "description": "Missing content",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422
