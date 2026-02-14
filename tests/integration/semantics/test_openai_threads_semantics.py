"""Exhaustive semantic tests for OpenAI-compatible Threads API endpoints.

Tests the /v1/threads, /v1/threads/{id}/messages, and /v1/threads/{id}/runs
endpoints including CRUD operations, response format validation,
error handling, pagination, and edge cases.

Thread endpoints follow OpenAI Assistants API (beta) conventions:
- POST /v1/threads - Create thread
- GET /v1/threads/{id} - Get thread
- POST /v1/threads/{id} - Modify thread
- DELETE /v1/threads/{id} - Delete thread
- POST /v1/threads/{id}/messages - Create message
- GET /v1/threads/{id}/messages - List messages
- GET /v1/threads/{id}/messages/{id} - Get message
- POST /v1/threads/{id}/messages/{id} - Modify message
- POST /v1/threads/{id}/runs - Create run
- GET /v1/threads/{id}/runs - List runs
- GET /v1/threads/{id}/runs/{id} - Get run
- POST /v1/threads/{id}/runs/{id}/cancel - Cancel run
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# =============================================================================
# Helpers
# =============================================================================


async def _create_thread(
    client: AsyncClient,
    headers: dict[str, str],
    metadata: dict[str, str] | None = None,
) -> dict[str, object]:
    """Helper to create a thread and return the response JSON."""
    body: dict[str, object] = {}
    if metadata is not None:
        body["metadata"] = metadata
    response = await client.post("/v1/threads", json=body, headers=headers)
    assert response.status_code == 200
    return response.json()


async def _create_message(
    client: AsyncClient,
    headers: dict[str, str],
    thread_id: str,
    role: str = "user",
    content: str = "Hello, world!",
    metadata: dict[str, str] | None = None,
) -> dict[str, object]:
    """Helper to create a message in a thread and return the response JSON."""
    body: dict[str, object] = {"role": role, "content": content}
    if metadata is not None:
        body["metadata"] = metadata
    response = await client.post(
        f"/v1/threads/{thread_id}/messages",
        json=body,
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


async def _create_run(
    client: AsyncClient,
    headers: dict[str, str],
    thread_id: str,
    assistant_id: str = "asst_test123",
    model: str | None = None,
) -> dict[str, object]:
    """Helper to create a run in a thread and return the response JSON."""
    body: dict[str, object] = {"assistant_id": assistant_id}
    if model is not None:
        body["model"] = model
    response = await client.post(
        f"/v1/threads/{thread_id}/runs",
        json=body,
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


# =============================================================================
# Threads: POST /v1/threads - Create
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_thread_returns_openai_format(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a thread returns OpenAI-compatible thread object.

    Validates the response contains 'id', 'object' set to 'thread',
    'created_at' as integer timestamp, and 'metadata' as dict.
    """
    # ACT
    response = await async_client.post(
        "/v1/threads",
        json={},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "thread"
    assert isinstance(data["id"], str)
    assert data["id"].startswith("thread_")
    assert isinstance(data["created_at"], int)
    assert data["created_at"] > 0
    assert isinstance(data["metadata"], dict)


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_thread_with_metadata(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a thread with metadata preserves the key-value pairs.

    Validates that metadata passed in the request body is stored and
    returned in the thread response.
    """
    # ACT
    response = await async_client.post(
        "/v1/threads",
        json={"metadata": {"project": "test", "priority": "high"}},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["project"] == "test"
    assert data["metadata"]["priority"] == "high"


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_thread_with_no_body(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a thread with no request body succeeds.

    The CreateThreadRequest is optional (default None), so an empty
    POST should create a thread with empty metadata.
    """
    # ACT
    response = await async_client.post("/v1/threads", headers=auth_headers)

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "thread"
    assert isinstance(data["id"], str)


# =============================================================================
# Threads: GET /v1/threads/{thread_id} - Retrieve
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_thread_returns_created_thread(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a thread by ID returns the same thread that was created.

    Validates round-trip consistency between create and get.
    """
    # ARRANGE
    created = await _create_thread(
        async_client, auth_headers, metadata={"env": "test"}
    )
    thread_id = created["id"]

    # ACT
    response = await async_client.get(
        f"/v1/threads/{thread_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == thread_id
    assert data["object"] == "thread"
    assert data["created_at"] == created["created_at"]
    assert data["metadata"]["env"] == "test"


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_nonexistent_thread_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a nonexistent thread returns 404.

    The endpoint raises HTTPException(404) when the thread is not found.
    """
    # ACT
    response = await async_client.get(
        "/v1/threads/thread_nonexistent_abc123",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404


# =============================================================================
# Threads: POST /v1/threads/{thread_id} - Modify
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_modify_thread_updates_metadata(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Modifying a thread replaces its metadata with the new values.

    OpenAI's modify thread endpoint replaces metadata entirely, not merge.
    """
    # ARRANGE
    created = await _create_thread(
        async_client, auth_headers, metadata={"old_key": "old_value"}
    )
    thread_id = created["id"]

    # ACT
    response = await async_client.post(
        f"/v1/threads/{thread_id}",
        json={"metadata": {"new_key": "new_value"}},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == thread_id
    assert data["metadata"] == {"new_key": "new_value"}
    # Old metadata should be gone (replaced, not merged)
    assert "old_key" not in data["metadata"]


@pytest.mark.integration
@pytest.mark.anyio
async def test_modify_nonexistent_thread_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Modifying a nonexistent thread returns 404."""
    # ACT
    response = await async_client.post(
        "/v1/threads/thread_nonexistent_xyz789",
        json={"metadata": {"key": "value"}},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404


# =============================================================================
# Threads: DELETE /v1/threads/{thread_id} - Delete
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_thread_returns_deletion_status(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a thread returns OpenAI deletion status object.

    Validates the response includes 'id', 'object' set to 'thread.deleted',
    and 'deleted' set to True.
    """
    # ARRANGE
    created = await _create_thread(async_client, auth_headers)
    thread_id = created["id"]

    # ACT
    response = await async_client.delete(
        f"/v1/threads/{thread_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == thread_id
    assert data["object"] == "thread.deleted"
    assert data["deleted"] is True


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_thread_makes_it_unretrievable(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """After deleting a thread, getting it returns 404.

    Validates that deletion actually removes the thread from storage.
    """
    # ARRANGE
    created = await _create_thread(async_client, auth_headers)
    thread_id = created["id"]

    # ACT - Delete
    delete_resp = await async_client.delete(
        f"/v1/threads/{thread_id}",
        headers=auth_headers,
    )
    assert delete_resp.status_code == 200

    # ACT - Try to get deleted thread
    get_resp = await async_client.get(
        f"/v1/threads/{thread_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert get_resp.status_code == 404


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_nonexistent_thread_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a nonexistent thread returns 404."""
    # ACT
    response = await async_client.delete(
        "/v1/threads/thread_nonexistent_delete123",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404


# =============================================================================
# Messages: POST /v1/threads/{thread_id}/messages - Create
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_message_returns_openai_format(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a message returns OpenAI-compatible thread message object.

    Validates the response has 'id', 'object' set to 'thread.message',
    'thread_id', 'role', 'content', and 'created_at' fields.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]

    # ACT
    response = await async_client.post(
        f"/v1/threads/{thread_id}/messages",
        json={"role": "user", "content": "Hello, assistant!"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "thread.message"
    assert isinstance(data["id"], str)
    assert data["id"].startswith("msg_")
    assert data["thread_id"] == thread_id
    assert data["role"] == "user"
    assert isinstance(data["created_at"], int)
    assert isinstance(data["content"], list)


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_message_content_is_text_block(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Created message content is wrapped in text content block structure.

    The service creates a MessageTextContent block with type='text' and
    text.value containing the original content string.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]

    # ACT
    data = await _create_message(
        async_client, auth_headers, thread_id, content="Test content"
    )

    # ASSERT
    assert len(data["content"]) >= 1
    text_block = data["content"][0]
    assert text_block["type"] == "text"
    assert text_block["text"]["value"] == "Test content"
    assert isinstance(text_block["text"]["annotations"], list)


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_message_with_metadata(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a message with metadata preserves the key-value pairs."""
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]

    # ACT
    data = await _create_message(
        async_client,
        auth_headers,
        thread_id,
        metadata={"source": "test", "version": "1"},
    )

    # ASSERT
    assert data["metadata"]["source"] == "test"
    assert data["metadata"]["version"] == "1"


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_message_rejects_empty_content(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a message with empty content returns validation error.

    The content field has min_length=1 constraint.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]

    # ACT
    response = await async_client.post(
        f"/v1/threads/{thread_id}/messages",
        json={"role": "user", "content": ""},
        headers=auth_headers,
    )

    # ASSERT - Validation error (400 for /v1/* or 422 for standard)
    assert response.status_code in (400, 422)


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_message_rejects_invalid_role(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a message with invalid role returns validation error.

    The role field is a Literal restricted to 'user' or 'assistant'.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]

    # ACT
    response = await async_client.post(
        f"/v1/threads/{thread_id}/messages",
        json={"role": "system", "content": "Not allowed"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code in (400, 422)


# =============================================================================
# Messages: GET /v1/threads/{thread_id}/messages - List
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_messages_returns_openai_list_format(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing messages returns OpenAI-compatible paginated list.

    Validates the response has 'object' set to 'list', 'data' as array,
    'first_id', 'last_id', and 'has_more' fields.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]
    await _create_message(async_client, auth_headers, thread_id, content="Message 1")

    # ACT
    response = await async_client.get(
        f"/v1/threads/{thread_id}/messages",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert isinstance(data["data"], list)
    assert "first_id" in data
    assert "last_id" in data
    assert "has_more" in data


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_messages_returns_created_messages(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing messages includes messages that were previously created.

    Creates multiple messages and verifies they all appear in the list.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]
    msg1 = await _create_message(
        async_client, auth_headers, thread_id, content="First message"
    )
    msg2 = await _create_message(
        async_client, auth_headers, thread_id, content="Second message"
    )

    # ACT
    response = await async_client.get(
        f"/v1/threads/{thread_id}/messages",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    message_ids = [m["id"] for m in data["data"]]
    assert msg1["id"] in message_ids
    assert msg2["id"] in message_ids


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_messages_empty_thread(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing messages on a thread with no messages returns empty list.

    The response should have empty data, null first/last IDs, and has_more=false.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]

    # ACT
    response = await async_client.get(
        f"/v1/threads/{thread_id}/messages",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["first_id"] is None
    assert data["last_id"] is None
    assert data["has_more"] is False


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_messages_respects_limit_parameter(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing messages with limit parameter constrains result count.

    Creates 3 messages but requests only 2, validating the limit is respected.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]
    for i in range(3):
        await _create_message(
            async_client, auth_headers, thread_id, content=f"Message {i}"
        )

    # ACT
    response = await async_client.get(
        f"/v1/threads/{thread_id}/messages",
        params={"limit": 2},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["has_more"] is True


# =============================================================================
# Messages: GET /v1/threads/{thread_id}/messages/{message_id} - Get
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_message_returns_created_message(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a message by ID returns the same message that was created.

    Validates round-trip consistency between create and get.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]
    created = await _create_message(
        async_client, auth_headers, thread_id, content="Specific message"
    )
    message_id = created["id"]

    # ACT
    response = await async_client.get(
        f"/v1/threads/{thread_id}/messages/{message_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == message_id
    assert data["thread_id"] == thread_id
    assert data["object"] == "thread.message"
    assert data["content"][0]["text"]["value"] == "Specific message"


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_nonexistent_message_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a nonexistent message returns 404."""
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]

    # ACT
    response = await async_client.get(
        f"/v1/threads/{thread_id}/messages/msg_nonexistent_abc",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404


# =============================================================================
# Messages: POST /v1/threads/{thread_id}/messages/{message_id} - Modify
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_modify_message_updates_metadata(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Modifying a message replaces its metadata with new values.

    The modify endpoint replaces metadata entirely (not merge).
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]
    created = await _create_message(
        async_client,
        auth_headers,
        thread_id,
        metadata={"old": "value"},
    )
    message_id = created["id"]

    # ACT
    response = await async_client.post(
        f"/v1/threads/{thread_id}/messages/{message_id}",
        json={"metadata": {"new": "updated"}},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"] == {"new": "updated"}
    assert "old" not in data["metadata"]


@pytest.mark.integration
@pytest.mark.anyio
async def test_modify_nonexistent_message_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Modifying a nonexistent message returns 404."""
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]

    # ACT
    response = await async_client.post(
        f"/v1/threads/{thread_id}/messages/msg_nonexistent_xyz",
        json={"metadata": {"key": "value"}},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404


# =============================================================================
# Runs: POST /v1/threads/{thread_id}/runs - Create
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_run_returns_openai_format(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a run returns OpenAI-compatible run object.

    Validates the response has 'id', 'object' set to 'thread.run',
    'thread_id', 'assistant_id', 'status', 'model', and timestamp fields.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]

    # ACT
    response = await async_client.post(
        f"/v1/threads/{thread_id}/runs",
        json={"assistant_id": "asst_test_run_format"},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "thread.run"
    assert isinstance(data["id"], str)
    assert data["id"].startswith("run_")
    assert data["thread_id"] == thread_id
    assert data["assistant_id"] == "asst_test_run_format"
    assert data["status"] == "queued"
    assert isinstance(data["created_at"], int)
    assert isinstance(data["tools"], list)
    assert isinstance(data["metadata"], dict)


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_run_with_model_override(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a run with model override uses the specified model.

    The model field overrides the default model on the assistant.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]

    # ACT
    data = await _create_run(
        async_client, auth_headers, thread_id, model="gpt-4-turbo"
    )

    # ASSERT
    assert data["model"] == "gpt-4-turbo"


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_run_requires_assistant_id(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Creating a run without assistant_id returns validation error.

    The assistant_id field is required with min_length=1.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]

    # ACT
    response = await async_client.post(
        f"/v1/threads/{thread_id}/runs",
        json={},
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code in (400, 422)


# =============================================================================
# Runs: GET /v1/threads/{thread_id}/runs - List
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_runs_returns_openai_list_format(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing runs returns OpenAI-compatible paginated list.

    Validates the response has 'object' set to 'list', 'data' as array,
    and pagination metadata fields.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]
    await _create_run(async_client, auth_headers, thread_id)

    # ACT
    response = await async_client.get(
        f"/v1/threads/{thread_id}/runs",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1
    assert "first_id" in data
    assert "last_id" in data
    assert "has_more" in data


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_runs_empty_thread(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing runs on a thread with no runs returns empty list."""
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]

    # ACT
    response = await async_client.get(
        f"/v1/threads/{thread_id}/runs",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["first_id"] is None
    assert data["last_id"] is None
    assert data["has_more"] is False


# =============================================================================
# Runs: GET /v1/threads/{thread_id}/runs/{run_id} - Get
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_run_returns_created_run(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a run by ID returns the same run that was created.

    Validates round-trip consistency between create and get.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]
    created = await _create_run(async_client, auth_headers, thread_id)
    run_id = created["id"]

    # ACT
    response = await async_client.get(
        f"/v1/threads/{thread_id}/runs/{run_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == run_id
    assert data["thread_id"] == thread_id
    assert data["object"] == "thread.run"
    assert data["status"] == "queued"


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_nonexistent_run_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a nonexistent run returns 404."""
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]

    # ACT
    response = await async_client.get(
        f"/v1/threads/{thread_id}/runs/run_nonexistent_abc",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404


# =============================================================================
# Runs: POST /v1/threads/{thread_id}/runs/{run_id}/cancel - Cancel
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_cancel_run_returns_cancelled_status(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Cancelling a queued run transitions it to cancelled status.

    The run starts in 'queued' status and should transition to 'cancelled'.
    """
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]
    created = await _create_run(async_client, auth_headers, thread_id)
    run_id = created["id"]

    # ACT
    response = await async_client.post(
        f"/v1/threads/{thread_id}/runs/{run_id}/cancel",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == run_id
    assert data["status"] == "cancelled"
    assert data["cancelled_at"] is not None


@pytest.mark.integration
@pytest.mark.anyio
async def test_cancel_nonexistent_run_returns_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Cancelling a nonexistent run returns 404."""
    # ARRANGE
    thread = await _create_thread(async_client, auth_headers)
    thread_id = thread["id"]

    # ACT
    response = await async_client.post(
        f"/v1/threads/{thread_id}/runs/run_nonexistent_cancel/cancel",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404


# =============================================================================
# Authentication
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_threads_require_authentication(
    async_client: AsyncClient,
) -> None:
    """Thread endpoints require authentication.

    Requests without API key or Bearer token should return 401.
    """
    # ACT
    response = await async_client.post("/v1/threads", json={})

    # ASSERT
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.anyio
async def test_threads_accept_bearer_auth(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """Thread endpoints accept Bearer token authentication.

    The BearerAuthMiddleware converts Authorization: Bearer <token>
    to X-API-Key for /v1/* routes.
    """
    # ACT
    response = await async_client.post(
        "/v1/threads",
        json={},
        headers={"Authorization": f"Bearer {test_api_key}"},
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "thread"
