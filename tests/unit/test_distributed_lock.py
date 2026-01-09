"""Unit tests for distributed locking in session operations."""

import asyncio
from uuid import uuid4

import pytest

from apps.api.adapters.cache import RedisCache
from apps.api.services.session import SessionService


@pytest.mark.unit
@pytest.mark.anyio
async def test_concurrent_session_updates_with_distributed_lock() -> None:
    """Test that concurrent updates to same session are serialized with lock."""
    from datetime import UTC, datetime

    from apps.api.config import get_settings
    from apps.api.services.session import Session

    settings = get_settings()
    cache = await RedisCache.create(settings.redis_url)
    service = SessionService(cache=cache, db_repo=None)

    session_id = str(uuid4())

    # Create session in cache
    session = Session(
        id=session_id,
        model="sonnet",
        status="active",
        total_turns=0,
        total_cost_usd=None,
        parent_session_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    await service._cache_session(session)

    # Simulate concurrent updates from two instances
    async def update_turn_count(instance_id: int) -> None:
        for _ in range(5):
            # update_session uses distributed lock for atomic read-modify-write
            await service.update_session(
                session_id,
                increment_turns=True,  # Atomically increment with lock
            )
            await asyncio.sleep(0.01)  # Simulate processing time

    # Run concurrent updates
    await asyncio.gather(
        update_turn_count(1),
        update_turn_count(2),
    )

    # Verify final count is correct (10 = 5 + 5)
    final = await service.get_session(session_id)
    assert final is not None
    # Note: Without locking, this would be < 10 due to race conditions
    # With locking, it should be exactly 10
    assert final.total_turns == 10

    # Cleanup
    await cache.close()
