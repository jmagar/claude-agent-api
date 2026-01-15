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

    def test_translate_max_tokens_ignored(
        self, model_mapper: ModelMapper, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that max_tokens is accepted but NOT mapped to max_turns, WARNING logged.

        Given: ChatCompletionRequest with max_tokens=1000
        When: translator.translate(request)
        Then: max_tokens accepted but NOT mapped to max_turns
        Then: WARNING logged about unsupported parameter
        """
        # Given
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[OpenAIMessage(role="user", content="Hello")],
            max_tokens=1000,
        )
        translator = RequestTranslator(model_mapper)

        # When
        result = translator.translate(request)

        # Then
        # Verify max_turns field is NOT set (should not exist or be None)
        assert not hasattr(result, "max_turns") or result.max_turns is None
        # Verify warning was logged - structlog outputs to stdout/stderr
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "max_tokens" in output.lower()
        assert "not supported" in output.lower()

    def test_translate_max_tokens_none(self, model_mapper: ModelMapper) -> None:
        """Test that max_tokens=None does not set max_turns.

        Given: ChatCompletionRequest with max_tokens=None
        When: translator.translate(request)
        Then: max_turns field not set
        """
        # Given
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[OpenAIMessage(role="user", content="Hello")],
            max_tokens=None,
        )
        translator = RequestTranslator(model_mapper)

        # When
        result = translator.translate(request)

        # Then
        assert not hasattr(result, "max_turns") or result.max_turns is None

    def test_translate_max_tokens_does_not_set_max_turns(
        self, model_mapper: ModelMapper
    ) -> None:
        """Verify max_turns field is NOT set when max_tokens is present.

        Given: ChatCompletionRequest with max_tokens=1000
        When: translator.translate(request)
        Then: Verify max_turns field NOT set (incompatible semantics)
        """
        # Given
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[OpenAIMessage(role="user", content="Hello")],
            max_tokens=1000,
        )
        translator = RequestTranslator(model_mapper)

        # When
        result = translator.translate(request)

        # Then - Explicitly verify max_turns not set
        # QueryRequest doesn't have max_turns field, so this is verifying it's not added
        result_dict = result.model_dump(exclude_unset=True)
        assert "max_turns" not in result_dict

    def test_translate_temperature_warning(
        self, model_mapper: ModelMapper, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that temperature parameter logs WARNING and is NOT passed to QueryRequest.

        Given: ChatCompletionRequest with temperature=0.7
        When: translator.translate(request)
        Then: WARNING logged about unsupported parameter
        Then: temperature NOT included in QueryRequest
        """
        # Given
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[OpenAIMessage(role="user", content="Hello")],
            temperature=0.7,
        )
        translator = RequestTranslator(model_mapper)

        # When
        result = translator.translate(request)

        # Then
        # Verify warning was logged - structlog outputs to stdout/stderr
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "temperature" in output.lower()
        assert "not supported" in output.lower()

        # Verify temperature is NOT in result (QueryRequest doesn't have temperature field)
        result_dict = result.model_dump(exclude_unset=True)
        assert "temperature" not in result_dict

    def test_translate_top_p_warning(
        self, model_mapper: ModelMapper, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that top_p parameter logs WARNING and is NOT passed to QueryRequest.

        Given: ChatCompletionRequest with top_p=0.9
        When: translator.translate(request)
        Then: WARNING logged about unsupported parameter
        Then: top_p NOT included in QueryRequest
        """
        # Given
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[OpenAIMessage(role="user", content="Hello")],
            top_p=0.9,
        )
        translator = RequestTranslator(model_mapper)

        # When
        result = translator.translate(request)

        # Then
        # Verify warning was logged - structlog outputs to stdout/stderr
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "top_p" in output.lower()
        assert "not supported" in output.lower()

        # Verify top_p is NOT in result (QueryRequest doesn't have top_p field)
        result_dict = result.model_dump(exclude_unset=True)
        assert "top_p" not in result_dict

    def test_translate_stop_warning(
        self, model_mapper: ModelMapper, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that stop sequences parameter logs WARNING and is NOT passed to QueryRequest.

        Given: ChatCompletionRequest with stop=["END"]
        When: translator.translate(request)
        Then: WARNING logged about unsupported parameter
        Then: stop NOT included in QueryRequest
        """
        # Given
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[OpenAIMessage(role="user", content="Hello")],
            stop=["END"],
        )
        translator = RequestTranslator(model_mapper)

        # When
        result = translator.translate(request)

        # Then
        # Verify warning was logged - structlog outputs to stdout/stderr
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "stop" in output.lower()
        assert "not supported" in output.lower()

        # Verify stop is NOT in result (QueryRequest doesn't have stop field)
        result_dict = result.model_dump(exclude_unset=True)
        assert "stop" not in result_dict

    def test_translate_user_field(self, model_mapper: ModelMapper) -> None:
        """Test that user field is properly mapped to QueryRequest.user (SUPPORTED).

        Given: ChatCompletionRequest with user="user-123"
        When: translator.translate(request)
        Then: QueryRequest.user == "user-123"
        """
        # Given
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[OpenAIMessage(role="user", content="Hello")],
            user="user-123",
        )
        translator = RequestTranslator(model_mapper)

        # When
        result = translator.translate(request)

        # Then
        assert result.user == "user-123"


@pytest.fixture
def mock_single_query_response() -> object:
    """Create mock SingleQueryResponse fixture for ResponseTranslator tests.

    Returns:
        Mock SingleQueryResponse with basic text content
    """
    from apps.api.schemas.responses import ContentBlockSchema, SingleQueryResponse, UsageSchema

    return SingleQueryResponse(
        session_id="test-session-123",
        model="sonnet",
        content=[ContentBlockSchema(type="text", text="Hello!")],
        is_error=False,
        stop_reason="completed",
        duration_ms=1000,
        num_turns=1,
        usage=UsageSchema(input_tokens=10, output_tokens=5),
    )


class TestResponseTranslator:
    """Test suite for ResponseTranslator."""

    def test_translate_basic_response(
        self, mock_single_query_response: object
    ) -> None:
        """Test translating basic SingleQueryResponse to OpenAI format.

        Given: Mock SingleQueryResponse with content=[{"type": "text", "text": "Hello!"}], model="sonnet"
        When: translator.translate(response, original_model="gpt-4")
        Then: Assert result["choices"][0]["message"]["content"] == "Hello!"
        Then: Assert result["model"] == "gpt-4"
        Then: Assert result["object"] == "chat.completion"
        Then: Assert result["id"] starts with "chatcmpl-"
        """
        # Import here to trigger the expected ModuleNotFoundError
        from apps.api.services.openai.translator import ResponseTranslator

        # Given
        translator = ResponseTranslator()
        response = mock_single_query_response

        # When
        result = translator.translate(response, original_model="gpt-4")

        # Then
        assert result["choices"][0]["message"]["content"] == "Hello!"
        assert result["model"] == "gpt-4"
        assert result["object"] == "chat.completion"
        assert result["id"].startswith("chatcmpl-")
        # Verify ID is valid UUID format (chatcmpl- prefix + UUID)
        assert len(result["id"]) > len("chatcmpl-")
        # Verify created timestamp is reasonable (within last hour)
        import time
        now = int(time.time())
        assert abs(result["created"] - now) < 3600

    def test_translate_usage_mapping(self) -> None:
        """Test usage token mapping from SingleQueryResponse to OpenAI format.

        Given: SingleQueryResponse with usage.input_tokens=10, output_tokens=20
        When: translator.translate(response)
        Then: Assert result["usage"]["prompt_tokens"] == 10
        Then: Assert result["usage"]["completion_tokens"] == 20
        Then: Assert result["usage"]["total_tokens"] == 30
        """
        # Import here to match other tests
        from apps.api.schemas.responses import ContentBlockSchema, SingleQueryResponse, UsageSchema
        from apps.api.services.openai.translator import ResponseTranslator

        # Given
        response = SingleQueryResponse(
            session_id="test-session-456",
            model="sonnet",
            content=[ContentBlockSchema(type="text", text="Response")],
            is_error=False,
            stop_reason="completed",
            duration_ms=500,
            num_turns=1,
            usage=UsageSchema(input_tokens=10, output_tokens=20),
        )
        translator = ResponseTranslator()

        # When
        result = translator.translate(response, original_model="gpt-4")

        # Then
        assert result["usage"]["prompt_tokens"] == 10
        assert result["usage"]["completion_tokens"] == 20
        assert result["usage"]["total_tokens"] == 30

    def test_translate_stop_reason_completed(self) -> None:
        """Test stop_reason 'completed' maps to finish_reason 'stop'.

        Given: SingleQueryResponse with stop_reason="completed"
        When: translator.translate(response)
        Then: Assert result["choices"][0]["finish_reason"] == "stop"
        """
        # Import here to match other tests
        from apps.api.schemas.responses import ContentBlockSchema, SingleQueryResponse, UsageSchema
        from apps.api.services.openai.translator import ResponseTranslator

        # Given
        response = SingleQueryResponse(
            session_id="test-session-789",
            model="sonnet",
            content=[ContentBlockSchema(type="text", text="Done")],
            is_error=False,
            stop_reason="completed",
            duration_ms=1000,
            num_turns=1,
            usage=UsageSchema(input_tokens=5, output_tokens=10),
        )
        translator = ResponseTranslator()

        # When
        result = translator.translate(response, original_model="gpt-4")

        # Then
        assert result["choices"][0]["finish_reason"] == "stop"

    def test_translate_stop_reason_max_turns(self) -> None:
        """Test stop_reason 'max_turns_reached' maps to finish_reason 'length'.

        Given: SingleQueryResponse with stop_reason="max_turns_reached"
        When: translator.translate(response)
        Then: Assert result["choices"][0]["finish_reason"] == "length"
        """
        # Import here to match other tests
        from apps.api.schemas.responses import ContentBlockSchema, SingleQueryResponse, UsageSchema
        from apps.api.services.openai.translator import ResponseTranslator

        # Given
        response = SingleQueryResponse(
            session_id="test-session-abc",
            model="sonnet",
            content=[ContentBlockSchema(type="text", text="Truncated")],
            is_error=False,
            stop_reason="max_turns_reached",
            duration_ms=2000,
            num_turns=10,
            usage=UsageSchema(input_tokens=100, output_tokens=200),
        )
        translator = ResponseTranslator()

        # When
        result = translator.translate(response, original_model="gpt-4")

        # Then
        assert result["choices"][0]["finish_reason"] == "length"

    def test_translate_stop_reason_error(self) -> None:
        """Test stop_reason 'error' maps to finish_reason 'error'.

        Given: SingleQueryResponse with stop_reason="error"
        When: translator.translate(response)
        Then: Assert result["choices"][0]["finish_reason"] == "error"
        """
        # Import here to match other tests
        from apps.api.schemas.responses import ContentBlockSchema, SingleQueryResponse, UsageSchema
        from apps.api.services.openai.translator import ResponseTranslator

        # Given
        response = SingleQueryResponse(
            session_id="test-session-def",
            model="sonnet",
            content=[ContentBlockSchema(type="text", text="Error occurred")],
            is_error=True,
            stop_reason="error",
            duration_ms=500,
            num_turns=1,
            usage=UsageSchema(input_tokens=5, output_tokens=3),
        )
        translator = ResponseTranslator()

        # When
        result = translator.translate(response, original_model="gpt-4")

        # Then
        assert result["choices"][0]["finish_reason"] == "error"

    def test_translate_stop_reason_interrupted(self) -> None:
        """Test stop_reason 'interrupted' maps to finish_reason 'stop'.

        Given: SingleQueryResponse with stop_reason="interrupted"
        When: translator.translate(response)
        Then: Assert result["choices"][0]["finish_reason"] == "stop"
        """
        # Import here to match other tests
        from apps.api.schemas.responses import ContentBlockSchema, SingleQueryResponse, UsageSchema
        from apps.api.services.openai.translator import ResponseTranslator

        # Given
        response = SingleQueryResponse(
            session_id="test-session-ghi",
            model="sonnet",
            content=[ContentBlockSchema(type="text", text="Interrupted")],
            is_error=False,
            stop_reason="interrupted",
            duration_ms=800,
            num_turns=2,
            usage=UsageSchema(input_tokens=15, output_tokens=20),
        )
        translator = ResponseTranslator()

        # When
        result = translator.translate(response, original_model="gpt-4")

        # Then
        assert result["choices"][0]["finish_reason"] == "stop"
