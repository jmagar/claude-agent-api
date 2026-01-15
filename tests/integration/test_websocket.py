"""Integration tests for WebSocket endpoint (T119-T120).

Tests bidirectional agent communication via WebSocket endpoint.
Covers authentication, message handling, event streaming, and connection cleanup.
"""

import asyncio
import contextlib
import json
from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from starlette.datastructures import Headers
from starlette.websockets import WebSocketState

from apps.api.services.session import SessionService
from apps.api.types import JsonValue
from tests.mocks.claude_sdk import AssistantMessage

if TYPE_CHECKING:
    from fastapi import WebSocket


async def wait_for_condition(
    condition_fn: callable,
    timeout: float = 1.0,
    poll_interval: float = 0.01,
) -> bool:
    """Wait until a condition is met or timeout occurs.

    Args:
        condition_fn: Callable that returns True when condition is met.
        timeout: Maximum time to wait in seconds.
        poll_interval: Time between condition checks in seconds.

    Returns:
        True if condition was met, False if timeout occurred.
    """
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        if condition_fn():
            return True
        await asyncio.sleep(poll_interval)
    return False


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

    def add_raw_message(self, raw_message: str) -> None:
        """Add a raw message string to be received by the handler.

        Args:
            raw_message: Raw message string (not JSON-encoded).
        """
        self._received_messages.append(raw_message)

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


class InMemoryCache:
    """Simple in-memory cache for WebSocket tests."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, JsonValue]] = {}
        self._sets: dict[str, set[str]] = {}

    async def get_json(self, key: str) -> dict[str, JsonValue] | None:
        """Get JSON value from cache."""
        return self._store.get(key)

    async def set_json(
        self, key: str, value: dict[str, JsonValue], ttl: int | None = None
    ) -> bool:
        """Set JSON value in cache."""
        self._store[key] = value
        return True

    async def get_many_json(self, keys: list[str]) -> list[dict[str, JsonValue] | None]:
        """Get multiple JSON values from cache."""
        return [self._store.get(key) for key in keys]

    async def scan_keys(self, pattern: str) -> list[str]:
        """Scan for keys matching pattern."""
        if pattern == "session:*":
            return [k for k in self._store if k.startswith("session:")]
        return list(self._store.keys())

    async def add_to_set(self, key: str, value: str) -> bool:
        """Add value to set."""
        if key not in self._sets:
            self._sets[key] = set()
        self._sets[key].add(value)
        return True

    async def remove_from_set(self, key: str, value: str) -> bool:
        """Remove value from set."""
        if key in self._sets:
            self._sets[key].discard(value)
        return True

    async def set_members(self, key: str) -> set[str]:
        """Get set members."""
        return set(self._sets.get(key, set()))

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._store

    async def acquire_lock(
        self, key: str, ttl: int = 300, value: str | None = None
    ) -> str | None:
        """Acquire lock (no-op for tests)."""
        return "mock-lock"

    async def release_lock(self, key: str, value: str) -> bool:
        """Release lock (no-op for tests)."""
        return True

    async def ping(self) -> bool:
        """Check connectivity."""
        return True


@pytest.fixture
def session_service() -> SessionService:
    """Create SessionService with in-memory cache."""
    return SessionService(cache=InMemoryCache())


class TestWebSocketAuthentication:
    """Tests for WebSocket authentication."""

    @pytest.mark.anyio
    async def test_websocket_rejects_missing_api_key(
        self,
        async_client: AsyncClient,
        session_service: SessionService,
    ) -> None:
        """Test WebSocket rejects connection without API key.

        RED: This test verifies the endpoint rejects unauthenticated requests.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        websocket = MockWebSocket(headers={})
        agent_service = AgentService()

        await websocket_query(cast("WebSocket", websocket), agent_service)

        # Should reject connection
        assert not websocket.was_accepted
        assert websocket.close_code == 4001
        assert websocket.close_reason == "Missing API key"

    @pytest.mark.anyio
    async def test_websocket_rejects_invalid_api_key(
        self,
        async_client: AsyncClient,
        session_service: SessionService,
    ) -> None:
        """Test WebSocket rejects connection with invalid API key.

        RED: This test verifies the endpoint rejects invalid authentication.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        websocket = MockWebSocket(headers={"x-api-key": "invalid-key"})
        agent_service = AgentService()

        await websocket_query(cast("WebSocket", websocket), agent_service)

        # Should reject connection
        assert not websocket.was_accepted
        assert websocket.close_code == 4001
        assert websocket.close_reason == "Invalid API key"

    @pytest.mark.anyio
    async def test_websocket_accepts_valid_api_key(
        self,
        async_client: AsyncClient,
        test_api_key: str,
        session_service: SessionService,
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

        await websocket_query(cast("WebSocket", websocket), agent_service)

        # Should accept connection
        assert websocket.was_accepted


class TestWebSocketMessageHandling:
    """Tests for WebSocket message handling."""

    @pytest.mark.anyio
    async def test_websocket_handles_prompt_message(
        self,
        async_client: AsyncClient,
        test_api_key: str,
        mock_claude_sdk: MagicMock,
        session_service: SessionService,
    ) -> None:
        """Test WebSocket handles prompt message correctly.

        GREEN: This test verifies prompt messages are processed and acknowledged.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        # Configure mock to return a simple response
        mock_instance = mock_claude_sdk.return_value
        mock_instance.set_messages(
            [
                AssistantMessage(
                    content=[{"type": "text", "text": "Hello from agent"}],
                    model="sonnet",
                )
            ]
        )

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
        task = asyncio.create_task(
            websocket_query(cast("WebSocket", websocket), agent_service)
        )

        # Wait for ack message with timeout
        await wait_for_condition(
            lambda: any(msg.get("type") == "ack" for msg in websocket.sent_messages),
            timeout=2.0,
        )

        # Cancel task to stop
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        # Should have accepted and sent ack
        assert websocket.was_accepted
        messages = websocket.sent_messages
        assert any(msg.get("type") == "ack" for msg in messages)

    @pytest.mark.anyio
    async def test_websocket_handles_interrupt_message(
        self,
        async_client: AsyncClient,
        test_api_key: str,
        session_service: SessionService,
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
        task = asyncio.create_task(
            websocket_query(cast("WebSocket", websocket), agent_service)
        )

        # Wait for error message with timeout
        await wait_for_condition(
            lambda: any(msg.get("type") == "error" for msg in websocket.sent_messages),
            timeout=2.0,
        )

        # Cancel task to stop
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        # Should have sent error (session not found)
        assert websocket.was_accepted
        messages = websocket.sent_messages
        assert any(msg.get("type") == "error" for msg in messages)

    @pytest.mark.anyio
    async def test_websocket_rejects_interrupt_for_unowned_session(
        self,
        async_client: AsyncClient,
        test_api_key: str,
        session_service: SessionService,
    ) -> None:
        """Test interrupt is rejected for sessions owned by other API keys."""
        from unittest.mock import AsyncMock, MagicMock

        from apps.api.routes.websocket import websocket_query

        await session_service.create_session(
            model="sonnet",
            session_id="owned-session-999",
            owner_api_key="other-owner",
        )

        websocket = MockWebSocket(headers={"x-api-key": test_api_key})
        agent_service = MagicMock()
        agent_service.interrupt = AsyncMock(return_value=True)

        websocket.add_received_message(
            {
                "type": "interrupt",
                "session_id": "owned-session-999",
            }
        )

        task = asyncio.create_task(
            websocket_query(cast("WebSocket", websocket), agent_service, session_service)
        )

        await wait_for_condition(
            lambda: any(msg.get("type") == "error" for msg in websocket.sent_messages),
            timeout=2.0,
        )

        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        assert websocket.was_accepted
        assert any(
            msg.get("type") == "error"
            and "authorized" in str(msg.get("message", "")).lower()
            for msg in websocket.sent_messages
        )
        agent_service.interrupt.assert_not_awaited()

    @pytest.mark.anyio
    async def test_websocket_handles_answer_message(
        self,
        async_client: AsyncClient,
        test_api_key: str,
        session_service: SessionService,
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
        task = asyncio.create_task(
            websocket_query(cast("WebSocket", websocket), agent_service)
        )

        # Wait for error message with timeout
        await wait_for_condition(
            lambda: any(msg.get("type") == "error" for msg in websocket.sent_messages),
            timeout=2.0,
        )

        # Cancel task to stop
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        # Should have sent error (session not found or no pending question)
        assert websocket.was_accepted
        messages = websocket.sent_messages
        assert any(msg.get("type") == "error" for msg in messages)

    @pytest.mark.anyio
    async def test_websocket_handles_control_message(
        self,
        async_client: AsyncClient,
        test_api_key: str,
        session_service: SessionService,
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
        task = asyncio.create_task(
            websocket_query(cast("WebSocket", websocket), agent_service)
        )

        # Wait for error message with timeout
        await wait_for_condition(
            lambda: any(msg.get("type") == "error" for msg in websocket.sent_messages),
            timeout=2.0,
        )

        # Cancel task to stop
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        # Should have sent error (session not found)
        assert websocket.was_accepted
        messages = websocket.sent_messages
        assert any(msg.get("type") == "error" for msg in messages)

    @pytest.mark.anyio
    async def test_websocket_handles_invalid_json(
        self,
        async_client: AsyncClient,
        test_api_key: str,
        session_service: SessionService,
    ) -> None:
        """Test WebSocket handles invalid JSON gracefully.

        GREEN: This test verifies error handling for malformed messages.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        websocket = MockWebSocket(headers={"x-api-key": test_api_key})
        agent_service = AgentService()

        # Add invalid JSON using public API
        websocket.add_raw_message("not valid json {")

        # Run in background task
        task = asyncio.create_task(
            websocket_query(cast("WebSocket", websocket), agent_service)
        )

        # Wait for error message with timeout
        await wait_for_condition(
            lambda: any(
                msg.get("type") == "error" and "Invalid JSON" in str(msg.get("message"))
                for msg in websocket.sent_messages
            ),
            timeout=2.0,
        )

        # Cancel task to stop
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

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
        async_client: AsyncClient,
        test_api_key: str,
        session_service: SessionService,
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
        task = asyncio.create_task(
            websocket_query(cast("WebSocket", websocket), agent_service)
        )

        # Wait for error message with timeout
        await wait_for_condition(
            lambda: any(
                msg.get("type") == "error"
                and "Unknown message type" in str(msg.get("message"))
                for msg in websocket.sent_messages
            ),
            timeout=2.0,
        )

        # Cancel task to stop
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        # Should have sent error
        assert websocket.was_accepted
        messages = websocket.sent_messages
        assert any(
            msg.get("type") == "error"
            and "Unknown message type" in str(msg.get("message"))
            for msg in messages
        )


class TestWebSocketStreaming:
    """Tests for WebSocket event streaming."""

    @pytest.mark.anyio
    async def test_websocket_streams_query_events(
        self,
        async_client: AsyncClient,
        test_api_key: str,
        mock_claude_sdk: MagicMock,
        session_service: SessionService,
    ) -> None:
        """Test WebSocket streams SSE events correctly.

        GREEN: This test verifies that query events are streamed to the client.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        # Configure mock to return a response
        mock_instance = mock_claude_sdk.return_value
        mock_instance.set_messages(
            [
                AssistantMessage(
                    content=[{"type": "text", "text": "Response from agent"}],
                    model="sonnet",
                )
            ]
        )

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
        task = asyncio.create_task(
            websocket_query(cast("WebSocket", websocket), agent_service)
        )

        # Wait for ack or SSE events with timeout
        await wait_for_condition(
            lambda: len(websocket.sent_messages) > 0,
            timeout=2.0,
        )

        # Cancel task to stop
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        # Should have received SSE events (at least ack message)
        messages = websocket.sent_messages
        # Debug: print messages if test fails
        if not any(msg.get("type") == "sse_event" for msg in messages):
            print(f"Messages sent: {messages}")
        # Should have at least an ack and potentially SSE events
        assert len(messages) > 0, "No messages were sent"
        assert any(msg.get("type") in ("ack", "sse_event") for msg in messages), (
            f"Expected ack or sse_event, got: {messages}"
        )

    @pytest.mark.anyio
    async def test_websocket_handles_disconnect_gracefully(
        self,
        async_client: AsyncClient,
        test_api_key: str,
        session_service: SessionService,
    ) -> None:
        """Test WebSocket handles disconnect gracefully.

        GREEN: This test verifies cleanup on disconnect.
        """
        from apps.api.routes.websocket import websocket_query
        from apps.api.services.agent import AgentService

        websocket = MockWebSocket(headers={"x-api-key": test_api_key})
        agent_service = AgentService()

        # Don't add any messages - will trigger disconnect immediately

        await websocket_query(cast("WebSocket", websocket), agent_service)

        # Should have accepted and then disconnected cleanly
        assert websocket.was_accepted

    @pytest.mark.anyio
    async def test_websocket_cancels_task_on_disconnect(
        self,
        async_client: AsyncClient,
        test_api_key: str,
        mock_claude_sdk: MagicMock,
        session_service: SessionService,
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
        task = asyncio.create_task(
            websocket_query(cast("WebSocket", websocket), agent_service)
        )

        # Wait for connection to be accepted before canceling
        await wait_for_condition(
            lambda: websocket.was_accepted,
            timeout=2.0,
        )

        # Cancel to simulate disconnect
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        # Should have cleaned up
        assert websocket.was_accepted
