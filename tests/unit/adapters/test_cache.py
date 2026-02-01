"""Unit tests for RedisCache adapter (Priority 6).

Tests all cache operations, locking, scanning, and error conditions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, patch

import pytest

from apps.api.adapters.cache import RedisCache
from apps.api.dependencies import get_cache

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from httpx import AsyncClient

    from apps.api.types import JsonValue


@pytest.fixture
async def cache(async_client: AsyncClient) -> AsyncGenerator[RedisCache, None]:
    """Get Redis cache instance from initialized app.

    Args:
        async_client: Initialized test client (ensures app is ready).

    Yields:
        RedisCache instance.
    """
    # async_client fixture ensures app and cache are initialized
    _ = async_client  # Mark as used to satisfy type checker
    cache_instance = await get_cache()
    yield cache_instance


class TestCacheBasicOperations:
    """Tests for basic cache operations (get, set, delete)."""

    @pytest.mark.anyio
    async def test_get_returns_none_for_nonexistent_key(
        self,
        cache: RedisCache,
    ) -> None:
        """Test that getting a nonexistent key returns None.

        GREEN: This test verifies missing key handling.
        """
        result = await cache.get("nonexistent-key-12345")

        assert result is None

    @pytest.mark.anyio
    async def test_cache_set_and_get_string_value(
        self,
        cache: RedisCache,
    ) -> None:
        """Test setting and retrieving a string value.

        GREEN: This test verifies basic cache operations.
        """
        key = "test-key-string"
        value = "test-value"

        success = await cache.cache_set(key, value)
        assert success is True

        result = await cache.get(key)
        assert result == value

    @pytest.mark.anyio
    async def test_cache_set_with_ttl(
        self,
        cache: RedisCache,
    ) -> None:
        """Test setting value with TTL.

        GREEN: This test verifies TTL handling.
        """
        key = "test-key-ttl"
        value = "test-value"

        success = await cache.cache_set(key, value, ttl=3600)
        assert success is True

        # Verify key exists
        exists = await cache.exists(key)
        assert exists is True

    @pytest.mark.anyio
    async def test_set_json_and_get_json(
        self,
        cache: RedisCache,
    ) -> None:
        """Test setting and retrieving JSON data.

        GREEN: This test verifies JSON serialization/deserialization.
        """
        key = "test-key-json"
        value: dict[str, JsonValue] = {
            "name": "test",
            "count": 42,
            "items": ["a", "b", "c"],
        }

        success = await cache.set_json(key, value)
        assert success is True

        result = await cache.get_json(key)
        assert result == value

    @pytest.mark.anyio
    async def test_get_json_returns_none_for_nonexistent_key(
        self,
        cache: RedisCache,
    ) -> None:
        """Test that getting nonexistent JSON key returns None.

        GREEN: This test verifies missing key handling for JSON.
        """
        result = await cache.get_json("nonexistent-json-key")

        assert result is None

    @pytest.mark.anyio
    async def test_delete_existing_key(
        self,
        cache: RedisCache,
    ) -> None:
        """Test deleting an existing key.

        GREEN: This test verifies deletion.
        """
        key = "test-key-delete"
        await cache.cache_set(key, "value")

        deleted = await cache.delete(key)
        assert deleted is True

        # Verify key is gone
        result = await cache.get(key)
        assert result is None

    @pytest.mark.anyio
    async def test_delete_nonexistent_key_returns_false(
        self,
        cache: RedisCache,
    ) -> None:
        """Test deleting nonexistent key returns False.

        GREEN: This test verifies deletion of missing keys.
        """
        deleted = await cache.delete("nonexistent-key-delete")

        assert deleted is False

    @pytest.mark.anyio
    async def test_exists_returns_true_for_existing_key(
        self,
        cache: RedisCache,
    ) -> None:
        """Test exists returns True for existing key.

        GREEN: This test verifies key existence check.
        """
        key = "test-key-exists"
        await cache.cache_set(key, "value")

        exists = await cache.exists(key)

        assert exists is True

    @pytest.mark.anyio
    async def test_exists_returns_false_for_nonexistent_key(
        self,
        cache: RedisCache,
    ) -> None:
        """Test exists returns False for nonexistent key.

        GREEN: This test verifies missing key detection.
        """
        exists = await cache.exists("nonexistent-key-exists")

        assert exists is False


class TestCacheBulkOperations:
    """Tests for bulk cache operations (get_many_json)."""

    @pytest.mark.anyio
    async def test_get_many_json_uses_mget_and_parses(self) -> None:
        """Test that get_many_json uses mget and parses JSON values safely."""
        mock_client = AsyncMock()
        mock_client.mget.return_value = [
            b'{"id": "s1"}',
            None,
            b'{"id": "s2"}',
        ]

        cache = RedisCache(mock_client)

        result = await cache.get_many_json(
            ["session:s1", "session:missing", "session:s2"]
        )

        mock_client.mget.assert_called_once_with(
            "session:s1",
            "session:missing",
            "session:s2",
        )
        assert result == [
            {"id": "s1"},
            None,
            {"id": "s2"},
        ]


class TestCacheScanOperations:
    """Tests for scan_keys with pattern matching and pagination."""

    @pytest.mark.anyio
    async def test_scan_keys_with_pattern_matching(
        self,
        cache: RedisCache,
    ) -> None:
        """Test pattern matching in scan.

        GREEN: This test verifies pattern matching works correctly.
        """
        # Create keys with pattern
        await cache.cache_set("session:123", "data1")
        await cache.cache_set("session:456", "data2")
        await cache.cache_set("checkpoint:789", "data3")

        # Scan for session keys
        results = await cache.scan_keys("session:*")

        assert len(results) >= 2
        assert "session:123" in results
        assert "session:456" in results
        assert "checkpoint:789" not in results

    @pytest.mark.anyio
    async def test_scan_keys_with_large_result_sets(
        self,
        cache: RedisCache,
    ) -> None:
        """Test scan_keys handles pagination properly.

        GREEN: This test verifies pagination and max_keys limit.
        """
        # Create many keys
        for i in range(50):
            await cache.cache_set(f"bulk:key:{i}", f"value{i}")

        # Scan with low max_keys to test limit
        results = await cache.scan_keys("bulk:key:*", max_keys=20)

        # Should respect max_keys limit
        assert len(results) <= 20

        # Should find some keys
        assert len(results) > 0

    @pytest.mark.anyio
    async def test_scan_keys_returns_empty_for_no_matches(
        self,
        cache: RedisCache,
    ) -> None:
        """Test scan_keys returns empty list when no keys match.

        GREEN: This test verifies no-match handling.
        """
        results = await cache.scan_keys("nonexistent-pattern:*")

        assert results == []


class TestCacheSetOperations:
    """Tests for Redis set operations (sadd, srem, smembers)."""

    @pytest.mark.anyio
    async def test_add_to_set(
        self,
        cache: RedisCache,
    ) -> None:
        """Test adding value to a set.

        GREEN: This test verifies set addition.
        """
        from uuid import uuid4

        key = f"test-set-add-{uuid4().hex[:8]}"
        value = "member1"

        added = await cache.add_to_set(key, value)

        assert added is True

    @pytest.mark.anyio
    async def test_add_duplicate_to_set_returns_false(
        self,
        cache: RedisCache,
    ) -> None:
        """Test adding duplicate to set returns False.

        GREEN: This test verifies duplicate detection.
        """
        from uuid import uuid4

        key = f"test-set-duplicate-{uuid4().hex[:8]}"
        value = "member1"

        # Add first time
        added1 = await cache.add_to_set(key, value)
        assert added1 is True

        # Add duplicate
        added2 = await cache.add_to_set(key, value)
        assert added2 is False

    @pytest.mark.anyio
    async def test_remove_from_set(
        self,
        cache: RedisCache,
    ) -> None:
        """Test removing value from a set.

        GREEN: This test verifies set removal.
        """
        key = "test-set-remove"
        value = "member1"

        await cache.add_to_set(key, value)
        removed = await cache.remove_from_set(key, value)

        assert removed is True

    @pytest.mark.anyio
    async def test_remove_nonexistent_from_set_returns_false(
        self,
        cache: RedisCache,
    ) -> None:
        """Test removing nonexistent value returns False.

        GREEN: This test verifies removal of missing members.
        """
        key = "test-set-remove-nonexistent"

        removed = await cache.remove_from_set(key, "nonexistent")

        assert removed is False

    @pytest.mark.anyio
    async def test_set_members_returns_all_members(
        self,
        cache: RedisCache,
    ) -> None:
        """Test getting all members of a set.

        GREEN: This test verifies set member retrieval.
        """
        key = "test-set-members"
        values = ["member1", "member2", "member3"]

        for value in values:
            await cache.add_to_set(key, value)

        members = await cache.set_members(key)

        assert len(members) == 3
        assert members == set(values)

    @pytest.mark.anyio
    async def test_set_members_returns_empty_for_nonexistent(
        self,
        cache: RedisCache,
    ) -> None:
        """Test getting members of nonexistent set returns empty.

        GREEN: This test verifies empty set handling.
        """
        members = await cache.set_members("nonexistent-set")

        assert members == set()


class TestCacheLocking:
    """Tests for distributed locking (acquire_lock, release_lock)."""

    @pytest.mark.anyio
    async def test_acquire_lock_with_custom_value(
        self,
        cache: RedisCache,
    ) -> None:
        """Test lock acquisition with specific value.

        GREEN: This test verifies lock acquisition with custom value.
        """
        from uuid import uuid4

        key = f"test-lock-custom-value-{uuid4().hex[:8]}"
        value = "my-custom-lock-value"

        lock_value = await cache.acquire_lock(key, ttl=60, value=value)

        assert lock_value == value

    @pytest.mark.anyio
    async def test_acquire_lock_returns_false_when_already_locked(
        self,
        cache: RedisCache,
    ) -> None:
        """Test lock contention.

        GREEN: This test verifies lock acquisition fails when already held.
        """
        from uuid import uuid4

        key = f"test-lock-contention-{uuid4().hex[:8]}"

        # First acquire succeeds
        lock1 = await cache.acquire_lock(key, ttl=60)
        assert lock1 is not None

        # Second acquire fails
        lock2 = await cache.acquire_lock(key, ttl=60)
        assert lock2 is None

    @pytest.mark.anyio
    async def test_release_lock_atomic_check_and_delete(
        self,
        cache: RedisCache,
    ) -> None:
        """Test atomic lock release verification.

        GREEN: This test verifies lock release uses atomic check-and-delete.
        """
        from uuid import uuid4

        key = f"test-lock-atomic-{uuid4().hex[:8]}"

        # Acquire lock
        lock_value = await cache.acquire_lock(key, ttl=60)
        assert lock_value is not None

        # Release with correct value
        released = await cache.release_lock(key, lock_value)
        assert released is True

        # Lock should be gone
        exists = await cache.exists(f"lock:{key}")
        assert exists is False

    @pytest.mark.anyio
    async def test_release_lock_only_releases_own_lock(
        self,
        cache: RedisCache,
    ) -> None:
        """Test security check for lock ownership.

        GREEN: This test verifies locks can only be released by owner.
        """
        from uuid import uuid4

        key = f"test-lock-ownership-{uuid4().hex[:8]}"

        # Acquire lock with value1
        lock_value1 = await cache.acquire_lock(key, ttl=60, value="value1")
        assert lock_value1 is not None

        # Try to release with wrong value
        released = await cache.release_lock(key, "wrong-value")
        assert released is False

        # Lock should still exist
        exists = await cache.exists(f"lock:{key}")
        assert exists is True

        # Release with correct value succeeds
        released = await cache.release_lock(key, "value1")
        assert released is True


class TestCacheCounterOperations:
    """Tests for counter operations (incr)."""

    @pytest.mark.anyio
    async def test_incr_increments_counter(
        self,
        cache: RedisCache,
    ) -> None:
        """Test counter increment.

        GREEN: This test verifies counter increments correctly.
        """
        from uuid import uuid4

        key = f"test-counter-incr-{uuid4().hex[:8]}"

        # First increment
        value1 = await cache.incr(key)
        assert value1 == 1

        # Second increment
        value2 = await cache.incr(key)
        assert value2 == 2

        # Third increment
        value3 = await cache.incr(key)
        assert value3 == 3

    @pytest.mark.anyio
    async def test_incr_initializes_if_not_exists(
        self,
        cache: RedisCache,
    ) -> None:
        """Test counter initialization.

        GREEN: This test verifies counter starts at 0 if not exists.
        """
        key = "test-counter-init"

        # Delete key if it exists
        await cache.delete(key)

        # First increment should initialize to 1
        value = await cache.incr(key)
        assert value == 1


class TestCacheExpiration:
    """Tests for TTL and expiration."""

    @pytest.mark.anyio
    async def test_expire_sets_ttl(
        self,
        cache: RedisCache,
    ) -> None:
        """Test TTL setting.

        GREEN: This test verifies expire sets TTL on key.
        """
        key = "test-expire-ttl"

        # Set key without TTL
        await cache.cache_set(key, "value")

        # Set expiration
        result = await cache.expire(key, 3600)
        assert result is True

    @pytest.mark.anyio
    async def test_expire_returns_false_for_nonexistent_key(
        self,
        cache: RedisCache,
    ) -> None:
        """Test error handling for expire on missing key.

        GREEN: This test verifies expire handles missing keys.
        """
        result = await cache.expire("nonexistent-key-expire", 3600)

        assert result is False


class TestCacheConnectivity:
    """Tests for connection and health checks."""

    @pytest.mark.anyio
    async def test_ping_returns_true_when_connected(
        self,
        cache: RedisCache,
    ) -> None:
        """Test ping returns True when connected.

        GREEN: This test verifies connectivity check.
        """
        result = await cache.ping()

        assert result is True

    @pytest.mark.anyio
    async def test_ping_returns_false_on_connection_error(self) -> None:
        """Test ping handles connection errors gracefully.

        GREEN: This test verifies error handling in ping.
        """
        # Create cache with invalid client that raises exception
        mock_client = AsyncMock()
        mock_client.ping.side_effect = ConnectionError("Connection failed")

        cache = RedisCache(mock_client)

        result = await cache.ping()

        assert result is False


class TestCacheCreation:
    """Tests for cache creation and lifecycle."""

    @pytest.mark.anyio
    async def test_create_cache_from_url(self) -> None:
        """Test creating cache from URL uses settings for pool configuration.

        GREEN: This test verifies cache creation with explicit URL.
        """
        with patch("apps.api.adapters.cache.redis.from_url") as mock_from_url:
            mock_client = Mock()
            mock_from_url.return_value = mock_client

            with patch("apps.api.adapters.cache.get_settings") as mock_settings:
                # Use different values to verify settings are used
                mock_settings.return_value.redis_max_connections = 75
                mock_settings.return_value.redis_socket_connect_timeout = 8
                mock_settings.return_value.redis_socket_timeout = 12

                cache = await RedisCache.create("redis://localhost:6379/0")

                assert cache._client == mock_client
                assert mock_from_url.call_count == 1
                _, call_kwargs = mock_from_url.call_args
                assert call_kwargs["encoding"] == "utf-8"
                assert call_kwargs["decode_responses"] is False
                assert call_kwargs["max_connections"] == 75
                assert call_kwargs["socket_connect_timeout"] == 8
                assert call_kwargs["socket_timeout"] == 12
                assert call_kwargs["retry"] is not None
                assert call_kwargs["retry_on_error"] is not None
                assert len(call_kwargs["retry_on_error"]) == 2

    @pytest.mark.anyio
    async def test_create_cache_uses_settings_when_url_not_provided(self) -> None:
        """Test cache creation uses settings for pool configuration."""
        with patch("apps.api.adapters.cache.redis.from_url") as mock_from_url:
            mock_client = Mock()
            mock_from_url.return_value = mock_client

            with patch("apps.api.adapters.cache.get_settings") as mock_settings:
                # Use DIFFERENT values than hardcoded to verify they're actually used
                mock_settings.return_value.redis_url = "redis://localhost:54379/0"
                mock_settings.return_value.redis_max_connections = (
                    100  # Different from 50
                )
                mock_settings.return_value.redis_socket_connect_timeout = (
                    10  # Different from 5
                )
                mock_settings.return_value.redis_socket_timeout = 15  # Different from 5

                cache = await RedisCache.create()

                assert cache._client == mock_client
                assert mock_from_url.call_count == 1
                _, call_kwargs = mock_from_url.call_args
                assert call_kwargs["encoding"] == "utf-8"
                assert call_kwargs["decode_responses"] is False
                assert call_kwargs["max_connections"] == 100
                assert call_kwargs["socket_connect_timeout"] == 10
                assert call_kwargs["socket_timeout"] == 15
                assert call_kwargs["retry"] is not None
                assert call_kwargs["retry_on_error"] is not None
                assert len(call_kwargs["retry_on_error"]) == 2

    @pytest.mark.anyio
    async def test_close_calls_aclose_if_available(self) -> None:
        """Test close uses aclose when available.

        GREEN: This test verifies async close method.
        """
        mock_client = AsyncMock()
        mock_client.aclose = AsyncMock()
        cache = RedisCache(mock_client)

        await cache.close()

        mock_client.aclose.assert_called_once()

    @pytest.mark.anyio
    async def test_close_fallback_to_close_method(self) -> None:
        """Test close falls back to close() when aclose not available.

        GREEN: This test verifies close method fallback.
        """
        mock_client = AsyncMock()
        # Remove aclose attribute
        delattr(mock_client, "aclose")
        mock_client.close = AsyncMock()

        cache = RedisCache(mock_client)

        await cache.close()

        mock_client.close.assert_called_once()
