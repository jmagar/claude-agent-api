"""Skill CRUD request schemas."""

from pydantic import BaseModel, Field


class SkillCreateRequest(BaseModel):
    """<summary>Request payload for creating a skill.</summary>"""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    content: str = Field(..., min_length=1)
    enabled: bool = True


class SkillUpdateRequest(BaseModel):
    """<summary>Request payload for updating a skill.</summary>"""

    id: str
    name: str
    description: str
    content: str
    enabled: bool = True
