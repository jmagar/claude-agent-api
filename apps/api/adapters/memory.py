"""Mem0 memory adapter implementation."""
import asyncio
from typing import cast

import structlog
from mem0 import Memory

from apps.api.config import Settings
from apps.api.protocols import MemorySearchResult

logger = structlog.get_logger(__name__)


class Mem0MemoryAdapter:
    """Adapter for Mem0 memory operations."""

    def __init__(self, settings: Settings) -> None:
        """Initialize Mem0 client with configuration."""
        self._settings = settings
        self._agent_id = settings.mem0_agent_id

        # Parse Qdrant URL
        qdrant_parts = settings.qdrant_url.replace("http://", "").replace("https://", "").split(":")
        qdrant_host = qdrant_parts[0]
        qdrant_port = int(qdrant_parts[1]) if len(qdrant_parts) > 1 else 6333

        config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "base_url": settings.llm_base_url,
                    "model": settings.llm_model,
                    "api_key": settings.llm_api_key,
                },
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "huggingface_base_url": f"{settings.tei_url}/v1",
                    "embedding_dims": settings.mem0_embedding_dims,
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
        """Search memories for a user."""
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self._memory.search(
                query=query,
                user_id=user_id,
                agent_id=self._agent_id,
                limit=limit,
                enable_graph=enable_graph,
            ),
        )

        return [
            cast(
                "MemorySearchResult",
                {
                    "id": r["id"],
                    "memory": r["memory"],
                    "score": r.get("score", 0.0),
                    "metadata": r.get("metadata", {}),
                },
            )
            for r in results
        ]

    async def add(
        self,
        messages: str,
        user_id: str,
        metadata: dict[str, object] | None = None,
        enable_graph: bool = True,
    ) -> list[dict[str, object]]:
        """Add memories from conversation."""
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self._memory.add(
                messages=messages,
                user_id=user_id,
                agent_id=self._agent_id,
                metadata=metadata or {},
                enable_graph=enable_graph,
            ),
        )
        return results

    async def get_all(
        self,
        user_id: str,
    ) -> list[dict[str, object]]:
        """Get all memories for a user."""
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self._memory.get_all(
                user_id=user_id,
                agent_id=self._agent_id,
            ),
        )
        return results

    async def delete(
        self,
        memory_id: str,
        user_id: str,
    ) -> None:
        """Delete a specific memory."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._memory.delete(
                memory_id=memory_id,
                user_id=user_id,
            ),
        )

    async def delete_all(
        self,
        user_id: str,
    ) -> None:
        """Delete all memories for a user."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._memory.delete_all(
                user_id=user_id,
            ),
        )
