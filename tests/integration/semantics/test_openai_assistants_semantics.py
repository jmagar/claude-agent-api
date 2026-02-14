"""Exhaustive semantic tests for OpenAI Assistants API endpoints.

Tests the /v1/assistants CRUD endpoints including creation, retrieval,
listing with pagination, modification, deletion, validation, error handling,
and OpenAI-format response structure.

These endpoints follow the OpenAI Assistants API (beta) specification:
https://platform.openai.com/docs/api-reference/assistants
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# =============================================================================
# Helpers
# =============================================================================


async def _create_assistant(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    *,
    model: str = "gpt-4",
    name: str | None = "Test Assistant",
    description: str | None = None,
    instructions: str | None = None,
    tools: list[dict[str, object]] | None = None,
    metadata: dict[str, str] | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
) -> dict[str, object]:
    """Create an assistant and return the response JSON.

    Args:
        async_client: HTTP test client.
        auth_headers: Authentication headers.
        model: Model identifier.
        name: Assistant name.
        description: Assistant description.
        instructions: System instructions.
        tools: Tool configurations.
        metadata: Key-value metadata.
        temperature: Sampling temperature.
        top_p: Nucleus sampling parameter.

    Returns:
        Response JSON as dict.
    """
    payload: dict[str, object] = {"model": model}
    if name is not None:
        payload["name"] = name
    if description is not None:
        payload["description"] = description
    if instructions is not None:
        payload["instructions"] = instructions
    if tools is not None:
        payload["tools"] = tools
    if metadata is not None:
        payload["metadata"] = metadata
    if temperature is not None:
        payload["temperature"] = temperature
    if top_p is not None:
        payload["top_p"] = top_p

    response = await async_client.post(
        "/v1/assistants",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200, f"Assistant creation failed: {response.text}"
    return response.json()


# =============================================================================
# Create Assistant: POST /v1/assistants
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_assistant_returns_openai_format(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an assistant returns OpenAI-formatted response with all required fields.

    Validates the response has 'id', 'object' set to 'assistant', 'created_at'
    as integer timestamp, 'model', 'tools' list, and 'metadata' dict.
    """
    data = await _create_assistant(async_client, auth_headers)

    assert isinstance(data["id"], str)
    assert data["object"] == "assistant"
    assert isinstance(data["created_at"], int)
    assert data["created_at"] > 0
    assert isinstance(data["model"], str)
    assert isinstance(data["tools"], list)
    assert isinstance(data["metadata"], dict)


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_assistant_with_all_fields(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an assistant with all optional fields preserves them in response.

    Validates name, description, instructions, metadata, temperature, and top_p
    are returned correctly in the response.
    """
    data = await _create_assistant(
        async_client,
        auth_headers,
        model="gpt-4",
        name="Full Assistant",
        description="A test assistant with all fields",
        instructions="You are a helpful assistant.",
        metadata={"env": "test", "version": "1"},
        temperature=0.7,
        top_p=0.9,
    )

    assert data["name"] == "Full Assistant"
    assert data["description"] == "A test assistant with all fields"
    assert data["instructions"] == "You are a helpful assistant."
    assert data["metadata"] == {"env": "test", "version": "1"}
    assert data["temperature"] == 0.7
    assert data["top_p"] == 0.9


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_assistant_with_tools(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an assistant with tool configurations returns tools in response.

    Validates that code_interpreter and function tools are preserved in the response.
    """
    tools: list[dict[str, object]] = [
        {"type": "code_interpreter"},
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                    },
                    "required": ["location"],
                },
            },
        },
    ]

    data = await _create_assistant(
        async_client,
        auth_headers,
        tools=tools,
    )

    assert isinstance(data["tools"], list)
    assert len(data["tools"]) == 2


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_assistant_generates_unique_ids(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating multiple assistants generates unique IDs for each.

    Each assistant should have a distinct ID string.
    """
    data1 = await _create_assistant(async_client, auth_headers, name="Assistant 1")
    data2 = await _create_assistant(async_client, auth_headers, name="Assistant 2")

    assert data1["id"] != data2["id"]
    assert isinstance(data1["id"], str)
    assert isinstance(data2["id"], str)


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_assistant_requires_model(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an assistant without model returns validation error.

    The model field is required with min_length=1.
    """
    response = await async_client.post(
        "/v1/assistants",
        json={"name": "No Model Assistant"},
        headers=auth_headers,
    )

    assert response.status_code in (400, 422)


# =============================================================================
# Get Assistant: GET /v1/assistants/{assistant_id}
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_assistant_by_id(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Retrieving an assistant by ID returns the correct assistant data.

    Creates an assistant, then fetches it by ID and validates the response
    matches the created data.
    """
    created = await _create_assistant(
        async_client,
        auth_headers,
        name="Retrievable Assistant",
        instructions="Be helpful",
    )

    response = await async_client.get(
        f"/v1/assistants/{created['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["object"] == "assistant"
    assert data["name"] == "Retrievable Assistant"
    assert data["instructions"] == "Be helpful"


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_nonexistent_assistant_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Retrieving a nonexistent assistant returns 404.

    The endpoint should respond with HTTP 404 when the assistant ID does not exist.
    """
    response = await async_client.get(
        "/v1/assistants/asst_nonexistent_12345",
        headers=auth_headers,
    )

    assert response.status_code == 404


# =============================================================================
# List Assistants: GET /v1/assistants
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_assistants_returns_list_format(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing assistants returns OpenAI paginated list format.

    Validates the response has 'object' set to 'list', a 'data' array,
    and pagination fields (first_id, last_id, has_more).
    """
    # Create at least one assistant to ensure non-empty list
    await _create_assistant(async_client, auth_headers, name="List Test Assistant")

    response = await async_client.get(
        "/v1/assistants",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert isinstance(data["data"], list)
    assert "first_id" in data
    assert "last_id" in data
    assert "has_more" in data
    assert isinstance(data["has_more"], bool)


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_assistants_respects_limit(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing assistants with limit parameter caps the number of results.

    Creates multiple assistants and requests with limit=1 to verify pagination.
    """
    # Create two assistants
    await _create_assistant(async_client, auth_headers, name="Limit Test 1")
    await _create_assistant(async_client, auth_headers, name="Limit Test 2")

    response = await async_client.get(
        "/v1/assistants",
        params={"limit": 1},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) <= 1


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_assistants_rejects_invalid_order(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing assistants with invalid order parameter returns validation error.

    The order parameter must be 'asc' or 'desc'. OpenAI-compatible endpoints
    translate validation errors to 400 status (not 422).
    """
    response = await async_client.get(
        "/v1/assistants",
        params={"order": "invalid"},
        headers=auth_headers,
    )

    assert response.status_code == 400


# =============================================================================
# Modify Assistant: POST /v1/assistants/{assistant_id}
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_modify_assistant_updates_fields(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Modifying an assistant updates the specified fields and returns updated data.

    Creates an assistant, then modifies its name and instructions, and verifies
    the response reflects the changes.
    """
    created = await _create_assistant(
        async_client,
        auth_headers,
        name="Original Name",
        instructions="Original instructions",
    )

    response = await async_client.post(
        f"/v1/assistants/{created['id']}",
        json={
            "name": "Updated Name",
            "instructions": "Updated instructions",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["name"] == "Updated Name"
    assert data["instructions"] == "Updated instructions"


@pytest.mark.integration
@pytest.mark.anyio
async def test_modify_nonexistent_assistant_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Modifying a nonexistent assistant returns 404.

    The endpoint should respond with HTTP 404 when the assistant ID does not exist.
    """
    response = await async_client.post(
        "/v1/assistants/asst_nonexistent_12345",
        json={"name": "Ghost Update"},
        headers=auth_headers,
    )

    assert response.status_code == 404


# =============================================================================
# Delete Assistant: DELETE /v1/assistants/{assistant_id}
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_assistant_returns_deletion_status(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting an assistant returns OpenAI deletion status with correct format.

    Validates the response has 'id', 'object' set to 'assistant.deleted',
    and 'deleted' set to True.
    """
    created = await _create_assistant(async_client, auth_headers, name="Delete Me")

    response = await async_client.delete(
        f"/v1/assistants/{created['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["object"] == "assistant.deleted"
    assert data["deleted"] is True


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_assistant_makes_it_unfetchable(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """After deleting an assistant, fetching it by ID returns 404.

    Validates the assistant is actually removed from storage.
    """
    created = await _create_assistant(async_client, auth_headers, name="Gone Soon")

    # Delete
    del_response = await async_client.delete(
        f"/v1/assistants/{created['id']}",
        headers=auth_headers,
    )
    assert del_response.status_code == 200

    # Fetch should 404
    get_response = await async_client.get(
        f"/v1/assistants/{created['id']}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_nonexistent_assistant_succeeds_silently(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a nonexistent assistant returns 200 when no DB repo is configured.

    Without a database repository, the cache-only delete path succeeds even when
    the assistant does not exist. The deletion status response is still returned.
    When a DB repo is active, this would return 404 instead.
    """
    response = await async_client.delete(
        "/v1/assistants/asst_nonexistent_12345",
        headers=auth_headers,
    )

    # Cache-only path returns 200; DB-backed path returns 404
    assert response.status_code in (200, 404)


# =============================================================================
# Authentication
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_assistants_require_authentication(
    async_client: AsyncClient,
) -> None:
    """All assistant endpoints require authentication.

    Requests without API key should return 401.
    """
    # List
    response = await async_client.get("/v1/assistants")
    assert response.status_code == 401

    # Create
    response = await async_client.post(
        "/v1/assistants",
        json={"model": "gpt-4"},
    )
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.anyio
async def test_assistants_accept_bearer_auth(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """Assistant endpoints accept Bearer token authentication.

    The BearerAuthMiddleware converts Authorization: Bearer <token>
    to X-API-Key for /v1/* routes.
    """
    response = await async_client.get(
        "/v1/assistants",
        headers={"Authorization": f"Bearer {test_api_key}"},
    )

    assert response.status_code == 200
