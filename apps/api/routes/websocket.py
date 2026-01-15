"""WebSocket routes for bidirectional agent communication (T119-T120)."""

import asyncio
import contextlib
import json
import secrets
from dataclasses import dataclass
from typing import Literal, NotRequired, Required, TypedDict, cast

import structlog
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from apps.api.config import get_settings
from apps.api.dependencies import get_agent_service, get_session_service
from apps.api.exceptions import SessionNotFoundError
from apps.api.schemas.requests.query import QueryRequest
from apps.api.services.agent import AgentService
from apps.api.services.session import SessionService

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["websocket"])

# Permission mode type alias (matches AgentService.update_permission_mode signature)
PermissionModeType = Literal["default", "acceptEdits", "plan", "bypassPermissions"]
VALID_PERMISSION_MODES: frozenset[str] = frozenset(
    {"default", "acceptEdits", "plan", "bypassPermissions"}
)


class WebSocketMessageDict(TypedDict):
    """WebSocket message format."""

    type: Required[Literal["prompt", "interrupt", "answer", "control"]]
    prompt: NotRequired[str | None]
    session_id: NotRequired[str | None]
    answer: NotRequired[str | None]
    # Query configuration options
    model: NotRequired[str | None]
    max_turns: NotRequired[int | None]
    allowed_tools: NotRequired[list[str] | None]
    disallowed_tools: NotRequired[list[str] | None]
    permission_mode: NotRequired[
        str | None
    ]  # Validated at runtime to match PermissionModeType
    include_partial_messages: NotRequired[bool | None]


class WebSocketResponseDict(TypedDict):
    """WebSocket response format."""

    type: Required[Literal["sse_event", "error", "ack"]]
    event: NotRequired[str | None]
    data: NotRequired[dict[str, object] | None]
    message: NotRequired[str | None]


@dataclass
class WebSocketState:
    """Mutable state for WebSocket connection."""

    query_task: asyncio.Task[None] | None = None
    current_session_id: str | None = None


async def _handle_prompt_message(
    websocket: WebSocket,
    message: WebSocketMessageDict,
    agent_service: AgentService,
    state: WebSocketState,
) -> None:
    """Handle prompt message to start a new query.

    Args:
        websocket: WebSocket connection.
        message: WebSocket message dict.
        agent_service: Agent service instance.
        state: WebSocket connection state.
    """
    prompt = message.get("prompt")
    if not prompt:
        await _send_error(websocket, "prompt is required")
        return

    # Build query request from WebSocket message
    request = QueryRequest(
        prompt=prompt,
        session_id=message.get("session_id"),
        model=message.get("model"),
        max_turns=message.get("max_turns"),
        allowed_tools=message.get("allowed_tools") or [],
        disallowed_tools=message.get("disallowed_tools") or [],
        permission_mode=cast(
            "Literal['default', 'acceptEdits', 'plan', 'bypassPermissions']",
            message.get("permission_mode") or "default",
        ),
        include_partial_messages=message.get("include_partial_messages") or False,
    )

    # Cancel existing query if running
    if state.query_task and not state.query_task.done():
        state.query_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await state.query_task

    # Start streaming query
    state.query_task = asyncio.create_task(
        _stream_query(websocket, agent_service, request)
    )
    state.current_session_id = request.session_id

    await _send_ack(websocket, "Query started")


async def _handle_interrupt_message(
    websocket: WebSocket,
    message: WebSocketMessageDict,
    agent_service: AgentService,
    session_service: SessionService,
    current_session_id: str | None,
    api_key: str,
) -> None:
    """Handle interrupt message to stop current query.

    Args:
        websocket: WebSocket connection.
        message: WebSocket message dict.
        agent_service: Agent service instance.
        session_service: Session service instance.
        current_session_id: Current session ID if any.
        api_key: API key of the requester.
    """
    session_id = message.get("session_id") or current_session_id
    if not session_id:
        await _send_error(websocket, "No active session to interrupt")
        return

    # Verify session ownership before allowing interrupt
    try:
        session = await session_service.get_session(session_id, current_api_key=api_key)
        if not session:
            await _send_error(websocket, "Session not found or not authorized")
            return
    except SessionNotFoundError:
        await _send_error(websocket, "Session not found or not authorized")
        return

    success = await agent_service.interrupt(session_id)
    if success:
        await _send_ack(websocket, "Query interrupted")
    else:
        await _send_error(websocket, "Session not found or not active")


async def _handle_answer_message(
    websocket: WebSocket,
    message: WebSocketMessageDict,
    agent_service: AgentService,
    current_session_id: str | None,
) -> None:
    """Handle answer message to respond to pending question.

    Args:
        websocket: WebSocket connection.
        message: WebSocket message dict.
        agent_service: Agent service instance.
        current_session_id: Current session ID if any.
    """
    session_id = message.get("session_id") or current_session_id
    answer = message.get("answer")

    if not answer:
        await _send_error(websocket, "answer is required")
        return

    if session_id:
        success = await agent_service.submit_answer(session_id, answer)
        if success:
            await _send_ack(websocket, "Answer submitted")
        else:
            await _send_error(websocket, "Session not found or no pending question")
    else:
        await _send_error(websocket, "No active session")


async def _handle_control_message(
    websocket: WebSocket,
    message: WebSocketMessageDict,
    agent_service: AgentService,
    current_session_id: str | None,
) -> None:
    """Handle control message for permission mode changes.

    Args:
        websocket: WebSocket connection.
        message: WebSocket message dict.
        agent_service: Agent service instance.
        current_session_id: Current session ID if any.
    """
    session_id = message.get("session_id") or current_session_id
    permission_mode_raw = message.get("permission_mode")

    if not (permission_mode_raw and session_id):
        await _send_error(websocket, "session_id and permission_mode required")
        return

    # Validate permission mode is a valid literal value
    if permission_mode_raw not in VALID_PERMISSION_MODES:
        await _send_error(
            websocket,
            f"Invalid permission_mode: {permission_mode_raw}. "
            f"Must be one of: {', '.join(sorted(VALID_PERMISSION_MODES))}",
        )
        return

    # Cast is safe after validation above
    validated_mode = cast("PermissionModeType", permission_mode_raw)
    success = await agent_service.update_permission_mode(session_id, validated_mode)
    if success:
        await _send_ack(websocket, "Permission mode updated")
    else:
        await _send_error(websocket, "Session not found or not active")


async def _process_websocket_message(
    websocket: WebSocket,
    message: WebSocketMessageDict,
    agent_service: AgentService,
    session_service: SessionService,
    state: WebSocketState,
    api_key: str,
) -> None:
    """Route and process a WebSocket message by type.

    Args:
        websocket: WebSocket connection.
        message: WebSocket message dict.
        agent_service: Agent service instance.
        session_service: Session service instance.
        state: WebSocket connection state.
        api_key: API key of the requester.
    """
    msg_type = message.get("type")

    if msg_type == "prompt":
        await _handle_prompt_message(websocket, message, agent_service, state)
    elif msg_type == "interrupt":
        await _handle_interrupt_message(
            websocket,
            message,
            agent_service,
            session_service,
            state.current_session_id,
            api_key,
        )
    elif msg_type == "answer":
        await _handle_answer_message(
            websocket, message, agent_service, state.current_session_id
        )
    elif msg_type == "control":
        await _handle_control_message(
            websocket, message, agent_service, state.current_session_id
        )
    else:
        await _send_error(websocket, f"Unknown message type: {msg_type}")


@router.websocket("/query/ws")
async def websocket_query(
    websocket: WebSocket,
    agent_service: AgentService = Depends(get_agent_service),
    session_service: SessionService = Depends(get_session_service),
) -> None:
    """WebSocket endpoint for bidirectional agent communication (T119-T120).

    This endpoint provides real-time bidirectional communication with the agent.

    Message Types (client -> server):
    - prompt: Start a new query with the agent
    - interrupt: Interrupt the current query
    - answer: Submit an answer to a pending AskUserQuestion
    - control: Send control events (e.g., permission mode changes)

    Response Types (server -> client):
    - sse_event: SSE event data (init, message, result, done, etc.)
    - error: Error message
    - ack: Acknowledgment of a received message
    """
    settings = get_settings()

    # Authenticate via header ONLY (don't allow query params for secrets)
    api_key = websocket.headers.get("x-api-key")

    if not api_key:
        await websocket.close(code=4001, reason="Missing API key")
        return

    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(api_key, settings.api_key.get_secret_value()):
        await websocket.close(code=4001, reason="Invalid API key")
        return

    await websocket.accept()
    logger.info("WebSocket connection accepted")

    state = WebSocketState()

    try:
        while True:
            raw_message = await websocket.receive_text()

            try:
                message: WebSocketMessageDict = json.loads(raw_message)
            except json.JSONDecodeError:
                await _send_error(websocket, "Invalid JSON message")
                continue

            await _process_websocket_message(
                websocket, message, agent_service, session_service, state, api_key
            )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error("WebSocket error", error=str(e), error_type=type(e).__name__)
        await _send_error(websocket, "An internal error occurred")
    finally:
        if state.query_task and not state.query_task.done():
            state.query_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await state.query_task


async def _stream_query(
    websocket: WebSocket,
    agent_service: AgentService,
    request: QueryRequest,
) -> None:
    """Stream query results to WebSocket.

    Args:
        websocket: WebSocket connection.
        agent_service: Agent service instance.
        request: Query request.
    """
    try:
        async for sse_event in agent_service.query_stream(request):
            # SSE event is a dict with 'event' and 'data' keys
            # Parse the JSON data string to send as structured WebSocket message
            event_type = sse_event.get("event", "")
            data_str = sse_event.get("data", "{}")

            try:
                event_data: dict[str, object] = json.loads(data_str)
            except json.JSONDecodeError:
                event_data = {"raw": data_str}

            response: WebSocketResponseDict = {
                "type": "sse_event",
                "event": event_type,
                "data": event_data,
            }
            await websocket.send_json(response)

    except asyncio.CancelledError:
        # Query was interrupted
        logger.info("WebSocket query cancelled")
        raise
    except Exception as e:
        logger.error(
            "WebSocket stream error", error=str(e), error_type=type(e).__name__
        )
        await _send_error(websocket, "Stream processing failed")


async def _send_error(websocket: WebSocket, message: str) -> None:
    """Send error message via WebSocket.

    Args:
        websocket: WebSocket connection.
        message: Error message.
    """
    response: WebSocketResponseDict = {
        "type": "error",
        "message": message,
    }
    await websocket.send_json(response)


async def _send_ack(websocket: WebSocket, message: str) -> None:
    """Send acknowledgment message via WebSocket.

    Args:
        websocket: WebSocket connection.
        message: Acknowledgment message.
    """
    response: WebSocketResponseDict = {
        "type": "ack",
        "message": message,
    }
    await websocket.send_json(response)
