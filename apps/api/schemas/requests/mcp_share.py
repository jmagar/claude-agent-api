"""MCP share request schemas."""

from pydantic import BaseModel, Field

class McpShareCreateRequest(BaseModel):
    """Request payload for creating MCP share tokens."""

    config: dict[str, object] = Field(
        ..., description="Sanitized MCP server configuration to share"
    )
