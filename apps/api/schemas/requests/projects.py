"""Project request schemas."""

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """<summary>Request payload for creating a project.</summary>"""

    name: str = Field(..., min_length=1, max_length=100)
    path: str | None = None
    metadata: dict[str, object] | None = None


class ProjectUpdateRequest(BaseModel):
    """<summary>Request payload for updating a project.</summary>"""

    name: str | None = Field(None, min_length=1, max_length=100)
    metadata: dict[str, object] | None = None
