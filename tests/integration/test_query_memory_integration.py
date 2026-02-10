"""Integration tests for query memory integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.api.schemas.requests.query import QueryRequest
from apps.api.services.agent.handlers import MessageHandler
from apps.api.services.agent.query_executor import QueryExecutor
from apps.api.services.agent.types import StreamContext
from apps.api.services.memory import MemoryService
from apps.api.utils.crypto import hash_api_key


@pytest.fixture
def mock_memory_service() -> AsyncMock:
    """Create mock memory service."""
    mock = AsyncMock(spec=MemoryService)
    mock.format_memory_context.return_value = (
        "RELEVANT MEMORIES:\n- User prefers technical explanations"
    )
    mock.add_memory.return_value = [{"id": "mem_123"}]
    return mock


@pytest.mark.anyio
async def test_query_executor_injects_memory_context(
    mock_memory_service: AsyncMock,
) -> None:
    """QueryExecutor should inject relevant memories into system prompt."""
    # Create a mock CommandsService
    mock_commands_service = MagicMock()
    mock_commands_service.parse_command.return_value = None

    # Mock the SDK client
    mock_client_instance = AsyncMock()
    mock_client_instance.query = AsyncMock()

    async def mock_receive():
        return
        yield  # Make it an async generator

    mock_client_instance.receive_response = mock_receive
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)

    with patch("claude_agent_sdk.ClaudeSDKClient", return_value=mock_client_instance):
        # Create QueryExecutor with MessageHandler
        message_handler = MessageHandler()
        executor = QueryExecutor(message_handler=message_handler)

        # Create a simple request
        request = QueryRequest(prompt="What do you know about me?")
        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )

        # Execute query with memory service and API key passed as parameters
        events = []
        async for event in executor.execute(
            request,
            ctx,
            mock_commands_service,
            memory_service=mock_memory_service,
            api_key="test-key",
        ):
            events.append(event)

        # Verify memory context was retrieved with hashed API key
        mock_memory_service.format_memory_context.assert_called_once_with(
            query="What do you know about me?",
            user_id=hash_api_key("test-key"),
        )

        # Verify SDK was called (query method should be called)
        mock_client_instance.query.assert_called_once()


@pytest.mark.anyio
async def test_query_executor_extracts_memories_after_response(
    mock_memory_service: AsyncMock,
) -> None:
    """QueryExecutor should extract and store memories after response."""
    # Create a mock response message
    mock_message = MagicMock()
    mock_message.type = "assistant"
    mock_message.content = [
        MagicMock(type="text", text="I understand you prefer technical explanations.")
    ]

    # Create a mock CommandsService
    mock_commands_service = MagicMock()
    mock_commands_service.parse_command.return_value = None

    # Mock the SDK client
    mock_client_instance = AsyncMock()
    mock_client_instance.query = AsyncMock()

    # Simulate a single message response
    async def mock_receive():
        yield mock_message

    mock_client_instance.receive_response = mock_receive
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)

    with patch("claude_agent_sdk.ClaudeSDKClient", return_value=mock_client_instance):
        # Create QueryExecutor with MessageHandler
        message_handler = MessageHandler()
        executor = QueryExecutor(message_handler=message_handler)

        # Create a simple request
        request = QueryRequest(prompt="What do you know about me?")
        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )

        # Execute query with memory service and API key passed as parameters
        events = []
        async for event in executor.execute(
            request,
            ctx,
            mock_commands_service,
            memory_service=mock_memory_service,
            api_key="test-key",
        ):
            events.append(event)

        # Verify memory was stored with conversation
        mock_memory_service.add_memory.assert_called_once()
        call_args = mock_memory_service.add_memory.call_args

        # Check that conversation includes both user prompt and assistant response
        messages = call_args.kwargs["messages"]
        assert "What do you know about me?" in messages
        assert "I understand you prefer technical explanations." in messages
        # Verify API key is hashed before passing to memory service
        assert call_args.kwargs["user_id"] == hash_api_key("test-key")


@pytest.mark.anyio
async def test_query_executor_handles_no_memories_found() -> None:
    """QueryExecutor should handle case when no memories are found."""
    # Mock memory service that returns no memories
    mock_memory_service = AsyncMock(spec=MemoryService)
    mock_memory_service.format_memory_context.return_value = ""
    mock_memory_service.add_memory.return_value = []

    # Create a mock CommandsService
    mock_commands_service = MagicMock()
    mock_commands_service.parse_command.return_value = None

    # Mock the SDK client
    mock_client_instance = AsyncMock()
    mock_client_instance.query = AsyncMock()

    async def mock_receive():
        return
        yield  # Make it an async generator

    mock_client_instance.receive_response = mock_receive
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)

    with patch("claude_agent_sdk.ClaudeSDKClient", return_value=mock_client_instance):
        # Create QueryExecutor with MessageHandler
        message_handler = MessageHandler()
        executor = QueryExecutor(message_handler=message_handler)

        # Create a simple request with existing system_prompt
        request = QueryRequest(
            prompt="Hello", system_prompt="You are a helpful assistant."
        )
        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )

        # Execute query with memory service and API key passed as parameters
        events = []
        async for event in executor.execute(
            request,
            ctx,
            mock_commands_service,
            memory_service=mock_memory_service,
            api_key="test-key",
        ):
            events.append(event)

        # Verify memory context was attempted
        mock_memory_service.format_memory_context.assert_called_once()

        # Memory should still be added even if none found
        mock_memory_service.add_memory.assert_called_once()
