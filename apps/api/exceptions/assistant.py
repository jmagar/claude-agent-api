"""Assistant-related exceptions."""

from apps.api.exceptions.base import APIError


class AssistantNotFoundError(APIError):
    """Raised when an assistant is not found."""

    def __init__(self, assistant_id: str) -> None:
        """Initialize assistant not found error.

        Args:
            assistant_id: The assistant ID that was not found.
        """
        super().__init__(
            message=f"Assistant '{assistant_id}' not found",
            code="ASSISTANT_NOT_FOUND",
            status_code=404,
            details={"assistant_id": assistant_id},
        )
