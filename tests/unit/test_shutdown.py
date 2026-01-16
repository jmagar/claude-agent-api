"""Unit tests for graceful shutdown handling (T131)."""

import asyncio

import pytest

from apps.api.services.shutdown import ShutdownManager, reset_shutdown_manager


@pytest.fixture
def shutdown_manager() -> ShutdownManager:
    """Create a fresh shutdown manager for each test."""
    return ShutdownManager()


class TestShutdownManager:
    """Tests for ShutdownManager class."""

    def test_initial_state(self, shutdown_manager: ShutdownManager) -> None:
        """Test initial manager state."""
        assert shutdown_manager.is_shutting_down is False
        assert shutdown_manager.active_session_count == 0

    def test_register_session(self, shutdown_manager: ShutdownManager) -> None:
        """Test registering a session."""
        result = shutdown_manager.register_session("session-1")

        assert result is True
        assert shutdown_manager.active_session_count == 1

    def test_register_multiple_sessions(
        self, shutdown_manager: ShutdownManager
    ) -> None:
        """Test registering multiple sessions."""
        shutdown_manager.register_session("session-1")
        shutdown_manager.register_session("session-2")
        shutdown_manager.register_session("session-3")

        assert shutdown_manager.active_session_count == 3

    def test_unregister_session(self, shutdown_manager: ShutdownManager) -> None:
        """Test unregistering a session."""
        shutdown_manager.register_session("session-1")
        shutdown_manager.unregister_session("session-1")

        assert shutdown_manager.active_session_count == 0

    def test_unregister_nonexistent_session(
        self, shutdown_manager: ShutdownManager
    ) -> None:
        """Test unregistering a session that doesn't exist."""
        # Should not raise
        shutdown_manager.unregister_session("nonexistent")
        assert shutdown_manager.active_session_count == 0

    def test_initiate_shutdown(self, shutdown_manager: ShutdownManager) -> None:
        """Test initiating shutdown."""
        shutdown_manager.initiate_shutdown()

        assert shutdown_manager.is_shutting_down is True

    def test_register_fails_during_shutdown(
        self, shutdown_manager: ShutdownManager
    ) -> None:
        """Test that registration fails during shutdown."""
        shutdown_manager.initiate_shutdown()

        result = shutdown_manager.register_session("session-1")

        assert result is False
        assert shutdown_manager.active_session_count == 0

    def test_get_active_sessions(self, shutdown_manager: ShutdownManager) -> None:
        """Test getting list of active sessions."""
        shutdown_manager.register_session("session-1")
        shutdown_manager.register_session("session-2")

        sessions = shutdown_manager.get_active_sessions()

        assert set(sessions) == {"session-1", "session-2"}

    @pytest.mark.anyio
    async def test_wait_for_sessions_no_active(
        self, shutdown_manager: ShutdownManager
    ) -> None:
        """Test waiting when no active sessions."""
        result = await shutdown_manager.wait_for_sessions(timeout=1)

        assert result is True

    @pytest.mark.anyio
    async def test_wait_for_sessions_completes(
        self, shutdown_manager: ShutdownManager
    ) -> None:
        """Test waiting for sessions to complete."""
        shutdown_manager.register_session("session-1")
        shutdown_manager.initiate_shutdown()

        # Unregister in background after short delay
        async def complete_session() -> None:
            await asyncio.sleep(0.1)
            shutdown_manager.unregister_session("session-1")

        _task = asyncio.create_task(complete_session())  # noqa: RUF006

        result = await shutdown_manager.wait_for_sessions(timeout=5)

        assert result is True
        assert shutdown_manager.active_session_count == 0

    @pytest.mark.anyio
    async def test_wait_for_sessions_timeout(
        self, shutdown_manager: ShutdownManager
    ) -> None:
        """Test waiting times out with active sessions."""
        shutdown_manager.register_session("session-1")
        shutdown_manager.initiate_shutdown()

        result = await shutdown_manager.wait_for_sessions(timeout=1)

        assert result is False
        assert shutdown_manager.active_session_count == 1


class TestGlobalShutdownManager:
    """Tests for global shutdown manager functions."""

    def test_reset_shutdown_manager(self) -> None:
        """Test resetting the global shutdown manager."""
        from apps.api.services.shutdown import get_shutdown_manager

        # Get initial manager and modify it
        manager1 = get_shutdown_manager()
        manager1.register_session("session-1")

        # Reset
        reset_shutdown_manager()

        # New manager should be fresh
        manager2 = get_shutdown_manager()
        assert manager2.active_session_count == 0
