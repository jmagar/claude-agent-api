"""Redis cache implementation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

import redis.asyncio as redis

from apps.api.config import get_settings

if TYPE_CHECKING:
    from collections.abc import Awaitable

    # Use generic type only during type checking
    RedisClient = redis.Redis[bytes]
else:
    # At runtime, just use the base type to avoid subscript error
    RedisClient = redis.Redis


class RedisCache:
    """Redis cache implementation of Cache protocol."""

    def __init__(self, client: RedisClient) -> None:
        """Initialize Redis cache.

        Args:
            client: Redis async client.
        """
        self._client = client

    @classmethod
    async def create(cls, url: str | None = None) -> RedisCache:
        """Create Redis cache instance.

        Args:
            url: Redis URL. Uses settings if not provided.

        Returns:
            RedisCache instance.
        """
        settings = get_settings()
        redis_url = url or settings.redis_url
        client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False,
        )
        return cls(client)

    async def close(self) -> None:
        """Close Redis connection.

        Note: redis.asyncio.Redis has aclose() at runtime but type stubs
        use close(). We use getattr to safely call the async close method.
        """
        close_method = getattr(self._client, "aclose", self._client.close)
        awaitable = close_method()
        if TYPE_CHECKING:
            awaitable = cast("Awaitable[None]", awaitable)
        await awaitable

    async def get(self, key: str) -> str | None:
        """Get a value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None.
        """
        value = await self._client.get(key)
        if value is None:
            return None
        return value.decode("utf-8")

    async def get_json(self, key: str) -> dict[str, object] | None:
        """Get a JSON value from cache.

        Args:
            key: Cache key.

        Returns:
            Parsed JSON dict or None.
        """
        value = await self.get(key)
        if value is None:
            return None
        parsed: dict[str, object] = json.loads(value)
        return parsed

    async def cache_set(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> bool:
        """Set a value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds.

        Returns:
            True if successful.
        """
        if ttl:
            await self._client.setex(key, ttl, value.encode("utf-8"))
        else:
            await self._client.set(key, value.encode("utf-8"))
        return True

    async def set_json(
        self,
        key: str,
        value: dict[str, object],
        ttl: int | None = None,
    ) -> bool:
        """Set a JSON value in cache.

        Args:
            key: Cache key.
            value: Dict to cache as JSON.
            ttl: Time to live in seconds.

        Returns:
            True if successful.
        """
        return await self.cache_set(key, json.dumps(value), ttl)

    async def scan_keys(self, pattern: str) -> list[str]:
        """Scan for keys matching pattern.

        Args:
            pattern: Glob-style pattern (e.g., 'session:*').

        Returns:
            List of matching keys.
        """
        all_keys: list[str] = []
        cursor: int = 0

        while True:
            cursor_result = await self._client.scan(
                cursor=cursor,
                match=pattern,
                count=100,
            )
            cursor = int(cursor_result[0])
            all_keys.extend(
                k.decode() if isinstance(k, bytes) else str(k) for k in cursor_result[1]
            )
            if cursor == 0:
                break

        return all_keys

    async def delete(self, key: str) -> bool:
        """Delete a value from cache.

        Args:
            key: Cache key.

        Returns:
            True if deleted.
        """
        result = await self._client.delete(key)
        return result > 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key.

        Returns:
            True if exists.
        """
        result = await self._client.exists(key)
        return result > 0

    async def add_to_set(self, key: str, value: str) -> bool:
        """Add value to a set.

        Args:
            key: Set key.
            value: Value to add.

        Returns:
            True if added.
        """
        result = await self._client.sadd(key, value.encode("utf-8"))
        return result > 0

    async def remove_from_set(self, key: str, value: str) -> bool:
        """Remove value from a set.

        Args:
            key: Set key.
            value: Value to remove.

        Returns:
            True if removed.
        """
        result = await self._client.srem(key, value.encode("utf-8"))
        return result > 0

    async def set_members(self, key: str) -> set[str]:
        """Get all members of a set.

        Args:
            key: Set key.

        Returns:
            Set of values.
        """
        members = await self._client.smembers(key)
        return {m.decode("utf-8") for m in members}

    async def acquire_lock(
        self,
        key: str,
        ttl: int = 300,
        value: str = "locked",
    ) -> bool:
        """Acquire a distributed lock.

        Args:
            key: Lock key.
            ttl: Lock TTL in seconds.
            value: Lock value.

        Returns:
            True if lock acquired.
        """
        result = await self._client.set(
            f"lock:{key}",
            value.encode("utf-8"),
            nx=True,
            ex=ttl,
        )
        return result is True

    async def release_lock(self, key: str) -> bool:
        """Release a distributed lock.

        Args:
            key: Lock key.

        Returns:
            True if released.
        """
        return await self.delete(f"lock:{key}")

    async def ping(self) -> bool:
        """Check cache connectivity.

        Returns:
            True if connected.
        """
        try:
            result = await self._client.ping()
            return result is True
        except Exception:
            return False

    async def incr(self, key: str) -> int:
        """Increment a counter.

        Args:
            key: Counter key.

        Returns:
            New counter value.
        """
        result = await self._client.incr(key)
        return int(result)

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on a key.

        Args:
            key: Cache key.
            ttl: Time to live in seconds.

        Returns:
            True if set.
        """
        result = await self._client.expire(key, ttl)
        return result is True
