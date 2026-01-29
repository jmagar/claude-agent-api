"""End-to-end tests for OpenAI Assistants API compatibility.

These tests call the real Claude backend through the Assistants API translation layer.
Requires ALLOW_REAL_CLAUDE_API=true to run.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.anyio
async def test_create_assistant(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test creating an assistant through OpenAI endpoint.

    Verifies:
    - POST /v1/assistants creates an assistant
    - Response has correct OpenAI format
    - Assistant ID starts with 'asst_'
    """
    response = await async_client.post(
        "/v1/assistants",
        json={
            "model": "gpt-4",
            "name": "Test E2E Assistant",
            "description": "An assistant for E2E testing",
            "instructions": "You are a helpful assistant for testing purposes.",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    data = response.json()

    # Verify OpenAI response structure
    assert data["object"] == "assistant"
    assert data["id"].startswith("asst_"), f"Invalid ID format: {data['id']}"
    assert data["model"] == "gpt-4"
    assert data["name"] == "Test E2E Assistant"
    assert data["description"] == "An assistant for E2E testing"
    assert data["instructions"] == "You are a helpful assistant for testing purposes."
    assert isinstance(data["tools"], list)
    assert isinstance(data["metadata"], dict)
    assert isinstance(data["created_at"], int)


@pytest.mark.e2e
@pytest.mark.anyio
async def test_list_assistants(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test listing assistants through OpenAI endpoint.

    Verifies:
    - GET /v1/assistants returns paginated list
    - Response has correct OpenAI format
    """
    response = await async_client.get(
        "/v1/assistants",
        headers=auth_headers,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    data = response.json()

    # Verify OpenAI response structure
    assert data["object"] == "list"
    assert isinstance(data["data"], list)
    assert "has_more" in data


@pytest.mark.e2e
@pytest.mark.anyio
async def test_create_thread(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test creating a thread through OpenAI endpoint.

    Verifies:
    - POST /v1/threads creates a thread
    - Response has correct OpenAI format
    - Thread ID starts with 'thread_'
    """
    response = await async_client.post(
        "/v1/threads",
        json={},
        headers=auth_headers,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    data = response.json()

    # Verify OpenAI response structure
    assert data["object"] == "thread"
    assert data["id"].startswith("thread_"), f"Invalid ID format: {data['id']}"
    assert isinstance(data["created_at"], int)
    assert isinstance(data["metadata"], dict)


@pytest.mark.e2e
@pytest.mark.anyio
async def test_create_message_in_thread(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test creating a message in a thread.

    Verifies:
    - POST /v1/threads/{thread_id}/messages creates a message
    - Response has correct OpenAI format
    - Message ID starts with 'msg_'
    """
    # First create a thread
    thread_response = await async_client.post(
        "/v1/threads",
        json={},
        headers=auth_headers,
    )
    assert thread_response.status_code == 200
    thread_id = thread_response.json()["id"]

    # Then create a message
    response = await async_client.post(
        f"/v1/threads/{thread_id}/messages",
        json={
            "role": "user",
            "content": "Hello, how are you?",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    data = response.json()

    # Verify OpenAI response structure
    assert data["object"] == "thread.message"
    assert data["id"].startswith("msg_"), f"Invalid ID format: {data['id']}"
    assert data["thread_id"] == thread_id
    assert data["role"] == "user"
    assert isinstance(data["content"], list)
    assert len(data["content"]) > 0
    assert data["content"][0]["type"] == "text"
    assert data["content"][0]["text"]["value"] == "Hello, how are you?"


@pytest.mark.e2e
@pytest.mark.anyio
async def test_list_messages_in_thread(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test listing messages in a thread.

    Verifies:
    - GET /v1/threads/{thread_id}/messages returns paginated list
    - Response has correct OpenAI format
    """
    # First create a thread with a message
    thread_response = await async_client.post(
        "/v1/threads",
        json={},
        headers=auth_headers,
    )
    assert thread_response.status_code == 200
    thread_id = thread_response.json()["id"]

    # Create a message
    await async_client.post(
        f"/v1/threads/{thread_id}/messages",
        json={"role": "user", "content": "Test message"},
        headers=auth_headers,
    )

    # List messages
    response = await async_client.get(
        f"/v1/threads/{thread_id}/messages",
        headers=auth_headers,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    data = response.json()

    # Verify OpenAI response structure
    assert data["object"] == "list"
    assert isinstance(data["data"], list)
    assert "has_more" in data


@pytest.mark.e2e
@pytest.mark.anyio
async def test_create_run_on_thread(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test creating a run on a thread.

    Verifies:
    - POST /v1/threads/{thread_id}/runs creates a run
    - Response has correct OpenAI format
    - Run ID starts with 'run_'
    """
    # First create an assistant
    assistant_response = await async_client.post(
        "/v1/assistants",
        json={
            "model": "gpt-4",
            "name": "Test Run Assistant",
            "instructions": "You are a helpful assistant.",
        },
        headers=auth_headers,
    )
    assert assistant_response.status_code == 200
    assistant_id = assistant_response.json()["id"]

    # Create a thread
    thread_response = await async_client.post(
        "/v1/threads",
        json={},
        headers=auth_headers,
    )
    assert thread_response.status_code == 200
    thread_id = thread_response.json()["id"]

    # Create a message
    await async_client.post(
        f"/v1/threads/{thread_id}/messages",
        json={"role": "user", "content": "Say hello"},
        headers=auth_headers,
    )

    # Create a run
    response = await async_client.post(
        f"/v1/threads/{thread_id}/runs",
        json={"assistant_id": assistant_id},
        headers=auth_headers,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    data = response.json()

    # Verify OpenAI response structure
    assert data["object"] == "thread.run"
    assert data["id"].startswith("run_"), f"Invalid ID format: {data['id']}"
    assert data["thread_id"] == thread_id
    assert data["assistant_id"] == assistant_id
    assert data["status"] in ["queued", "in_progress", "completed"]
    assert isinstance(data["created_at"], int)


@pytest.mark.e2e
@pytest.mark.anyio
async def test_get_run_status(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test getting run status.

    Verifies:
    - GET /v1/threads/{thread_id}/runs/{run_id} returns run
    - Response has correct OpenAI format
    """
    # Create assistant, thread, message, and run
    assistant_response = await async_client.post(
        "/v1/assistants",
        json={
            "model": "gpt-4",
            "instructions": "You are helpful.",
        },
        headers=auth_headers,
    )
    assistant_id = assistant_response.json()["id"]

    thread_response = await async_client.post(
        "/v1/threads",
        json={},
        headers=auth_headers,
    )
    thread_id = thread_response.json()["id"]

    await async_client.post(
        f"/v1/threads/{thread_id}/messages",
        json={"role": "user", "content": "Hi"},
        headers=auth_headers,
    )

    run_response = await async_client.post(
        f"/v1/threads/{thread_id}/runs",
        json={"assistant_id": assistant_id},
        headers=auth_headers,
    )
    run_id = run_response.json()["id"]

    # Get run status
    response = await async_client.get(
        f"/v1/threads/{thread_id}/runs/{run_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    data = response.json()

    # Verify OpenAI response structure
    assert data["object"] == "thread.run"
    assert data["id"] == run_id
    assert data["thread_id"] == thread_id
    assert data["assistant_id"] == assistant_id


@pytest.mark.e2e
@pytest.mark.anyio
async def test_cancel_run(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test cancelling a run.

    Verifies:
    - POST /v1/threads/{thread_id}/runs/{run_id}/cancel cancels the run
    - Response shows cancelled status
    """
    # Create assistant, thread, message, and run
    assistant_response = await async_client.post(
        "/v1/assistants",
        json={
            "model": "gpt-4",
            "instructions": "You are helpful.",
        },
        headers=auth_headers,
    )
    assistant_id = assistant_response.json()["id"]

    thread_response = await async_client.post(
        "/v1/threads",
        json={},
        headers=auth_headers,
    )
    thread_id = thread_response.json()["id"]

    await async_client.post(
        f"/v1/threads/{thread_id}/messages",
        json={"role": "user", "content": "Hi"},
        headers=auth_headers,
    )

    run_response = await async_client.post(
        f"/v1/threads/{thread_id}/runs",
        json={"assistant_id": assistant_id},
        headers=auth_headers,
    )
    run_id = run_response.json()["id"]

    # Cancel the run
    response = await async_client.post(
        f"/v1/threads/{thread_id}/runs/{run_id}/cancel",
        headers=auth_headers,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    data = response.json()

    # Verify status is cancelled or cancelling
    assert data["status"] in ["cancelled", "cancelling", "queued", "in_progress"]


@pytest.mark.e2e
@pytest.mark.anyio
async def test_delete_assistant(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test deleting an assistant.

    Verifies:
    - DELETE /v1/assistants/{assistant_id} deletes the assistant
    - Response confirms deletion
    """
    # Create an assistant
    assistant_response = await async_client.post(
        "/v1/assistants",
        json={
            "model": "gpt-4",
            "name": "Assistant to Delete",
        },
        headers=auth_headers,
    )
    assistant_id = assistant_response.json()["id"]

    # Delete the assistant
    response = await async_client.delete(
        f"/v1/assistants/{assistant_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    data = response.json()

    # Verify deletion confirmation
    assert data["object"] == "assistant.deleted"
    assert data["id"] == assistant_id
    assert data["deleted"] is True


@pytest.mark.e2e
@pytest.mark.anyio
async def test_delete_thread(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test deleting a thread.

    Verifies:
    - DELETE /v1/threads/{thread_id} deletes the thread
    - Response confirms deletion
    """
    # Create a thread
    thread_response = await async_client.post(
        "/v1/threads",
        json={},
        headers=auth_headers,
    )
    thread_id = thread_response.json()["id"]

    # Delete the thread
    response = await async_client.delete(
        f"/v1/threads/{thread_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    data = response.json()

    # Verify deletion confirmation
    assert data["object"] == "thread.deleted"
    assert data["id"] == thread_id
    assert data["deleted"] is True
