"""Health-related service abstractions."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.api.adapters.cache import RedisCache


class CacheHealthService:
    """Service wrapper for cache health checks."""

    def __init__(self, cache: "RedisCache") -> None:
        self._cache = cache

    async def ping(self) -> bool:
        """Check cache connectivity."""
        return await self._cache.ping()
