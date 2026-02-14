"""Memory management API routes."""

from __future__ import annotations

import hashlib
import time
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


def _validate_memory_record(record: dict[str, JsonValue]) -> MemoryRecordDict:
    """Validate and convert memory service response to MemoryRecordDict.

    Args:
        record: Raw memory record from service.

    Returns:
        Validated MemoryRecordDict with required fields.

    Raises:
        ValueError: If required fields are missing or invalid.
    """
    memory_value = record.get("memory")
    if not isinstance(memory_value, str):
        raise ValueError("Memory record missing required 'memory' field")

    record_id = record.get("id")
    if isinstance(record_id, str) and record_id:
        memory_id = record_id
    else:
        # Include timestamp in fallback ID to prevent collisions when same content is added multiple times
        timestamp = str(int(time.time() * 1000000))  # microsecond precision
        content_hash = hashlib.sha256(memory_value.encode()).hexdigest()[:12]
        memory_id = f"mem_{content_hash}_{timestamp}"

    # Build result with required fields
    result: MemoryRecordDict = {
        "id": memory_id,
        "memory": memory_value,
    }

    # Add optional fields if present
    if "hash" in record and isinstance(record["hash"], str):
        result["hash"] = str(record["hash"])
    if "created_at" in record and isinstance(record["created_at"], str):
        result["created_at"] = str(record["created_at"])
    if "updated_at" in record and isinstance(record["updated_at"], str):
        result["updated_at"] = str(record["updated_at"])
    if "user_id" in record and isinstance(record["user_id"], str):
        result["user_id"] = str(record["user_id"])
    if "agent_id" in record and isinstance(record["agent_id"], str):
        result["agent_id"] = str(record["agent_id"])
    if "metadata" in record and isinstance(record["metadata"], dict):
        result["metadata"] = cast("dict[str, object]", record["metadata"])

    return result


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
                metadata=(
                    cast("dict[str, object]", r.get("metadata"))
                    if isinstance(r.get("metadata"), dict)
                    else {}
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

    # Cast Pydantic dict[str, object] to JsonValue for service layer type safety
    metadata = cast("dict[str, JsonValue] | None", request.metadata)

    results = await memory_service.add_memory(
        messages=request.messages,
        user_id=user_id,
        metadata=metadata,
        enable_graph=request.enable_graph,
    )

    # Validate records before returning to ensure type safety
    validated_results = [_validate_memory_record(record) for record in results]

    return MemoryAddResponse(memories=validated_results, count=len(validated_results))


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

    # Validate records before returning to ensure type safety
    validated_memories = [_validate_memory_record(record) for record in memories]

    return MemoryListResponse(
        memories=validated_memories, count=len(validated_memories)
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
