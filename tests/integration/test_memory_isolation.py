"""Integration tests for multi-tenant memory isolation.

Requirements:
- Neo4j must be running (docker compose up -d neo4j)
- Qdrant must be accessible at localhost:53333
- TEI must be accessible at 100.74.16.82:52000

These tests verify that API keys cannot access each other's memories
through the Mem0 user_id scoping mechanism.
"""

import os
import socket
from urllib.parse import urlparse

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.config import get_settings
from apps.api.main import app


def _set_api_key(api_key: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set API_KEY env var and clear cached settings."""
    monkeypatch.setenv("API_KEY", api_key)
    get_settings.cache_clear()


def _is_truthy(value: str | None) -> bool:
    """Return True when an env var is set to a truthy value."""
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _can_connect(host: str, port: int, timeout: float = 1.0) -> bool:
    """Return True if a TCP connection can be established."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _service_available(url: str) -> bool:
    """Return True if the host:port in the URL is reachable."""
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host:
        return False
    return _can_connect(host, port)


def _neo4j_available(neo4j_url: str) -> bool:
    """Return True if Neo4j bolt endpoint is reachable."""
    parsed = urlparse(neo4j_url)
    host = parsed.hostname
    port = parsed.port or 7687
    if not host:
        return False
    return _can_connect(host, port)


def _mem0_dependencies_available() -> bool:
    """Check that TEI, Qdrant, and Neo4j are reachable."""
    if not _is_truthy(os.environ.get("RUN_MEM0_INTEGRATION")):
        return False
    settings = get_settings()
    return (
        _service_available(settings.tei_url)
        and _service_available(settings.qdrant_url)
        and _neo4j_available(settings.neo4j_url)
    )


@pytest.mark.anyio
@pytest.mark.integration
async def test_memories_isolated_by_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Memories should be isolated between different API keys."""
    if not _mem0_dependencies_available():
        pytest.skip("Mem0 dependencies unavailable (TEI/Qdrant/Neo4j)")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Clean up any existing memories for test users
        _set_api_key("test-user-a", monkeypatch)
        await client.delete(
            "/api/v1/memories",
            headers={"X-API-Key": "test-user-a"},
        )
        _set_api_key("test-user-b", monkeypatch)
        await client.delete(
            "/api/v1/memories",
            headers={"X-API-Key": "test-user-b"},
        )

        # User A adds a memory about Python
        _set_api_key("test-user-a", monkeypatch)
        response_a = await client.post(
            "/api/v1/memories",
            json={"messages": "User A prefers Python for backend development"},
            headers={"X-API-Key": "test-user-a"},
        )
        assert response_a.status_code == 201

        # User B adds a memory about JavaScript
        _set_api_key("test-user-b", monkeypatch)
        response_b = await client.post(
            "/api/v1/memories",
            json={"messages": "User B prefers JavaScript for frontend development"},
            headers={"X-API-Key": "test-user-b"},
        )
        assert response_b.status_code == 201

        # User A searches for programming preferences
        _set_api_key("test-user-a", monkeypatch)
        search_a = await client.post(
            "/api/v1/memories/search",
            json={"query": "programming language preferences"},
            headers={"X-API-Key": "test-user-a"},
        )
        assert search_a.status_code == 200
        results_a = search_a.json()["results"]

        # Verify User A only sees their own memories
        assert len(results_a) > 0
        assert all(
            "Python" in r["memory"] or "backend" in r["memory"] for r in results_a
        )
        assert not any("JavaScript" in r["memory"] for r in results_a)

        # User B searches for programming preferences
        _set_api_key("test-user-b", monkeypatch)
        search_b = await client.post(
            "/api/v1/memories/search",
            json={"query": "programming language preferences"},
            headers={"X-API-Key": "test-user-b"},
        )
        assert search_b.status_code == 200
        results_b = search_b.json()["results"]

        # Verify User B only sees their own memories
        assert len(results_b) > 0
        assert all(
            "JavaScript" in r["memory"] or "frontend" in r["memory"] for r in results_b
        )
        assert not any("Python" in r["memory"] for r in results_b)


@pytest.mark.anyio
@pytest.mark.integration
async def test_user_cannot_delete_other_user_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Users should not be able to delete other users' memories."""
    if not _mem0_dependencies_available():
        pytest.skip("Mem0 dependencies unavailable (TEI/Qdrant/Neo4j)")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # User A adds a memory
        _set_api_key("test-user-a", monkeypatch)
        response_a = await client.post(
            "/api/v1/memories",
            json={"messages": "User A secret information"},
            headers={"X-API-Key": "test-user-a"},
        )
        assert response_a.status_code == 201
        memory_id = response_a.json()["memories"][0]["id"]

        # User B tries to delete User A's memory
        # (This should either fail or silently do nothing)
        _set_api_key("test-user-b", monkeypatch)
        await client.delete(
            f"/api/v1/memories/{memory_id}",
            headers={"X-API-Key": "test-user-b"},
        )

        # Verify User A's memory still exists
        _set_api_key("test-user-a", monkeypatch)
        list_a = await client.get(
            "/api/v1/memories",
            headers={"X-API-Key": "test-user-a"},
        )
        memories_a = list_a.json()["memories"]
        memory_ids_a = [m["id"] for m in memories_a]

        # Memory should still exist for User A
        assert memory_id in memory_ids_a
