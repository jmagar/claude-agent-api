"""Integration tests for distributed session state management."""

import pytest
from httpx import AsyncClient
from uuid import uuid4

from apps.api.dependencies import get_cache
from apps.api.services.agent.service import AgentService


@pytest.mark.integration
@pytest.mark.anyio
async def test_active_session_registered_in_redis(_async_client: AsyncClient):
    """Test that active sessions are tracked in Redis, not in-memory."""
    cache = await get_cache()
    service = AgentService(cache=cache)

    session_id = str(uuid4())

    # Register session as active
    await service._register_active_session(session_id)

    # Verify it's in Redis, not just in-memory
    is_active = await service._is_session_active(session_id)
    assert is_active is True

    # Verify it's in Redis directly (not in-memory dict)
    redis_key = f"active_session:{session_id}"
    redis_value = await cache.exists(redis_key)
    assert redis_value is True


@pytest.mark.integration
@pytest.mark.anyio
async def test_interrupt_signal_propagates_across_instances(_async_client: AsyncClient):
    """Test that interrupt signals propagate via Redis pub/sub."""
    cache = await get_cache()

    # Create two service instances (simulating two API pods)
    service1 = AgentService(cache=cache)
    service2 = AgentService(cache=cache)

    session_id = str(uuid4())

    # Register session as active in instance 1
    await service1._register_active_session(session_id)

    # Instance 2 interrupts the session
    await service2.interrupt(session_id)

    # Instance 1 should detect the interrupt
    is_interrupted = await service1._check_interrupt(session_id)
    assert is_interrupted is True

    # Verify interrupt marker exists in Redis
    interrupt_key = f"interrupted:{session_id}"
    exists = await cache.exists(interrupt_key)
    assert exists is True
