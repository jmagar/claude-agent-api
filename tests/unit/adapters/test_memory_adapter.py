"""Tests for Mem0 memory adapter."""

from unittest.mock import MagicMock, patch

import pytest

from apps.api.adapters.memory import Mem0MemoryAdapter
from apps.api.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        api_key="test-key",
        llm_api_key="test-key",
        llm_base_url="https://cli-api.tootie.tv/v1",
        llm_model="gemini-3-flash-preview",
        neo4j_url="bolt://localhost:54687",
        neo4j_username="neo4j",
        neo4j_password="testpass",
        neo4j_database="neo4j",
        qdrant_url="http://localhost:53333",
        tei_url="http://100.74.16.82:52000",
        mem0_collection_name="mem0_memories",
        mem0_embedding_dims=1024,
        mem0_agent_id="main",
    )


@pytest.mark.anyio
async def test_mem0_adapter_search(settings: Settings) -> None:
    """Mem0 adapter should search memories for a user."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.search.return_value = [
            {
                "id": "mem_123",
                "memory": "User prefers technical explanations",
                "score": 0.95,
                "metadata": {"category": "preferences"},
            }
        ]
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.search(
            query="What are user preferences?",
            user_id="test-api-key",
            limit=10,
            enable_graph=True,
        )

        assert len(results) == 1
        assert results[0]["id"] == "mem_123"
        assert results[0]["memory"] == "User prefers technical explanations"
        assert results[0]["score"] == 0.95
        mock_memory.search.assert_called_once_with(
            query="What are user preferences?",
            user_id="test-api-key",
            agent_id="main",
            limit=10,
            enable_graph=True,
        )


@pytest.mark.anyio
async def test_mem0_adapter_add(settings: Settings) -> None:
    """Mem0 adapter should add memories from conversation."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.add.return_value = [
            {"id": "mem_456", "memory": "User likes Python"}
        ]
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.add(
            messages="I really enjoy coding in Python",
            user_id="test-api-key",
            metadata={"source": "conversation"},
            enable_graph=True,
        )

        assert len(results) == 1
        assert results[0]["id"] == "mem_456"
        mock_memory.add.assert_called_once_with(
            messages="I really enjoy coding in Python",
            user_id="test-api-key",
            agent_id="main",
            metadata={"source": "conversation"},
            enable_graph=True,
        )


@pytest.mark.anyio
async def test_mem0_adapter_get_all(settings: Settings) -> None:
    """Mem0 adapter should retrieve all memories for a user."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.get_all.return_value = [{"id": "mem_123", "memory": "Test memory"}]
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.get_all(user_id="test-api-key")

        assert len(results) == 1
        assert results[0]["id"] == "mem_123"
        mock_memory.get_all.assert_called_once_with(
            user_id="test-api-key",
            agent_id="main",
        )


@pytest.mark.anyio
async def test_mem0_adapter_delete(settings: Settings) -> None:
    """Mem0 adapter should delete a specific memory."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.delete.return_value = None
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        await adapter.delete(memory_id="mem_123", user_id="test-api-key")

        mock_memory.delete.assert_called_once_with(
            memory_id="mem_123",
            user_id="test-api-key",
        )


@pytest.mark.anyio
async def test_mem0_adapter_delete_all(settings: Settings) -> None:
    """Mem0 adapter should delete all memories for a user."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.delete_all.return_value = None
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        await adapter.delete_all(user_id="test-api-key")

        mock_memory.delete_all.assert_called_once_with(
            user_id="test-api-key",
        )
