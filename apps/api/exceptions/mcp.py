"""MCP-related exceptions."""

from apps.api.exceptions.base import APIError


class McpShareNotFoundError(APIError):
    """Raised when an MCP share token is not found."""

    def __init__(self, token: str) -> None:
        """Initialize MCP share not found error.

        Args:
            token: Share token that was not found.
        """
        super().__init__(
            message="MCP share token not found",
            code="MCP_SHARE_NOT_FOUND",
            status_code=404,
            details={"token": token},
        )
