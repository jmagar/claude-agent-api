"""Base exception class for the API."""


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

    def __repr__(self) -> str:
        """Return string representation for debugging.

        Returns:
            Debug string with class name and key attributes.
        """
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code!r}, "
            f"status_code={self.status_code})"
        )
