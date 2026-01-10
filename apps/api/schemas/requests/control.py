"""Control request schemas."""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class RewindRequest(BaseModel):
    """Request to rewind session to a checkpoint."""

    checkpoint_id: str = Field(
        ..., min_length=1, description="ID of checkpoint to rewind to"
    )


class ControlRequest(BaseModel):
    """Request to send a control event to an active session.

    Control events allow dynamic changes during streaming, such as changing
    the permission mode mid-session.
    """

    type: Literal["permission_mode_change"] = Field(
        ..., description="Type of control event"
    )
    permission_mode: (
        Literal["default", "acceptEdits", "plan", "bypassPermissions"] | None
    ) = Field(
        None, description="New permission mode (required for permission_mode_change)"
    )

    @model_validator(mode="after")
    def validate_permission_mode_for_change(self) -> Self:
        """Validate that permission_mode is provided for permission_mode_change type."""
        if self.type == "permission_mode_change" and self.permission_mode is None:
            raise ValueError(
                "permission_mode is required for permission_mode_change control event"
            )
        return self
