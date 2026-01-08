"""Agent execution exceptions."""

from apps.api.exceptions.base import APIError


class AgentError(APIError):
    """Raised when the Claude Agent SDK returns an error."""

    def __init__(self, message: str, original_error: str | None = None) -> None:
        """Initialize agent error.

        Args:
            message: Error message.
            original_error: Original error from SDK.
        """
        details: dict[str, str | int | float | bool | list[str] | None] = {}
        if original_error:
            details["original_error"] = original_error
        super().__init__(
            message=message,
            code="AGENT_ERROR",
            status_code=500,
            details=details,
        )


class ToolNotAllowedError(APIError):
    """Raised when a tool is not in the allowed list."""

    def __init__(self, tool_name: str, allowed_tools: list[str]) -> None:
        """Initialize tool not allowed error.

        Args:
            tool_name: The disallowed tool name.
            allowed_tools: List of allowed tool names.
        """
        super().__init__(
            message=f"Tool '{tool_name}' is not allowed",
            code="TOOL_NOT_ALLOWED",
            status_code=400,
            details={"tool_name": tool_name, "allowed_tools": allowed_tools},
        )


class HookError(APIError):
    """Raised when a hook webhook fails."""

    def __init__(
        self,
        hook_event: str,
        message: str,
        webhook_url: str | None = None,
    ) -> None:
        """Initialize hook error.

        Args:
            hook_event: The hook event type.
            message: Error message.
            webhook_url: The webhook URL that failed.
        """
        details: dict[str, str | int | float | bool | list[str] | None] = {
            "hook_event": hook_event
        }
        if webhook_url:
            details["webhook_url"] = webhook_url
        super().__init__(
            message=message,
            code="HOOK_ERROR",
            status_code=502,
            details=details,
        )
