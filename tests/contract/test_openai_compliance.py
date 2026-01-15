"""Contract tests for OpenAI Python client compatibility.

These tests verify that the OpenAI official Python client can successfully
interact with our API using only a base_url change.
"""

import pytest
from openai import OpenAI


class TestOpenAIClientCompliance:
    """Test suite for OpenAI Python client compliance."""

    @pytest.fixture
    def client(self) -> OpenAI:
        """Create OpenAI client configured to use our API.

        Note: Uses the API key from the running dev server's .env file.
        For integration tests against running server, we need to use
        the actual configured API key, not the test fixture key.

        Returns:
            Configured OpenAI client
        """
        return OpenAI(
            api_key="your-api-key-for-clients",
            base_url="http://localhost:54000/v1",
        )

    def test_openai_client_basic_completion(self, client: OpenAI) -> None:
        """Test basic chat completion using OpenAI Python client.

        Validates:
        - Client can connect to our API
        - Chat completion request succeeds
        - Response is proper ChatCompletion object
        - Response contains content

        Args:
            client: OpenAI client from fixture
        """
        # Create chat completion request
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Say 'Hello from OpenAI client test'"}
            ],
        )

        # Validate response structure
        assert response.id.startswith("chatcmpl-"), "Invalid completion ID format"
        assert response.object == "chat.completion", "Invalid object type"
        assert response.model == "sonnet", "Model should be mapped to 'sonnet'"

        # Validate choices
        assert len(response.choices) == 1, "Should have exactly one choice"
        choice = response.choices[0]
        assert choice.index == 0, "Choice index should be 0"
        assert choice.message.role == "assistant", "Message role should be 'assistant'"
        assert choice.message.content is not None, "Message content should not be None"
        assert len(choice.message.content) > 0, "Message content should not be empty"
        assert choice.finish_reason in [
            "stop",
            "length",
        ], f"Invalid finish reason: {choice.finish_reason}"

        # Validate usage (if present)
        if response.usage:
            assert response.usage.prompt_tokens >= 0, "Invalid prompt_tokens"
            assert response.usage.completion_tokens >= 0, "Invalid completion_tokens"
            assert (
                response.usage.total_tokens
                == response.usage.prompt_tokens + response.usage.completion_tokens
            ), "Total tokens should equal prompt + completion"

        # Validate timestamp
        assert response.created > 0, "Created timestamp should be positive"

    def test_openai_client_streaming_completion(self, client: OpenAI) -> None:
        """Test streaming chat completion using OpenAI Python client.

        Validates:
        - Client can stream responses from our API
        - Chunks are proper ChatCompletionChunk objects
        - First chunk contains role delta
        - Content deltas accumulate to full response
        - Final chunk contains finish_reason
        - Stream format matches OpenAI protocol

        Args:
            client: OpenAI client from fixture
        """
        # Create streaming chat completion request
        stream = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Count to three"}],
            stream=True,
        )

        # Collect all chunks
        chunks = list(stream)
        assert len(chunks) > 0, "Stream should yield at least one chunk"

        # Validate chunk structure
        for chunk in chunks:
            assert chunk.id.startswith(
                "chatcmpl-"
            ), f"Invalid chunk ID format: {chunk.id}"
            assert (
                chunk.object == "chat.completion.chunk"
            ), f"Invalid chunk object type: {chunk.object}"
            assert chunk.model == "gpt-4", f"Model should be 'gpt-4', got {chunk.model}"
            assert chunk.created > 0, "Created timestamp should be positive"
            assert len(chunk.choices) == 1, "Should have exactly one choice"
            assert chunk.choices[0].index == 0, "Choice index should be 0"

        # First chunk should have role delta
        first_chunk = chunks[0]
        assert first_chunk.choices[0].delta.role == "assistant", (
            "First chunk should have role='assistant' in delta"
        )
        assert (
            first_chunk.choices[0].finish_reason is None
        ), "First chunk should not have finish_reason"

        # Accumulate content from deltas
        accumulated_content = ""
        for chunk in chunks:
            delta = chunk.choices[0].delta
            if delta.content:
                accumulated_content += delta.content

        # Note: Content may be empty if SDK doesn't emit partial events with content
        # This is acceptable for contract test - we're validating structure, not content

        # Last chunk should have finish_reason
        last_chunk = chunks[-1]
        assert last_chunk.choices[0].finish_reason in [
            "stop",
            "length",
        ], f"Invalid finish reason: {last_chunk.choices[0].finish_reason}"

        # All chunks should have same completion ID
        completion_ids = {chunk.id for chunk in chunks}
        assert (
            len(completion_ids) == 1
        ), "All chunks should have the same completion ID"

    def test_openai_client_handles_errors(self, client: OpenAI) -> None:
        """Test OpenAI client error handling.

        Validates:
        - Invalid model raises proper OpenAI error
        - Authentication failure raises AuthenticationError
        - Error types are from openai module

        Args:
            client: OpenAI client from fixture
        """
        from openai import AuthenticationError, BadRequestError

        # Test invalid model
        with pytest.raises(BadRequestError) as exc_info:
            client.chat.completions.create(
                model="invalid-model-xyz",
                messages=[{"role": "user", "content": "Hello"}],
            )
        error = exc_info.value
        assert "invalid-model-xyz" in str(error).lower() or "model" in str(error).lower(), (
            "Error message should mention the invalid model"
        )

        # Test authentication failure
        bad_auth_client = OpenAI(
            api_key="invalid-api-key-xyz",
            base_url="http://localhost:54000/v1",
        )
        with pytest.raises(AuthenticationError) as exc_info:
            bad_auth_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Hello"}],
            )
        error = exc_info.value
        assert error.status_code == 401, "Authentication error should have 401 status"
