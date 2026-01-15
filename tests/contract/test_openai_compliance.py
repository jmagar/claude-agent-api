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
