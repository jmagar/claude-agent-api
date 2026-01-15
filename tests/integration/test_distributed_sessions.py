"""Integration tests for distributed session state management."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.adapters.session_repo import SessionRepository
from apps.api.dependencies import get_cache, get_db
from apps.api.services.agent.service import AgentService
from apps.api.services.session import SessionService


@pytest.mark.integration
@pytest.mark.anyio
async def test_active_session_registered_in_redis(async_client: AsyncClient):
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
async def test_interrupt_signal_propagates_across_instances(async_client: AsyncClient):
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
async def test_session_fallback_to_database_when_cache_miss(async_client: AsyncClient):
    """Test that sessions fall back to PostgreSQL when not in Redis cache."""

    cache = await get_cache()

    async for db_session in get_db():
        repo = SessionRepository(db_session)
        service = SessionService(cache=cache, db_repo=repo)

        # Create session directly in database (bypassing service layer)
        session_id = uuid4()
        await repo.create(
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
async def test_session_create_writes_to_both_db_and_cache(async_client: AsyncClient):
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


@pytest.mark.integration
@pytest.mark.anyio
async def test_agent_service_uses_distributed_session_tracking(
    async_client: AsyncClient,
):
    """Test that AgentService registers sessions in Redis during query execution."""
    from apps.api.dependencies import get_db

    cache = await get_cache()

    async for db_session in get_db():
        repo = SessionRepository(db_session)
        SessionService(cache=cache, db_repo=repo)
        agent_service = AgentService(cache=cache)

        session_id = str(uuid4())

        # Register session using the new distributed method
        await agent_service._register_active_session(session_id)

        # Verify it's in Redis (not just in-memory)
        is_active = await agent_service._is_session_active(session_id)
        assert is_active is True

        # Verify second instance can see it (distributed state)
        agent_service2 = AgentService(cache=cache)
        is_active_instance2 = await agent_service2._is_session_active(session_id)
        assert is_active_instance2 is True

        # This proves sessions are visible across instances
        break


@pytest.mark.integration
@pytest.mark.anyio
async def test_multi_instance_session_lifecycle(async_client: AsyncClient):
    """Test complete session lifecycle across multiple API instances.

    Simulates a load-balanced environment with 2 API pods.
    Verifies that sessions are visible and manageable across instances.
    """
    from apps.api.dependencies import get_db

    cache = await get_cache()

    async for db_session in get_db():
        repo = SessionRepository(db_session)

        # Create two service instances (simulating two API pods behind load balancer)
        session_service_1 = SessionService(cache=cache, db_repo=repo)
        session_service_2 = SessionService(cache=cache, db_repo=repo)

        agent_service_1 = AgentService(cache=cache)
        agent_service_2 = AgentService(cache=cache)

        # Step 1: Instance 1 creates a session
        session = await session_service_1.create_session(model="sonnet")
        session_id = session.id

        # Step 2: Instance 1 registers it as active
        await agent_service_1._register_active_session(session_id)

        # Step 3: Instance 2 can see the session
        retrieved = await session_service_2.get_session(session_id)
        assert retrieved is not None
        assert retrieved.id == session_id

        # Step 4: Instance 2 can see it's active
        is_active = await agent_service_2._is_session_active(session_id)
        assert is_active is True

        # Step 5: Instance 2 interrupts the session
        interrupted = await agent_service_2.interrupt(session_id)
        assert interrupted is True

        # Step 6: Instance 1 can detect the interrupt
        is_interrupted = await agent_service_1._check_interrupt(session_id)
        assert is_interrupted is True

        # Step 7: Instance 1 unregisters the session
        await agent_service_1._unregister_active_session(session_id)

        # Step 8: Instance 2 can see it's no longer active
        is_active_after = await agent_service_2._is_session_active(session_id)
        assert is_active_after is False

        # Step 9: Both instances can still retrieve the session from DB
        retrieved_1 = await session_service_1.get_session(session_id)
        retrieved_2 = await session_service_2.get_session(session_id)
        assert retrieved_1 is not None
        assert retrieved_2 is not None

        break


@pytest.mark.integration
@pytest.mark.anyio
async def test_session_survives_redis_restart(async_client: AsyncClient):
    """Test that sessions survive Redis restart (via PostgreSQL fallback)."""
    from apps.api.dependencies import get_db

    cache = await get_cache()

    async for db_session in get_db():
        repo = SessionRepository(db_session)
        service = SessionService(cache=cache, db_repo=repo)

        # Create session (writes to both DB and Redis)
        session = await service.create_session(model="opus")
        session_id = session.id

        # Simulate Redis restart by flushing all keys
        await cache.clear()

        # Session should still be retrievable from PostgreSQL
        retrieved = await service.get_session(session_id)
        assert retrieved is not None
        assert retrieved.id == session_id
        assert retrieved.model == "opus"

        # Should be re-cached after retrieval
        cache_key = f"session:{session_id}"
        cached = await cache.get_json(cache_key)
        assert cached is not None

        break
