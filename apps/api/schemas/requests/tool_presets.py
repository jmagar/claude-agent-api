"""Tool preset request schemas."""

from pydantic import BaseModel, Field


class ToolPresetCreateRequest(BaseModel):
    """Request payload for creating a tool preset."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    tools: list[str] = Field(default_factory=list)
    is_default: bool | None = None
    allowed_tools: list[str] | None = None
    disallowed_tools: list[str] | None = None


class ToolPresetUpdateRequest(BaseModel):
    """Request payload for updating a tool preset."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    tools: list[str] | None = None
    allowed_tools: list[str] | None = None
    disallowed_tools: list[str] | None = None
