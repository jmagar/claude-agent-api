"""MCP server request schemas."""

from pydantic import BaseModel, Field


class McpServerCreateRequest(BaseModel):
    """<summary>Request payload for creating an MCP server config.</summary>"""

    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., description="Connection type")
    config: dict[str, object] = Field(default_factory=dict)


class McpServerUpdateRequest(BaseModel):
    """<summary>Request payload for updating an MCP server config.</summary>"""

    type: str | None = None
    config: dict[str, object] | None = None
    is_shared: bool | None = None
