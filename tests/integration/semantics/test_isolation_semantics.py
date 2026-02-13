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
