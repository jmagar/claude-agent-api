"""Session-related request schemas."""

from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from apps.api.constants import BUILT_IN_TOOLS
from apps.api.schemas.requests.config import HooksConfigSchema, ImageContentSchema
from apps.api.schemas.validators import validate_model_name, validate_tool_name


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

    @field_validator("allowed_tools", "disallowed_tools")
    @classmethod
    def validate_tool_names(cls, tools: list[str] | None) -> list[str] | None:
        """Validate that all tool names are valid."""
        if tools is None:
            return None
        invalid_tools = [t for t in tools if not validate_tool_name(t)]
        if invalid_tools:
            valid_tools_msg = ", ".join(BUILT_IN_TOOLS[:5]) + "..."
            raise ValueError(
                f"Invalid tool names: {invalid_tools}. "
                f"Valid tools include: {valid_tools_msg}, "
                "or MCP tools with mcp__* prefix."
            )
        return tools

    @model_validator(mode="after")
    def validate_no_tool_conflicts(self) -> Self:
        """Validate no conflicts between allowed and disallowed tools."""
        if self.allowed_tools and self.disallowed_tools:
            conflicts = set(self.allowed_tools) & set(self.disallowed_tools)
            if conflicts:
                raise ValueError(
                    f"Tool conflict: {conflicts} appear in both "
                    "allowed_tools and disallowed_tools"
                )
        return self


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

    @field_validator("allowed_tools", "disallowed_tools")
    @classmethod
    def validate_tool_names(cls, tools: list[str] | None) -> list[str] | None:
        """Validate that all tool names are valid."""
        if tools is None:
            return None
        invalid_tools = [t for t in tools if not validate_tool_name(t)]
        if invalid_tools:
            valid_tools_msg = ", ".join(BUILT_IN_TOOLS[:5]) + "..."
            raise ValueError(
                f"Invalid tool names: {invalid_tools}. "
                f"Valid tools include: {valid_tools_msg}, "
                "or MCP tools with mcp__* prefix."
            )
        return tools

    @model_validator(mode="after")
    def validate_no_tool_conflicts(self) -> Self:
        """Validate no conflicts between allowed and disallowed tools."""
        if self.allowed_tools and self.disallowed_tools:
            conflicts = set(self.allowed_tools) & set(self.disallowed_tools)
            if conflicts:
                raise ValueError(
                    f"Tool conflict: {conflicts} appear in both "
                    "allowed_tools and disallowed_tools"
                )
        return self

    @field_validator("model")
    @classmethod
    def validate_model(cls, model: str | None) -> str | None:
        """Validate that the model name is valid."""
        return validate_model_name(model)


class AnswerRequest(BaseModel):
    """Request to answer an AskUserQuestion from the agent."""

    answer: str = Field(..., min_length=1, max_length=100000)


class PromoteRequest(BaseModel):
    """Request to promote a brainstorm session to code mode."""

    project_id: str = Field(..., description="Project ID to associate with session")


class UpdateTagsRequest(BaseModel):
    """Request to update session tags."""

    tags: list[str] = Field(..., description="List of tags to set for the session")
