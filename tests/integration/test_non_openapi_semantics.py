"""Semantic validation tests for non-OpenAPI routes.

These tests assert route behavior and state semantics (not just availability).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
async def test_interrupt_active_session_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_active_session_id: str,
) -> None:
    """Interrupt returns accepted semantic response for active sessions."""
    response = await async_client.post(
        f"/api/v1/sessions/{mock_active_session_id}/interrupt",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "interrupted"
    assert data["session_id"] == mock_active_session_id


@pytest.mark.integration
@pytest.mark.anyio
async def test_control_active_session_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_active_session_id: str,
) -> None:
    """Control event updates permission mode for active sessions."""
    response = await async_client.post(
        f"/api/v1/sessions/{mock_active_session_id}/control",
        json={"type": "permission_mode_change", "permission_mode": "default"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["session_id"] == mock_active_session_id
    assert data["permission_mode"] == "default"


@pytest.mark.integration
@pytest.mark.anyio
async def test_answer_active_session_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_active_session_id: str,
) -> None:
    """Answer endpoint accepts responses for active sessions."""
    response = await async_client.post(
        f"/api/v1/sessions/{mock_active_session_id}/answer",
        json={"answer": "Approved"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["session_id"] == mock_active_session_id


@pytest.mark.integration
@pytest.mark.anyio
async def test_session_control_requires_active_session(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Session-control routes return not-found semantics for inactive sessions."""
    from apps.api.services.agent import AgentService

    app_state = async_client.app.state.app_state
    assert app_state.cache is not None
    # Avoid lazy Mem0/Neo4j initialization for this semantic contract test.
    app_state.agent_service = AgentService(cache=app_state.cache)

    missing_session_id = str(uuid4())

    interrupt_response = await async_client.post(
        f"/api/v1/sessions/{missing_session_id}/interrupt",
        headers=auth_headers,
    )
    control_response = await async_client.post(
        f"/api/v1/sessions/{missing_session_id}/control",
        json={"type": "permission_mode_change", "permission_mode": "default"},
        headers=auth_headers,
    )
    answer_response = await async_client.post(
        f"/api/v1/sessions/{missing_session_id}/answer",
        json={"answer": "Approved"},
        headers=auth_headers,
    )

    for response in (interrupt_response, control_response, answer_response):
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "SESSION_NOT_FOUND"
        assert data["error"]["details"]["session_id"] == missing_session_id


@pytest.mark.integration
@pytest.mark.anyio
async def test_rewind_invalid_checkpoint_returns_domain_error(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Rewind validates checkpoint ownership and returns domain-level error."""
    from uuid import uuid4

    from apps.api.adapters.session_repo import SessionRepository
    from apps.api.services.session import SessionService

    app_state = async_client.app.state.app_state
    assert app_state.cache is not None
    assert app_state.session_maker is not None

    async with app_state.session_maker() as db_session:
        repo = SessionRepository(db_session)
        session_service = SessionService(cache=app_state.cache, db_repo=repo)
        session = await session_service.create_session(
            model="sonnet",
            session_id=str(uuid4()),
            owner_api_key=auth_headers["X-API-Key"],
        )
        session_id = session.id

    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/rewind",
        json={"checkpoint_id": "invalid-checkpoint"},
        headers=auth_headers,
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_CHECKPOINT"
    assert data["error"]["details"]["session_id"] == session_id
    assert data["error"]["details"]["checkpoint_id"] == "invalid-checkpoint"


@pytest.mark.integration
@pytest.mark.anyio
async def test_projects_enforce_unique_name_or_path(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Projects reject duplicates by name/path with domain error semantics."""
    suffix = uuid4().hex[:8]
    name = f"semantic-project-{suffix}"
    path = f"/tmp/semantic-project-{suffix}"

    create_response = await async_client.post(
        "/api/v1/projects",
        json={"name": name, "path": path},
        headers=auth_headers,
    )
    assert create_response.status_code == 201

    duplicate_name = await async_client.post(
        "/api/v1/projects",
        json={"name": name, "path": f"/tmp/another-path-{suffix}"},
        headers=auth_headers,
    )
    assert duplicate_name.status_code == 409
    duplicate_name_data = duplicate_name.json()
    assert duplicate_name_data["error"]["code"] == "PROJECT_EXISTS"

    duplicate_path = await async_client.post(
        "/api/v1/projects",
        json={"name": f"semantic-project-2-{suffix}", "path": path},
        headers=auth_headers,
    )
    assert duplicate_path.status_code == 409
    duplicate_path_data = duplicate_path.json()
    assert duplicate_path_data["error"]["code"] == "PROJECT_EXISTS"


@pytest.mark.integration
@pytest.mark.anyio
async def test_agent_share_persists_share_state(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Sharing an agent persists share token/url and flips share state."""
    create_response = await async_client.post(
        "/api/v1/agents",
        json={
            "name": "semantic-agent",
            "description": "semantic validation",
            "prompt": "You are a semantic validation agent.",
            "tools": ["Read"],
            "model": "sonnet",
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    agent_id = create_response.json()["id"]

    share_response = await async_client.post(
        f"/api/v1/agents/{agent_id}/share",
        headers=auth_headers,
    )
    assert share_response.status_code == 200
    share_data = share_response.json()
    assert share_data["share_token"]
    assert agent_id in share_data["share_url"]

    get_response = await async_client.get(
        f"/api/v1/agents/{agent_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["is_shared"] is True
    assert get_data["share_url"] == share_data["share_url"]
    # Token is returned only by the share endpoint and not exposed on reads.
    assert "share_token" not in get_data


@pytest.mark.integration
@pytest.mark.anyio
async def test_tool_presets_support_tools_legacy_field(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Legacy `tools` field is interpreted as `allowed_tools`."""
    create_response = await async_client.post(
        "/api/v1/tool-presets",
        json={
            "name": "semantic-legacy-tools",
            "tools": ["Read", "Write"],
            "disallowed_tools": ["Bash"],
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    preset_id = created["id"]
    assert created["allowed_tools"] == ["Read", "Write"]
    assert created["disallowed_tools"] == ["Bash"]

    update_response = await async_client.put(
        f"/api/v1/tool-presets/{preset_id}",
        json={
            "name": "semantic-legacy-tools-updated",
            "tools": ["Read"],
        },
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["allowed_tools"] == ["Read"]
    assert updated["disallowed_tools"] == []


@pytest.mark.integration
@pytest.mark.anyio
async def test_mcp_readonly_and_resource_error_contracts(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """MCP routes return stable domain errors for readonly and missing resources."""
    readonly_update = await async_client.put(
        "/api/v1/mcp-servers/fs:demo",
        json={"type": "sse", "config": {"url": "https://example.com"}},
        headers=auth_headers,
    )
    assert readonly_update.status_code == 400
    readonly_update_data = readonly_update.json()
    assert readonly_update_data["error"]["code"] == "MCP_SERVER_READONLY"

    readonly_delete = await async_client.delete(
        "/api/v1/mcp-servers/fs:demo",
        headers=auth_headers,
    )
    assert readonly_delete.status_code == 400
    readonly_delete_data = readonly_delete.json()
    assert readonly_delete_data["error"]["code"] == "MCP_SERVER_READONLY"

    server_name = f"semantic-{uuid4().hex[:8]}"
    create_response = await async_client.post(
        "/api/v1/mcp-servers",
        json={
            "name": server_name,
            "type": "sse",
            "config": {
                "url": "https://example.com",
                "resources": [
                    {
                        "uri": "resource://present",
                        "name": "Present",
                        "mimeType": "text/plain",
                        "text": "present text",
                    }
                ],
            },
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201

    missing_resource = await async_client.get(
        f"/api/v1/mcp-servers/{server_name}/resources/resource://missing",
        headers=auth_headers,
    )
    assert missing_resource.status_code == 404
    missing_resource_data = missing_resource.json()
    assert missing_resource_data["error"]["code"] == "MCP_RESOURCE_NOT_FOUND"

    missing_server = await async_client.get(
        f"/api/v1/mcp-servers/{uuid4().hex}/resources",
        headers=auth_headers,
    )
    assert missing_server.status_code == 404
    missing_server_data = missing_server.json()
    assert missing_server_data["error"]["code"] == "MCP_SERVER_NOT_FOUND"
