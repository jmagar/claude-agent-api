"""Health-related service abstractions."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.api.protocols import Cache


class CacheHealthService:
    """Service wrapper for cache health checks."""

    def __init__(self, cache: "Cache") -> None:
        self._cache = cache

    async def ping(self) -> bool:
        """Check cache connectivity."""
        return await self._cache.ping()
