"""Memory management API routes."""

import structlog
from fastapi import APIRouter, status

from apps.api.dependencies import ApiKey, MemorySvc
from apps.api.schemas.memory import (
    MemoryAddRequest,
    MemoryAddResponse,
    MemoryDeleteResponse,
    MemoryListResponse,
    MemoryResult,
    MemorySearchRequest,
    MemorySearchResponse,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/memories", tags=["memories"])


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(
    request: MemorySearchRequest,
    api_key: ApiKey,
    memory_service: MemorySvc,
) -> MemorySearchResponse:
    """Search memories for the current user.

    Args:
        request: Search parameters including query and limit.
        api_key: API key from auth middleware (used as user_id for multi-tenant isolation).
        memory_service: Injected memory service.

    Returns:
        Search results with memories and count.
    """
    results = await memory_service.search_memories(
        query=request.query,
        user_id=api_key,
        limit=request.limit,
        enable_graph=request.enable_graph,
    )

    return MemorySearchResponse(
        results=[MemoryResult(**r) for r in results],
        count=len(results),
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=MemoryAddResponse)
async def add_memory(
    request: MemoryAddRequest,
    api_key: ApiKey,
    memory_service: MemorySvc,
) -> MemoryAddResponse:
    """Add a memory for the current user.

    Args:
        request: Memory content and metadata.
        api_key: API key from auth middleware (used as user_id for multi-tenant isolation).
        memory_service: Injected memory service.

    Returns:
        Created memories with count.
    """
    results = await memory_service.add_memory(
        messages=request.messages,
        user_id=api_key,
        metadata=request.metadata,
        enable_graph=request.enable_graph,
    )

    return MemoryAddResponse(memories=results, count=len(results))


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    api_key: ApiKey,
    memory_service: MemorySvc,
) -> MemoryListResponse:
    """List all memories for the current user.

    Args:
        api_key: API key from auth middleware (used as user_id for multi-tenant isolation).
        memory_service: Injected memory service.

    Returns:
        All user memories with count.
    """
    memories = await memory_service.get_all_memories(user_id=api_key)

    return MemoryListResponse(memories=memories, count=len(memories))


@router.delete("/{memory_id}", response_model=MemoryDeleteResponse)
async def delete_memory(
    memory_id: str,
    api_key: ApiKey,
    memory_service: MemorySvc,
) -> MemoryDeleteResponse:
    """Delete a specific memory.

    Args:
        memory_id: Unique memory identifier.
        api_key: API key from auth middleware (used as user_id for multi-tenant isolation).
        memory_service: Injected memory service.

    Returns:
        Deletion confirmation.
    """
    await memory_service.delete_memory(memory_id=memory_id, user_id=api_key)

    return MemoryDeleteResponse(deleted=True, message=f"Memory {memory_id} deleted")


@router.delete("", response_model=MemoryDeleteResponse)
async def delete_all_memories(
    api_key: ApiKey,
    memory_service: MemorySvc,
) -> MemoryDeleteResponse:
    """Delete all memories for the current user.

    Args:
        api_key: API key from auth middleware (used as user_id for multi-tenant isolation).
        memory_service: Injected memory service.

    Returns:
        Deletion confirmation.
    """
    await memory_service.delete_all_memories(user_id=api_key)

    return MemoryDeleteResponse(deleted=True, message="All memories deleted")
