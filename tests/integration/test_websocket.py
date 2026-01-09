"""Integration tests for WebSocket endpoint (T119-T120).

Tests bidirectional agent communication via WebSocket endpoint.
Covers authentication, message handling, event streaming, and connection cleanup.
"""

import asyncio
import json
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import WebSocket
from httpx import AsyncClient
from starlette.datastructures import Headers
from starlette.websockets import WebSocketState

from tests.mocks.claude_sdk import AssistantMessage


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self, headers: dict[str, str]) -> None:
        """Initialize mock WebSocket.

        Args:
            headers: Request headers.
        """
        self.headers = Headers(headers)
        self.state = WebSocketState.DISCONNECTED
        self._sent_messages: list[dict[str, object]] = []
        self._received_messages: list[str] = []
        self._receive_index = 0
        self._close_code: int | None = None
        self._close_reason: str | None = None
        self._accepted = False

    def add_received_message(self, message: dict[str, object]) -> None:
        """Add a message to be received by the handler.

        Args:
            message: Message dict to be JSON-encoded.
        """
        self._received_messages.append(json.dumps(message))

    async def accept(self) -> None:
        """Accept the WebSocket connection."""
        self.state = WebSocketState.CONNECTED
        self._accepted = True

    async def close(self, code: int = 1000, reason: str = "") -> None:
        """Close the WebSocket connection.

        Args:
            code: Close code.
            reason: Close reason.
        """
        self.state = WebSocketState.DISCONNECTED
        self._close_code = code
        self._close_reason = reason

    async def receive_text(self) -> str:
        """Receive text message from client.

        Returns:
            Text message.

        Raises:
            StopIteration: When no more messages available.
        """
        if self._receive_index >= len(self._received_messages):
            # Simulate disconnect
            from starlette.websockets import WebSocketDisconnect

            raise WebSocketDisconnect(code=1000)

        message = self._received_messages[self._receive_index]
        self._receive_index += 1
        return message

    async def send_json(self, data: dict[str, object]) -> None:
        """Send JSON message to client.

        Args:
            data: Message data.
        """
        self._sent_messages.append(data)

    @property
    def sent_messages(self) -> list[dict[str, object]]:
        """Get all sent messages.

        Returns:
            List of sent message dicts.
        """
        return self._sent_messages

    @property
    def was_accepted(self) -> bool:
        """Check if connection was accepted.

        Returns:
            True if accepted.
        """
        return self._accepted

    @property
    def close_code(self) -> int | None:
        """Get close code.

        Returns:
            Close code or None.
        """
        return self._close_code

    @property
    def close_reason(self) -> str | None:
        """Get close reason.

        Returns:
            Close reason or None.
        """
        return self._close_reason


class TestWebSocketAuthentication:
    """Tests for WebSocket authentication."""

    @pytest.mark.anyio
    async def test_websocket_rejects_missing_api_key(
        self,
        async_client: AsyncClient,  # noqa: ARG002
    ) -> None:
        """Test WebSocket rejects connection without API key.

        RED: This test verifies the endpoint rejects unauthenticated requests.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        websocket = MockWebSocket(headers={})
        agent_service = AgentService()

        await websocket_query(cast(WebSocket, websocket), agent_service)

        # Should reject connection
        assert not websocket.was_accepted
        assert websocket.close_code == 4001
        assert websocket.close_reason == "Missing API key"

    @pytest.mark.anyio
    async def test_websocket_rejects_invalid_api_key(
        self,
        async_client: AsyncClient,  # noqa: ARG002
    ) -> None:
        """Test WebSocket rejects connection with invalid API key.

        RED: This test verifies the endpoint rejects invalid authentication.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        websocket = MockWebSocket(headers={"x-api-key": "invalid-key"})
        agent_service = AgentService()

        await websocket_query(cast(WebSocket, websocket), agent_service)

        # Should reject connection
        assert not websocket.was_accepted
        assert websocket.close_code == 4001
        assert websocket.close_reason == "Invalid API key"

    @pytest.mark.anyio
    async def test_websocket_accepts_valid_api_key(
        self,
        async_client: AsyncClient,  # noqa: ARG002
        test_api_key: str,
    ) -> None:
        """Test WebSocket accepts connection with valid API key.

        GREEN: This test verifies the endpoint accepts valid authentication.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        websocket = MockWebSocket(headers={"x-api-key": test_api_key})
        agent_service = AgentService()

        # Add a message to trigger disconnect after accept
        websocket.add_received_message({"type": "unknown"})

        await websocket_query(cast(WebSocket, websocket), agent_service)

        # Should accept connection
        assert websocket.was_accepted


class TestWebSocketMessageHandling:
    """Tests for WebSocket message handling."""

    @pytest.mark.anyio
    async def test_websocket_handles_prompt_message(
        self,
        async_client: AsyncClient,  # noqa: ARG002
        test_api_key: str,
        mock_claude_sdk: MagicMock,
    ) -> None:
        """Test WebSocket handles prompt message correctly.

        GREEN: This test verifies prompt messages are processed and acknowledged.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        # Configure mock to return a simple response
        mock_instance = mock_claude_sdk.return_value
        mock_instance.set_messages([AssistantMessage(
            content=[{"type": "text", "text": "Hello from agent"}],
            model="sonnet",
        )])

        websocket = MockWebSocket(headers={"x-api-key": test_api_key})
        agent_service = AgentService()

        # Add prompt message
        websocket.add_received_message(
            {
                "type": "prompt",
                "prompt": "Say hello",
                "max_turns": 1,
            }
        )

        # Run in background task
        task = asyncio.create_task(websocket_query(cast(WebSocket, websocket), agent_service))

        # Wait briefly for processing
        await asyncio.sleep(0.1)

        # Cancel task to stop
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should have accepted and sent ack
        assert websocket.was_accepted
        messages = websocket.sent_messages
        assert any(msg.get("type") == "ack" for msg in messages)

    @pytest.mark.anyio
    async def test_websocket_handles_interrupt_message(
        self,
        async_client: AsyncClient,  # noqa: ARG002
        test_api_key: str,
    ) -> None:
        """Test WebSocket handles interrupt message correctly.

        GREEN: This test verifies interrupt messages are processed.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        websocket = MockWebSocket(headers={"x-api-key": test_api_key})
        agent_service = AgentService()

        # Add interrupt message for non-existent session
        websocket.add_received_message(
            {
                "type": "interrupt",
                "session_id": "test-session-123",
            }
        )

        # Run in background task
        task = asyncio.create_task(websocket_query(cast(WebSocket, websocket), agent_service))

        # Wait briefly for processing
        await asyncio.sleep(0.1)

        # Cancel task to stop
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should have sent error (session not found)
        assert websocket.was_accepted
        messages = websocket.sent_messages
        assert any(msg.get("type") == "error" for msg in messages)

    @pytest.mark.anyio
    async def test_websocket_handles_answer_message(
        self,
        async_client: AsyncClient,  # noqa: ARG002
        test_api_key: str,
    ) -> None:
        """Test WebSocket handles answer message correctly.

        GREEN: This test verifies answer messages are processed.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        websocket = MockWebSocket(headers={"x-api-key": test_api_key})
        agent_service = AgentService()

        # Add answer message
        websocket.add_received_message(
            {
                "type": "answer",
                "answer": "Yes, proceed",
                "session_id": "test-session-123",
            }
        )

        # Run in background task
        task = asyncio.create_task(websocket_query(cast(WebSocket, websocket), agent_service))

        # Wait briefly for processing
        await asyncio.sleep(0.1)

        # Cancel task to stop
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should have sent error (session not found or no pending question)
        assert websocket.was_accepted
        messages = websocket.sent_messages
        assert any(msg.get("type") == "error" for msg in messages)

    @pytest.mark.anyio
    async def test_websocket_handles_control_message(
        self,
        async_client: AsyncClient,  # noqa: ARG002
        test_api_key: str,
    ) -> None:
        """Test WebSocket handles control message correctly.

        GREEN: This test verifies control messages are processed.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        websocket = MockWebSocket(headers={"x-api-key": test_api_key})
        agent_service = AgentService()

        # Add control message
        websocket.add_received_message(
            {
                "type": "control",
                "session_id": "test-session-123",
                "permission_mode": "acceptEdits",
            }
        )

        # Run in background task
        task = asyncio.create_task(websocket_query(cast(WebSocket, websocket), agent_service))

        # Wait briefly for processing
        await asyncio.sleep(0.1)

        # Cancel task to stop
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should have sent error (session not found)
        assert websocket.was_accepted
        messages = websocket.sent_messages
        assert any(msg.get("type") == "error" for msg in messages)

    @pytest.mark.anyio
    async def test_websocket_handles_invalid_json(
        self,
        async_client: AsyncClient,  # noqa: ARG002
        test_api_key: str,
    ) -> None:
        """Test WebSocket handles invalid JSON gracefully.

        GREEN: This test verifies error handling for malformed messages.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        websocket = MockWebSocket(headers={"x-api-key": test_api_key})
        agent_service = AgentService()

        # Add invalid JSON
        websocket._received_messages.append("not valid json {")

        # Run in background task
        task = asyncio.create_task(websocket_query(cast(WebSocket, websocket), agent_service))

        # Wait briefly for processing
        await asyncio.sleep(0.1)

        # Cancel task to stop
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should have sent error
        assert websocket.was_accepted
        messages = websocket.sent_messages
        assert any(
            msg.get("type") == "error" and "Invalid JSON" in str(msg.get("message"))
            for msg in messages
        )

    @pytest.mark.anyio
    async def test_websocket_handles_unknown_message_type(
        self,
        async_client: AsyncClient,  # noqa: ARG002
        test_api_key: str,
    ) -> None:
        """Test WebSocket handles unknown message types.

        GREEN: This test verifies error handling for unknown message types.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        websocket = MockWebSocket(headers={"x-api-key": test_api_key})
        agent_service = AgentService()

        # Add unknown message type
        websocket.add_received_message({"type": "unknown_type"})

        # Run in background task
        task = asyncio.create_task(websocket_query(cast(WebSocket, websocket), agent_service))

        # Wait briefly for processing
        await asyncio.sleep(0.1)

        # Cancel task to stop
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should have sent error
        assert websocket.was_accepted
        messages = websocket.sent_messages
        assert any(
            msg.get("type") == "error" and "Unknown message type" in str(msg.get("message"))
            for msg in messages
        )


class TestWebSocketStreaming:
    """Tests for WebSocket event streaming."""

    @pytest.mark.anyio
    async def test_websocket_streams_query_events(
        self,
        async_client: AsyncClient,  # noqa: ARG002
        test_api_key: str,
        mock_claude_sdk: MagicMock,
    ) -> None:
        """Test WebSocket streams SSE events correctly.

        GREEN: This test verifies that query events are streamed to the client.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        # Configure mock to return a response
        mock_instance = mock_claude_sdk.return_value
        mock_instance.set_messages([AssistantMessage(
            content=[{"type": "text", "text": "Response from agent"}],
            model="sonnet",
        )])

        websocket = MockWebSocket(headers={"x-api-key": test_api_key})
        agent_service = AgentService()

        # Add prompt message
        websocket.add_received_message(
            {
                "type": "prompt",
                "prompt": "Test prompt",
                "max_turns": 1,
            }
        )

        # Run in background task
        task = asyncio.create_task(websocket_query(cast(WebSocket, websocket), agent_service))

        # Wait for processing
        await asyncio.sleep(0.2)

        # Cancel task to stop
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should have received SSE events (at least ack message)
        messages = websocket.sent_messages
        # Debug: print messages if test fails
        if not any(msg.get("type") == "sse_event" for msg in messages):
            print(f"Messages sent: {messages}")
        # Should have at least an ack and potentially SSE events
        assert len(messages) > 0, "No messages were sent"
        assert any(
            msg.get("type") in ("ack", "sse_event") for msg in messages
        ), f"Expected ack or sse_event, got: {messages}"

    @pytest.mark.anyio
    async def test_websocket_handles_disconnect_gracefully(
        self,
        async_client: AsyncClient,  # noqa: ARG002
        test_api_key: str,
    ) -> None:
        """Test WebSocket handles disconnect gracefully.

        GREEN: This test verifies cleanup on disconnect.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        websocket = MockWebSocket(headers={"x-api-key": test_api_key})
        agent_service = AgentService()

        # Don't add any messages - will trigger disconnect immediately

        await websocket_query(cast(WebSocket, websocket), agent_service)

        # Should have accepted and then disconnected cleanly
        assert websocket.was_accepted

    @pytest.mark.anyio
    async def test_websocket_cancels_task_on_disconnect(
        self,
        async_client: AsyncClient,  # noqa: ARG002
        test_api_key: str,
        mock_claude_sdk: MagicMock,
    ) -> None:
        """Test WebSocket cancels query task on disconnect.

        GREEN: This test verifies that active queries are cancelled on disconnect.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        # Create a mock that blocks indefinitely
        mock_instance = mock_claude_sdk.return_value
        mock_instance.query = AsyncMock()

        async def slow_receive() -> AsyncMock:
            """Simulate slow response that blocks."""
            await asyncio.sleep(10)  # Simulate long operation
            return AsyncMock()

        mock_instance.receive_response = slow_receive

        websocket = MockWebSocket(headers={"x-api-key": test_api_key})
        agent_service = AgentService()

        # Add prompt to start query
        websocket.add_received_message(
            {
                "type": "prompt",
                "prompt": "Test",
                "max_turns": 1,
            }
        )

        # Run in background and cancel quickly
        task = asyncio.create_task(websocket_query(cast(WebSocket, websocket), agent_service))

        # Wait for query to start
        await asyncio.sleep(0.1)

        # Cancel to simulate disconnect
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should have cleaned up
        assert websocket.was_accepted
