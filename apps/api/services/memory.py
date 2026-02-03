"""Memory service for managing conversation memories."""

import structlog

from apps.api.protocols import MemoryProtocol, MemorySearchResult
from apps.api.types import JsonValue

logger = structlog.get_logger(__name__)


class MemoryService:
    """Service for memory operations.

    This service provides a business logic layer between API routes and the
    MemoryProtocol adapter. It wraps memory operations with convenience methods
    and handles formatting of memories for prompt injection.

    Args:
        memory_client: MemoryProtocol implementation for memory operations.
    """

    def __init__(self, memory_client: MemoryProtocol) -> None:
        """Initialize memory service.

        Args:
            memory_client: MemoryProtocol implementation for memory operations.
        """
        self._client = memory_client

    async def search_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        enable_graph: bool = True,
    ) -> list[MemorySearchResult]:
        """Search memories for a user.

        Args:
            query: Search query string.
            user_id: User identifier for multi-tenant isolation.
            limit: Maximum results to return.
            enable_graph: Include graph context in search.

        Returns:
            List of memory search results with id, memory, score, and metadata.
        """
        return await self._client.search(
            query=query,
            user_id=user_id,
            limit=limit,
            enable_graph=enable_graph,
        )

    async def add_memory(
        self,
        messages: str,
        user_id: str,
        metadata: dict[str, JsonValue] | None = None,
        enable_graph: bool = True,
    ) -> list[dict[str, JsonValue]]:
        """Add memories from conversation.

        Args:
            messages: Content to extract memories from.
            user_id: User identifier for multi-tenant isolation.
            metadata: Optional metadata to attach to memories.
            enable_graph: Enable graph memory extraction.

        Returns:
            List of created memory records with id and memory text.
        """
        return await self._client.add(
            messages=messages,
            user_id=user_id,
            metadata=metadata,
            enable_graph=enable_graph,
        )

    async def get_all_memories(
        self,
        user_id: str,
    ) -> list[dict[str, JsonValue]]:
        """Get all memories for a user.

        Args:
            user_id: User identifier for multi-tenant isolation.

        Returns:
            List of all memories for the user.
        """
        return await self._client.get_all(user_id=user_id)

    async def delete_memory(
        self,
        memory_id: str,
        user_id: str,
    ) -> None:
        """Delete a specific memory.

        Args:
            memory_id: Memory identifier to delete.
            user_id: User identifier for authorization.
        """
        await self._client.delete(memory_id=memory_id, user_id=user_id)

    async def delete_all_memories(
        self,
        user_id: str,
    ) -> None:
        """Delete all memories for a user.

        Args:
            user_id: User identifier for authorization.
        """
        await self._client.delete_all(user_id=user_id)

    async def format_memory_context(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
    ) -> str:
        """Format memories as context string for injection into prompts.

        Searches for relevant memories and formats them as a structured text
        block that can be prepended to user prompts to provide context.

        Args:
            query: Search query string.
            user_id: User identifier for multi-tenant isolation.
            limit: Maximum memories to include.

        Returns:
            Formatted context string with memories, or empty string if none found.
        """
        memories = await self.search_memories(
            query=query,
            user_id=user_id,
            limit=limit,
        )

        if not memories:
            return ""

        context_parts = ["RELEVANT MEMORIES:"]
        for mem in memories:
            context_parts.append(f"- {mem['memory']}")

        return "\n".join(context_parts)
