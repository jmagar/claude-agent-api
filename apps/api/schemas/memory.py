"""Memory API request/response schemas."""

from typing import Any

from pydantic import BaseModel, Field

# JSON-serializable value type (recursive union for nested structures)
JsonValue = str | int | float | bool | None | dict[str, Any] | list[Any]


class MemoryAddRequest(BaseModel):
    """Request to add a memory."""

    messages: str = Field(..., description="Content to extract memories from")
    metadata: dict[str, JsonValue] | None = Field(
        None, description="Optional metadata to attach to memories"
    )
    enable_graph: bool = Field(
        True, description="Enable graph memory extraction (slower but richer)"
    )


class MemorySearchRequest(BaseModel):
    """Request to search memories."""

    query: str = Field(..., description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    enable_graph: bool = Field(True, description="Include graph context in search")


class MemoryResult(BaseModel):
    """Single memory result."""

    id: str = Field(..., description="Unique memory identifier")
    memory: str = Field(..., description="Memory content text")
    score: float = Field(0.0, description="Relevance score (0.0-1.0)")
    metadata: dict[str, JsonValue] = Field(
        default_factory=dict, description="Associated metadata"
    )


class MemorySearchResponse(BaseModel):
    """Response from memory search."""

    results: list[MemoryResult]
    count: int


class MemoryListResponse(BaseModel):
    """Response from listing all memories."""

    memories: list[dict[str, JsonValue]]
    count: int


class MemoryDeleteResponse(BaseModel):
    """Response from deleting memory."""

    deleted: bool
    message: str
