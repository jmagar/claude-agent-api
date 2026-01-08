"""Pydantic request models for API endpoints.

NOTE: This is a transitional module during refactoring. Config schemas have
been extracted to requests/config.py and QueryRequest to requests/query.py.
This module will be fully migrated in later tasks.
"""

from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

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
from apps.api.schemas.validators import validate_model_name

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


class ResumeRequest(BaseModel):
    """Request to resume an existing session."""

    prompt: str = Field(..., min_length=1, max_length=100000)
    images: list[ImageContentSchema] | None = Field(
        None, description="Images to include"
    )

    # Optional configuration overrides
    allowed_tools: list[str] | None = Field(None, description="Override allowed tools")
    disallowed_tools: list[str] | None = Field(
        None, description="Override disallowed tools"
    )
    permission_mode: (
        Literal["default", "acceptEdits", "plan", "bypassPermissions"] | None
    ) = None
    max_turns: int | None = Field(None, ge=1, le=1000)
    hooks: HooksConfigSchema | None = None


class ForkRequest(BaseModel):
    """Request to fork an existing session."""

    prompt: str = Field(..., min_length=1, max_length=100000)
    images: list[ImageContentSchema] | None = Field(
        None, description="Images to include"
    )

    # Optional configuration overrides (inherited from parent if not specified)
    allowed_tools: list[str] | None = Field(None, description="Override allowed tools")
    disallowed_tools: list[str] | None = Field(
        None, description="Override disallowed tools"
    )
    permission_mode: (
        Literal["default", "acceptEdits", "plan", "bypassPermissions"] | None
    ) = None
    max_turns: int | None = Field(None, ge=1, le=1000)
    model: str | None = Field(None, description="Override model for forked session")
    hooks: HooksConfigSchema | None = None

    @field_validator("model")
    @classmethod
    def validate_model(cls, model: str | None) -> str | None:
        """Validate that the model name is valid."""
        return validate_model_name(model)


class AnswerRequest(BaseModel):
    """Request to answer an AskUserQuestion from the agent."""

    answer: str = Field(..., min_length=1, max_length=100000)


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
