"""Agent request schemas."""

from pydantic import BaseModel, Field


class AgentCreateRequest(BaseModel):
    """<summary>Request payload for creating an agent.</summary>"""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    prompt: str = Field(..., min_length=1, max_length=50000)
    tools: list[str] | None = None
    model: str | None = None


class AgentUpdateRequest(BaseModel):
    """<summary>Request payload for updating an agent.</summary>"""

    id: str
    name: str
    description: str
    prompt: str
    tools: list[str] | None = None
    model: str | None = None
