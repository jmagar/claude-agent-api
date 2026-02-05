"""Mem0 memory adapter implementation."""

import asyncio

import structlog
from mem0 import Memory

from apps.api.config import Settings
from apps.api.protocols import MemorySearchResult
from apps.api.types import JsonValue

logger = structlog.get_logger(__name__)


class Mem0MemoryAdapter:
    """Adapter for Mem0 memory operations."""

    def __init__(self, settings: Settings) -> None:
        """Initialize Mem0 client with configuration."""
        self._settings = settings
        self._agent_id = settings.mem0_agent_id

        # Parse Qdrant URL
        qdrant_parts = (
            settings.qdrant_url.replace("http://", "")
            .replace("https://", "")
            .split(":")
        )
        qdrant_host = qdrant_parts[0]
        qdrant_port = int(qdrant_parts[1]) if len(qdrant_parts) > 1 else 6333

        config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "openai_base_url": settings.llm_base_url,
                    "model": settings.llm_model,
                    "api_key": settings.llm_api_key,
                },
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "huggingface_base_url": f"{settings.tei_url}/v1",
                    "embedding_dims": settings.mem0_embedding_dims,
                    "api_key": settings.tei_api_key,
                },
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": qdrant_host,
                    "port": qdrant_port,
                    "collection_name": settings.mem0_collection_name,
                    "embedding_model_dims": settings.mem0_embedding_dims,
                    "on_disk": True,
                },
            },
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": settings.neo4j_url,
                    "username": settings.neo4j_username,
                    "password": settings.neo4j_password,
                    "database": settings.neo4j_database,
                },
            },
            "version": "v1.1",
        }

        self._memory = Memory.from_config(config)
        logger.info("mem0_client_initialized", config_version="v1.1")

    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        enable_graph: bool = True,
    ) -> list[MemorySearchResult]:
        """Search memories for a user.

        Performs semantic search across user's memory store with optional
        graph context enhancement. Results are scoped to user_id for
        multi-tenant isolation.

        Args:
            query: Search query string for semantic matching.
            user_id: User identifier for multi-tenant isolation.
            limit: Maximum number of results to return.
            enable_graph: Include graph relationships in search.
                Adds ~100-200ms latency when enabled.

        Returns:
            List of memory search results sorted by relevance score.
        """
        results = await asyncio.to_thread(
            self._memory.search,
            query=query,
            user_id=user_id,
            agent_id=self._agent_id,
            limit=limit,
            enable_graph=enable_graph,
        )

        return [
            MemorySearchResult(
                id=r["id"],
                memory=r["memory"],
                score=r.get("score", 0.0),
                metadata=r.get("metadata", {}),
            )
            for r in results
        ]

    async def add(
        self,
        messages: str,
        user_id: str,
        metadata: dict[str, JsonValue] | None = None,
        enable_graph: bool = True,
    ) -> list[dict[str, JsonValue]]:
        """Add memories from conversation.

        Extracts and stores memories from conversation text. Uses LLM to
        identify meaningful information for future retrieval.

        Args:
            messages: Conversation content to extract memories from.
            user_id: User identifier for multi-tenant isolation.
            metadata: Optional metadata to attach to extracted memories.
            enable_graph: Enable graph-based entity/relationship extraction.
                Adds ~100-200ms latency when enabled.

        Returns:
            List of created memory records with IDs and content.
        """
        results = await asyncio.to_thread(
            self._memory.add,
            messages=messages,
            user_id=user_id,
            agent_id=self._agent_id,
            metadata=metadata or {},
            enable_graph=enable_graph,
        )
        return results

    async def get_all(
        self,
        user_id: str,
    ) -> list[dict[str, JsonValue]]:
        """Get all memories for a user.

        Retrieves all stored memories without filtering by relevance.
        Results are scoped to user_id for multi-tenant isolation.

        Args:
            user_id: User identifier for multi-tenant isolation.

        Returns:
            List of all memory records for the user.
        """
        results = await asyncio.to_thread(
            self._memory.get_all,
            user_id=user_id,
            agent_id=self._agent_id,
        )
        return results

    async def delete(
        self,
        memory_id: str,
        user_id: str,
    ) -> None:
        """Delete a specific memory.

        Removes a memory from both vector and graph stores. Requires
        user_id for authorization verification.

        Args:
            memory_id: Memory identifier to delete.
            user_id: User identifier for authorization check.

        Raises:
            ValueError: If memory does not belong to user_id.
        """
        await asyncio.to_thread(
            self._memory.delete,
            memory_id=memory_id,
            user_id=user_id,
        )

    async def delete_all(
        self,
        user_id: str,
    ) -> None:
        """Delete all memories for a user.

        Removes all memories from both vector and graph stores for the
        specified user. This operation is irreversible.

        Args:
            user_id: User identifier whose memories should be deleted.
        """
        await asyncio.to_thread(
            self._memory.delete_all,
            user_id=user_id,
        )
