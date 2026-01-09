"""Redis cache implementation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import redis.asyncio as redis
import structlog

from apps.api.config import get_settings

logger = structlog.get_logger(__name__)

if TYPE_CHECKING:
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
        await close_method()

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
        if ttl is not None:
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

    async def scan_keys(self, pattern: str, max_keys: int = 10000) -> list[str]:
        """Scan for keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "session:*")
            max_keys: Maximum number of keys to return (default: 10000)

        Returns:
            List of matching keys (up to max_keys)

        Note:
            If more than max_keys match, only the first max_keys are returned.
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

            # Decode and add keys
            batch = [
                k.decode() if isinstance(k, bytes) else str(k)
                for k in cursor_result[1]
            ]
            all_keys.extend(batch)

            # Safety limit to prevent OOM
            if len(all_keys) >= max_keys:
                logger.warning(
                    "scan_keys hit limit",
                    pattern=pattern,
                    max_keys=max_keys,
                    found=len(all_keys),
                )
                break

            if cursor == 0:
                break

        return all_keys[:max_keys]

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
        value: str | None = None,
    ) -> str | None:
        """Acquire a distributed lock.

        Args:
            key: Lock key.
            ttl: Lock TTL in seconds.
            value: Lock value.

        Returns:
            Lock value if acquired, None otherwise.
        """
        import uuid
        lock_value = value or str(uuid.uuid4())
        result = await self._client.set(
            f"lock:{key}",
            lock_value.encode("utf-8"),
            nx=True,
            ex=ttl,
        )
        return lock_value if result is True else None

    async def release_lock(self, key: str, value: str) -> bool:
        """Release a distributed lock.

        Args:
            key: Lock key.
            value: Lock value for ownership verification.

        Returns:
            True if released.
        """
        # Lua script for atomic check-and-delete
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        # Redis eval returns int (1 or 0) - type stubs are incomplete
        result: int = await self._client.eval(script, 1, f"lock:{key}", value)  # type: ignore[no-untyped-call]
        return bool(result == 1)

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
