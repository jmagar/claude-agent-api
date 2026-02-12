"""Distributed locking utilities for session operations."""

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, TypeVar

import structlog

T = TypeVar("T")

if TYPE_CHECKING:
    from apps.api.protocols import Cache

logger = structlog.get_logger(__name__)


class SessionLockManager:
    """Coordinates lock acquisition/release for per-session operations."""

    _LOCK_INITIAL_RETRY_DELAY = 0.01
    _LOCK_MAX_RETRY_DELAY = 0.5

    def __init__(self, cache: "Cache | None") -> None:
        self._cache = cache

    async def with_session_lock(
        self,
        session_id: str,
        operation: str,
        func: Callable[[], Awaitable[T]],
        acquire_timeout: float = 5.0,
        lock_ttl: int = 30,
    ) -> T:
        """Execute an async operation while holding a distributed session lock."""
        if self._cache is None:
            return await func()

        lock_key = f"session_lock:{session_id}"
        start_time = time.monotonic()
        retry_delay = self._LOCK_INITIAL_RETRY_DELAY

        while True:
            lock_value = await self._cache.acquire_lock(lock_key, ttl=lock_ttl)
            if lock_value is not None:
                break

            elapsed = time.monotonic() - start_time
            if elapsed >= acquire_timeout:
                logger.warning(
                    "failed_to_acquire_session_lock",
                    session_id=session_id,
                    operation=operation,
                    timeout=acquire_timeout,
                    elapsed=elapsed,
                )
                raise TimeoutError(f"Could not acquire lock for session {session_id}")

            jittered_delay = retry_delay * (1 + random.uniform(-0.1, 0.1))
            await asyncio.sleep(jittered_delay)
            retry_delay = min(retry_delay * 2, self._LOCK_MAX_RETRY_DELAY)

        try:
            logger.debug("acquired_session_lock", session_id=session_id, operation=operation)
            return await func()
        finally:
            try:
                await self._cache.release_lock(lock_key, lock_value)
                logger.debug("released_session_lock", session_id=session_id, operation=operation)
            except Exception as release_error:
                logger.error(
                    "failed_to_release_session_lock",
                    session_id=session_id,
                    operation=operation,
                    error=str(release_error),
                )
