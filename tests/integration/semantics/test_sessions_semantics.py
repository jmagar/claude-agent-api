"""Sessions CRUD, operations, and SSE streaming tests for Phase 2 semantic validation.

Tests cover:
- Sessions CRUD operations (list, get)
- Session operations (resume, fork, interrupt)
- Session state management (promote, tags)
- SSE streaming event sequence validation
- Validation and error handling
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# ---------------------------------------------------------------------------
# CRUD: List Sessions
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_sessions_pagination(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """List sessions returns paginated response with total count."""
    # ARRANGE - mock_session fixture creates one session

    # ACT
    response = await async_client.get(
        "/api/v1/sessions",
        params={"page": 1, "page_size": 10},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total"] >= 1
    assert len(data["sessions"]) >= 1

    # Verify session structure
    session = data["sessions"][0]
    assert "id" in session
    assert "status" in session
    assert "created_at" in session
    assert "updated_at" in session


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_sessions_pagination_params(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """List sessions respects page_size parameter."""
    # ARRANGE - mock_session creates one session

    # ACT - Request with page_size=1
    response = await async_client.get(
        "/api/v1/sessions",
        params={"page": 1, "page_size": 1},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["page_size"] == 1
    assert len(data["sessions"]) <= 1


# ---------------------------------------------------------------------------
# CRUD: Get Session
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_session_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Get session by ID returns full session data."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["status"] in ("active", "completed", "error")
    assert data["model"] == "sonnet"
    assert "created_at" in data
    assert "updated_at" in data
    assert "total_turns" in data


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_session_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Get nonexistent session returns 404 with SESSION_NOT_FOUND."""
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.get(
        f"/api/v1/sessions/{fake_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_session_invalid_uuid(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Get session with invalid UUID format returns 422."""
    # ARRANGE
    invalid_id = "not-a-uuid"

    # ACT
    response = await async_client.get(
        f"/api/v1/sessions/{invalid_id}",
        headers=auth_headers,
    )

    # ASSERT - ValidationError for invalid UUID format
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_session_wrong_owner(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """Get session owned by different tenant returns 404."""
    # ARRANGE
    session_id = mock_session_other_tenant  # Owned by second tenant

    # ACT - Primary tenant tries to access it
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers,
    )

    # ASSERT - Returns 404 (not 403) to prevent enumeration
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


# ---------------------------------------------------------------------------
# Session Operations: Resume
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_resume_nonexistent_session(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Resume nonexistent session returns 404."""
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{fake_id}/resume",
        json={"prompt": "continue working"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_resume_validates_prompt_required(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Resume with empty prompt returns 422."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/resume",
        json={"prompt": ""},
        headers=auth_headers,
    )

    # ASSERT - Pydantic validation catches empty prompt
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_resume_validates_max_turns(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Resume with invalid max_turns returns 422."""
    # ARRANGE
    session_id = mock_session

    # ACT - max_turns must be >= 1
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/resume",
        json={"prompt": "test", "max_turns": 0},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.anyio
async def test_resume_wrong_owner(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """Resume session owned by different tenant returns 404."""
    # ARRANGE
    session_id = mock_session_other_tenant  # Owned by second tenant

    # ACT - Primary tenant tries to resume it
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/resume",
        json={"prompt": "test prompt"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


# ---------------------------------------------------------------------------
# Session Operations: Fork
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_fork_nonexistent_session(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Fork nonexistent session returns 404."""
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{fake_id}/fork",
        json={"prompt": "fork this session"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_fork_validates_prompt_required(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Fork with empty prompt returns 422."""
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
async def test_fork_wrong_owner(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """Fork session owned by different tenant returns 404."""
    # ARRANGE
    session_id = mock_session_other_tenant  # Owned by second tenant

    # ACT - Primary tenant tries to fork it
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/fork",
        json={"prompt": "fork this"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_fork_validates_model_name(
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
        json={"prompt": "test", "model": "invalid-model-xyz"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Session Operations: Interrupt
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_interrupt_nonexistent_session(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Interrupt nonexistent session returns 404."""
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
async def test_interrupt_wrong_owner(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """Interrupt session owned by different tenant returns 404."""
    # ARRANGE
    session_id = mock_session_other_tenant  # Owned by second tenant

    # ACT - Primary tenant tries to interrupt it
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/interrupt",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


# ---------------------------------------------------------------------------
# State Management: Promote
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_promote_session_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
    mock_project: dict[str, object],
) -> None:
    """Promote brainstorm session to code mode succeeds."""
    # ARRANGE
    session_id = mock_session
    project_id = str(mock_project["id"])

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/promote",
        json={"project_id": project_id},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["mode"] == "code"
    assert data["project_id"] == project_id


@pytest.mark.integration
@pytest.mark.anyio
async def test_promote_nonexistent_session(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Promote nonexistent session returns 404."""
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{fake_id}/promote",
        json={"project_id": "some-project-id"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_promote_wrong_owner(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """Promote session owned by different tenant returns 404."""
    # ARRANGE
    session_id = mock_session_other_tenant  # Owned by second tenant

    # ACT - Primary tenant tries to promote it
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/promote",
        json={"project_id": "some-project-id"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_promote_invalid_session_id(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Promote with invalid UUID format returns 422."""
    # ARRANGE
    invalid_id = "not-a-valid-uuid"

    # ACT
    response = await async_client.post(
        f"/api/v1/sessions/{invalid_id}/promote",
        json={"project_id": "some-project-id"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# State Management: Tags
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_session_tags_succeeds(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Update session tags succeeds and returns updated session."""
    # ARRANGE
    session_id = mock_session
    tags = ["feature", "priority-high", "reviewed"]

    # ACT
    response = await async_client.patch(
        f"/api/v1/sessions/{session_id}/tags",
        json={"tags": tags},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["tags"] == tags


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_tags_nonexistent_session(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Update tags on nonexistent session returns 404."""
    # ARRANGE
    fake_id = str(uuid4())

    # ACT
    response = await async_client.patch(
        f"/api/v1/sessions/{fake_id}/tags",
        json={"tags": ["test"]},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_tags_wrong_owner(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session_other_tenant: str,
) -> None:
    """Update tags on session owned by different tenant returns 404."""
    # ARRANGE
    session_id = mock_session_other_tenant  # Owned by second tenant

    # ACT - Primary tenant tries to update tags
    response = await async_client.patch(
        f"/api/v1/sessions/{session_id}/tags",
        json={"tags": ["hijacked"]},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_tags_empty_list(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Update tags with empty list clears all tags."""
    # ARRANGE
    session_id = mock_session

    # First set some tags
    await async_client.patch(
        f"/api/v1/sessions/{session_id}/tags",
        json={"tags": ["initial-tag"]},
        headers=auth_headers,
    )

    # ACT - Clear all tags
    response = await async_client.patch(
        f"/api/v1/sessions/{session_id}/tags",
        json={"tags": []},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["tags"] == []


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_tags_invalid_uuid(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Update tags with invalid UUID format returns 422."""
    # ARRANGE
    invalid_id = "not-a-uuid"

    # ACT
    response = await async_client.patch(
        f"/api/v1/sessions/{invalid_id}/tags",
        json={"tags": ["test"]},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Session Timestamps
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_session_timestamps_timezone_aware(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """Session timestamps include timezone information."""
    # ARRANGE
    session_id = mock_session

    # ACT
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()

    # Timestamps should be ISO 8601 with timezone info
    created_at = data["created_at"]
    updated_at = data["updated_at"]

    # Should contain timezone offset (Z or +00:00)
    assert "T" in created_at, "created_at should be ISO 8601 datetime"
    assert "T" in updated_at, "updated_at should be ISO 8601 datetime"


# ---------------------------------------------------------------------------
# List Sessions Filtering
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_sessions_filter_by_mode(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """List sessions filters by mode parameter."""
    # ARRANGE - Promote session to 'code' mode first
    session_id = mock_session

    # Create a project to promote with
    project_response = await async_client.post(
        "/api/v1/projects",
        json={"name": f"filter-test-{uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # Promote session to code mode
    await async_client.post(
        f"/api/v1/sessions/{session_id}/promote",
        json={"project_id": project_id},
        headers=auth_headers,
    )

    # ACT - Filter by code mode
    response = await async_client.get(
        "/api/v1/sessions",
        params={"mode": "code"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    # All returned sessions should be in code mode
    for session in data["sessions"]:
        assert session["mode"] == "code"


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_sessions_filter_by_tags(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    mock_session: str,
) -> None:
    """List sessions filters by tags parameter."""
    # ARRANGE - Tag the session
    session_id = mock_session
    test_tag = f"filter-tag-{uuid4().hex[:8]}"

    await async_client.patch(
        f"/api/v1/sessions/{session_id}/tags",
        json={"tags": [test_tag]},
        headers=auth_headers,
    )

    # ACT - Filter by tag
    response = await async_client.get(
        "/api/v1/sessions",
        params={"tags": [test_tag]},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    # Verify the tagged session is in results
    session_ids = [s["id"] for s in data["sessions"]]
    assert session_id in session_ids
