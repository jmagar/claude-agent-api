"""Infrastructure-related exceptions."""

from apps.api.exceptions.base import APIError


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


class RequestTimeoutError(APIError):
    """Raised when a request times out.

    This error is raised when a query or operation exceeds
    the configured timeout limit.
    """

    def __init__(
        self,
        message: str = "Request timed out",
        timeout_seconds: int | None = None,
        operation: str | None = None,
    ) -> None:
        """Initialize request timeout error.

        Args:
            message: Error message.
            timeout_seconds: The timeout limit that was exceeded.
            operation: The operation that timed out.
        """
        details: dict[str, str | int | float | bool | list[str] | None] = {}
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
        super().__init__(
            message=message,
            code="REQUEST_TIMEOUT",
            status_code=504,
            details=details,
        )


class ServiceUnavailableError(APIError):
    """Raised when the service is temporarily unavailable.

    This can occur during graceful shutdown or maintenance.
    """

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: int | None = None,
    ) -> None:
        """Initialize service unavailable error.

        Args:
            message: Error message.
            retry_after: Suggested retry time in seconds.
        """
        details: dict[str, str | int | float | bool | list[str] | None] = {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=503,
            details=details,
        )
