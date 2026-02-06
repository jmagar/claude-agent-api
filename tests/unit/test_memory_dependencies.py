"""Tests for memory dependency injection."""

from unittest.mock import MagicMock, patch

from apps.api.dependencies import get_memory_service
from apps.api.services.memory import MemoryService


def test_get_memory_service_returns_service() -> None:
    """get_memory_service should return MemoryService instance."""
    # Clear cache first to ensure clean state
    get_memory_service.cache_clear()

    with patch("apps.api.adapters.memory.Mem0MemoryAdapter") as mock_adapter_class:
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        service = get_memory_service()
        assert isinstance(service, MemoryService)

        # Cleanup lru_cache for next test
        get_memory_service.cache_clear()


def test_get_memory_service_is_singleton() -> None:
    """get_memory_service should return same instance (singleton via lru_cache)."""
    from apps.api import dependencies

    # Clear both cache and global singleton
    get_memory_service.cache_clear()
    original_singleton = dependencies._memory_service
    dependencies._memory_service = None

    try:
        # First call creates and caches the service
        service1 = get_memory_service()
        # Second call returns cached instance
        service2 = get_memory_service()
        # Third call still returns same instance
        service3 = get_memory_service()

        # Verify same instance returned (singleton behavior guaranteed by lru_cache)
        assert service1 is service2
        assert service2 is service3
        assert isinstance(service1, MemoryService)
    finally:
        # Restore original state
        dependencies._memory_service = original_singleton
        get_memory_service.cache_clear()
