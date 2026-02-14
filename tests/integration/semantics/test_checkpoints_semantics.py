"""Checkpoint listing and rewind tests for Phase 2 semantic validation.

Tests cover:
- List checkpoints for a session (empty and populated)
- Checkpoint response structure validation
- Rewind to valid checkpoint (validation flow)
- Rewind with invalid checkpoint ID
- Session not found returns 404
- Cross-tenant access returns 404
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_checkpoint(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    session_id: str,
) -> dict[str, object]:
    """Create a checkpoint for a session via the checkpoint service.

    Uses the service layer directly since there is no public POST endpoint
    for checkpoint creation (checkpoints are created by the SDK during queries).

    Args:
        async_client: HTTP client for extracting app state.
        auth_headers: Auth headers (unused but kept for consistency).
        session_id: Session to attach the checkpoint to.

    Returns:
        Dict with checkpoint fields (id, session_id, user_message_uuid, etc.).
    """
    from fastapi import Request

    from apps.api.dependencies import get_app_state
    from apps.api.services.checkpoint import CheckpointService

    request = Request(
        scope={"type": "http", "app": async_client._transport.app}  # type: ignore[arg-type]
    )
    app_state = get_app_state(request)
    assert app_state.cache is not None, "Cache must be initialized"

    service = CheckpointService(cache=app_state.cache)
    checkpoint = await service.create_checkpoint(
        session_id=session_id,
        user_message_uuid=str(uuid4()),
        files_modified=["src/main.py", "tests/test_main.py"],
    )

    return {
        "id": checkpoint.id,
        "session_id": checkpoint.session_id,
        "user_message_uuid": checkpoint.user_message_uuid,
        "created_at": checkpoint.created_at.isoformat(),
        "files_modified": checkpoint.files_modified,
    }


# ---------------------------------------------------------------------------
# List Checkpoints: Empty session
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_checkpoints_empty_session(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """List checkpoints for a session with no checkpoints returns empty list."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}/checkpoints",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert "checkpoints" in data
    assert isinstance(data["checkpoints"], list)
    assert len(data["checkpoints"]) == 0


# ---------------------------------------------------------------------------
# List Checkpoints: Populated session
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_checkpoints_returns_all(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """List checkpoints returns all checkpoints for the session."""
    # ARRANGE - create two checkpoints
    session_id = mock_session
    cp1 = await _create_checkpoint(async_client, auth_headers, session_id)
    cp2 = await _create_checkpoint(async_client, auth_headers, session_id)

    # ACT
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}/checkpoints",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert len(data["checkpoints"]) >= 2

    checkpoint_ids = [cp["id"] for cp in data["checkpoints"]]
    assert cp1["id"] in checkpoint_ids
    assert cp2["id"] in checkpoint_ids


# ---------------------------------------------------------------------------
# List Checkpoints: Structure validation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_checkpoints_structure(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Checkpoint response contains all required fields with correct types."""
    # ARRANGE
    session_id = mock_session
    await _create_checkpoint(async_client, auth_headers, session_id)

    # ACT
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}/checkpoints",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert len(data["checkpoints"]) >= 1

    cp = data["checkpoints"][0]
    assert "id" in cp
    assert "session_id" in cp
    assert "user_message_uuid" in cp
    assert "created_at" in cp
    assert "files_modified" in cp

    assert isinstance(cp["id"], str)
    assert isinstance(cp["session_id"], str)
    assert isinstance(cp["user_message_uuid"], str)
    assert isinstance(cp["created_at"], str)
    assert isinstance(cp["files_modified"], list)
    assert cp["session_id"] == session_id


# ---------------------------------------------------------------------------
# List Checkpoints: Checkpoint ordering
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_checkpoints_ordered_by_creation(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Checkpoints are returned ordered by created_at ascending."""
    # ARRANGE
    session_id = mock_session
    cp1 = await _create_checkpoint(async_client, auth_headers, session_id)
    cp2 = await _create_checkpoint(async_client, auth_headers, session_id)

    # ACT
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}/checkpoints",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    checkpoints = data["checkpoints"]
    assert len(checkpoints) >= 2

    # Verify ascending order by created_at
    timestamps = [cp["created_at"] for cp in checkpoints]
    assert timestamps == sorted(timestamps), "Checkpoints should be sorted by created_at ascending"


# ---------------------------------------------------------------------------
# List Checkpoints: Session not found
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_checkpoints_session_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """List checkpoints for nonexistent session returns 404."""
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.get(
        f"/api/v1/sessions/{fake_id}/checkpoints",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


# ---------------------------------------------------------------------------
# List Checkpoints: Cross-tenant isolation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_checkpoints_wrong_owner(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """List checkpoints for session owned by different tenant returns 404."""
    # ARRANGE
    session_id = mock_session_other_tenant  # Owned by second tenant

    # ACT - Primary tenant tries to access it
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}/checkpoints",
        headers=auth_headers,
    )

    # ASSERT - Returns 404 (not 403) to prevent session enumeration
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


# ---------------------------------------------------------------------------
# List Checkpoints: Files modified field
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_checkpoints_files_modified(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Checkpoint files_modified contains expected file paths."""
    # ARRANGE
    session_id = mock_session
    await _create_checkpoint(async_client, auth_headers, session_id)

    # ACT
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}/checkpoints",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    cp = data["checkpoints"][0]
    assert isinstance(cp["files_modified"], list)
    assert len(cp["files_modified"]) == 2
    for path in cp["files_modified"]:
        assert isinstance(path, str)


# ---------------------------------------------------------------------------
# Rewind: Valid checkpoint
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_rewind_valid_checkpoint(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Rewind to a valid checkpoint returns validated status."""
    # ARRANGE
    session_id = mock_session
    cp = await _create_checkpoint(async_client, auth_headers, session_id)

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/rewind",
        json={"checkpoint_id": cp["id"]},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "validated"
    assert data["checkpoint_id"] == cp["id"]
    assert "message" in data
    assert isinstance(data["message"], str)


# ---------------------------------------------------------------------------
# Rewind: Response structure validation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_rewind_response_structure(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Rewind response contains all required fields with correct types."""
    # ARRANGE
    session_id = mock_session
    cp = await _create_checkpoint(async_client, auth_headers, session_id)

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/rewind",
        json={"checkpoint_id": cp["id"]},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["status"], str)
    assert isinstance(data["checkpoint_id"], str)
    assert isinstance(data["message"], str)
    assert data["status"] == "validated"


# ---------------------------------------------------------------------------
# Rewind: Invalid checkpoint ID
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_rewind_invalid_checkpoint_id(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Rewind with nonexistent checkpoint ID returns 400 INVALID_CHECKPOINT."""
    # ARRANGE
    session_id = mock_session
    fake_checkpoint_id = str(uuid4())

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/rewind",
        json={"checkpoint_id": fake_checkpoint_id},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_CHECKPOINT"


# ---------------------------------------------------------------------------
# Rewind: Empty checkpoint_id
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_rewind_empty_checkpoint_id(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Rewind with empty checkpoint_id returns 422 validation error."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/rewind",
        json={"checkpoint_id": ""},
        headers=auth_headers,
    )

    # ASSERT - Pydantic min_length=1 validation catches empty string
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Rewind: Missing checkpoint_id field
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_rewind_missing_checkpoint_id(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Rewind with missing checkpoint_id field returns 422."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/rewind",
        json={},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Rewind: Session not found
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_rewind_session_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Rewind on nonexistent session returns 404 SESSION_NOT_FOUND."""
    # ARRANGE
    fake_session_id = str(uuid4())
    fake_checkpoint_id = str(uuid4())

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{fake_session_id}/rewind",
        json={"checkpoint_id": fake_checkpoint_id},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


# ---------------------------------------------------------------------------
# Rewind: Cross-tenant isolation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_rewind_wrong_owner(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """Rewind on session owned by different tenant returns 404."""
    # ARRANGE
    session_id = mock_session_other_tenant  # Owned by second tenant
    fake_checkpoint_id = str(uuid4())

    # ACT - Primary tenant tries to rewind it
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/rewind",
        json={"checkpoint_id": fake_checkpoint_id},
        headers=auth_headers,
    )

    # ASSERT - Returns 404 (not 403) to prevent session enumeration
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


# ---------------------------------------------------------------------------
# Rewind: Checkpoint from different session
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_rewind_checkpoint_from_different_session(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Rewind with checkpoint belonging to a different session returns 400."""
    # ARRANGE - Create a second session and attach a checkpoint to it
    from fastapi import Request

    from apps.api.adapters.session_repo import SessionRepository
    from apps.api.dependencies import get_app_state
    from apps.api.services.session import SessionService

    request = Request(
        scope={"type": "http", "app": async_client._transport.app}  # type: ignore[arg-type]
    )
    app_state = get_app_state(request)
    assert app_state.cache is not None
    assert app_state.session_maker is not None

    # Create second session owned by same tenant
    async with app_state.session_maker() as db_session:
        repo = SessionRepository(db_session)
        service = SessionService(cache=app_state.cache, db_repo=repo)
        other_session = await service.create_session(
            model="sonnet",
            session_id=str(uuid4()),
            owner_api_key=auth_headers["X-API-Key"],
        )

    # Create checkpoint on the OTHER session
    cp = await _create_checkpoint(async_client, auth_headers, other_session.id)

    # ACT - Try to rewind mock_session using checkpoint from other_session
    response = await async_client.post(
        f"/api/v1/sessions/{mock_session}/rewind",
        json={"checkpoint_id": cp["id"]},
        headers=auth_headers,
    )

    # ASSERT - Checkpoint doesn't belong to this session
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_CHECKPOINT"
