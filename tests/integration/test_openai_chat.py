"""Integration tests for OpenAI chat completions endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_non_streaming_completion_basic(async_client: AsyncClient) -> None:
    """Test basic non-streaming chat completion with OpenAI format.

    Verifies:
    - POST /v1/chat/completions with stream=false works
    - Response has correct OpenAI format (id, object, choices, usage)
    - choices[0].message.content is a string
    - Status code is 200
    """
    # Arrange
    request_data = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "stream": False
    }
    headers = {
        "Authorization": "Bearer test-api-key-12345",
        "Content-Type": "application/json"
    }

    # Act
    response = await async_client.post(
        "/v1/chat/completions",
        json=request_data,
        headers=headers
    )

    # Assert
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()

    # Verify OpenAI format structure
    assert "id" in data, "Response missing 'id' field"
    assert data["id"].startswith("chatcmpl-"), f"ID should start with 'chatcmpl-', got: {data['id']}"

    assert "object" in data, "Response missing 'object' field"
    assert data["object"] == "chat.completion", f"Expected object='chat.completion', got: {data['object']}"

    assert "choices" in data, "Response missing 'choices' field"
    assert isinstance(data["choices"], list), "choices should be a list"
    assert len(data["choices"]) > 0, "choices should have at least one element"

    choice = data["choices"][0]
    assert "message" in choice, "Choice missing 'message' field"
    assert "content" in choice["message"], "Message missing 'content' field"
    assert isinstance(choice["message"]["content"], str), "Message content should be a string"
    assert len(choice["message"]["content"]) > 0, "Message content should not be empty"

    assert "usage" in data, "Response missing 'usage' field"
    assert "prompt_tokens" in data["usage"], "Usage missing 'prompt_tokens'"
    assert "completion_tokens" in data["usage"], "Usage missing 'completion_tokens'"
    assert "total_tokens" in data["usage"], "Usage missing 'total_tokens'"
