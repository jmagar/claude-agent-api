"""Integration tests for memory routes."""

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.fixture
def mock_memory_service(async_client: "AsyncClient") -> AsyncMock:
    """Create mock memory service and inject it as singleton (M-13)."""
    from fastapi import Request

    from apps.api.dependencies import get_app_state

    # Create mock
    mock = AsyncMock()
    mock.search_memories.return_value = [
        {
            "id": "mem_123",
            "memory": "User prefers technical explanations",
            "score": 0.95,
            "metadata": {"category": "preferences"},
        }
    ]
    mock.add_memory.return_value = [{"id": "mem_456", "memory": "User likes Python"}]
    mock.get_all_memories.return_value = [
        {"id": "mem_123", "memory": "User prefers technical explanations"},
        {"id": "mem_456", "memory": "User likes Python"},
    ]

    # Get app state and set singleton
    request = Request(scope={"type": "http", "app": async_client._transport.app})  # type: ignore[arg-type]
    app_state = get_app_state(request)
    app_state.memory_service = mock

    return mock


@pytest.mark.anyio
async def test_search_memories(
    async_client: "AsyncClient",
    auth_headers: dict[str, str],
    mock_memory_service: AsyncMock,
) -> None:
    """POST /api/v1/memories/search should search memories."""
    response = await async_client.post(
        "/api/v1/memories/search",
        json={"query": "What are user preferences?", "limit": 10},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["memory"] == "User prefers technical explanations"


@pytest.mark.anyio
async def test_add_memory(
    async_client: "AsyncClient",
    auth_headers: dict[str, str],
    mock_memory_service: AsyncMock,
) -> None:
    """POST /api/v1/memories should add a memory."""
    response = await async_client.post(
        "/api/v1/memories",
        json={
            "messages": "I enjoy coding in Python",
            "metadata": {"source": "conversation"},
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["memories"]) == 1


@pytest.mark.anyio
async def test_list_memories(
    async_client: "AsyncClient",
    auth_headers: dict[str, str],
    mock_memory_service: AsyncMock,
) -> None:
    """GET /api/v1/memories should list all memories for user."""
    response = await async_client.get(
        "/api/v1/memories",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["memories"]) == 2


@pytest.mark.anyio
async def test_delete_memory(
    async_client: "AsyncClient",
    auth_headers: dict[str, str],
    mock_memory_service: AsyncMock,
) -> None:
    """DELETE /api/v1/memories/{memory_id} should delete a memory."""
    response = await async_client.delete(
        "/api/v1/memories/mem_123",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True


@pytest.mark.anyio
async def test_delete_all_memories(
    async_client: "AsyncClient",
    auth_headers: dict[str, str],
    mock_memory_service: AsyncMock,
) -> None:
    """DELETE /api/v1/memories should delete all memories for user."""
    response = await async_client.delete(
        "/api/v1/memories",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True
