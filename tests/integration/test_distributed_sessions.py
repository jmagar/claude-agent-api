"""Integration tests for distributed session state management."""

import pytest
from httpx import AsyncClient
from uuid import uuid4

from apps.api.dependencies import get_cache, get_db
from apps.api.services.agent.service import AgentService
from apps.api.services.session import SessionService
from apps.api.adapters.session_repo import SessionRepository


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


@pytest.mark.integration
@pytest.mark.anyio
async def test_session_fallback_to_database_when_cache_miss(_async_client: AsyncClient):
    """Test that sessions fall back to PostgreSQL when not in Redis cache."""
    from uuid import UUID

    cache = await get_cache()

    async for db_session in get_db():
        repo = SessionRepository(db_session)
        service = SessionService(cache=cache, db_repo=repo)

        # Create session directly in database (bypassing service layer)
        session_id = uuid4()
        db_record = await repo.create(
            session_id=session_id,
            model="sonnet",
            working_directory=None,
            parent_session_id=None,
            metadata=None,
        )

        # Note: Session is NOT in Redis cache (simulating cache expiration or cold start)

        # Should still retrieve from PostgreSQL
        retrieved = await service.get_session(str(session_id))

        assert retrieved is not None
        assert retrieved.id == str(session_id)
        assert retrieved.model == "sonnet"

        # Verify it was re-cached after retrieval
        cache_key = f"session:{session_id}"
        cached_after = await cache.get_json(cache_key)
        assert cached_after is not None

        break


@pytest.mark.integration
@pytest.mark.anyio
async def test_session_create_writes_to_both_db_and_cache(_async_client: AsyncClient):
    """Test that creating a session writes to both PostgreSQL and Redis."""
    from apps.api.dependencies import get_db

    cache = await get_cache()

    async for db_session in get_db():
        repo = SessionRepository(db_session)
        service = SessionService(cache=cache, db_repo=repo)

        # Create session
        session = await service.create_session(
            model="opus",
            session_id=None,
        )
        session_id = session.id

        # Verify it's in Redis cache
        cache_key = f"session:{session_id}"
        cached = await cache.get_json(cache_key)
        assert cached is not None
        assert cached["model"] == "opus"

        # Verify it's in PostgreSQL
        from uuid import UUID
        db_session_result = await repo.get(UUID(session_id))
        assert db_session_result is not None
        assert db_session_result.model == "opus"

        break
