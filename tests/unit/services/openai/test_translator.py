"""Tests for OpenAI request translation to Claude Agent SDK format."""

import pytest

from apps.api.schemas.openai.requests import ChatCompletionRequest, OpenAIMessage
from apps.api.services.openai.models import ModelMapper
from apps.api.services.openai.translator import RequestTranslator


@pytest.fixture
def model_mapper() -> ModelMapper:
    """Create mock ModelMapper fixture that returns 'sonnet' for 'gpt-4'."""
    return ModelMapper({"gpt-4": "sonnet"})


class TestRequestTranslator:
    """Test suite for RequestTranslator."""

    def test_translate_single_user_message(self, model_mapper: ModelMapper) -> None:
        """Test translating a single user message to Claude format.

        Given: ChatCompletionRequest with model="gpt-4", messages=[{"role": "user", "content": "Hello"}]
        When: translator.translate(request)
        Then: Assert result.prompt == "USER: Hello\n\n"
        Then: Assert result.model == "sonnet" (via mock ModelMapper)
        """
        # Given
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[OpenAIMessage(role="user", content="Hello")],
        )
        translator = RequestTranslator(model_mapper)

        # When
        result = translator.translate(request)

        # Then
        assert result.prompt == "USER: Hello\n\n"
        assert result.model == "sonnet"

    def test_translate_system_message_extraction(self, model_mapper: ModelMapper) -> None:
        """Test extraction of system message to system_prompt field.

        Given: messages=[{"role": "system", "content": "You are helpful"}, {"role": "user", "content": "Hello"}]
        When: translator.translate(request)
        Then: Assert result.system_prompt == "You are helpful"
        Then: Assert result.prompt == "USER: Hello\n\n" (system NOT in prompt)
        """
        # Given
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[
                OpenAIMessage(role="system", content="You are helpful"),
                OpenAIMessage(role="user", content="Hello"),
            ],
        )
        translator = RequestTranslator(model_mapper)

        # When
        result = translator.translate(request)

        # Then
        assert result.system_prompt == "You are helpful"
        assert result.prompt == "USER: Hello\n\n"

    def test_translate_multi_turn_conversation(self, model_mapper: ModelMapper) -> None:
        """Test translating multi-turn conversation with user and assistant messages.

        Given: messages=[user, assistant, user] with different content
        When: translator.translate(request)
        Then: Assert prompt contains all messages with role prefixes in order
        """
        # Given
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[
                OpenAIMessage(role="user", content="What is 2+2?"),
                OpenAIMessage(role="assistant", content="2+2 equals 4."),
                OpenAIMessage(role="user", content="What about 3+3?"),
            ],
        )
        translator = RequestTranslator(model_mapper)

        # When
        result = translator.translate(request)

        # Then
        expected_prompt = "USER: What is 2+2?\n\nASSISTANT: 2+2 equals 4.\n\nUSER: What about 3+3?\n\n"
        assert result.prompt == expected_prompt
        assert result.model == "sonnet"
