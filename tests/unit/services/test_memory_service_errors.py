"""Unit tests for memory service error handling."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.services.memory import MemoryService


class TestNetworkErrors:
    """Tests for network timeout and connection errors."""

    @pytest.mark.anyio
    async def test_search_network_timeout(self) -> None:
        """Test that search handles network timeout to Qdrant gracefully."""
        # Create mock memory client that raises timeout
        mock_client = MagicMock()
        mock_client.search = AsyncMock(
            side_effect=TimeoutError("Connection timeout")
        )

        service = MemoryService(mock_client)

        # Verify timeout is propagated (caller should handle)
        with pytest.raises(asyncio.TimeoutError):
            await service.search_memories(
                query="test query",
                user_id="user-123",
                limit=10,
            )

    @pytest.mark.anyio
    async def test_add_memory_network_timeout(self) -> None:
        """Test that add_memory handles network timeout gracefully."""
        # Create mock client that times out
        mock_client = MagicMock()
        mock_client.add = AsyncMock(side_effect=TimeoutError("Neo4j timeout"))

        service = MemoryService(mock_client)

        # Verify timeout is propagated
        with pytest.raises(asyncio.TimeoutError):
            await service.add_memory(
                messages="User likes Python programming",
                user_id="user-123",
            )

    @pytest.mark.anyio
    async def test_search_connection_refused(self) -> None:
        """Test that search handles connection refused to Qdrant."""
        # Simulate connection refused error
        mock_client = MagicMock()
        mock_client.search = AsyncMock(
            side_effect=ConnectionRefusedError("Qdrant not available")
        )

        service = MemoryService(mock_client)

        # Verify error is propagated
        with pytest.raises(ConnectionRefusedError):
            await service.search_memories(
                query="test query",
                user_id="user-123",
            )

    @pytest.mark.anyio
    async def test_get_all_network_error(self) -> None:
        """Test that get_all handles network errors."""
        mock_client = MagicMock()
        mock_client.get_all = AsyncMock(side_effect=OSError("Network unreachable"))

        service = MemoryService(mock_client)

        # Verify error is propagated
        with pytest.raises(OSError):
            await service.get_all_memories(user_id="user-123")


class TestIdempotentOperations:
    """Tests for idempotent delete operations."""

    @pytest.mark.anyio
    async def test_delete_nonexistent_memory_succeeds(self) -> None:
        """Test that deleting nonexistent memory is idempotent (no error)."""
        # Mock client that completes successfully even for nonexistent ID
        mock_client = MagicMock()
        mock_client.delete = AsyncMock(return_value=None)

        service = MemoryService(mock_client)

        # Should not raise error
        await service.delete_memory(
            memory_id="nonexistent-id",
            user_id="user-123",
        )

        # Verify delete was called
        mock_client.delete.assert_called_once_with(
            memory_id="nonexistent-id",
            user_id="user-123",
        )

    @pytest.mark.anyio
    async def test_delete_memory_not_found_error(self) -> None:
        """Test that delete handles 'not found' errors gracefully."""
        # Mock client that raises KeyError for nonexistent memory
        mock_client = MagicMock()
        mock_client.delete = AsyncMock(side_effect=KeyError("Memory not found"))

        service = MemoryService(mock_client)

        # Verify error is propagated (caller decides how to handle)
        with pytest.raises(KeyError):
            await service.delete_memory(
                memory_id="nonexistent-id",
                user_id="user-123",
            )

    @pytest.mark.anyio
    async def test_delete_all_empty_user(self) -> None:
        """Test that delete_all succeeds even when user has no memories."""
        # Mock client that completes successfully
        mock_client = MagicMock()
        mock_client.delete_all = AsyncMock(return_value=None)

        service = MemoryService(mock_client)

        # Should not raise error
        await service.delete_all_memories(user_id="empty-user")

        # Verify delete_all was called
        mock_client.delete_all.assert_called_once_with(user_id="empty-user")


class TestGracefulDegradation:
    """Tests for graceful degradation when memory operations fail."""

    @pytest.mark.anyio
    async def test_format_memory_context_handles_empty_results(self) -> None:
        """Test that format_memory_context returns empty string when no memories found."""
        # Mock client that returns empty list
        mock_client = MagicMock()
        mock_client.search = AsyncMock(return_value=[])

        service = MemoryService(mock_client)

        # Should return empty string (not raise error)
        context = await service.format_memory_context(
            query="test query",
            user_id="user-123",
            limit=5,
        )

        assert context == ""

    @pytest.mark.anyio
    async def test_format_memory_context_handles_search_failure(self) -> None:
        """Test that format_memory_context propagates search failures."""
        # Mock client that fails
        mock_client = MagicMock()
        mock_client.search = AsyncMock(side_effect=RuntimeError("Qdrant error"))

        service = MemoryService(mock_client)

        # Error should propagate (caller handles graceful degradation)
        with pytest.raises(RuntimeError):
            await service.format_memory_context(
                query="test query",
                user_id="user-123",
            )

    @pytest.mark.anyio
    async def test_search_partial_results_on_graph_error(self) -> None:
        """Test that search can return partial results if graph lookup fails."""
        # Mock client that returns results despite graph issues
        mock_client = MagicMock()
        mock_client.search = AsyncMock(
            return_value=[
                {
                    "id": "mem-1",
                    "memory": "User prefers Python",
                    "score": 0.9,
                    "metadata": {"source": "vector_only"},
                }
            ]
        )

        service = MemoryService(mock_client)

        # Should succeed with partial results
        results = await service.search_memories(
            query="programming preferences",
            user_id="user-123",
            enable_graph=True,
        )

        assert len(results) == 1
        assert results[0]["memory"] == "User prefers Python"


class TestCorruptedData:
    """Tests for handling corrupted or invalid data from Mem0."""

    @pytest.mark.anyio
    async def test_search_handles_malformed_response(self) -> None:
        """Test that search handles malformed response structure."""
        # Mock client that returns data with missing required fields
        mock_client = MagicMock()
        mock_client.search = AsyncMock(
            return_value=[
                {"id": "mem-1"},  # Missing 'memory' field
            ]
        )

        service = MemoryService(mock_client)

        # Should return results as-is (validation happens at schema layer)
        results = await service.search_memories(
            query="test",
            user_id="user-123",
        )

        assert len(results) == 1
        assert results[0]["id"] == "mem-1"

    @pytest.mark.anyio
    async def test_add_memory_handles_extraction_failure(self) -> None:
        """Test that add_memory handles LLM extraction failures."""
        # Mock client that returns empty list (no memories extracted)
        mock_client = MagicMock()
        mock_client.add = AsyncMock(return_value=[])

        service = MemoryService(mock_client)

        # Should return empty list (not raise error)
        results = await service.add_memory(
            messages="Gibberish text !@#$%",
            user_id="user-123",
        )

        assert results == []

    @pytest.mark.anyio
    async def test_get_all_handles_corrupted_metadata(self) -> None:
        """Test that get_all handles memories with corrupted metadata."""
        # Mock client that returns memories with various metadata issues
        mock_client = MagicMock()
        mock_client.get_all = AsyncMock(
            return_value=[
                {
                    "id": "mem-1",
                    "memory": "Valid memory",
                    "metadata": None,  # Null metadata
                },
                {
                    "id": "mem-2",
                    "memory": "Another memory",
                    "metadata": {"invalid": float("inf")},  # Invalid JSON value
                },
            ]
        )

        service = MemoryService(mock_client)

        # Should return results as-is (validation at API boundary)
        results = await service.get_all_memories(user_id="user-123")

        assert len(results) == 2
        assert results[0]["id"] == "mem-1"
        assert results[1]["id"] == "mem-2"

    @pytest.mark.anyio
    async def test_format_memory_context_handles_missing_memory_field(self) -> None:
        """Test that format_memory_context handles memories missing 'memory' field."""
        # Mock client that returns malformed results
        mock_client = MagicMock()
        mock_client.search = AsyncMock(
            return_value=[
                {"id": "mem-1", "score": 0.9},  # Missing 'memory' field
            ]
        )

        service = MemoryService(mock_client)

        # Should raise KeyError when trying to access missing field
        with pytest.raises(KeyError):
            await service.format_memory_context(
                query="test",
                user_id="user-123",
            )


class TestConcurrentOperations:
    """Tests for concurrent memory operations."""

    @pytest.mark.anyio
    async def test_concurrent_searches(self) -> None:
        """Test that concurrent searches don't interfere with each other."""
        # Mock client with async behavior
        mock_client = MagicMock()

        async def mock_search(query: str, user_id: str, limit: int, enable_graph: bool):
            await asyncio.sleep(0.01)  # Simulate network delay
            return [
                {
                    "id": f"mem-{query}",
                    "memory": f"Result for {query}",
                    "score": 0.9,
                    "metadata": {},
                }
            ]

        mock_client.search = mock_search

        service = MemoryService(mock_client)

        # Execute multiple searches concurrently
        tasks = [
            service.search_memories(f"query-{i}", "user-123", 10) for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        # Verify all searches completed successfully
        assert len(results) == 5
        for i, result in enumerate(results):
            assert len(result) == 1
            assert result[0]["memory"] == f"Result for query-{i}"

    @pytest.mark.anyio
    async def test_concurrent_add_and_search(self) -> None:
        """Test that add and search operations can run concurrently."""
        mock_client = MagicMock()

        async def mock_add(messages: str, user_id: str, metadata, enable_graph: bool):
            await asyncio.sleep(0.01)
            return [{"id": "mem-new", "memory": messages}]

        async def mock_search(query: str, user_id: str, limit: int, enable_graph: bool):
            await asyncio.sleep(0.01)
            return [{"id": "mem-1", "memory": "Existing", "score": 0.9, "metadata": {}}]

        mock_client.add = mock_add
        mock_client.search = mock_search

        service = MemoryService(mock_client)

        # Run add and search concurrently
        add_task = service.add_memory("New memory", "user-123")
        search_task = service.search_memories("query", "user-123")

        add_result, search_result = await asyncio.gather(add_task, search_task)

        # Both should succeed
        assert len(add_result) == 1
        assert len(search_result) == 1

    @pytest.mark.anyio
    async def test_concurrent_delete_operations(self) -> None:
        """Test that concurrent deletes are handled safely."""
        mock_client = MagicMock()

        call_count = 0

        async def mock_delete(memory_id: str, user_id: str):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            # First call succeeds, subsequent calls for same ID could fail
            if call_count > 1 and memory_id == "mem-1":
                raise KeyError("Already deleted")

        mock_client.delete = mock_delete

        service = MemoryService(mock_client)

        # Try to delete same memory twice concurrently
        task1 = service.delete_memory("mem-1", "user-123")
        task2 = service.delete_memory("mem-1", "user-123")

        # One should succeed, one should fail
        results = await asyncio.gather(task1, task2, return_exceptions=True)

        # At least one should be an exception
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) >= 1
        assert isinstance(exceptions[0], KeyError)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.anyio
    async def test_search_with_empty_query(self) -> None:
        """Test that search handles empty query string."""
        mock_client = MagicMock()
        mock_client.search = AsyncMock(return_value=[])

        service = MemoryService(mock_client)

        # Should not raise error
        results = await service.search_memories(
            query="",
            user_id="user-123",
        )

        assert results == []

    @pytest.mark.anyio
    async def test_search_with_very_long_query(self) -> None:
        """Test that search handles very long query strings."""
        mock_client = MagicMock()
        mock_client.search = AsyncMock(return_value=[])

        service = MemoryService(mock_client)

        # Very long query (10KB)
        long_query = "a" * 10000

        # Should not raise error (protocol handles limits)
        results = await service.search_memories(
            query=long_query,
            user_id="user-123",
        )

        assert results == []

    @pytest.mark.anyio
    async def test_add_memory_with_empty_message(self) -> None:
        """Test that add_memory handles empty message."""
        mock_client = MagicMock()
        mock_client.add = AsyncMock(return_value=[])

        service = MemoryService(mock_client)

        # Should return empty list
        results = await service.add_memory(
            messages="",
            user_id="user-123",
        )

        assert results == []

    @pytest.mark.anyio
    async def test_delete_with_special_characters_in_id(self) -> None:
        """Test that delete handles memory IDs with special characters."""
        mock_client = MagicMock()
        mock_client.delete = AsyncMock(return_value=None)

        service = MemoryService(mock_client)

        # IDs with special characters
        special_ids = [
            "mem-123-abc",
            "mem_with_underscore",
            "mem:with:colons",
            "mem/with/slashes",
        ]

        for memory_id in special_ids:
            await service.delete_memory(
                memory_id=memory_id,
                user_id="user-123",
            )

        # All should complete without error
        assert mock_client.delete.call_count == len(special_ids)

    @pytest.mark.anyio
    async def test_format_memory_context_with_unicode_content(self) -> None:
        """Test that format_memory_context handles unicode characters."""
        mock_client = MagicMock()
        mock_client.search = AsyncMock(
            return_value=[
                {
                    "id": "mem-1",
                    "memory": "User likes 日本語 programming",
                    "score": 0.9,
                    "metadata": {},
                },
                {
                    "id": "mem-2",
                    "memory": "Préfère le français 🇫🇷",
                    "score": 0.8,
                    "metadata": {},
                },
            ]
        )

        service = MemoryService(mock_client)

        context = await service.format_memory_context(
            query="languages",
            user_id="user-123",
        )

        # Should format unicode correctly
        assert "日本語" in context
        assert "français" in context
        assert "🇫🇷" in context
