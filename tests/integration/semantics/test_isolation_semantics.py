"""Cross-tenant isolation tests for Phase 2 semantic validation.

Validates that API key A cannot access API key B's resources.
All cross-tenant access returns 404 (not 403) to prevent enumeration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
async def test_sessions_cross_tenant_isolation(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    second_auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """API key A cannot access API key B's session (returns 404)."""
    # ARRANGE
    session_id = mock_session_other_tenant  # Owned by tenant B

    # ACT - Tenant A tries to access it
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers,  # Tenant A
    )

    # ASSERT - Returns 404 (not 403) to prevent enumeration
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_session_operations_cross_tenant(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    second_auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """API key A cannot resume/fork/interrupt API key B's session (returns 404).

    Validates that session modification operations enforce multi-tenant isolation.
    All cross-tenant operations return 404 (not 403) to prevent enumeration.
    """
    # ARRANGE
    session_id = mock_session_other_tenant  # Owned by tenant B

    # ACT - Tenant A tries resume operation
    resume_response = await async_client.post(
        f"/api/v1/sessions/{session_id}/resume",
        json={"prompt": "test prompt"},
        headers=auth_headers,  # Tenant A
    )

    # ACT - Tenant A tries fork operation
    fork_response = await async_client.post(
        f"/api/v1/sessions/{session_id}/fork",
        json={"prompt": "test fork prompt"},
        headers=auth_headers,  # Tenant A
    )

    # ACT - Tenant A tries interrupt operation
    interrupt_response = await async_client.post(
        f"/api/v1/sessions/{session_id}/interrupt",
        headers=auth_headers,  # Tenant A
    )

    # ASSERT - All operations return 404 with SESSION_NOT_FOUND
    assert resume_response.status_code == 404
    resume_data = resume_response.json()
    assert "error" in resume_data
    assert resume_data["error"]["code"] == "SESSION_NOT_FOUND"

    assert fork_response.status_code == 404
    fork_data = fork_response.json()
    assert "error" in fork_data
    assert fork_data["error"]["code"] == "SESSION_NOT_FOUND"

    assert interrupt_response.status_code == 404
    interrupt_data = interrupt_response.json()
    assert "error" in interrupt_data
    assert interrupt_data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.xfail(
    reason="Projects lack multi-tenant isolation (no owner_api_key tracking). "
    "Test documents expected behavior for future implementation."
)
async def test_projects_cross_tenant_isolation(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    second_auth_headers: dict[str, str],
    mock_project_other_tenant: dict[str, object],
) -> None:
    """API key A cannot access API key B's project (returns 404).

    NOTE: This test currently FAILS because Projects do not implement multi-tenant
    isolation (no owner_api_key field or filtering). When tenant isolation is added,
    remove the @pytest.mark.xfail decorator.

    Expected behavior when implemented:
    - Projects store owner_api_key (like Sessions do)
    - GET /api/v1/projects/{id} filters by current_api_key
    - Cross-tenant access returns 404 (not 403) to prevent enumeration
    """
    # ARRANGE
    project_id = mock_project_other_tenant["id"]  # Owned by tenant B

    # ACT - Tenant A tries to access it
    response = await async_client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,  # Tenant A
    )

    # ASSERT - Should return 404 when isolation is implemented
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "PROJECT_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_memories_cross_tenant_isolation(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    second_auth_headers: dict[str, str],
    mock_memory_other_tenant: dict[str, str],
) -> None:
    """API key A cannot search API key B's memories."""
    # ARRANGE
    memory_content = mock_memory_other_tenant["content"]

    # ACT - Tenant A searches for Tenant B's memory
    response = await async_client.post(
        "/api/v1/memories/search",
        json={"query": memory_content},
        headers=auth_headers,  # Tenant A (user_id derived from header)
    )

    # ASSERT - No results (scoped to Tenant A)
    assert response.status_code == 200
    data = response.json()
    # Verify Tenant B's memory is not in results
    memory_ids = [m["id"] for m in data["results"]]
    assert mock_memory_other_tenant["id"] not in memory_ids


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.xfail(
    reason="Projects lack multi-tenant isolation (no owner_api_key tracking). "
    "Test documents expected behavior for future implementation."
)
async def test_project_operations_cross_tenant(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    second_auth_headers: dict[str, str],
    mock_project_other_tenant: dict[str, object],
) -> None:
    """API key A cannot update/delete API key B's project (returns 404).

    Validates that project modification operations enforce multi-tenant isolation.
    All cross-tenant operations return 404 (not 403) to prevent enumeration.

    NOTE: This test currently FAILS because Projects do not implement multi-tenant
    isolation (no owner_api_key field or filtering). When tenant isolation is added,
    remove the @pytest.mark.xfail decorator.

    Expected behavior when implemented:
    - Projects store owner_api_key (like Sessions do)
    - PUT /api/v1/projects/{id} filters by current_api_key
    - DELETE /api/v1/projects/{id} filters by current_api_key
    - Cross-tenant access returns 404 (not 403) to prevent enumeration
    """
    # ARRANGE
    project_id = mock_project_other_tenant["id"]  # Owned by tenant B

    # ACT - Tenant A tries update operation
    update_response = await async_client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "Updated Name"},
        headers=auth_headers,  # Tenant A
    )

    # ACT - Tenant A tries delete operation
    delete_response = await async_client.delete(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,  # Tenant A
    )

    # ASSERT - Both operations return 404 with PROJECT_NOT_FOUND
    assert update_response.status_code == 404
    update_data = update_response.json()
    assert "error" in update_data
    assert update_data["error"]["code"] == "PROJECT_NOT_FOUND"

    assert delete_response.status_code == 404
    delete_data = delete_response.json()
    assert "error" in delete_data
    assert delete_data["error"]["code"] == "PROJECT_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_memory_operations_cross_tenant(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    second_auth_headers: dict[str, str],
    mock_memory_other_tenant: dict[str, str],
) -> None:
    """API key A cannot delete API key B's memory (returns 404).

    Validates that Mem0's user_id scoping prevents cross-tenant deletes.
    Memory deletion is scoped by user_id derived from API key.
    """
    # ARRANGE
    memory_id = mock_memory_other_tenant["id"]  # Owned by tenant B

    # ACT - Tenant A tries to delete Tenant B's memory
    response = await async_client.delete(
        f"/api/v1/memories/{memory_id}",
        headers=auth_headers,  # Tenant A
    )

    # ASSERT - Returns 404 with MEMORY_NOT_FOUND (scoped by user_id)
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MEMORY_NOT_FOUND"
