"""Unit tests for RunExecutor (TDD - RED phase)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from apps.api.services.assistants.run_executor import ToolOutput
    from apps.api.services.assistants.run_service import ToolCall


@pytest.fixture
def mock_run_service() -> AsyncMock:
    """Create mock run service."""
    service = AsyncMock()
    service.start_run = AsyncMock()
    service.complete_run = AsyncMock()
    service.fail_run = AsyncMock()
    service.require_action = AsyncMock()
    service.submit_tool_outputs = AsyncMock()
    return service


@pytest.fixture
def mock_message_service() -> AsyncMock:
    """Create mock message service."""
    service = AsyncMock()
    service.create_message = AsyncMock()
    return service


@pytest.fixture
def mock_assistant_service() -> AsyncMock:
    """Create mock assistant service."""
    service = AsyncMock()
    service.get_assistant = AsyncMock()
    return service


@pytest.fixture
def mock_thread_service() -> AsyncMock:
    """Create mock thread service."""
    service = AsyncMock()
    service.get_thread = AsyncMock()
    return service


class TestRunExecutorImport:
    """Tests for RunExecutor import."""

    def test_can_import_executor(self) -> None:
        """Executor can be imported from the module."""
        from apps.api.services.assistants.run_executor import RunExecutor

        assert RunExecutor is not None

    def test_can_import_execution_result(self) -> None:
        """ExecutionResult can be imported."""
        from apps.api.services.assistants.run_executor import ExecutionResult

        assert ExecutionResult is not None

    def test_can_import_tool_output(self) -> None:
        """ToolOutput type can be imported."""
        from apps.api.services.assistants.run_executor import ToolOutput

        assert ToolOutput is not None


class TestRunExecutorCreate:
    """Tests for creating RunExecutor."""

    def test_create_executor(
        self,
        mock_run_service: AsyncMock,
        mock_message_service: AsyncMock,
        mock_assistant_service: AsyncMock,
        mock_thread_service: AsyncMock,
    ) -> None:
        """Create a RunExecutor instance."""
        from apps.api.services.assistants.run_executor import RunExecutor

        executor = RunExecutor(
            run_service=mock_run_service,
            message_service=mock_message_service,
            assistant_service=mock_assistant_service,
            thread_service=mock_thread_service,
        )

        assert executor is not None


class TestRunExecutorExecute:
    """Tests for executing runs."""

    @pytest.mark.anyio
    async def test_execute_run_success(
        self,
        mock_run_service: AsyncMock,
        mock_message_service: AsyncMock,
        mock_assistant_service: AsyncMock,
        mock_thread_service: AsyncMock,
    ) -> None:
        """Execute a run successfully."""
        from apps.api.services.assistants.run_executor import (
            ExecutionResult,
            RunExecutor,
        )
        from apps.api.services.assistants.run_service import Run

        # Setup mock run
        mock_run = MagicMock(spec=Run)
        mock_run.id = "run_abc123"
        mock_run.thread_id = "thread_abc123"
        mock_run.assistant_id = "asst_abc123"
        mock_run.model = "gpt-4"
        mock_run.instructions = "You are a helpful assistant."
        mock_run.status = "queued"

        mock_run_service.start_run = AsyncMock(return_value=mock_run)
        mock_run_service.complete_run = AsyncMock(return_value=mock_run)

        # Setup mock assistant
        mock_assistant = MagicMock()
        mock_assistant.model = "gpt-4"
        mock_assistant.instructions = "You are a helpful assistant."
        mock_assistant.tools = []
        mock_assistant_service.get_assistant = AsyncMock(return_value=mock_assistant)

        # Setup mock thread
        mock_thread = MagicMock()
        mock_thread.id = "thread_abc123"
        mock_thread_service.get_thread = AsyncMock(return_value=mock_thread)

        # Setup mock message
        mock_message = MagicMock()
        mock_message.id = "msg_abc123"
        mock_message_service.create_message = AsyncMock(return_value=mock_message)

        executor = RunExecutor(
            run_service=mock_run_service,
            message_service=mock_message_service,
            assistant_service=mock_assistant_service,
            thread_service=mock_thread_service,
        )

        # Mock the SDK response
        with patch.object(executor, "_execute_with_sdk") as mock_execute:
            mock_execute.return_value = ExecutionResult(
                response_text="Hello! How can I help you?",
                tool_calls=[],
                usage={
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
            )

            result = await executor.execute_run(
                thread_id="thread_abc123",
                run_id="run_abc123",
            )

        assert result is not None
        assert result.response_text == "Hello! How can I help you?"

        # Verify run was started
        mock_run_service.start_run.assert_called_once_with(
            "thread_abc123", "run_abc123"
        )

    @pytest.mark.anyio
    async def test_execute_run_with_tool_calls(
        self,
        mock_run_service: AsyncMock,
        mock_message_service: AsyncMock,
        mock_assistant_service: AsyncMock,
        mock_thread_service: AsyncMock,
    ) -> None:
        """Execute run that requires tool calls."""
        from apps.api.services.assistants.run_executor import (
            ExecutionResult,
            RunExecutor,
        )
        from apps.api.services.assistants.run_service import Run

        # Setup mock run
        mock_run = MagicMock(spec=Run)
        mock_run.id = "run_abc123"
        mock_run.thread_id = "thread_abc123"
        mock_run.assistant_id = "asst_abc123"
        mock_run.model = "gpt-4"
        mock_run.status = "queued"

        mock_run_service.start_run = AsyncMock(return_value=mock_run)
        mock_run_service.require_action = AsyncMock(return_value=mock_run)

        # Setup mock assistant
        mock_assistant = MagicMock()
        mock_assistant.model = "gpt-4"
        mock_assistant.instructions = None
        mock_assistant.tools = [
            {"type": "function", "function": {"name": "get_weather"}}
        ]
        mock_assistant_service.get_assistant = AsyncMock(return_value=mock_assistant)

        # Setup mock thread
        mock_thread = MagicMock()
        mock_thread.id = "thread_abc123"
        mock_thread_service.get_thread = AsyncMock(return_value=mock_thread)

        executor = RunExecutor(
            run_service=mock_run_service,
            message_service=mock_message_service,
            assistant_service=mock_assistant_service,
            thread_service=mock_thread_service,
        )

        # Mock the SDK response with tool calls
        tool_calls: list[ToolCall] = [
            {
                "id": "call_abc123",
                "type": "function",
                "function": {"name": "get_weather", "arguments": '{"location": "NYC"}'},
            }
        ]

        with patch.object(executor, "_execute_with_sdk") as mock_execute:
            mock_execute.return_value = ExecutionResult(
                response_text=None,
                tool_calls=tool_calls,
                usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            )

            result = await executor.execute_run(
                thread_id="thread_abc123",
                run_id="run_abc123",
            )

        assert result is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["function"]["name"] == "get_weather"

        # Verify run transitioned to requires_action
        mock_run_service.require_action.assert_called_once()

    @pytest.mark.anyio
    async def test_execute_run_failure(
        self,
        mock_run_service: AsyncMock,
        mock_message_service: AsyncMock,
        mock_assistant_service: AsyncMock,
        mock_thread_service: AsyncMock,
    ) -> None:
        """Execute run that fails."""
        from apps.api.services.assistants.run_executor import RunExecutor
        from apps.api.services.assistants.run_service import Run

        # Setup mock run
        mock_run = MagicMock(spec=Run)
        mock_run.id = "run_abc123"
        mock_run.thread_id = "thread_abc123"
        mock_run.assistant_id = "asst_abc123"
        mock_run.model = "gpt-4"
        mock_run.status = "queued"

        mock_run_service.start_run = AsyncMock(return_value=mock_run)
        mock_run_service.fail_run = AsyncMock(return_value=mock_run)

        # Setup mock assistant
        mock_assistant = MagicMock()
        mock_assistant.model = "gpt-4"
        mock_assistant.instructions = None
        mock_assistant.tools = []
        mock_assistant_service.get_assistant = AsyncMock(return_value=mock_assistant)

        # Setup mock thread
        mock_thread = MagicMock()
        mock_thread.id = "thread_abc123"
        mock_thread_service.get_thread = AsyncMock(return_value=mock_thread)

        executor = RunExecutor(
            run_service=mock_run_service,
            message_service=mock_message_service,
            assistant_service=mock_assistant_service,
            thread_service=mock_thread_service,
        )

        # Mock the SDK to raise an error
        with patch.object(executor, "_execute_with_sdk") as mock_execute:
            mock_execute.side_effect = Exception("SDK error")

            result = await executor.execute_run(
                thread_id="thread_abc123",
                run_id="run_abc123",
            )

        # Verify run was marked as failed
        mock_run_service.fail_run.assert_called_once()

        # Result should indicate failure
        assert result is None or result.response_text is None

    @pytest.mark.anyio
    async def test_execute_run_not_found(
        self,
        mock_run_service: AsyncMock,
        mock_message_service: AsyncMock,
        mock_assistant_service: AsyncMock,
        mock_thread_service: AsyncMock,
    ) -> None:
        """Execute run that doesn't exist."""
        from apps.api.services.assistants.run_executor import RunExecutor

        mock_run_service.start_run = AsyncMock(return_value=None)

        executor = RunExecutor(
            run_service=mock_run_service,
            message_service=mock_message_service,
            assistant_service=mock_assistant_service,
            thread_service=mock_thread_service,
        )

        result = await executor.execute_run(
            thread_id="thread_abc123",
            run_id="run_nonexistent",
        )

        assert result is None


class TestRunExecutorToolOutputs:
    """Tests for submitting tool outputs."""

    @pytest.mark.anyio
    async def test_submit_tool_outputs(
        self,
        mock_run_service: AsyncMock,
        mock_message_service: AsyncMock,
        mock_assistant_service: AsyncMock,
        mock_thread_service: AsyncMock,
    ) -> None:
        """Submit tool outputs and continue execution."""
        from apps.api.services.assistants.run_executor import (
            ExecutionResult,
            RunExecutor,
        )
        from apps.api.services.assistants.run_service import Run

        # Setup mock run in requires_action state
        mock_run = MagicMock(spec=Run)
        mock_run.id = "run_abc123"
        mock_run.thread_id = "thread_abc123"
        mock_run.assistant_id = "asst_abc123"
        mock_run.model = "gpt-4"
        mock_run.status = "requires_action"
        mock_run.required_action = {
            "type": "submit_tool_outputs",
            "submit_tool_outputs": {
                "tool_calls": [
                    {
                        "id": "call_abc123",
                        "type": "function",
                        "function": {"name": "get_weather", "arguments": "{}"},
                    }
                ]
            },
        }

        mock_run_service.submit_tool_outputs = AsyncMock(return_value=mock_run)
        mock_run_service.complete_run = AsyncMock(return_value=mock_run)

        # Setup mock assistant
        mock_assistant = MagicMock()
        mock_assistant.model = "gpt-4"
        mock_assistant.instructions = None
        mock_assistant.tools = []
        mock_assistant_service.get_assistant = AsyncMock(return_value=mock_assistant)

        # Setup mock thread
        mock_thread = MagicMock()
        mock_thread.id = "thread_abc123"
        mock_thread_service.get_thread = AsyncMock(return_value=mock_thread)

        executor = RunExecutor(
            run_service=mock_run_service,
            message_service=mock_message_service,
            assistant_service=mock_assistant_service,
            thread_service=mock_thread_service,
        )

        tool_outputs: list[ToolOutput] = [
            {"tool_call_id": "call_abc123", "output": '{"temperature": 72}'}
        ]

        # Mock the SDK response after tool outputs
        with patch.object(executor, "_execute_with_sdk") as mock_execute:
            mock_execute.return_value = ExecutionResult(
                response_text="The weather in NYC is 72°F.",
                tool_calls=[],
                usage={
                    "prompt_tokens": 20,
                    "completion_tokens": 10,
                    "total_tokens": 30,
                },
            )

            result = await executor.submit_tool_outputs(
                thread_id="thread_abc123",
                run_id="run_abc123",
                tool_outputs=tool_outputs,
            )

        assert result is not None
        assert result.response_text == "The weather in NYC is 72°F."

        # Verify tool outputs were submitted
        mock_run_service.submit_tool_outputs.assert_called_once()


class TestRunExecutorStreaming:
    """Tests for streaming execution."""

    @pytest.mark.anyio
    async def test_stream_run(
        self,
        mock_run_service: AsyncMock,
        mock_message_service: AsyncMock,
        mock_assistant_service: AsyncMock,
        mock_thread_service: AsyncMock,
    ) -> None:
        """Stream run execution."""
        from apps.api.services.assistants.run_executor import RunExecutor
        from apps.api.services.assistants.run_service import Run

        # Setup mock run
        mock_run = MagicMock(spec=Run)
        mock_run.id = "run_abc123"
        mock_run.thread_id = "thread_abc123"
        mock_run.assistant_id = "asst_abc123"
        mock_run.model = "gpt-4"
        mock_run.status = "queued"

        mock_run_service.start_run = AsyncMock(return_value=mock_run)
        mock_run_service.complete_run = AsyncMock(return_value=mock_run)

        # Setup mock assistant
        mock_assistant = MagicMock()
        mock_assistant.model = "gpt-4"
        mock_assistant.instructions = None
        mock_assistant.tools = []
        mock_assistant_service.get_assistant = AsyncMock(return_value=mock_assistant)

        # Setup mock thread
        mock_thread = MagicMock()
        mock_thread.id = "thread_abc123"
        mock_thread_service.get_thread = AsyncMock(return_value=mock_thread)

        # Setup mock message
        mock_message = MagicMock()
        mock_message.id = "msg_abc123"
        mock_message_service.create_message = AsyncMock(return_value=mock_message)

        executor = RunExecutor(
            run_service=mock_run_service,
            message_service=mock_message_service,
            assistant_service=mock_assistant_service,
            thread_service=mock_thread_service,
        )

        # Mock streaming response
        async def mock_stream() -> AsyncIterator[dict[str, Any]]:
            yield {"type": "run.created", "run_id": "run_abc123"}
            yield {"type": "run.in_progress", "run_id": "run_abc123"}
            yield {"type": "message.delta", "delta": {"content": "Hello"}}
            yield {"type": "message.delta", "delta": {"content": " World"}}
            yield {"type": "run.completed", "run_id": "run_abc123"}

        with patch.object(executor, "_stream_with_sdk") as mock_stream_sdk:
            mock_stream_sdk.return_value = mock_stream()

            events = []
            async for event in executor.stream_run(
                thread_id="thread_abc123",
                run_id="run_abc123",
            ):
                events.append(event)

        assert len(events) == 5
        assert events[0]["type"] == "run.created"
        assert events[-1]["type"] == "run.completed"


class TestRunExecutorMessages:
    """Tests for message creation during execution."""

    @pytest.mark.anyio
    async def test_creates_assistant_message(
        self,
        mock_run_service: AsyncMock,
        mock_message_service: AsyncMock,
        mock_assistant_service: AsyncMock,
        mock_thread_service: AsyncMock,
    ) -> None:
        """Creates assistant message after successful execution."""
        from apps.api.services.assistants.run_executor import (
            ExecutionResult,
            RunExecutor,
        )
        from apps.api.services.assistants.run_service import Run

        # Setup mock run
        mock_run = MagicMock(spec=Run)
        mock_run.id = "run_abc123"
        mock_run.thread_id = "thread_abc123"
        mock_run.assistant_id = "asst_abc123"
        mock_run.model = "gpt-4"
        mock_run.status = "queued"

        mock_run_service.start_run = AsyncMock(return_value=mock_run)
        mock_run_service.complete_run = AsyncMock(return_value=mock_run)

        # Setup mock assistant
        mock_assistant = MagicMock()
        mock_assistant.id = "asst_abc123"
        mock_assistant.model = "gpt-4"
        mock_assistant.instructions = None
        mock_assistant.tools = []
        mock_assistant_service.get_assistant = AsyncMock(return_value=mock_assistant)

        # Setup mock thread
        mock_thread = MagicMock()
        mock_thread.id = "thread_abc123"
        mock_thread_service.get_thread = AsyncMock(return_value=mock_thread)

        # Setup mock message
        mock_message = MagicMock()
        mock_message.id = "msg_response"
        mock_message_service.create_message = AsyncMock(return_value=mock_message)

        executor = RunExecutor(
            run_service=mock_run_service,
            message_service=mock_message_service,
            assistant_service=mock_assistant_service,
            thread_service=mock_thread_service,
        )

        # Mock the SDK response
        with patch.object(executor, "_execute_with_sdk") as mock_execute:
            mock_execute.return_value = ExecutionResult(
                response_text="Hello! How can I help you?",
                tool_calls=[],
                usage={
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
            )

            await executor.execute_run(
                thread_id="thread_abc123",
                run_id="run_abc123",
            )

        # Verify assistant message was created
        mock_message_service.create_message.assert_called_once()
        call_kwargs = mock_message_service.create_message.call_args[1]
        assert call_kwargs["role"] == "assistant"
        assert call_kwargs["content"] == "Hello! How can I help you?"
        assert call_kwargs["assistant_id"] == "asst_abc123"
        assert call_kwargs["run_id"] == "run_abc123"


class TestRunExecutorGetMessages:
    """Tests for getting thread messages for context."""

    @pytest.mark.anyio
    async def test_gets_thread_messages(
        self,
        mock_run_service: AsyncMock,
        mock_message_service: AsyncMock,
        mock_assistant_service: AsyncMock,
        mock_thread_service: AsyncMock,
    ) -> None:
        """Gets thread messages for context."""
        from apps.api.services.assistants.message_service import (
            Message,
            MessageListResult,
        )
        from apps.api.services.assistants.run_executor import RunExecutor

        # Setup mock messages in thread
        mock_messages = [
            MagicMock(spec=Message),
            MagicMock(spec=Message),
        ]
        mock_messages[0].role = "user"
        mock_messages[0].content = [
            {"type": "text", "text": {"value": "Hello", "annotations": []}}
        ]
        mock_messages[1].role = "assistant"
        mock_messages[1].content = [
            {"type": "text", "text": {"value": "Hi there!", "annotations": []}}
        ]

        mock_message_service.list_messages = AsyncMock(
            return_value=MessageListResult(
                data=mock_messages,
                first_id="msg_1",
                last_id="msg_2",
                has_more=False,
            )
        )

        executor = RunExecutor(
            run_service=mock_run_service,
            message_service=mock_message_service,
            assistant_service=mock_assistant_service,
            thread_service=mock_thread_service,
        )

        messages = await executor._get_thread_messages("thread_abc123")

        assert len(messages) == 2
        mock_message_service.list_messages.assert_called_once_with(
            "thread_abc123",
            limit=100,
            order="asc",
        )
