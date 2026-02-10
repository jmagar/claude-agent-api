"""Integration tests for SessionService cache operations with hashed API keys.

Tests verify that SessionService correctly uses hashed API keys for cache indexes
and ownership enforcement (Phase 2 migration).

Coverage:
- Cache index uses hashed owner keys
- Delete removes hashed index entries
- List operations use cache with hashed keys
- Ownership enforcement uses hashed keys
"""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.adapters.session_repo import SessionRepository
from apps.api.dependencies import get_cache, get_db
from apps.api.exceptions.session import SessionNotFoundError
from apps.api.protocols import Cache
from apps.api.services.session import SessionService
from apps.api.utils.crypto import hash_api_key


@pytest.fixture
async def db_session(_async_client: AsyncClient) -> AsyncGenerator[AsyncSession, None]:
    """Get database session from initialized app.

    Args:
        _async_client: Initialized test client.

    Yields:
        Async database session.
    """
    agen = get_db()
    session = await anext(agen)
    try:
        yield session
    finally:
        await agen.aclose()


@pytest.fixture
async def redis_cache(_async_client: AsyncClient) -> Cache:
    """Get Redis cache instance from initialized app.

    Args:
        _async_client: Initialized test client.

    Returns:
        Cache protocol implementation (Redis adapter).
    """
    return await get_cache()


@pytest.fixture
async def session_service(
    db_session: AsyncSession,
    redis_cache: Cache,
) -> SessionService:
    """Create SessionService with real DB and Redis dependencies.

    Args:
        db_session: Real async database session.
        redis_cache: Real Redis cache instance.

    Returns:
        SessionService configured with database and cache.
    """
    repository = SessionRepository(db_session)
    return SessionService(cache=redis_cache, db_repo=repository)


class TestSessionServiceCacheHashing:
    """Tests that SessionService cache operations use hashed API keys."""

    @pytest.mark.anyio
    async def test_session_service_cache_uses_hashed_owner_index(
        self,
        session_service: SessionService,
        redis_cache: Cache,
    ) -> None:
        """SessionService should create hashed owner index in Redis cache."""
        # Use unique API key to avoid test conflicts
        api_key = f"owner-{uuid4()}"
        session_id = str(uuid4())

        # Create session with owner
        session = await session_service.create_session(
            model="sonnet",
            session_id=session_id,
            owner_api_key=api_key,
        )

        assert session.id == session_id
        # Phase 3: Check via hash (plaintext column removed)
        assert session.owner_api_key_hash == hash_api_key(api_key)

        # Verify Redis cache has hashed owner index key
        hashed_key = hash_api_key(api_key)
        owner_index_key = f"session:owner:{hashed_key}"

        # Check that session ID is in the owner index set
        session_ids = await redis_cache.set_members(owner_index_key)
        assert session_id in session_ids

        # Verify plaintext API key is NOT used as index
        plaintext_index_key = f"session:owner:{api_key}"
        plaintext_members = await redis_cache.set_members(plaintext_index_key)
        assert session_id not in plaintext_members

        # Verify list_sessions uses the hashed index (cache hit)
        result = await session_service.list_sessions(current_api_key=api_key)
        assert result.total >= 1
        session_found = any(s.id == session_id for s in result.sessions)
        assert session_found, "Session should be found via hashed owner index"

    @pytest.mark.anyio
    async def test_session_service_delete_removes_hashed_index(
        self,
        session_service: SessionService,
        redis_cache: Cache,
    ) -> None:
        """SessionService.delete_session should remove session from hashed owner index."""
        # Use unique API key to avoid test conflicts
        api_key = f"owner-{uuid4()}"
        session_id = str(uuid4())

        # Create session with owner
        await session_service.create_session(
            model="sonnet",
            session_id=session_id,
            owner_api_key=api_key,
        )

        # Verify session is in hashed owner index
        hashed_key = hash_api_key(api_key)
        owner_index_key = f"session:owner:{hashed_key}"
        session_ids_before = await redis_cache.set_members(owner_index_key)
        assert session_id in session_ids_before

        # Delete session
        deleted = await session_service.delete_session(session_id)
        assert deleted is True

        # Verify hashed owner index key no longer contains session ID
        session_ids_after = await redis_cache.set_members(owner_index_key)
        assert session_id not in session_ids_after

        # Verify session is actually deleted from cache
        cache_key = f"session:{session_id}"
        exists = await redis_cache.exists(cache_key)
        assert not exists, "Session should be removed from cache"

    @pytest.mark.anyio
    async def test_session_service_list_uses_cache_with_hash(
        self,
        session_service: SessionService,
        redis_cache: Cache,
    ) -> None:
        """SessionService.list_sessions should use hashed keys for cache operations."""
        # Use unique API key to avoid test conflicts
        api_key = f"owner-{uuid4()}"

        # Create multiple sessions via SessionService
        session_ids = []
        for _ in range(3):
            session_id = str(uuid4())
            await session_service.create_session(
                model="sonnet",
                session_id=session_id,
                owner_api_key=api_key,
            )
            session_ids.append(session_id)

        # Verify all sessions are in hashed owner index
        hashed_key = hash_api_key(api_key)
        owner_index_key = f"session:owner:{hashed_key}"
        cached_session_ids = await redis_cache.set_members(owner_index_key)

        for session_id in session_ids:
            assert session_id in cached_session_ids

        # Verify plaintext key is NOT used
        plaintext_index_key = f"session:owner:{api_key}"
        plaintext_members = await redis_cache.set_members(plaintext_index_key)
        for session_id in session_ids:
            assert session_id not in plaintext_members

        # List sessions by owner (should use hashed cache index)
        result = await session_service.list_sessions(current_api_key=api_key)

        # Should return at least our 3 sessions
        assert result.total >= 3

        # Verify all our sessions are in the result
        result_ids = {s.id for s in result.sessions}
        for session_id in session_ids:
            assert session_id in result_ids, (
                f"Session {session_id} should be in results"
            )

        # Verify sessions have correct owner (check via hash, plaintext removed in Phase 3)
        api_key_hash = hash_api_key(api_key)
        for session in result.sessions:
            if session.id in session_ids:
                assert session.owner_api_key_hash == api_key_hash

    @pytest.mark.anyio
    async def test_session_service_enforce_owner_uses_hash(
        self,
        session_service: SessionService,
    ) -> None:
        """SessionService should enforce ownership using hashed API key comparison."""
        # Create two different API keys (unique per test run)
        owner_a = f"owner-a-{uuid4()}"
        owner_b = f"owner-b-{uuid4()}"

        # Create session owned by A
        session_id = str(uuid4())
        session = await session_service.create_session(
            model="sonnet",
            session_id=session_id,
            owner_api_key=owner_a,
        )

        # Phase 3: Check via hash (plaintext column removed)
        assert session.owner_api_key_hash == hash_api_key(owner_a)

        # Attempt to get session with wrong API key (owner B)
        with pytest.raises(SessionNotFoundError) as exc_info:
            await session_service.get_session(
                session_id,
                current_api_key=owner_b,
            )

        # Verify error contains session ID
        assert session_id in str(exc_info.value)

        # Verify correct key works (owner A can access)
        retrieved = await session_service.get_session(
            session_id,
            current_api_key=owner_a,
        )

        assert retrieved is not None
        assert retrieved.id == session_id
        # Phase 3: Check via hash (plaintext column removed)
        assert retrieved.owner_api_key_hash == hash_api_key(owner_a)

        # Verify different key (owner B) cannot access owned session
        with pytest.raises(SessionNotFoundError):
            await session_service.get_session(
                session_id,
                current_api_key=owner_b,
            )

    @pytest.mark.anyio
    async def test_session_service_update_preserves_hashed_index(
        self,
        session_service: SessionService,
        redis_cache: Cache,
    ) -> None:
        """SessionService.update_session should preserve hashed owner index."""
        # Use unique API key to avoid test conflicts
        api_key = f"owner-{uuid4()}"
        session_id = str(uuid4())

        # Create session with owner
        await session_service.create_session(
            model="sonnet",
            session_id=session_id,
            owner_api_key=api_key,
        )

        # Update session
        updated = await session_service.update_session(
            session_id,
            status="completed",
            total_turns=5,
            current_api_key=api_key,
        )

        assert updated is not None
        assert updated.status == "completed"
        assert updated.total_turns == 5

        # Verify hashed owner index still contains session ID
        hashed_key = hash_api_key(api_key)
        owner_index_key = f"session:owner:{hashed_key}"
        session_ids = await redis_cache.set_members(owner_index_key)
        assert session_id in session_ids

        # Verify session can still be listed
        result = await session_service.list_sessions(current_api_key=api_key)
        session_found = any(s.id == session_id for s in result.sessions)
        assert session_found, "Updated session should still be in owner index"

    @pytest.mark.anyio
    async def test_session_service_null_owner_has_no_index(
        self,
        session_service: SessionService,
        redis_cache: Cache,
    ) -> None:
        """Sessions with NULL owner_api_key should not create owner index entries."""
        session_id = str(uuid4())

        # Create session without owner (public session)
        session = await session_service.create_session(
            model="sonnet",
            session_id=session_id,
            owner_api_key=None,
        )

        # Phase 3: Only hash column exists (plaintext removed)
        assert session.owner_api_key_hash is None

        # Verify no owner index was created (check common hash patterns)
        # Hash of empty string
        empty_hash = hash_api_key("")
        empty_index_key = f"session:owner:{empty_hash}"
        empty_members = await redis_cache.set_members(empty_index_key)
        assert session_id not in empty_members

        # Hash of "None" string
        none_hash = hash_api_key("None")
        none_index_key = f"session:owner:{none_hash}"
        none_members = await redis_cache.set_members(none_index_key)
        assert session_id not in none_members

        # Verify session exists in cache by direct key
        cache_key = f"session:{session_id}"
        exists = await redis_cache.exists(cache_key)
        assert exists, "Public session should exist in cache"

    @pytest.mark.anyio
    async def test_session_service_different_keys_different_indexes(
        self,
        session_service: SessionService,
        redis_cache: Cache,
    ) -> None:
        """Different API keys should create different hashed owner indexes."""
        # Create two unique API keys
        api_key_1 = f"owner-1-{uuid4()}"
        api_key_2 = f"owner-2-{uuid4()}"

        session_id_1 = str(uuid4())
        session_id_2 = str(uuid4())

        # Create session with owner 1
        await session_service.create_session(
            model="sonnet",
            session_id=session_id_1,
            owner_api_key=api_key_1,
        )

        # Create session with owner 2
        await session_service.create_session(
            model="sonnet",
            session_id=session_id_2,
            owner_api_key=api_key_2,
        )

        # Verify owner 1's hashed index contains only their session
        hash_1 = hash_api_key(api_key_1)
        index_1 = f"session:owner:{hash_1}"
        members_1 = await redis_cache.set_members(index_1)
        assert session_id_1 in members_1
        assert session_id_2 not in members_1

        # Verify owner 2's hashed index contains only their session
        hash_2 = hash_api_key(api_key_2)
        index_2 = f"session:owner:{hash_2}"
        members_2 = await redis_cache.set_members(index_2)
        assert session_id_2 in members_2
        assert session_id_1 not in members_2

        # Verify hashes are different
        assert hash_1 != hash_2
        assert index_1 != index_2

    @pytest.mark.anyio
    async def test_session_service_same_key_same_hash_across_sessions(
        self,
        session_service: SessionService,
        redis_cache: Cache,
    ) -> None:
        """Same API key should produce identical hash across multiple sessions."""
        # Use shared API key for multiple sessions
        shared_api_key = f"shared-owner-{uuid4()}"

        session_id_1 = str(uuid4())
        session_id_2 = str(uuid4())

        # Create two sessions with same owner
        await session_service.create_session(
            model="sonnet",
            session_id=session_id_1,
            owner_api_key=shared_api_key,
        )

        await session_service.create_session(
            model="sonnet",
            session_id=session_id_2,
            owner_api_key=shared_api_key,
        )

        # Verify both sessions are in the same hashed owner index
        hashed_key = hash_api_key(shared_api_key)
        owner_index_key = f"session:owner:{hashed_key}"
        session_ids = await redis_cache.set_members(owner_index_key)

        assert session_id_1 in session_ids
        assert session_id_2 in session_ids

        # Verify list_sessions returns both sessions
        result = await session_service.list_sessions(current_api_key=shared_api_key)
        result_ids = {s.id for s in result.sessions}
        assert session_id_1 in result_ids
        assert session_id_2 in result_ids
