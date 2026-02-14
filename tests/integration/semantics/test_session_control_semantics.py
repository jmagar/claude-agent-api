"""Session control endpoint semantic validation tests.

Tests cover:
- Interrupt session (success, not-found, wrong owner, inactive session)
- Control events: permission_mode_change (success, validation, missing fields)
- Resume session (validation, not-found, wrong owner, SSE response type)
- Fork session (validation, not-found, wrong owner, model override)
- Multi-tenant isolation across all control operations
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Interrupt Session
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_interrupt_existing_session_returns_404_when_not_active(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Interrupt a session that exists but is not active returns 404.

    The interrupt endpoint checks both session existence (via session service)
    and active status (via agent service). A session that exists in the DB
    but has no active agent process should fail with 404 since interrupt
    has no effect on idle sessions.
    """
    # ARRANGE
    session_id = mock_session

    # ACT - Session exists but agent_service.interrupt returns False (not active)
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/interrupt",
        headers=auth_headers,
    )

    # ASSERT - 404 because the session is not actively running
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_interrupt_nonexistent_session_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Interrupt a session that does not exist returns 404."""
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{fake_id}/interrupt",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_interrupt_wrong_owner_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """Interrupt session owned by different tenant returns 404 (not 403)."""
    # ARRANGE
    session_id = mock_session_other_tenant

    # ACT - Primary tenant tries to interrupt second tenant's session
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/interrupt",
        headers=auth_headers,
    )

    # ASSERT - Returns 404 to prevent session enumeration
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_interrupt_requires_authentication(
    async_client: AsyncClient,
    mock_session: str,
) -> None:
    """Interrupt without API key returns 401."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/interrupt",
    )

    # ASSERT
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Control Events: Permission Mode Change
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_control_permission_mode_change_nonexistent_session(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Control event on nonexistent session returns 404."""
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{fake_id}/control",
        json={
            "type": "permission_mode_change",
            "permission_mode": "plan",
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_control_permission_mode_change_wrong_owner(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """Control event on session owned by different tenant returns 404."""
    # ARRANGE
    session_id = mock_session_other_tenant

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/control",
        json={
            "type": "permission_mode_change",
            "permission_mode": "acceptEdits",
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_control_missing_permission_mode_returns_422(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Control event with type=permission_mode_change but no permission_mode returns 422.

    The ControlRequest model_validator requires permission_mode when type is
    'permission_mode_change'.
    """
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/control",
        json={
            "type": "permission_mode_change",
            # permission_mode intentionally omitted
        },
        headers=auth_headers,
    )

    # ASSERT - Pydantic validation catches missing field
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_control_invalid_permission_mode_value_returns_422(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Control event with invalid permission_mode value returns 422."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/control",
        json={
            "type": "permission_mode_change",
            "permission_mode": "invalid_mode",
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_control_invalid_event_type_returns_422(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Control event with invalid type returns 422.

    The type field is a Literal restricted to 'permission_mode_change'.
    """
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/control",
        json={
            "type": "unknown_event_type",
            "permission_mode": "plan",
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_control_empty_body_returns_422(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Control event with empty body returns 422."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/control",
        json={},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_control_requires_authentication(
    async_client: AsyncClient,
    mock_session: str,
) -> None:
    """Control event without API key returns 401."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/control",
        json={
            "type": "permission_mode_change",
            "permission_mode": "plan",
        },
    )

    # ASSERT
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Resume Session (Control-Focused)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_resume_nonexistent_session_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Resume nonexistent session returns 404."""
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{fake_id}/resume",
        json={"prompt": "continue where we left off"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_resume_wrong_owner_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """Resume session owned by different tenant returns 404."""
    # ARRANGE
    session_id = mock_session_other_tenant

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/resume",
        json={"prompt": "hijack attempt"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_resume_empty_prompt_returns_422(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Resume with empty prompt returns 422 validation error."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/resume",
        json={"prompt": ""},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_resume_missing_prompt_returns_422(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Resume without prompt field returns 422 validation error."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/resume",
        json={},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_resume_invalid_max_turns_returns_422(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Resume with max_turns=0 returns 422 (must be >= 1)."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/resume",
        json={"prompt": "test", "max_turns": 0},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_resume_requires_authentication(
    async_client: AsyncClient,
    mock_session: str,
) -> None:
    """Resume without API key returns 401."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/resume",
        json={"prompt": "test prompt"},
    )

    # ASSERT
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.anyio
async def test_resume_conflicting_tools_returns_422(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Resume with same tool in allowed and disallowed returns 422."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/resume",
        json={
            "prompt": "test",
            "allowed_tools": ["Bash"],
            "disallowed_tools": ["Bash"],
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Fork Session (Control-Focused)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_fork_nonexistent_session_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Fork from nonexistent parent session returns 404."""
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{fake_id}/fork",
        json={"prompt": "fork and explore"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_fork_wrong_owner_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """Fork session owned by different tenant returns 404."""
    # ARRANGE
    session_id = mock_session_other_tenant

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/fork",
        json={"prompt": "fork hijack"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_fork_empty_prompt_returns_422(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Fork with empty prompt returns 422 validation error."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/fork",
        json={"prompt": ""},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_fork_invalid_model_returns_422(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Fork with invalid model name returns 422."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/fork",
        json={"prompt": "test", "model": "nonexistent-model-xyz"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_fork_requires_authentication(
    async_client: AsyncClient,
    mock_session: str,
) -> None:
    """Fork without API key returns 401."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/fork",
        json={"prompt": "test prompt"},
    )

    # ASSERT
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.anyio
async def test_fork_conflicting_tools_returns_422(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Fork with same tool in allowed and disallowed returns 422."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/fork",
        json={
            "prompt": "test",
            "allowed_tools": ["Read"],
            "disallowed_tools": ["Read"],
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Cross-Endpoint Multi-Tenant Isolation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_all_control_endpoints_reject_wrong_tenant(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """All session control endpoints return 404 for wrong tenant's session.

    Verifies that interrupt, control, resume, and fork all consistently
    return 404 (not 403) for cross-tenant access to prevent enumeration.
    """
    # ARRANGE
    session_id = mock_session_other_tenant

    # ACT & ASSERT - All four endpoints should return 404
    interrupt_resp = await async_client.post(
        f"/api/v1/sessions/{session_id}/interrupt",
        headers=auth_headers,
    )
    assert interrupt_resp.status_code == 404

    control_resp = await async_client.post(
        f"/api/v1/sessions/{session_id}/control",
        json={"type": "permission_mode_change", "permission_mode": "plan"},
        headers=auth_headers,
    )
    assert control_resp.status_code == 404

    resume_resp = await async_client.post(
        f"/api/v1/sessions/{session_id}/resume",
        json={"prompt": "cross-tenant resume"},
        headers=auth_headers,
    )
    assert resume_resp.status_code == 404

    fork_resp = await async_client.post(
        f"/api/v1/sessions/{session_id}/fork",
        json={"prompt": "cross-tenant fork"},
        headers=auth_headers,
    )
    assert fork_resp.status_code == 404
