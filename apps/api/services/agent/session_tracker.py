"""<summary>Redis-backed session tracking for AgentService.</summary>"""

from typing import TYPE_CHECKING

import structlog

from apps.api.config import Settings, get_settings

if TYPE_CHECKING:
    from apps.api.protocols import Cache

logger = structlog.get_logger(__name__)


class AgentSessionTracker:
    """<summary>Tracks active sessions and interrupts in Redis.</summary>"""

    def __init__(self, cache: "Cache | None", settings: Settings | None = None) -> None:
        """<summary>Initialize tracker.</summary>"""
        self._cache = cache
        self._settings = settings if settings is not None else get_settings()

    async def register(self, session_id: str) -> None:
        """<summary>Register session as active.</summary>"""
        if not self._cache:
            raise RuntimeError("Cache is required for distributed session tracking")
        key = f"active_session:{session_id}"
        await self._cache.cache_set(key, "true", ttl=self._settings.redis_session_ttl)
        logger.info("Registered active session", session_id=session_id, storage="redis")

    async def is_active(self, session_id: str) -> bool:
        """<summary>Return True if session is active.</summary>"""
        if not self._cache:
            raise RuntimeError("Cache is required for distributed session tracking")
        key = f"active_session:{session_id}"
        return await self._cache.exists(key)

    async def unregister(self, session_id: str) -> None:
        """<summary>Unregister session.</summary>"""
        if not self._cache:
            raise RuntimeError("Cache is required for distributed session tracking")
        key = f"active_session:{session_id}"
        await self._cache.delete(key)
        logger.info(
            "Unregistered active session", session_id=session_id, storage="redis"
        )

    async def is_interrupted(self, session_id: str) -> bool:
        """<summary>Return True if interrupt marker exists.</summary>"""
        if not self._cache:
            raise RuntimeError("Cache is required for distributed interrupt checking")
        interrupt_key = f"interrupted:{session_id}"
        return await self._cache.exists(interrupt_key)

    async def mark_interrupted(self, session_id: str) -> None:
        """<summary>Mark session as interrupted.</summary>"""
        if not self._cache:
            raise RuntimeError("Cache is required for distributed interrupt signaling")
        interrupt_key = f"interrupted:{session_id}"
        await self._cache.cache_set(
            interrupt_key, "true", ttl=self._settings.redis_interrupt_ttl
        )
        logger.info(
            "Marked session as interrupted", session_id=session_id, storage="redis"
        )
