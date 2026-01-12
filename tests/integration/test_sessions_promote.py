"""Integration tests for session promotion endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
async def test_promote_session_updates_metadata(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_id: str,
) -> None:
    """Promoting a session should set mode and project_id metadata."""
    response = await async_client.post(
        f"/api/v1/sessions/{mock_session_id}/promote",
        json={"project_id": "11111111-1111-1111-1111-111111111111"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == mock_session_id
    assert data["mode"] == "code"
    assert data["project_id"] == "11111111-1111-1111-1111-111111111111"
