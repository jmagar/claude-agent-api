"""Memory API request/response schemas."""

from typing import NotRequired, Required, TypedDict

from pydantic import BaseModel, Field


class MemoryAddRequest(BaseModel):
    """Request to add a memory."""

    messages: str = Field(..., description="Content to extract memories from")
    metadata: dict[str, object] | None = Field(
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
    metadata: dict[str, object] = Field(
        default_factory=dict, description="Associated metadata"
    )


class MemorySearchResponse(BaseModel):
    """Response from memory search."""

    results: list[MemoryResult]
    count: int


class MemoryRecordDict(TypedDict):
    """Memory record structure from Mem0."""

    id: Required[str]
    memory: Required[str]
    hash: NotRequired[str]
    created_at: NotRequired[str]
    updated_at: NotRequired[str]
    user_id: NotRequired[str]
    agent_id: NotRequired[str]
    metadata: NotRequired[dict[str, object]]


class MemoryAddResponse(BaseModel):
    """Response from adding memories."""

    memories: list[MemoryRecordDict]
    count: int


class MemoryListResponse(BaseModel):
    """Response from listing all memories."""

    memories: list[MemoryRecordDict]
    count: int


class MemoryDeleteResponse(BaseModel):
    """Response from deleting memory."""

    deleted: bool
    message: str
