"""Redis cache implementation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Protocol, cast

import redis.asyncio as redis
import structlog

from apps.api.config import get_settings

if TYPE_CHECKING:
    from apps.api.types import JsonValue

logger = structlog.get_logger(__name__)


class RedisClientProtocol(Protocol):
    """Protocol for Redis client with typed eval method."""

    async def eval(
        self,
        script: str,
        numkeys: int,
        *keys_and_args: str,
    ) -> int:
        """Execute Lua script atomically."""
        ...

    async def get(self, name: str) -> bytes | None:
        """Get value."""
        ...

    async def mget(self, *names: str) -> list[bytes | None]:
        """Get multiple values.

        Args:
            *names: Variable number of key names to fetch.

        Returns:
            List of values in the same order as keys.
            None for missing keys.
        """
        ...

    async def set(
        self,
        name: str,
        value: bytes,
        ex: int | None = None,
        px: int | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool | None:
        """Set value."""
        ...

    async def delete(self, *names: str) -> int:
        """Delete keys."""
        ...

    async def exists(self, *names: str) -> int:
        """Check if keys exist."""
        ...

    async def ping(self) -> bool:
        """Ping server."""
        ...

    async def smembers(self, name: str) -> AbstractSet[bytes]:
        """Get set members."""
        ...

    async def sadd(self, name: str, *values: bytes) -> int:
        """Add to set."""
        ...

    async def srem(self, name: str, *values: bytes) -> int:
        """Remove from set."""
        ...

    async def incr(self, name: str, amount: int = 1) -> int:
        """Increment."""
        ...


if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

    # Use generic type only during type checking
    RedisClient = redis.Redis[bytes]
else:
    # At runtime, just use the base type to avoid subscript error
    AbstractSet = set
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
        """Create Redis cache instance with retry configuration.

        Args:
            url: Redis URL. Uses settings if not provided.

        Returns:
            RedisCache instance.
        """
        from redis import exceptions as redis_exceptions
        from redis.backoff import ExponentialBackoff
        from redis.retry import Retry

        settings = get_settings()
        redis_url = url or settings.redis_url

        # Configure exponential backoff retry policy
        retry_policy = Retry(
            ExponentialBackoff(base=settings.redis_retry_backoff_base_ms / 1000),
            retries=settings.redis_retry_max_attempts,
        )

        client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False,
            max_connections=settings.redis_max_connections,
            socket_connect_timeout=settings.redis_socket_connect_timeout,
            socket_timeout=settings.redis_socket_timeout,
            retry=retry_policy,
            retry_on_error=[
                redis_exceptions.ConnectionError,
                redis_exceptions.TimeoutError,
            ],
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

    async def get_json(self, key: str) -> dict[str, JsonValue] | None:
        """Get a JSON value from cache.

        Args:
            key: Cache key.

        Returns:
            Parsed JSON dict or None.
        """
        value = await self.get(key)
        if value is None or not value.strip():
            return None
        try:
            parsed: dict[str, JsonValue] = json.loads(value)
            return parsed
        except (json.JSONDecodeError, ValueError):
            return None

    async def get_many_json(self, keys: list[str]) -> list[dict[str, JsonValue] | None]:
        """Get multiple JSON values from cache using Redis mget.

        Args:
            keys: List of cache keys to fetch.

        Returns:
            List of parsed JSON dicts in same order as keys.
            None for missing keys or JSON decode errors.
        """
        if not keys:
            return []

        values = await self._client.mget(*keys)
        results: list[dict[str, JsonValue] | None] = []

        for raw in values:
            if raw is None:
                results.append(None)
                continue
            try:
                decoded = raw.decode("utf-8")
                results.append(json.loads(decoded))
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as e:
                logger.debug(
                    "get_many_json decode error",
                    key=keys[len(results)],
                    error=str(e) or type(e).__name__,
                )
                results.append(None)

        return results

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
        value: dict[str, JsonValue],
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

    async def scan_keys(self, pattern: str, max_keys: int = 1000) -> list[str]:
        """Scan for keys matching a pattern.

        DEPRECATED: Only use for scoped patterns (e.g., 'run:{thread_id}:*').
        NEVER use for unbounded patterns (e.g., 'session:*' without scope).

        WARNING: O(N) operation that scans entire Redis keyspace. Dangerous in
        production with many keys. Prefer indexed lookups (e.g., owner index sets).

        Args:
            pattern: Redis SCAN pattern. MUST be scoped to bounded entity.
            max_keys: Safety limit (default: 1000, max: 10000).

        Returns:
            List of matching keys (up to max_keys).

        Raises:
            ValueError: If max_keys exceeds 10000 (safety limit).
        """
        if max_keys > 10000:
            raise ValueError(
                f"max_keys={max_keys} exceeds safety limit of 10000. "
                "Use indexed lookups for large result sets."
            )

        # Log deprecation warning for unbounded patterns
        # A pattern is considered unbounded if it uses wildcards without specific IDs
        is_unbounded = self._is_unbounded_pattern(pattern)
        if is_unbounded:
            logger.warning(
                "scan_keys_unbounded_pattern",
                pattern=pattern,
                msg="Unbounded pattern detected. Prefer indexed lookups (owner sets).",
            )

        all_keys: list[str] = []
        cursor: int = 0

        while True:
            cursor_result = await self._client.scan(
                cursor=cursor,
                match=pattern,
                count=1000,
            )
            cursor = int(cursor_result[0])

            # Decode and add keys
            batch = [
                k.decode() if isinstance(k, bytes) else str(k) for k in cursor_result[1]
            ]
            all_keys.extend(batch)

            # Safety limit to prevent OOM
            if len(all_keys) >= max_keys:
                logger.warning(
                    "scan_keys_hit_limit",
                    pattern=pattern,
                    max_keys=max_keys,
                    found=len(all_keys),
                    msg="Consider using indexed lookups instead of scan",
                )
                break

            if cursor == 0:
                break

        return all_keys[:max_keys]

    def _is_unbounded_pattern(self, pattern: str) -> bool:
        """Check if a Redis pattern is unbounded (matches many keys).

        A pattern is unbounded if it doesn't contain specific identifiers (UUIDs,
        API key hashes) and uses wildcards broadly.

        Examples:
            "session:*" -> True (unbounded, no specific ID)
            "session:owner:*" -> True (unbounded, no specific owner hash)
            "session:abc123...:*" -> False (scoped to specific ID)
            "session:*:messages" -> True (wildcard in middle)
            "prefix:with:colons:*" -> True (ends with wildcard, no specific ID)
        """
        import re

        # Pattern ends with wildcard (very broad)
        if pattern.endswith("*") or pattern.endswith("?"):
            # Check if there's a UUID-like segment (scopes the pattern)
            # UUID pattern: 8-4-4-4-12 hex digits
            uuid_pattern = (
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
            )
            # SHA-256 hash pattern: 64 hex digits
            hash_pattern = r"[0-9a-f]{64}"

            return not (
                re.search(uuid_pattern, pattern) or re.search(hash_pattern, pattern)
            )

        # Wildcard in the middle (matches many keys at multiple levels)
        return "*" in pattern[:-1] or "?" in pattern[:-1]

    async def clear(self) -> bool:
        """Clear all cached entries.

        Returns:
            True if the cache was cleared.
        """
        result = await self._client.flushdb()
        return bool(result)

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

    async def _eval_script(self, script: str, num_keys: int, *args: str) -> int:
        """Typed wrapper for Redis eval command.

        Args:
            script: Lua script to execute.
            num_keys: Number of keys in the script.
            *args: Keys and arguments for the script.

        Returns:
            Integer result from the script (1 for success, 0 for failure).
        """
        # Type-safe wrapper using RedisClientProtocol
        client = cast("RedisClientProtocol", self._client)
        return await client.eval(script, num_keys, *args)

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
        # Use typed wrapper to execute Lua script
        result = await self._eval_script(script, 1, f"lock:{key}", value)
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
