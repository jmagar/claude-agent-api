"""Tests for memory dependency injection (M-02, ARC-05)."""

from unittest.mock import MagicMock, patch

import pytest

from apps.api.dependencies import AppState, get_memory_service, reset_dependencies
from apps.api.services.memory import MemoryService


@pytest.mark.anyio
async def test_get_memory_service_returns_service() -> None:
    """get_memory_service should return MemoryService instance from AppState."""
    # Create fresh state
    state = AppState()

    with patch("apps.api.adapters.memory.Mem0MemoryAdapter") as mock_adapter_class:
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        service = await get_memory_service(state=state)
        assert isinstance(service, MemoryService)


@pytest.mark.anyio
async def test_get_memory_service_is_singleton() -> None:
    """get_memory_service should return same instance (singleton via AppState)."""
    # Create fresh state (no singleton set)
    state = AppState()

    # First call creates and caches the service
    service1 = await get_memory_service(state=state)
    # Second call returns cached instance
    service2 = await get_memory_service(state=state)
    # Third call still returns same instance
    service3 = await get_memory_service(state=state)

    # Verify same instance returned (singleton behavior via state.memory_service)
    assert service1 is service2
    assert service2 is service3
    assert isinstance(service1, MemoryService)


@pytest.mark.anyio
async def test_get_memory_service_respects_test_singleton() -> None:
    """get_memory_service should return test singleton if set (M-02, M-13)."""
    # Create state with singleton
    state = AppState()
    mock_service = MagicMock(spec=MemoryService)
    state.memory_service = mock_service

    # Should return singleton
    service = await get_memory_service(state=state)
    assert service is mock_service

    # Reset and verify fresh instance created
    reset_dependencies(state)
    service2 = await get_memory_service(state=state)
    assert service2 is not mock_service
