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
