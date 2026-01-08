"""Builders for mock SSE events."""

import json


def build_init_event(
    session_id: str = "test-session-001",
    model: str = "sonnet",
    tools: list[str] | None = None,
    mcp_servers: list[dict[str, object]] | None = None,
    plugins: list[str] | None = None,
    commands: list[str] | None = None,
    permission_mode: str = "default",
) -> dict[str, str]:
    """Build init SSE event.

    Args:
        session_id: Session ID
        model: Model name
        tools: List of allowed tools
        mcp_servers: List of MCP server status
        plugins: List of plugin names
        commands: List of available commands
        permission_mode: Permission mode

    Returns:
        SSE event dict with 'event' and 'data' keys
    """
    data = {
        "session_id": session_id,
        "model": model,
        "tools": tools or [],
        "mcp_servers": mcp_servers or [],
        "plugins": plugins or [],
        "commands": commands or [],
        "permission_mode": permission_mode,
    }

    return {
        "event": "init",
        "data": json.dumps(data),
    }


def build_message_event(
    message_type: str = "assistant",
    content: list[dict[str, object]] | None = None,
    model: str = "sonnet",
    uuid: str | None = None,
    usage: dict[str, int] | None = None,
) -> dict[str, str]:
    """Build message SSE event.

    Args:
        message_type: Type of message (user/assistant/system)
        content: List of content blocks
        model: Model name
        uuid: Message UUID
        usage: Token usage info

    Returns:
        SSE event dict
    """
    if content is None:
        content = [{"type": "text", "text": "Mocked response"}]

    data: dict[str, object] = {
        "type": message_type,
        "content": content,
        "model": model,
    }

    if uuid:
        data["uuid"] = uuid
    if usage:
        data["usage"] = usage

    return {
        "event": "message",
        "data": json.dumps(data),
    }


def build_result_event(
    session_id: str = "test-session-001",
    is_error: bool = False,
    duration_ms: int = 1500,
    num_turns: int = 1,
    total_cost_usd: float | None = 0.001,
    model_usage: dict[str, dict[str, int]] | None = None,
    result: str | None = None,
    structured_output: dict[str, object] | None = None,
) -> dict[str, str]:
    """Build result SSE event.

    Args:
        session_id: Session ID
        is_error: Whether an error occurred
        duration_ms: Request duration in milliseconds
        num_turns: Number of conversation turns
        total_cost_usd: Total cost in USD
        model_usage: Token usage by model
        result: Result text
        structured_output: Structured output if requested

    Returns:
        SSE event dict
    """
    data: dict[str, object] = {
        "session_id": session_id,
        "is_error": is_error,
        "duration_ms": duration_ms,
        "num_turns": num_turns,
        "total_cost_usd": total_cost_usd,
        "model_usage": model_usage,
        "result": result,
        "structured_output": structured_output,
    }

    return {
        "event": "result",
        "data": json.dumps(data),
    }


def build_done_event(
    reason: str = "completed",
) -> dict[str, str]:
    """Build done SSE event.

    Args:
        reason: Completion reason (completed/interrupted/error)

    Returns:
        SSE event dict
    """
    return {
        "event": "done",
        "data": json.dumps({"reason": reason}),
    }


def build_error_event(
    code: str = "INTERNAL_ERROR",
    message: str = "An error occurred",
    details: dict[str, object] | None = None,
) -> dict[str, str]:
    """Build error SSE event.

    Args:
        code: Error code
        message: Error message
        details: Additional error details

    Returns:
        SSE event dict
    """
    data = {
        "code": code,
        "message": message,
        "details": details or {},
    }

    return {
        "event": "error",
        "data": json.dumps(data),
    }


def build_standard_response(
    session_id: str = "test-session-001",
    model: str = "sonnet",
    response_text: str = "Mocked response",
) -> list[dict[str, str]]:
    """Build standard mock response with init, message, result, done events.

    Note: This only builds SDK events (message), not API-level events (init/result/done).
    The API service layer adds init/result/done events around the SDK message events.

    Args:
        session_id: Session ID
        model: Model name
        response_text: Response text content

    Returns:
        List of SSE events from SDK
    """
    return [
        build_message_event(
            content=[{"type": "text", "text": response_text}],
            model=model,
            usage={
                "input_tokens": 100,
                "output_tokens": 50,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
            },
        ),
    ]
