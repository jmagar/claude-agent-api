"""Session-related request schemas."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from apps.api.schemas.requests.config import HooksConfigSchema, ImageContentSchema
from apps.api.schemas.validators import validate_model_name


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
