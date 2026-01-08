"""Pydantic request models for API endpoints.

NOTE: This is a transitional module during refactoring. Config schemas have
been extracted to requests/config.py, QueryRequest to requests/query.py,
and session schemas (ResumeRequest, ForkRequest, AnswerRequest) to
requests/sessions.py. This module will be fully migrated in later tasks.
"""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

from apps.api.schemas.requests.config import (
    AgentDefinitionSchema,
    HooksConfigSchema,
    ImageContentSchema,
    McpServerConfigSchema,
    OutputFormatSchema,
    SandboxSettingsSchema,
    SdkPluginConfigSchema,
)

# QueryRequest migrated to requests/query.py
from apps.api.schemas.requests.query import QueryRequest

# Session schemas migrated to requests/sessions.py
from apps.api.schemas.requests.sessions import (
    AnswerRequest,
    ForkRequest,
    ResumeRequest,
)

# Re-export config schemas for backward compatibility
__all__ = [
    "AgentDefinitionSchema",
    "AnswerRequest",
    "ControlRequest",
    "ForkRequest",
    "HooksConfigSchema",
    "ImageContentSchema",
    "McpServerConfigSchema",
    "OutputFormatSchema",
    "QueryRequest",
    "ResumeRequest",
    "RewindRequest",
    "SandboxSettingsSchema",
    "SdkPluginConfigSchema",
]


class RewindRequest(BaseModel):
    """Request to rewind session to a checkpoint."""

    checkpoint_id: str = Field(..., description="ID of checkpoint to rewind to")


class ControlRequest(BaseModel):
    """Request to send a control event to an active session (FR-015).

    Control events allow dynamic changes during streaming, such as changing
    the permission mode mid-session.
    """

    type: Literal["permission_mode_change"] = Field(
        ..., description="Type of control event"
    )
    permission_mode: (
        Literal["default", "acceptEdits", "plan", "bypassPermissions"] | None
    ) = Field(None, description="New permission mode (required for permission_mode_change)")

    @model_validator(mode="after")
    def validate_permission_mode_for_change(self) -> Self:
        """Validate that permission_mode is provided for permission_mode_change type."""
        if self.type == "permission_mode_change" and self.permission_mode is None:
            raise ValueError(
                "permission_mode is required for permission_mode_change control event"
            )
        return self
