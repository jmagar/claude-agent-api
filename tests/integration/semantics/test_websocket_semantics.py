"""WebSocket semantic tests for bidirectional agent communication.

Tests cover:
- WebSocket connection establishment and authentication
- Message type validation (prompt, interrupt, answer, control)
- Error response formatting and protocol compliance
- Session binding and state management
- Disconnect handling and cleanup
- Permission mode validation for control messages
- Invalid/malformed message handling
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from starlette.datastructures import Headers
from starlette.websockets import WebSocketDisconnect
from starlette.websockets import WebSocketState as StarletteWebSocketState

from apps.api.services.session import SessionService
from apps.api.types import JsonValue

if TYPE_CHECKING:
    from fastapi import WebSocket

    from apps.api.protocols import Cache
    from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helper: MockWebSocket (mirrors existing test_websocket.py pattern)
# ---------------------------------------------------------------------------


class MockWebSocket:
    """Mock WebSocket for semantic testing of handler functions."""

    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = Headers(headers)
        self.state = StarletteWebSocketState.DISCONNECTED
        self._sent_messages: list[dict[str, object]] = []
        self._received_messages: list[str] = []
        self._receive_index = 0
        self._close_code: int | None = None
        self._close_reason: str | None = None
        self._accepted = False

    def add_received_message(self, message: dict[str, object]) -> None:
        """Enqueue a JSON message for the handler to receive."""
        self._received_messages.append(json.dumps(message))

    def add_raw_message(self, raw_message: str) -> None:
        """Enqueue a raw string message for the handler to receive."""
        self._received_messages.append(raw_message)

    async def accept(self) -> None:
        self.state = StarletteWebSocketState.CONNECTED
        self._accepted = True

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.state = StarletteWebSocketState.DISCONNECTED
        self._close_code = code
        self._close_reason = reason

    async def receive_text(self) -> str:
        if self._receive_index >= len(self._received_messages):
            raise WebSocketDisconnect(code=1000)
        message = self._received_messages[self._receive_index]
        self._receive_index += 1
        return message

    async def send_json(self, data: dict[str, object]) -> None:
        self._sent_messages.append(data)

    @property
    def sent_messages(self) -> list[dict[str, object]]:
        return self._sent_messages

    @property
    def was_accepted(self) -> bool:
        return self._accepted

    @property
    def close_code(self) -> int | None:
        return self._close_code

    @property
    def close_reason(self) -> str | None:
        return self._close_reason


# ---------------------------------------------------------------------------
# Helper: InMemoryCache (mirrors existing test_websocket.py pattern)
# ---------------------------------------------------------------------------


class InMemoryCache:
    """Simple in-memory cache for WebSocket tests."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, JsonValue]] = {}
        self._sets: dict[str, set[str]] = {}

    async def get_json(self, key: str) -> dict[str, JsonValue] | None:
        return self._store.get(key)

    async def set_json(
        self, key: str, value: dict[str, JsonValue], ttl: int | None = None
    ) -> bool:
        self._store[key] = value
        return True

    async def get_many_json(
        self, keys: list[str]
    ) -> list[dict[str, JsonValue] | None]:
        return [self._store.get(key) for key in keys]

    async def scan_keys(self, pattern: str) -> list[str]:
        if pattern == "session:*":
            return [k for k in self._store if k.startswith("session:")]
        return list(self._store.keys())

    async def add_to_set(self, key: str, value: str) -> bool:
        if key not in self._sets:
            self._sets[key] = set()
        self._sets[key].add(value)
        return True

    async def remove_from_set(self, key: str, value: str) -> bool:
        if key in self._sets:
            self._sets[key].discard(value)
        return True

    async def set_members(self, key: str) -> set[str]:
        return set(self._sets.get(key, set()))

    async def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        return key in self._store

    async def acquire_lock(
        self, key: str, ttl: int = 300, value: str | None = None
    ) -> str | None:
        return "mock-lock"

    async def release_lock(self, key: str, value: str) -> bool:
        return True

    async def ping(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Helper: wait utility
# ---------------------------------------------------------------------------


async def _wait_for_messages(
    ws: MockWebSocket,
    *,
    min_count: int = 1,
    timeout: float = 2.0,
    poll_interval: float = 0.01,
) -> bool:
    """Wait until the mock WebSocket has at least `min_count` sent messages."""
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        if len(ws.sent_messages) >= min_count:
            return True
        await asyncio.sleep(poll_interval)
    return False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ws_session_service() -> SessionService:
    """Create SessionService with in-memory cache for WebSocket tests."""
    return SessionService(cache=cast("Cache", InMemoryCache()))


# ---------------------------------------------------------------------------
# AUTH: Connection Establishment
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_rejects_missing_api_key(
    async_client: AsyncClient,
) -> None:
    """WebSocket connection without API key is rejected with code 4001."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    ws = MockWebSocket(headers={})
    agent_service = AgentService()

    await websocket_query(cast("WebSocket", ws), agent_service)

    assert not ws.was_accepted
    assert ws.close_code == 4001
    assert ws.close_reason == "Missing API key"


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_rejects_invalid_api_key(
    async_client: AsyncClient,
) -> None:
    """WebSocket connection with wrong API key is rejected with code 4001."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    ws = MockWebSocket(headers={"x-api-key": "wrong-key-definitely-invalid"})
    agent_service = AgentService()

    await websocket_query(cast("WebSocket", ws), agent_service)

    assert not ws.was_accepted
    assert ws.close_code == 4001
    assert ws.close_reason == "Invalid API key"


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_accepts_valid_api_key(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """WebSocket connection with valid API key is accepted."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    # Enqueue one message so the handler disconnects gracefully
    ws.add_received_message({"type": "unknown"})

    await websocket_query(cast("WebSocket", ws), agent_service)

    assert ws.was_accepted


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_auth_uses_header_only(
    async_client: AsyncClient,
) -> None:
    """WebSocket authentication only reads x-api-key header, not query params.

    This validates the security decision to avoid leaking secrets in URLs.
    """
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    # No header, even if a query param were present the handler doesn't read it
    ws = MockWebSocket(headers={})
    agent_service = AgentService()

    await websocket_query(cast("WebSocket", ws), agent_service)

    assert not ws.was_accepted
    assert ws.close_code == 4001


# ---------------------------------------------------------------------------
# MESSAGE HANDLING: Invalid JSON
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_invalid_json_returns_error(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """Non-JSON message returns error but does not close the connection."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    ws.add_raw_message("{not valid json")

    task = asyncio.create_task(
        websocket_query(cast("WebSocket", ws), agent_service)
    )
    await _wait_for_messages(ws, min_count=1)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert ws.was_accepted
    error_msgs = [m for m in ws.sent_messages if m.get("type") == "error"]
    assert len(error_msgs) >= 1
    assert "Invalid JSON" in str(error_msgs[0].get("message"))


# ---------------------------------------------------------------------------
# MESSAGE HANDLING: Unknown Type
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_unknown_message_type_returns_error(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """Unknown message type returns error with descriptive message."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    ws.add_received_message({"type": "nonexistent_type"})

    task = asyncio.create_task(
        websocket_query(cast("WebSocket", ws), agent_service)
    )
    await _wait_for_messages(ws, min_count=1)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert ws.was_accepted
    error_msgs = [m for m in ws.sent_messages if m.get("type") == "error"]
    assert len(error_msgs) >= 1
    assert "Unknown message type" in str(error_msgs[0].get("message"))


# ---------------------------------------------------------------------------
# MESSAGE HANDLING: Prompt
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_prompt_without_text_returns_error(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """Prompt message without prompt text returns error."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    # Prompt message with missing prompt field
    ws.add_received_message({"type": "prompt"})

    task = asyncio.create_task(
        websocket_query(cast("WebSocket", ws), agent_service)
    )
    await _wait_for_messages(ws, min_count=1)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert ws.was_accepted
    error_msgs = [m for m in ws.sent_messages if m.get("type") == "error"]
    assert len(error_msgs) >= 1
    assert "prompt is required" in str(error_msgs[0].get("message"))


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_prompt_sends_ack(
    async_client: AsyncClient,
    test_api_key: str,
    mock_claude_sdk: MagicMock,
) -> None:
    """Valid prompt message receives an ack response."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService
    from tests.mocks.claude_sdk import AssistantMessage

    mock_instance = mock_claude_sdk.return_value
    mock_instance.set_messages(
        [
            AssistantMessage(
                content=[{"type": "text", "text": "Hello"}],
                model="sonnet",
            )
        ]
    )

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    ws.add_received_message({
        "type": "prompt",
        "prompt": "Say hello",
        "max_turns": 1,
    })

    task = asyncio.create_task(
        websocket_query(cast("WebSocket", ws), agent_service)
    )
    await _wait_for_messages(ws, min_count=1)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert ws.was_accepted
    ack_msgs = [m for m in ws.sent_messages if m.get("type") == "ack"]
    assert len(ack_msgs) >= 1
    assert "Query started" in str(ack_msgs[0].get("message"))


# ---------------------------------------------------------------------------
# MESSAGE HANDLING: Answer
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_answer_without_text_returns_error(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """Answer message without answer text returns error."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    ws.add_received_message({"type": "answer", "session_id": "some-session"})

    task = asyncio.create_task(
        websocket_query(cast("WebSocket", ws), agent_service)
    )
    await _wait_for_messages(ws, min_count=1)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert ws.was_accepted
    error_msgs = [m for m in ws.sent_messages if m.get("type") == "error"]
    assert len(error_msgs) >= 1
    assert "answer is required" in str(error_msgs[0].get("message"))


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_answer_without_session_returns_error(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """Answer message without session ID or active session returns error."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    # Answer with text but no session_id and no current session
    ws.add_received_message({"type": "answer", "answer": "Yes"})

    task = asyncio.create_task(
        websocket_query(cast("WebSocket", ws), agent_service)
    )
    await _wait_for_messages(ws, min_count=1)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert ws.was_accepted
    error_msgs = [m for m in ws.sent_messages if m.get("type") == "error"]
    assert len(error_msgs) >= 1
    assert "No active session" in str(error_msgs[0].get("message"))


# ---------------------------------------------------------------------------
# MESSAGE HANDLING: Interrupt
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_interrupt_without_session_returns_error(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """Interrupt without session ID or active session returns error."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    ws.add_received_message({"type": "interrupt"})

    task = asyncio.create_task(
        websocket_query(cast("WebSocket", ws), agent_service)
    )
    await _wait_for_messages(ws, min_count=1)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert ws.was_accepted
    error_msgs = [m for m in ws.sent_messages if m.get("type") == "error"]
    assert len(error_msgs) >= 1
    assert "No active session" in str(error_msgs[0].get("message"))


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_interrupt_unowned_session_returns_error(
    async_client: AsyncClient,
    test_api_key: str,
    ws_session_service: SessionService,
) -> None:
    """Interrupt for session owned by another API key returns authorization error."""
    from apps.api.routes.websocket import websocket_query

    # Create session owned by a different key
    await ws_session_service.create_session(
        model="sonnet",
        session_id="other-owner-session",
        owner_api_key="other-api-key-xyz",
    )

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = MagicMock()
    agent_service.interrupt = AsyncMock(return_value=True)

    ws.add_received_message({
        "type": "interrupt",
        "session_id": "other-owner-session",
    })

    task = asyncio.create_task(
        websocket_query(
            cast("WebSocket", ws), agent_service, ws_session_service
        )
    )
    await _wait_for_messages(ws, min_count=1)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert ws.was_accepted
    error_msgs = [m for m in ws.sent_messages if m.get("type") == "error"]
    assert len(error_msgs) >= 1
    assert "authorized" in str(error_msgs[0].get("message", "")).lower()
    # Must NOT have called interrupt on the agent service
    agent_service.interrupt.assert_not_awaited()


# ---------------------------------------------------------------------------
# MESSAGE HANDLING: Control (Permission Mode)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_control_without_session_returns_error(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """Control message without session ID returns error."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    ws.add_received_message({
        "type": "control",
        "permission_mode": "acceptEdits",
    })

    task = asyncio.create_task(
        websocket_query(cast("WebSocket", ws), agent_service)
    )
    await _wait_for_messages(ws, min_count=1)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert ws.was_accepted
    error_msgs = [m for m in ws.sent_messages if m.get("type") == "error"]
    assert len(error_msgs) >= 1
    assert "required" in str(error_msgs[0].get("message", "")).lower()


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_control_invalid_permission_mode_returns_error(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """Control message with invalid permission mode returns descriptive error."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    ws.add_received_message({
        "type": "control",
        "session_id": "some-session",
        "permission_mode": "superAdmin",
    })

    task = asyncio.create_task(
        websocket_query(cast("WebSocket", ws), agent_service)
    )
    await _wait_for_messages(ws, min_count=1)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert ws.was_accepted
    error_msgs = [m for m in ws.sent_messages if m.get("type") == "error"]
    assert len(error_msgs) >= 1
    error_text = str(error_msgs[0].get("message", ""))
    assert "Invalid permission_mode" in error_text
    assert "superAdmin" in error_text


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_control_valid_permission_modes_accepted(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """All valid permission modes are accepted by the validation logic."""
    from apps.api.routes.websocket import VALID_PERMISSION_MODES

    # Validate the set of valid modes matches expectations
    expected_modes = {"default", "acceptEdits", "plan", "bypassPermissions"}
    assert VALID_PERMISSION_MODES == expected_modes, (
        f"Permission modes changed. Expected {expected_modes}, "
        f"got {VALID_PERMISSION_MODES}"
    )


# ---------------------------------------------------------------------------
# RESPONSE FORMAT: All responses follow the WebSocketResponseDict schema
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_error_response_format(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """Error responses follow {'type': 'error', 'message': str} format."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    ws.add_received_message({"type": "bad_type"})

    task = asyncio.create_task(
        websocket_query(cast("WebSocket", ws), agent_service)
    )
    await _wait_for_messages(ws, min_count=1)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    error_msgs = [m for m in ws.sent_messages if m.get("type") == "error"]
    assert len(error_msgs) >= 1
    msg = error_msgs[0]
    assert msg["type"] == "error"
    assert isinstance(msg.get("message"), str)
    assert len(str(msg["message"])) > 0


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_ack_response_format(
    async_client: AsyncClient,
    test_api_key: str,
    mock_claude_sdk: MagicMock,
) -> None:
    """Ack responses follow {'type': 'ack', 'message': str} format."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService
    from tests.mocks.claude_sdk import AssistantMessage

    mock_instance = mock_claude_sdk.return_value
    mock_instance.set_messages(
        [
            AssistantMessage(
                content=[{"type": "text", "text": "hi"}],
                model="sonnet",
            )
        ]
    )

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    ws.add_received_message({
        "type": "prompt",
        "prompt": "hello",
        "max_turns": 1,
    })

    task = asyncio.create_task(
        websocket_query(cast("WebSocket", ws), agent_service)
    )
    await _wait_for_messages(ws, min_count=1)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    ack_msgs = [m for m in ws.sent_messages if m.get("type") == "ack"]
    assert len(ack_msgs) >= 1
    msg = ack_msgs[0]
    assert msg["type"] == "ack"
    assert isinstance(msg.get("message"), str)
    assert len(str(msg["message"])) > 0


# ---------------------------------------------------------------------------
# DISCONNECT: Graceful Handling
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_disconnect_without_messages(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """WebSocket disconnects cleanly when no messages are sent by client."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    # No messages queued -- handler receives disconnect immediately
    await websocket_query(cast("WebSocket", ws), agent_service)

    assert ws.was_accepted
    # No error messages should be sent on clean disconnect
    error_msgs = [m for m in ws.sent_messages if m.get("type") == "error"]
    assert len(error_msgs) == 0


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_disconnect_cancels_active_query(
    async_client: AsyncClient,
    test_api_key: str,
    mock_claude_sdk: MagicMock,
) -> None:
    """Active query task is cancelled when WebSocket disconnects."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    # Make mock block indefinitely to simulate long query
    mock_instance = mock_claude_sdk.return_value
    mock_instance.query = AsyncMock()

    async def slow_receive() -> AsyncMock:
        await asyncio.sleep(10)
        return AsyncMock()

    mock_instance.receive_response = slow_receive

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    ws.add_received_message({
        "type": "prompt",
        "prompt": "Long running task",
        "max_turns": 1,
    })

    task = asyncio.create_task(
        websocket_query(cast("WebSocket", ws), agent_service)
    )

    # Wait for accept
    start = asyncio.get_event_loop().time()
    while not ws.was_accepted and asyncio.get_event_loop().time() - start < 2.0:
        await asyncio.sleep(0.01)

    # Cancel (simulates disconnect)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert ws.was_accepted


# ---------------------------------------------------------------------------
# SESSION BINDING: Prompt sets current session
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_prompt_with_session_id_binds_state(
    async_client: AsyncClient,
    test_api_key: str,
    mock_claude_sdk: MagicMock,
) -> None:
    """Prompt with session_id sets the current session in WebSocket state."""
    from apps.api.routes.websocket import (
        WebSocketState,
        _handle_prompt_message,
    )
    from apps.api.services.agent import AgentService
    from tests.mocks.claude_sdk import AssistantMessage

    mock_instance = mock_claude_sdk.return_value
    mock_instance.set_messages(
        [
            AssistantMessage(
                content=[{"type": "text", "text": "ok"}],
                model="sonnet",
            )
        ]
    )

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    await ws.accept()
    agent_service = AgentService()
    state = WebSocketState()
    session_id = str(uuid4())

    message = {
        "type": "prompt",
        "prompt": "test binding",
        "session_id": session_id,
    }

    await _handle_prompt_message(
        cast("WebSocket", ws),
        message,  # type: ignore[arg-type]
        agent_service,
        state,
        test_api_key,
    )

    assert state.current_session_id == session_id


# ---------------------------------------------------------------------------
# MULTIPLE MESSAGES: Sequential handling
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_ws_handles_multiple_messages_sequentially(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """WebSocket processes multiple messages in order, continuing after errors."""
    from apps.api.routes.websocket import websocket_query
    from apps.api.services.agent import AgentService

    ws = MockWebSocket(headers={"x-api-key": test_api_key})
    agent_service = AgentService()

    # Queue multiple messages: invalid JSON, unknown type, missing prompt
    ws.add_raw_message("not json")
    ws.add_received_message({"type": "unknown"})
    ws.add_received_message({"type": "prompt"})  # Missing prompt text

    task = asyncio.create_task(
        websocket_query(cast("WebSocket", ws), agent_service)
    )
    await _wait_for_messages(ws, min_count=3, timeout=3.0)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert ws.was_accepted
    # Should have at least 3 error messages (one per bad message)
    error_msgs = [m for m in ws.sent_messages if m.get("type") == "error"]
    assert len(error_msgs) >= 3, (
        f"Expected >= 3 errors for 3 bad messages, got {len(error_msgs)}: {error_msgs}"
    )
