"""Tests for Mem0 memory adapter."""

import os
import sys
import types
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from apps.api.adapters.memory import Mem0MemoryAdapter, _patch_langchain_neo4j
from apps.api.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        api_key=SecretStr("test-key"),
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


def test_patch_langchain_neo4j_shifts_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """Shim should treat legacy positional database argument as database."""
    captured: dict[str, str | None] = {}

    class DummyNeo4jGraph:
        def __init__(
            self,
            url: str | None = None,
            username: str | None = None,
            password: str | None = None,
            token: str | None = None,
            database: str | None = None,
            **_kwargs: object,
        ) -> None:
            captured["url"] = url
            captured["username"] = username
            captured["password"] = password
            captured["token"] = token
            captured["database"] = database

    module = types.SimpleNamespace(Neo4jGraph=DummyNeo4jGraph)
    monkeypatch.setitem(sys.modules, "langchain_neo4j", module)

    _patch_langchain_neo4j()

    module.Neo4jGraph("bolt://localhost:54687", "neo4j", "neo4jpassword", "neo4j")

    assert captured["database"] == "neo4j"
    assert captured["token"] is None


def test_mem0_adapter_does_not_set_openai_api_key_env(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mem0 adapter should NOT set OPENAI_API_KEY (handled by lifespan startup)."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory_class.from_config.return_value = MagicMock()
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        Mem0MemoryAdapter(settings)

        # Should NOT set the env var - this is done in main.py lifespan startup
        assert os.environ.get("OPENAI_API_KEY") is None


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
        await adapter.search(
            query="What are user preferences?",
            user_id="test-api-key",
            limit=10,
            enable_graph=True,
        )


@pytest.mark.anyio
async def test_mem0_adapter_search_handles_string_results(settings: Settings) -> None:
    """Adapter should normalize non-dict search results."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.search.return_value = ["User prefers Python"]
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.search(
            query="What are user preferences?",
            user_id="test-api-key",
            limit=10,
            enable_graph=True,
        )

        assert len(results) == 1
        assert results[0]["memory"] == "User prefers Python"


@pytest.mark.anyio
async def test_mem0_adapter_search_unwraps_results(settings: Settings) -> None:
    """Adapter should unwrap structured search responses."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.search.return_value = {
            "results": [
                {"id": "mem_123", "memory": "Graph result", "score": 0.5},
            ],
            "relations": [{"from": "mem_123", "to": "mem_456"}],
        }
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.search(
            query="graph memory",
            user_id="test-api-key",
            limit=5,
            enable_graph=True,
        )

        assert len(results) == 1
        assert results[0]["id"] == "mem_123"
        assert results[0]["memory"] == "Graph result"
        assert results[0]["score"] == 0.5


@pytest.mark.anyio
async def test_mem0_adapter_search_omits_enable_graph_when_unsupported(
    settings: Settings,
) -> None:
    """Adapter should avoid enable_graph when mem0 doesn't support it."""

    class DummyMemory:
        def __init__(self) -> None:
            self.kwargs: dict[str, object] | None = None

        def search(
            self, query: str, user_id: str, agent_id: str, limit: int
        ) -> list[dict[str, object]]:
            self.kwargs = {
                "query": query,
                "user_id": user_id,
                "agent_id": agent_id,
                "limit": limit,
            }
            return []

    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        dummy = DummyMemory()
        mock_memory_class.from_config.return_value = dummy

        adapter = Mem0MemoryAdapter(settings)
        await adapter.search(
            query="What are user preferences?",
            user_id="test-api-key",
            limit=10,
            enable_graph=True,
        )

        assert dummy.kwargs is not None
        assert "enable_graph" not in dummy.kwargs


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
        expected = {
            "messages": "I really enjoy coding in Python",
            "user_id": "test-api-key",
            "agent_id": "main",
            "metadata": {"source": "conversation"},
            "enable_graph": True,
        }
        mock_memory.add.assert_called_once_with(**expected)


@pytest.mark.anyio
async def test_mem0_adapter_add_handles_wrapped_response(settings: Settings) -> None:
    """Adapter should unwrap structured add responses (memories key)."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.add.return_value = {
            "memories": [
                {"id": "mem_789", "memory": "Extracted memory", "metadata": {}},
            ],
        }
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.add(
            messages="Test conversation",
            user_id="test-api-key",
            enable_graph=False,
        )

        assert len(results) == 1
        assert results[0]["id"] == "mem_789"
        assert results[0]["memory"] == "Extracted memory"


@pytest.mark.anyio
async def test_mem0_adapter_add_handles_results_key(settings: Settings) -> None:
    """Adapter should unwrap structured add responses (results key)."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.add.return_value = {
            "results": [
                {"id": "mem_999", "memory": "Graph memory"},
            ],
        }
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.add(
            messages="Graph conversation",
            user_id="test-api-key",
            enable_graph=True,
        )

        assert len(results) == 1
        assert results[0]["id"] == "mem_999"


@pytest.mark.anyio
async def test_mem0_adapter_add_strips_none_fields(settings: Settings) -> None:
    """Adapter should strip None values from add results."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.add.return_value = [
            {
                "id": "mem_111",
                "memory": "Test",
                "metadata": None,
                "score": None,
            }
        ]
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.add(
            messages="Test",
            user_id="test-api-key",
        )

        assert len(results) == 1
        assert "metadata" not in results[0]
        assert "score" not in results[0]
        assert results[0]["id"] == "mem_111"


@pytest.mark.anyio
async def test_mem0_adapter_add_handles_string_results(settings: Settings) -> None:
    """Adapter should normalize string add results to dict format."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.add.return_value = ["Memory text 1", "Memory text 2"]
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.add(
            messages="Test",
            user_id="test-api-key",
        )

        assert len(results) == 2
        assert results[0]["memory"] == "Memory text 1"
        assert results[1]["memory"] == "Memory text 2"


@pytest.mark.anyio
async def test_mem0_adapter_add_handles_string_response(settings: Settings) -> None:
    """Adapter should normalize single string add response."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.add.return_value = "Single memory string"
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.add(
            messages="Test",
            user_id="test-api-key",
        )

        assert len(results) == 1
        assert results[0]["memory"] == "Single memory string"


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
async def test_mem0_adapter_get_all_handles_wrapped_response(
    settings: Settings,
) -> None:
    """Adapter should unwrap get_all responses containing a memories key."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.get_all.return_value = {
            "memories": [{"id": "mem_123", "memory": "Test memory"}]
        }
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.get_all(user_id="test-api-key")

        assert len(results) == 1
        assert results[0]["id"] == "mem_123"


@pytest.mark.anyio
async def test_mem0_adapter_get_all_handles_results_key(
    settings: Settings,
) -> None:
    """Adapter should unwrap get_all responses containing a results key."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.get_all.return_value = {
            "results": [{"id": "mem_789", "memory": "Another memory"}],
            "relations": [],
        }
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.get_all(user_id="test-api-key")

        assert len(results) == 1
        assert results[0]["id"] == "mem_789"


@pytest.mark.anyio
async def test_mem0_adapter_get_all_strips_none_fields(
    settings: Settings,
) -> None:
    """Adapter should drop None fields from get_all results."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.get_all.return_value = [
            {
                "id": "mem_999",
                "memory": "Test memory",
                "created_at": "2026-02-05T00:00:00Z",
                "updated_at": None,
            }
        ]
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.get_all(user_id="test-api-key")

        assert len(results) == 1
        assert results[0]["id"] == "mem_999"
        assert "updated_at" not in results[0]


@pytest.mark.anyio
async def test_mem0_adapter_delete(settings: Settings) -> None:
    """Mem0 adapter should delete a specific memory after authorization."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        # Mock get to return memory with matching user_id for authorization
        mock_memory.get.return_value = {"user_id": "test-api-key", "id": "mem_123"}
        mock_memory.delete.return_value = None
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        await adapter.delete(memory_id="mem_123", user_id="test-api-key")

        # Verify authorization check happened
        mock_memory.get.assert_called_once_with(memory_id="mem_123")
        # Verify deletion after authorization
        mock_memory.delete.assert_called_once_with(memory_id="mem_123")


@pytest.mark.anyio
async def test_mem0_adapter_delete_unauthorized(settings: Settings) -> None:
    """Mem0 adapter should reject deletion if user_id doesn't match."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        # Mock get to return memory with different user_id
        mock_memory.get.return_value = {"user_id": "other-user", "id": "mem_123"}
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)

        # Should raise ValueError for unauthorized access
        with pytest.raises(ValueError, match="Memory does not belong to this user"):
            await adapter.delete(memory_id="mem_123", user_id="test-api-key")

        # Verify get was called but delete was NOT called
        mock_memory.get.assert_called_once_with(memory_id="mem_123")
        mock_memory.delete.assert_not_called()


@pytest.mark.anyio
async def test_mem0_adapter_delete_invalid_format(settings: Settings) -> None:
    """Mem0 adapter should reject deletion if memory data is not a dict."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        # Mock get to return non-dict (e.g., None, list, or other type)
        mock_memory.get.return_value = None
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)

        # Should raise ValueError for invalid format (fail-closed)
        with pytest.raises(
            ValueError, match="Memory not found or returned unexpected format"
        ):
            await adapter.delete(memory_id="mem_123", user_id="test-api-key")

        # Verify get was called but delete was NOT called
        mock_memory.get.assert_called_once_with(memory_id="mem_123")
        mock_memory.delete.assert_not_called()


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
