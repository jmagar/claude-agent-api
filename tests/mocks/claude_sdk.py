"""Mock Claude SDK client for testing."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tests.mocks.event_builders import build_standard_response


class AssistantMessage:
    """Mock AssistantMessage from SDK.

    Matches the structure of claude_agent_sdk.AssistantMessage.
    The class name must match exactly for MessageHandler type checking.
    """

    def __init__(
        self,
        content: list[dict[str, object]] | None = None,
        model: str = "sonnet",
        usage: dict[str, int] | None = None,
    ) -> None:
        """Initialize mock assistant message.

        Args:
            content: List of content blocks
            model: Model name
            usage: Token usage info
        """
        self.content = content or [{"type": "text", "text": "Mocked response"}]
        self.model = model
        self.usage = usage


class MockClaudeSDKClient:
    """Mock implementation of ClaudeSDKClient.

    The real SDK has two methods:
    - query(prompt): Async method to send the prompt
    - receive_response(): Async generator that yields message objects
    """

    def __init__(self, options: object) -> None:
        """Initialize mock client.

        Args:
            options: Agent options (ignored in mock)
        """
        self.options = options
        self._messages: list[object] = []

    async def __aenter__(self) -> "MockClaudeSDKClient":
        """Context manager entry."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Context manager exit."""
        pass

    def set_messages(self, messages: list[object]) -> None:
        """Set messages to return from receive_response().

        Args:
            messages: List of SDK message objects to return
        """
        self._messages = messages

    async def query(self, prompt: str | list[dict[str, object]]) -> None:
        """Mock query method that sends the prompt.

        Args:
            prompt: Query prompt (text or multimodal content)
        """
        # If no messages set, prepare standard response
        if not self._messages:
            self._messages = [
                AssistantMessage(
                    content=[{"type": "text", "text": "Mocked response"}],
                    model="sonnet",
                    usage={
                        "input_tokens": 100,
                        "output_tokens": 50,
                        "cache_read_input_tokens": 0,
                        "cache_creation_input_tokens": 0,
                    },
                )
            ]

    async def receive_response(self) -> AsyncGenerator[object, None]:
        """Mock receive_response method that yields message objects.

        Yields:
            SDK message objects (AssistantMessage, UserMessage, etc.)
        """
        for message in self._messages:
            yield message


@pytest.fixture
def mock_claude_sdk() -> Any:
    """Mock the ClaudeSDKClient for testing.

    Patches the SDK at its source module since it's imported inside functions.

    Yields:
        Mock client class that returns standard response events
    """
    with patch("claude_agent_sdk.ClaudeSDKClient") as mock:
        # Create a mock that returns MockClaudeSDKClient instance
        def create_mock_instance(options: object) -> MockClaudeSDKClient:
            return MockClaudeSDKClient(options)

        mock.side_effect = create_mock_instance

        yield mock
