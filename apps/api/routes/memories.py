"""Memory management API routes."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import structlog
from fastapi import APIRouter, status

from apps.api.dependencies import ApiKey, MemorySvc  # noqa: TC001
from apps.api.schemas.memory import (
    MemoryAddRequest,
    MemoryAddResponse,
    MemoryDeleteResponse,
    MemoryListResponse,
    MemoryRecordDict,
    MemoryResult,
    MemorySearchRequest,
    MemorySearchResponse,
)
from apps.api.utils.crypto import hash_api_key

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/memories", tags=["memories"])

if TYPE_CHECKING:
    from apps.api.types import JsonValue


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(
    request: MemorySearchRequest,
    api_key: ApiKey,
    memory_service: MemorySvc,
) -> MemorySearchResponse:
    """Search memories for the current user.

    Args:
        request: Search parameters including query and limit.
        api_key: API key from auth middleware (hashed for secure storage).
        memory_service: Injected memory service.

    Returns:
        Search results with memories and count.
    """
    # Hash API key to prevent plaintext storage in Qdrant/Neo4j metadata
    user_id = hash_api_key(api_key)

    results = await memory_service.search_memories(
        query=request.query,
        user_id=user_id,
        limit=request.limit,
        enable_graph=request.enable_graph,
    )

    # Convert search results to MemoryResult models
    return MemorySearchResponse(
        results=[
            MemoryResult(
                id=str(r.get("id", "")),
                memory=str(r.get("memory", "")),
                score=float(r.get("score", 0.0)),
                metadata=cast(
                    "dict[str, str | int | float | bool | None]",
                    r.get("metadata", {}),
                ),
            )
            for r in results
        ],
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
        api_key: API key from auth middleware (hashed for secure storage).
        memory_service: Injected memory service.

    Returns:
        Created memories with count.
    """
    # Hash API key to prevent plaintext storage in Qdrant/Neo4j metadata
    user_id = hash_api_key(api_key)

    # Cast Any to JsonValue for service layer type safety
    metadata = cast("dict[str, JsonValue] | None", request.metadata)

    results = await memory_service.add_memory(
        messages=request.messages,
        user_id=user_id,
        metadata=metadata,
        enable_graph=request.enable_graph,
    )

    return MemoryAddResponse(
        memories=cast("list[MemoryRecordDict]", results), count=len(results)
    )


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    api_key: ApiKey,
    memory_service: MemorySvc,
) -> MemoryListResponse:
    """List all memories for the current user.

    Args:
        api_key: API key from auth middleware (hashed for secure storage).
        memory_service: Injected memory service.

    Returns:
        All user memories with count.
    """
    # Hash API key to prevent plaintext storage in Qdrant/Neo4j metadata
    user_id = hash_api_key(api_key)

    memories = await memory_service.get_all_memories(user_id=user_id)

    return MemoryListResponse(
        memories=cast("list[MemoryRecordDict]", memories), count=len(memories)
    )


@router.delete("/{memory_id}", response_model=MemoryDeleteResponse)
async def delete_memory(
    memory_id: str,
    api_key: ApiKey,
    memory_service: MemorySvc,
) -> MemoryDeleteResponse:
    """Delete a specific memory.

    Args:
        memory_id: Unique memory identifier.
        api_key: API key from auth middleware (hashed for secure storage).
        memory_service: Injected memory service.

    Returns:
        Deletion confirmation.
    """
    # Hash API key to prevent plaintext storage in Qdrant/Neo4j metadata
    user_id = hash_api_key(api_key)

    await memory_service.delete_memory(memory_id=memory_id, user_id=user_id)

    return MemoryDeleteResponse(deleted=True, message=f"Memory {memory_id} deleted")


@router.delete("", response_model=MemoryDeleteResponse)
async def delete_all_memories(
    api_key: ApiKey,
    memory_service: MemorySvc,
) -> MemoryDeleteResponse:
    """Delete all memories for the current user.

    Args:
        api_key: API key from auth middleware (hashed for secure storage).
        memory_service: Injected memory service.

    Returns:
        Deletion confirmation.
    """
    # Hash API key to prevent plaintext storage in Qdrant/Neo4j metadata
    user_id = hash_api_key(api_key)

    await memory_service.delete_all_memories(user_id=user_id)

    return MemoryDeleteResponse(deleted=True, message="All memories deleted")
