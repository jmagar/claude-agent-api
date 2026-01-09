"""Graceful shutdown handling for active sessions (T131)."""

import asyncio
from typing import Final

import structlog

logger = structlog.get_logger(__name__)

# Default timeout for waiting on active sessions
DEFAULT_SHUTDOWN_TIMEOUT: Final[int] = 30


class ShutdownManager:
    """Manages graceful shutdown of active sessions.

    This manager tracks active sessions and ensures they are properly
    cleaned up during application shutdown.
    """

    def __init__(self) -> None:
        """Initialize shutdown manager."""
        self._shutting_down = False
        self._active_sessions: set[str] = set()
        self._shutdown_event = asyncio.Event()

    @property
    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress.

        Returns:
            True if shutdown has been initiated.
        """
        return self._shutting_down

    @property
    def active_session_count(self) -> int:
        """Get count of active sessions.

        Returns:
            Number of currently active sessions.
        """
        return len(self._active_sessions)

    def register_session(self, session_id: str) -> bool:
        """Register an active session.

        Args:
            session_id: Session ID to register.

        Returns:
            True if registered, False if shutdown is in progress.
        """
        if self._shutting_down:
            logger.warning(
                "Cannot register session during shutdown",
                session_id=session_id,
            )
            return False

        self._active_sessions.add(session_id)
        logger.debug(
            "Session registered",
            session_id=session_id,
            active_count=len(self._active_sessions),
        )
        return True

    def unregister_session(self, session_id: str) -> None:
        """Unregister a completed session.

        Args:
            session_id: Session ID to unregister.
        """
        self._active_sessions.discard(session_id)
        logger.debug(
            "Session unregistered",
            session_id=session_id,
            active_count=len(self._active_sessions),
        )

        # Signal if all sessions done during shutdown
        if self._shutting_down and len(self._active_sessions) == 0:
            self._shutdown_event.set()

    def initiate_shutdown(self) -> None:
        """Initiate graceful shutdown.

        Sets the shutdown flag to prevent new sessions.
        """
        self._shutting_down = True
        logger.info(
            "Shutdown initiated",
            active_sessions=len(self._active_sessions),
        )

        # If no active sessions, signal immediately
        if len(self._active_sessions) == 0:
            self._shutdown_event.set()

    async def wait_for_sessions(self, timeout: int = DEFAULT_SHUTDOWN_TIMEOUT) -> bool:
        """Wait for active sessions to complete.

        Args:
            timeout: Maximum seconds to wait for sessions.

        Returns:
            True if all sessions completed, False if timeout.
        """
        if len(self._active_sessions) == 0:
            return True

        logger.info(
            "Waiting for active sessions to complete",
            active_sessions=len(self._active_sessions),
            timeout=timeout,
        )

        try:
            await asyncio.wait_for(
                self._shutdown_event.wait(),
                timeout=timeout,
            )
            logger.info("All sessions completed gracefully")
            return True
        except TimeoutError:
            logger.warning(
                "Shutdown timeout - forcing closure",
                remaining_sessions=list(self._active_sessions),
            )
            return False

    def get_active_sessions(self) -> list[str]:
        """Get list of active session IDs.

        Returns:
            List of active session IDs.
        """
        return list(self._active_sessions)


# Global shutdown manager instance
_shutdown_manager: ShutdownManager | None = None


def get_shutdown_manager() -> ShutdownManager:
    """Get the global shutdown manager instance.

    Returns:
        ShutdownManager instance.
    """
    global _shutdown_manager
    if _shutdown_manager is None:
        _shutdown_manager = ShutdownManager()
    return _shutdown_manager


def reset_shutdown_manager() -> None:
    """Reset the shutdown manager (for testing).

    Creates a new manager instance.
    """
    global _shutdown_manager
    _shutdown_manager = ShutdownManager()
