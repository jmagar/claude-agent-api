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
