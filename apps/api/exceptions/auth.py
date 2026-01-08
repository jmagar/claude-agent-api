"""Authentication and authorization exceptions."""

from apps.api.exceptions.base import APIError


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
