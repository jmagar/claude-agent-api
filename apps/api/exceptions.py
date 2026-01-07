"""Custom exception classes for the API."""


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, str | int | float | bool | list[str] | None] | None = None,
    ) -> None:
        """Initialize API error.

        Args:
            message: Human-readable error message.
            code: Machine-readable error code.
            status_code: HTTP status code.
            details: Additional error details.
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details: dict[str, str | int | float | bool | list[str] | None] = (
            details or {}
        )

    def to_dict(
        self,
    ) -> dict[
        str, dict[str, str | dict[str, str | int | float | bool | list[str] | None]]
    ]:
        """Convert error to dictionary for JSON response.

        Returns:
            Error dictionary.
        """
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class SessionNotFoundError(APIError):
    """Raised when a session is not found."""

    def __init__(self, session_id: str) -> None:
        """Initialize session not found error.

        Args:
            session_id: The session ID that was not found.
        """
        super().__init__(
            message=f"Session '{session_id}' not found",
            code="SESSION_NOT_FOUND",
            status_code=404,
            details={"session_id": session_id},
        )


class SessionLockedError(APIError):
    """Raised when a session is currently locked by another operation."""

    def __init__(self, session_id: str) -> None:
        """Initialize session locked error.

        Args:
            session_id: The locked session ID.
        """
        super().__init__(
            message=f"Session '{session_id}' is currently in use",
            code="SESSION_LOCKED",
            status_code=409,
            details={"session_id": session_id},
        )


class SessionCompletedError(APIError):
    """Raised when trying to resume a completed or errored session."""

    def __init__(self, session_id: str, status: str) -> None:
        """Initialize session completed error.

        Args:
            session_id: The session ID.
            status: Current session status.
        """
        super().__init__(
            message=f"Session '{session_id}' has already {status}",
            code="SESSION_COMPLETED",
            status_code=400,
            details={"session_id": session_id, "status": status},
        )


class ValidationError(APIError):
    """Raised when request validation fails."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize validation error.

        Args:
            message: Validation error message.
            field: Optional field that failed validation.
        """
        details: dict[str, str | int | float | bool | list[str] | None] = {}
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class AuthenticationError(APIError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Invalid or missing API key") -> None:
        """Initialize authentication error.

        Args:
            message: Authentication error message.
        """
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int | None = None) -> None:
        """Initialize rate limit error.

        Args:
            retry_after: Seconds until retry is allowed.
        """
        details: dict[str, str | int | float | bool | list[str] | None] = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            message="Rate limit exceeded",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
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


class CheckpointNotFoundError(APIError):
    """Raised when a checkpoint is not found."""

    def __init__(self, checkpoint_uuid: str) -> None:
        """Initialize checkpoint not found error.

        Args:
            checkpoint_uuid: The checkpoint UUID that was not found.
        """
        super().__init__(
            message=f"Checkpoint '{checkpoint_uuid}' not found",
            code="CHECKPOINT_NOT_FOUND",
            status_code=404,
            details={"checkpoint_uuid": checkpoint_uuid},
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


class DatabaseError(APIError):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "Database operation failed") -> None:
        """Initialize database error.

        Args:
            message: Error message.
        """
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
        )


class CacheError(APIError):
    """Raised when a cache operation fails."""

    def __init__(self, message: str = "Cache operation failed") -> None:
        """Initialize cache error.

        Args:
            message: Error message.
        """
        super().__init__(
            message=message,
            code="CACHE_ERROR",
            status_code=500,
        )
