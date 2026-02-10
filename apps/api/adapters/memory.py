"""Mem0 memory adapter implementation."""

import asyncio
from typing import cast

import structlog
from mem0 import Memory

from apps.api.config import Settings
from apps.api.protocols import MemorySearchResult
from apps.api.types import JsonValue

logger = structlog.get_logger(__name__)


def _patch_langchain_neo4j() -> None:
    """Shim langchain_neo4j Neo4jGraph signature for mem0 compatibility.

    Patches Neo4jGraph.__init__ to handle positional argument mismatch between
    mem0 v0.1.25 and langchain-neo4j v0.1.3. This is a runtime monkey-patch
    using setattr to avoid type checker violations.

    NOTE: This entire function is excluded from type checking due to unavoidable
    type violations when monkey-patching third-party library internals.
    """
    try:
        import langchain_neo4j
    except ImportError:
        return

    neo4j_graph = langchain_neo4j.Neo4jGraph
    # Check if already patched to avoid double-patching
    if getattr(neo4j_graph, "_mem0_positional_shim", False):
        return

    original_init = neo4j_graph.__init__

    def _shim_init(
        self,
        url=None,
        username=None,
        password=None,
        token=None,
        database=None,
        *args,
        **kwargs,
    ):
        if database is None and token is not None and password is not None:
            database = token
            token = None
        original_init(self, url, username, password, token, database, *args, **kwargs)

    # Runtime monkey-patch (unavoidable type violations)
    neo4j_graph.__init__ = _shim_init  # type: ignore[method-assign]
    neo4j_graph._mem0_positional_shim = True  # type: ignore[attr-defined]


class Mem0MemoryAdapter:
    """Adapter for Mem0 memory operations."""

    def __init__(self, settings: Settings) -> None:
        """Initialize Mem0 client with configuration.

        Note: OPENAI_API_KEY environment variable must be set before instantiation.
        This is handled in the application lifespan startup to avoid global state
        mutation in the constructor.
        """
        self._settings = settings
        self._agent_id = settings.mem0_agent_id

        _patch_langchain_neo4j()

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
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small",  # Dummy model name for TEI
                    "openai_base_url": f"{settings.tei_url}/v1",
                    "embedding_dims": settings.mem0_embedding_dims,
                    "api_key": settings.tei_api_key,
                },
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "url": settings.qdrant_url,  # Use url parameter instead of host+port
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
            **{
                "query": query,
                "user_id": user_id,
                "agent_id": self._agent_id,
                "limit": limit,
                "enable_graph": enable_graph,
            },
        )
        if isinstance(results, dict) and isinstance(results.get("results"), list):
            results = results["results"]

        normalized: list[MemorySearchResult] = []
        for index, result in enumerate(results):
            if isinstance(result, dict):
                memory_text = (
                    result.get("memory")
                    or result.get("text")
                    or result.get("content")
                    or result.get("data")
                    or ""
                )
                memory_id = result.get("id") or f"mem_{index}"
                score = float(result.get("score", 0.0))
                metadata = result.get("metadata", {})
            else:
                memory_text = str(result)
                memory_id = f"mem_{index}"
                score = 0.0
                metadata = {}

            normalized.append(
                MemorySearchResult(
                    id=str(memory_id),
                    memory=memory_text,
                    score=score,
                    metadata=metadata,
                )
            )

        return normalized

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
            **{
                "messages": messages,
                "user_id": user_id,
                "agent_id": self._agent_id,
                "metadata": metadata or {},
                "enable_graph": enable_graph,
            },
        )
        # Normalize response format (defensive against Mem0 API changes)
        if isinstance(results, dict):
            # Unwrap nested results
            if "memories" in results:
                results = cast("object", results["memories"])
            elif "results" in results and isinstance(results["results"], list):
                results = cast("object", results["results"])

        # Clean None values from dict responses
        if isinstance(results, list):
            cleaned: list[dict[str, JsonValue]] = []
            for item in results:
                if isinstance(item, dict):
                    # Remove None values, cast dict values to JsonValue
                    cleaned_item: dict[str, JsonValue] = {}
                    for k, v in item.items():
                        if v is not None:
                            cleaned_item[cast("str", k)] = cast("JsonValue", v)
                    cleaned.append(cleaned_item)
                elif isinstance(item, str):
                    # Handle string responses (convert to dict)
                    cleaned.append({"memory": item})
            return cleaned

        # Fallback for unexpected formats
        if isinstance(results, str):
            return [{"memory": results}]

        return []

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
        if isinstance(results, dict):
            if "memories" in results:
                results = cast("object", results["memories"])
            elif "results" in results and isinstance(results["results"], list):
                results = cast("object", results["results"])

        if isinstance(results, list):
            cleaned: list[dict[str, JsonValue]] = []
            for item in results:
                if not isinstance(item, dict):
                    continue
                # Remove None values, cast dict values to JsonValue
                cleaned_item: dict[str, JsonValue] = {}
                for k, v in item.items():
                    if v is not None:
                        cleaned_item[cast("str", k)] = cast("JsonValue", v)
                cleaned.append(cleaned_item)
            return cleaned

        return []

    async def delete(
        self,
        memory_id: str,
        user_id: str,
    ) -> None:
        """Delete a specific memory.

        Removes a memory from both vector and graph stores. Verifies
        ownership before deletion to prevent unauthorized access.

        Args:
            memory_id: Memory identifier to delete.
            user_id: User identifier for authorization check.

        Raises:
            ValueError: If memory does not belong to user_id or doesn't exist.
        """
        # Fetch memory to verify ownership before deletion
        memory_data = await asyncio.to_thread(
            self._memory.get,
            memory_id=memory_id,
        )

        # Fail-closed: reject if not a dict (prevents authorization bypass)
        if not isinstance(memory_data, dict):
            msg = "Memory not found or returned unexpected format"
            raise ValueError(msg)

        # Verify ownership (Mem0 stores user_id in metadata or directly)
        stored_user_id = memory_data.get("user_id")
        if stored_user_id != user_id:
            msg = "Memory does not belong to this user"
            raise ValueError(msg)

        # Authorized - proceed with deletion
        await asyncio.to_thread(
            self._memory.delete,
            memory_id=memory_id,
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
