"""Tool preset exceptions."""

from apps.api.exceptions.base import APIError


class ToolPresetNotFoundError(APIError):
    """Raised when a tool preset is not found."""

    def __init__(self, preset_id: str) -> None:
        """Initialize tool preset not found error.

        Args:
            preset_id: Missing preset identifier.
        """
        super().__init__(
            message=f"Tool preset '{preset_id}' not found",
            code="TOOL_PRESET_NOT_FOUND",
            status_code=404,
            details={"preset_id": preset_id},
        )
