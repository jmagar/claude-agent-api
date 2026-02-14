"""Exhaustive semantic tests for Agents endpoints.

Tests full CRUD operations, validation, edge cases, and error handling.
Covers Task 7 from Phase 3 semantic tests plan.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


def _agent_payload(
    *,
    name: str | None = None,
    description: str | None = None,
    prompt: str | None = None,
    tools: list[str] | None = None,
    model: str | None = None,
) -> dict[str, object]:
    """Build a valid agent creation payload with sensible defaults.

    Only includes keys for explicitly provided values plus required fields.
    """
    suffix = uuid4().hex[:8]
    payload: dict[str, object] = {
        "name": name if name is not None else f"test-agent-{suffix}",
        "description": description if description is not None else f"Agent for testing {suffix}",
        "prompt": prompt if prompt is not None else f"You are a helpful test agent {suffix}.",
    }
    if tools is not None:
        payload["tools"] = tools
    if model is not None:
        payload["model"] = model
    return payload


async def _create_agent(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    name: str | None = None,
    description: str | None = None,
    prompt: str | None = None,
    tools: list[str] | None = None,
    model: str | None = None,
) -> dict[str, object]:
    """Create an agent via API and return response data.

    Raises AssertionError if creation fails.
    """
    payload = _agent_payload(
        name=name,
        description=description,
        prompt=prompt,
        tools=tools,
        model=model,
    )
    response = await client.post("/api/v1/agents", json=payload, headers=headers)
    assert response.status_code == 201, f"Agent creation failed: {response.text}"
    return response.json()


# =============================================================================
# List Agents Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_agents_returns_array(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing agents returns response with agents array.

    Validates the response shape includes an 'agents' key with a list value.
    """
    # ARRANGE - create an agent so the list is non-empty
    await _create_agent(async_client, auth_headers)

    # ACT
    response = await async_client.get("/api/v1/agents", headers=auth_headers)

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert isinstance(data["agents"], list)
    assert len(data["agents"]) >= 1

    # Verify each agent has required fields
    for agent in data["agents"]:
        assert "id" in agent
        assert "name" in agent
        assert "description" in agent
        assert "prompt" in agent
        assert "created_at" in agent


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_agents_includes_created_agent(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """A newly created agent appears in the list response.

    Validates that create followed by list returns the agent with matching ID.
    """
    # ARRANGE
    created = await _create_agent(async_client, auth_headers)

    # ACT
    response = await async_client.get("/api/v1/agents", headers=auth_headers)

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    agent_ids = [a["id"] for a in data["agents"]]
    assert created["id"] in agent_ids


# =============================================================================
# Create Agent Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_agent_returns_201_with_all_fields(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an agent returns 201 with complete agent definition.

    Validates the response includes id, name, description, prompt,
    created_at, and the is_shared default of false.
    """
    # ARRANGE
    payload = _agent_payload(
        name="full-agent",
        description="A fully specified agent",
        prompt="You are a test agent.",
        tools=["Bash", "Read"],
        model="sonnet",
    )

    # ACT
    response = await async_client.post(
        "/api/v1/agents", json=payload, headers=auth_headers
    )

    # ASSERT
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "full-agent"
    assert data["description"] == "A fully specified agent"
    assert data["prompt"] == "You are a test agent."
    assert data["tools"] == ["Bash", "Read"]
    assert data["model"] == "sonnet"
    assert "id" in data
    assert "created_at" in data
    assert data.get("is_shared") is False
    assert data.get("share_url") is None


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_agent_without_optional_fields(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an agent without tools and model succeeds with null values.

    Validates that optional fields default to null when omitted.
    """
    # ARRANGE
    payload = _agent_payload()
    # Ensure no optional fields
    payload.pop("tools", None)
    payload.pop("model", None)

    # ACT
    response = await async_client.post(
        "/api/v1/agents", json=payload, headers=auth_headers
    )

    # ASSERT
    assert response.status_code == 201
    data = response.json()
    assert data["tools"] is None
    assert data["model"] is None


# =============================================================================
# Get Agent Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_agent_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting an agent by ID returns full agent data matching creation payload.

    Validates round-trip: create then get returns identical data.
    """
    # ARRANGE
    created = await _create_agent(
        async_client,
        auth_headers,
        name="get-test-agent",
        description="Agent for get test",
        prompt="Get test prompt.",
    )

    # ACT
    response = await async_client.get(
        f"/api/v1/agents/{created['id']}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["name"] == "get-test-agent"
    assert data["description"] == "Agent for get test"
    assert data["prompt"] == "Get test prompt."
    assert data["created_at"] == created["created_at"]


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_agent_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a nonexistent agent returns 404 with AGENT_NOT_FOUND code.

    Validates error response structure for consistent client-side handling.
    """
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.get(
        f"/api/v1/agents/{fake_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "AGENT_NOT_FOUND"


# =============================================================================
# Update Agent Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_agent_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Updating an agent replaces all fields and sets updated_at timestamp.

    The PUT endpoint performs a full replacement. Validates that all provided
    fields are persisted and updated_at is populated after the update.
    """
    # ARRANGE
    created = await _create_agent(async_client, auth_headers)
    agent_id = created["id"]

    update_payload = {
        "id": agent_id,
        "name": "updated-agent-name",
        "description": "Updated description",
        "prompt": "Updated prompt text.",
        "tools": ["Glob"],
        "model": "haiku",
    }

    # ACT
    response = await async_client.put(
        f"/api/v1/agents/{agent_id}",
        json=update_payload,
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == agent_id
    assert data["name"] == "updated-agent-name"
    assert data["description"] == "Updated description"
    assert data["prompt"] == "Updated prompt text."
    assert data["tools"] == ["Glob"]
    assert data["model"] == "haiku"
    assert data["updated_at"] is not None
    # created_at should be preserved
    assert data["created_at"] == created["created_at"]

    # Verify persistence via GET
    get_response = await async_client.get(
        f"/api/v1/agents/{agent_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["name"] == "updated-agent-name"
    assert fetched["description"] == "Updated description"


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_agent_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Updating a nonexistent agent returns 404 with AGENT_NOT_FOUND code.

    Validates that attempting to update an agent that does not exist
    returns a proper error response rather than silently creating.
    """
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.put(
        f"/api/v1/agents/{fake_id}",
        json={
            "id": fake_id,
            "name": "ghost-agent",
            "description": "Should not exist",
            "prompt": "Ghost prompt.",
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "AGENT_NOT_FOUND"


# =============================================================================
# Delete Agent Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_agent_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting an agent returns 204 and subsequent GET returns 404.

    Creates a dedicated agent then deletes it and verifies removal.
    """
    # ARRANGE
    created = await _create_agent(async_client, auth_headers)
    agent_id = created["id"]

    # ACT
    delete_response = await async_client.delete(
        f"/api/v1/agents/{agent_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert delete_response.status_code == 204

    # Verify agent is gone
    get_response = await async_client.get(
        f"/api/v1/agents/{agent_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404
    data = get_response.json()
    assert data["error"]["code"] == "AGENT_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_agent_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a nonexistent agent returns 404 with AGENT_NOT_FOUND code.

    Validates proper error handling for delete on missing resources.
    """
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.delete(
        f"/api/v1/agents/{fake_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "AGENT_NOT_FOUND"


# =============================================================================
# Validation Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_agent_validates_name_required(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an agent without required name returns 422 validation error.

    The name field is required with min_length=1. Omitting it triggers
    Pydantic validation.
    """
    # ACT - missing name
    response = await async_client.post(
        "/api/v1/agents",
        json={
            "description": "Missing name",
            "prompt": "Should fail.",
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_agent_validates_name_length(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an agent with empty or oversized name returns 422.

    Validates both min_length=1 and max_length=100 constraints.
    """
    # ACT - empty name
    empty_response = await async_client.post(
        "/api/v1/agents",
        json={
            "name": "",
            "description": "Empty name test",
            "prompt": "Should fail.",
        },
        headers=auth_headers,
    )
    assert empty_response.status_code == 422

    # ACT - name exceeding max_length=100
    long_response = await async_client.post(
        "/api/v1/agents",
        json={
            "name": "x" * 101,
            "description": "Long name test",
            "prompt": "Should fail.",
        },
        headers=auth_headers,
    )
    assert long_response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_agent_validates_description_required(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an agent without required description returns 422.

    The description field is required with min_length=1.
    """
    # ACT
    response = await async_client.post(
        "/api/v1/agents",
        json={
            "name": "no-desc-agent",
            "prompt": "Should fail.",
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_agent_validates_prompt_required(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating an agent without required prompt returns 422.

    The prompt field is required with min_length=1.
    """
    # ACT
    response = await async_client.post(
        "/api/v1/agents",
        json={
            "name": "no-prompt-agent",
            "description": "Agent without prompt",
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422
