"""Tests for memory service."""

from unittest.mock import AsyncMock

import pytest

from apps.api.protocols import MemoryProtocol
from apps.api.services.memory import MemoryService


@pytest.fixture
def mock_memory_client() -> AsyncMock:
    """Create mock memory client."""
    mock = AsyncMock(spec=MemoryProtocol)
    mock.search.return_value = [
        {
            "id": "mem_123",
            "memory": "User prefers technical explanations",
            "score": 0.95,
            "metadata": {"category": "preferences"},
        }
    ]
    mock.add.return_value = [{"id": "mem_456", "memory": "User likes Python"}]
    mock.get_all.return_value = [
        {"id": "mem_123", "memory": "User prefers technical explanations"},
        {"id": "mem_456", "memory": "User likes Python"},
    ]
    return mock


@pytest.mark.anyio
async def test_memory_service_search(mock_memory_client: AsyncMock) -> None:
    """Memory service should search and return results."""
    service = MemoryService(mock_memory_client)

    results = await service.search_memories(
        query="What are user preferences?",
        user_id="test-api-key",
        limit=10,
    )

    assert len(results) == 1
    assert results[0]["memory"] == "User prefers technical explanations"
    mock_memory_client.search.assert_called_once_with(
        query="What are user preferences?",
        user_id="test-api-key",
        limit=10,
        enable_graph=True,
    )


@pytest.mark.anyio
async def test_memory_service_add(mock_memory_client: AsyncMock) -> None:
    """Memory service should add memories."""
    service = MemoryService(mock_memory_client)

    results = await service.add_memory(
        messages="I really enjoy coding in Python",
        user_id="test-api-key",
        metadata={"source": "conversation"},
    )

    assert len(results) == 1
    mock_memory_client.add.assert_called_once_with(
        messages="I really enjoy coding in Python",
        user_id="test-api-key",
        metadata={"source": "conversation"},
        enable_graph=True,
    )


@pytest.mark.anyio
async def test_memory_service_get_all(mock_memory_client: AsyncMock) -> None:
    """Memory service should get all memories for a user."""
    service = MemoryService(mock_memory_client)

    results = await service.get_all_memories(user_id="test-api-key")

    assert len(results) == 2
    assert results[0]["memory"] == "User prefers technical explanations"
    assert results[1]["memory"] == "User likes Python"
    mock_memory_client.get_all.assert_called_once_with(user_id="test-api-key")


@pytest.mark.anyio
async def test_memory_service_delete(mock_memory_client: AsyncMock) -> None:
    """Memory service should delete a specific memory."""
    service = MemoryService(mock_memory_client)

    await service.delete_memory(memory_id="mem_123", user_id="test-api-key")

    mock_memory_client.delete.assert_called_once_with(
        memory_id="mem_123", user_id="test-api-key"
    )


@pytest.mark.anyio
async def test_memory_service_delete_all(mock_memory_client: AsyncMock) -> None:
    """Memory service should delete all memories for a user."""
    service = MemoryService(mock_memory_client)

    await service.delete_all_memories(user_id="test-api-key")

    mock_memory_client.delete_all.assert_called_once_with(user_id="test-api-key")


@pytest.mark.anyio
async def test_memory_service_format_context(mock_memory_client: AsyncMock) -> None:
    """Memory service should format memories as context string."""
    service = MemoryService(mock_memory_client)

    context = await service.format_memory_context(
        query="What are user preferences?",
        user_id="test-api-key",
    )

    assert "User prefers technical explanations" in context
    assert "RELEVANT MEMORIES" in context


@pytest.mark.anyio
async def test_memory_service_format_context_empty(
    mock_memory_client: AsyncMock,
) -> None:
    """Memory service should return empty string when no memories found."""
    mock_memory_client.search.return_value = []
    service = MemoryService(mock_memory_client)

    context = await service.format_memory_context(
        query="What are user preferences?",
        user_id="test-api-key",
    )

    assert context == ""


@pytest.mark.anyio
async def test_memory_service_search_with_graph_disabled(
    mock_memory_client: AsyncMock,
) -> None:
    """Memory service should pass enable_graph parameter correctly."""
    service = MemoryService(mock_memory_client)

    await service.search_memories(
        query="test query",
        user_id="test-api-key",
        enable_graph=False,
    )

    mock_memory_client.search.assert_called_once_with(
        query="test query",
        user_id="test-api-key",
        limit=10,
        enable_graph=False,
    )


@pytest.mark.anyio
async def test_memory_service_add_with_graph_disabled(
    mock_memory_client: AsyncMock,
) -> None:
    """Memory service should pass enable_graph parameter correctly."""
    service = MemoryService(mock_memory_client)

    await service.add_memory(
        messages="test message",
        user_id="test-api-key",
        enable_graph=False,
    )

    mock_memory_client.add.assert_called_once_with(
        messages="test message",
        user_id="test-api-key",
        metadata=None,
        enable_graph=False,
    )
