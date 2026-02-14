"""Memory-specific exceptions."""

from apps.api.exceptions.base import APIError


class MemoryNotFoundError(APIError):
    """Raised when a memory does not exist or user is not authorized to access it."""

    def __init__(self, memory_id: str, message: str | None = None) -> None:
        """Initialize memory not found error.

        Args:
            memory_id: Memory identifier that was not found.
            message: Optional custom error message.
        """
        msg = message or f"Memory {memory_id} not found or not authorized"
        super().__init__(
            message=msg,
            code="MEMORY_NOT_FOUND",
            status_code=404,
            details={"memory_id": memory_id},
        )
