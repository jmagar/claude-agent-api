"""Unit tests for MessageHandler (Priority 4).

Tests message handling, content extraction, and SSE formatting.
"""

import json
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from apps.api.schemas.responses import ContentBlockSchema
from apps.api.services.agent.handlers import MessageHandler
from apps.api.services.agent.types import StreamContext


@dataclass
class MockSDKMessage:
    """Mock SDK message with attributes."""

    content: list[dict[str, object]] | str
    model: str = "sonnet"
    usage: dict[str, int] | None = None
    uuid: str | None = None


@dataclass
class MockResultMessage:
    """Mock ResultMessage from SDK."""

    is_error: bool = False
    num_turns: int = 1
    total_cost_usd: float | None = None
    result: str | None = None
    model_usage: dict[str, dict[str, int]] | None = None
    structured_output: dict[str, object] | None = None


@dataclass
class MockPartialStart:
    """Mock ContentBlockStart message."""

    index: int
    content_block: object


@dataclass
class MockPartialDelta:
    """Mock ContentBlockDelta message."""

    index: int
    delta: object


@dataclass
class MockPartialStop:
    """Mock ContentBlockStop message."""

    index: int


@dataclass
class MockContentBlock:
    """Mock content block object."""

    type: str
    text: str | None = None
    id: str | None = None
    name: str | None = None


@dataclass
class MockDelta:
    """Mock delta object."""

    type: str
    text: str | None = None
    thinking: str | None = None
    partial_json: str | None = None


@pytest.fixture
def handler() -> MessageHandler:
    """Create MessageHandler instance.

    Returns:
        MessageHandler instance.
    """
    return MessageHandler()


@pytest.fixture
def stream_context() -> StreamContext:
    """Create stream context for testing.

    Returns:
        StreamContext instance.
    """
    return StreamContext(
        session_id="test-session-001",
        model="sonnet",
        start_time=0.0,
        enable_file_checkpointing=False,
        include_partial_messages=False,
    )


class TestResultMessage:
    """Tests for ResultMessage handling."""

    @pytest.mark.anyio
    async def test_handle_result_message_extracts_all_fields(
        self,
        handler: MessageHandler,
        stream_context: StreamContext,
    ) -> None:
        """Test full result extraction with all fields.

        GREEN: This test verifies all result fields are extracted correctly.
        """
        result_msg = MockResultMessage(
            is_error=False,
            num_turns=5,
            total_cost_usd=0.05,
            result="Operation completed",
        )

        handler._handle_result_message(result_msg, stream_context)

        assert stream_context.is_error is False
        assert stream_context.num_turns == 5
        assert stream_context.total_cost_usd == 0.05
        assert stream_context.result_text == "Operation completed"

    @pytest.mark.anyio
    async def test_handle_result_message_with_model_usage(
        self,
        handler: MessageHandler,
        stream_context: StreamContext,
    ) -> None:
        """Test usage tracking from result message.

        GREEN: This test verifies model usage extraction.
        """
        result_msg = MockResultMessage(
            model_usage={
                "sonnet": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cache_read_input_tokens": 0,
                    "cache_creation_input_tokens": 0,
                }
            }
        )

        handler._handle_result_message(result_msg, stream_context)

        assert stream_context.model_usage is not None
        assert "sonnet" in stream_context.model_usage
        assert stream_context.model_usage["sonnet"]["input_tokens"] == 100

    @pytest.mark.anyio
    async def test_handle_result_message_with_structured_output(
        self,
        handler: MessageHandler,
        stream_context: StreamContext,
    ) -> None:
        """Test structured output extraction.

        GREEN: This test verifies structured data extraction.
        """
        result_msg = MockResultMessage(
            structured_output={"type": "user", "name": "John", "age": 30}
        )

        handler._handle_result_message(result_msg, stream_context)

        assert stream_context.structured_output is not None
        assert stream_context.structured_output["type"] == "user"
        assert stream_context.structured_output["name"] == "John"


class TestPartialMessages:
    """Tests for partial/streaming messages."""

    @pytest.mark.anyio
    async def test_handle_partial_start_creates_event(
        self,
        handler: MessageHandler,
        stream_context: StreamContext,
    ) -> None:
        """Test partial start event creation.

        GREEN: This test verifies ContentBlockStart handling.
        """
        content_block = MockContentBlock(type="text", text="Hello")
        start_msg = MockPartialStart(index=0, content_block=content_block)

        result = handler._handle_partial_start(start_msg, stream_context)

        assert result["event"] == "partial"
        data = json.loads(result["data"])
        assert data["type"] == "content_block_start"
        assert data["index"] == 0
        assert data["content_block"]["type"] == "text"

    @pytest.mark.anyio
    async def test_handle_partial_delta_creates_event(
        self,
        handler: MessageHandler,
        stream_context: StreamContext,
    ) -> None:
        """Test partial delta event creation.

        GREEN: This test verifies ContentBlockDelta handling.
        """
        delta = MockDelta(type="text_delta", text=" world")
        delta_msg = MockPartialDelta(index=0, delta=delta)

        result = handler._handle_partial_delta(delta_msg, stream_context)

        assert result["event"] == "partial"
        data = json.loads(result["data"])
        assert data["type"] == "content_block_delta"
        assert data["index"] == 0
        assert data["delta"]["text"] == " world"

    @pytest.mark.anyio
    async def test_handle_partial_stop_creates_event(
        self,
        handler: MessageHandler,
        stream_context: StreamContext,
    ) -> None:
        """Test partial stop event creation.

        GREEN: This test verifies ContentBlockStop handling.
        """
        stop_msg = MockPartialStop(index=0)

        result = handler._handle_partial_stop(stop_msg, stream_context)

        assert result["event"] == "partial"
        data = json.loads(result["data"])
        assert data["type"] == "content_block_stop"
        assert data["index"] == 0


class TestSpecialToolUses:
    """Tests for special tool detection."""

    @pytest.mark.anyio
    async def test_check_special_tool_uses_detects_ask_user_question(
        self,
        handler: MessageHandler,
        stream_context: StreamContext,
    ) -> None:
        """Test AskUserQuestion detection.

        GREEN: This test verifies question event generation.
        """
        content_blocks = [
            ContentBlockSchema(
                type="tool_use",
                id="tool-123",
                name="AskUserQuestion",
                input={"question": "Should I proceed?"},
            )
        ]

        result = handler._check_special_tool_uses(content_blocks, stream_context)

        assert result is not None
        assert result["event"] == "question"
        data = json.loads(result["data"])
        assert data["question"] == "Should I proceed?"
        assert data["tool_use_id"] == "tool-123"

    @pytest.mark.anyio
    async def test_check_special_tool_uses_detects_todo_write(
        self,
        handler: MessageHandler,
        stream_context: StreamContext,
    ) -> None:
        """Test TodoWrite logging.

        GREEN: This test verifies TodoWrite is detected (logs but no event).
        """
        content_blocks = [
            ContentBlockSchema(
                type="tool_use",
                id="tool-456",
                name="TodoWrite",
                input={"todos": [{"content": "Task 1", "status": "pending"}]},
            )
        ]

        # TodoWrite doesn't return an event, just logs
        result = handler._check_special_tool_uses(content_blocks, stream_context)

        assert result is None


class TestContentExtraction:
    """Tests for content block extraction."""

    @pytest.mark.anyio
    async def test_extract_content_blocks_from_string(
        self,
        handler: MessageHandler,
    ) -> None:
        """Test string content extraction.

        GREEN: This test verifies string content is wrapped in text block.
        """
        message = MagicMock()
        message.content = "Hello, world!"

        blocks = handler._extract_content_blocks(message)

        assert len(blocks) == 1
        assert blocks[0].type == "text"
        assert blocks[0].text == "Hello, world!"

    @pytest.mark.anyio
    async def test_extract_content_blocks_from_dataclass(
        self,
        handler: MessageHandler,
    ) -> None:
        """Test dataclass content extraction.

        GREEN: This test verifies dataclass blocks are mapped correctly.
        """

        @dataclass
        class MockBlock:
            type: str
            text: str

        message = MagicMock()
        message.content = [MockBlock(type="text", text="Test content")]

        blocks = handler._extract_content_blocks(message)

        assert len(blocks) == 1
        assert blocks[0].type == "text"
        assert blocks[0].text == "Test content"


class TestUsageExtraction:
    """Tests for usage extraction."""

    @pytest.mark.anyio
    async def test_extract_usage_from_dict(
        self,
        handler: MessageHandler,
    ) -> None:
        """Test usage extraction from dict.

        GREEN: This test verifies dict usage mapping.
        """
        message = MagicMock()
        message.usage = {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_input_tokens": 10,
            "cache_creation_input_tokens": 5,
        }

        usage = handler._extract_usage(message)

        assert usage is not None
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.cache_read_input_tokens == 10
        assert usage.cache_creation_input_tokens == 5

    @pytest.mark.anyio
    async def test_extract_usage_from_dataclass(
        self,
        handler: MessageHandler,
    ) -> None:
        """Test usage extraction from dataclass.

        GREEN: This test verifies dataclass usage mapping.
        """

        @dataclass
        class MockUsage:
            input_tokens: int
            output_tokens: int
            cache_read_input_tokens: int
            cache_creation_input_tokens: int

        message = MagicMock()
        message.usage = MockUsage(
            input_tokens=200,
            output_tokens=100,
            cache_read_input_tokens=20,
            cache_creation_input_tokens=10,
        )

        usage = handler._extract_usage(message)

        assert usage is not None
        assert usage.input_tokens == 200
        assert usage.output_tokens == 100
