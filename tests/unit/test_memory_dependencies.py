"""Tests for memory dependency injection."""

from unittest.mock import MagicMock, patch

from apps.api.dependencies import get_memory_service
from apps.api.services.memory import MemoryService


def test_get_memory_service_returns_service() -> None:
    """get_memory_service should return MemoryService instance."""
    with patch("apps.api.dependencies.Mem0MemoryAdapter") as mock_adapter_class:
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        service = get_memory_service()
        assert isinstance(service, MemoryService)

        # Cleanup lru_cache for next test
        get_memory_service.cache_clear()


def test_get_memory_service_is_singleton() -> None:
    """get_memory_service should return same instance (singleton)."""
    with patch("apps.api.dependencies.Mem0MemoryAdapter") as mock_adapter_class:
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        service1 = get_memory_service()
        service2 = get_memory_service()
        assert service1 is service2

        # Verify adapter was only created once (singleton)
        mock_adapter_class.assert_called_once()

        # Cleanup lru_cache
        get_memory_service.cache_clear()
