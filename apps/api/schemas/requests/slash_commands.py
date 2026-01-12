"""Slash command request schemas."""

from pydantic import BaseModel, Field


class SlashCommandCreateRequest(BaseModel):
    """<summary>Request payload for creating a slash command.</summary>"""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    content: str = Field(..., min_length=1)
    enabled: bool = True


class SlashCommandUpdateRequest(BaseModel):
    """<summary>Request payload for updating a slash command.</summary>"""

    id: str
    name: str
    description: str
    content: str
    enabled: bool = True
