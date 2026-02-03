"""Integration tests for API key hashing (Phase 2 migration)."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.adapters.session_repo import SessionRepository
from apps.api.dependencies import get_db
from apps.api.models.session import Session
from apps.api.utils.crypto import hash_api_key


@pytest.fixture
async def db_session(_async_client: AsyncClient) -> AsyncGenerator[AsyncSession, None]:
    """Get database session from initialized app.

    Args:
        async_client: Initialized test client.

    Yields:
        Async database session.
    """
    # Get database session from dependencies
    agen = get_db()
    session = await anext(agen)
    try:
        yield session
    finally:
        await agen.aclose()


class TestSessionRepositoryHashing:
    """Tests that SessionRepository hashes API keys correctly."""

    @pytest.mark.anyio
    @pytest.mark.anyio
    async def test_create_hashes_owner_api_key(self, db_session: AsyncSession) -> None:
        """SessionRepository.create() should hash owner_api_key before storage."""
        repository = SessionRepository(db_session)
        session_id = uuid4()
        api_key = "test-key-12345"

        # Create session with API key
        await repository.create(
            session_id=session_id,
            model="sonnet",
            owner_api_key=api_key,
        )

        # Verify hash column is populated
        stmt = select(Session).where(Session.id == session_id)
        result = await db_session.execute(stmt)
        session = result.scalar_one()

        # Phase 3: Only hash column exists (plaintext removed)
        assert session.owner_api_key_hash is not None
        assert session.owner_api_key_hash == hash_api_key(api_key)

    @pytest.mark.anyio
    async def test_create_handles_null_owner_api_key(self, db_session: AsyncSession) -> None:
        """SessionRepository.create() should handle NULL owner_api_key."""
        repository = SessionRepository(db_session)
        session_id = uuid4()

        # Create session without API key (public session)
        await repository.create(
            session_id=session_id,
            model="sonnet",
            owner_api_key=None,
        )

        # Verify hash column is also NULL
        stmt = select(Session).where(Session.id == session_id)
        result = await db_session.execute(stmt)
        session = result.scalar_one()

        # Phase 3: Only hash column exists (plaintext removed)
        assert session.owner_api_key_hash is None

    @pytest.mark.anyio
    async def test_list_sessions_filters_by_hashed_key(
        self, db_session: AsyncSession
    ) -> None:
        """SessionRepository.list_sessions() should filter by hashed API key."""
        repository = SessionRepository(db_session)

        # Use unique API keys per test run to avoid conflicts
        owner_a = f"owner-a-{uuid4()}"
        owner_b = f"owner-b-{uuid4()}"

        id_a1 = uuid4()
        id_a2 = uuid4()
        id_b = uuid4()

        await repository.create(id_a1, "sonnet", owner_api_key=owner_a)
        await repository.create(id_a2, "sonnet", owner_api_key=owner_a)
        await repository.create(id_b, "sonnet", owner_api_key=owner_b)

        # List sessions for owner A
        sessions, total = await repository.list_sessions(owner_api_key=owner_a)

        # Should only return sessions owned by A
        assert total == 2
        assert len(sessions) == 2
        assert {s.id for s in sessions} == {id_a1, id_a2}

        # Verify filtering used hashed comparison
        for session in sessions:
            assert session.owner_api_key_hash == hash_api_key(owner_a)

    @pytest.mark.anyio
    async def test_list_sessions_filter_by_owner_or_public_uses_hash(
        self, db_session: AsyncSession
    ) -> None:
        """list_sessions with filter_by_owner_or_public should use hashed keys."""
        repository = SessionRepository(db_session)

        # Use unique API keys per test run
        public_id = uuid4()
        owner_a_id = uuid4()
        owner_b_id = uuid4()

        owner_a = f"owner-a-{uuid4()}"
        owner_b = f"owner-b-{uuid4()}"

        await repository.create(public_id, "sonnet", owner_api_key=None)
        await repository.create(owner_a_id, "sonnet", owner_api_key=owner_a)
        await repository.create(owner_b_id, "sonnet", owner_api_key=owner_b)

        # List sessions for owner A (public + owned)
        sessions, total = await repository.list_sessions(
            owner_api_key=owner_a,
            filter_by_owner_or_public=True,
        )

        # Should return public sessions + owner A session
        # Total might include other public sessions from previous tests
        assert total >= 2

        # Verify both our sessions are included
        session_ids = {s.id for s in sessions}
        assert public_id in session_ids
        assert owner_a_id in session_ids

        # Verify owner B session is NOT included
        assert owner_b_id not in session_ids

        # Verify owner A session uses hashed key
        owner_a_session = next(s for s in sessions if s.id == owner_a_id)
        assert owner_a_session.owner_api_key_hash == hash_api_key(owner_a)

        # Verify public session has NULL hash
        public_session = next(s for s in sessions if s.id == public_id)
        assert public_session.owner_api_key_hash is None

    @pytest.mark.anyio
    async def test_different_keys_produce_different_hashes(
        self, db_session: AsyncSession
    ) -> None:
        """Different API keys should produce different hash values."""
        repository = SessionRepository(db_session)

        id1 = uuid4()
        id2 = uuid4()

        key1 = "key-1"
        key2 = "key-2"

        await repository.create(id1, "sonnet", owner_api_key=key1)
        await repository.create(id2, "sonnet", owner_api_key=key2)

        # Retrieve sessions
        stmt = select(Session).where(Session.id.in_([id1, id2]))
        result = await db_session.execute(stmt)
        sessions = result.scalars().all()

        hash1 = next(s.owner_api_key_hash for s in sessions if s.id == id1)
        hash2 = next(s.owner_api_key_hash for s in sessions if s.id == id2)

        assert hash1 != hash2
        assert hash1 == hash_api_key(key1)
        assert hash2 == hash_api_key(key2)

    @pytest.mark.anyio
    async def test_same_key_produces_same_hash(self, db_session: AsyncSession) -> None:
        """Same API key should produce identical hash across sessions."""
        repository = SessionRepository(db_session)

        id1 = uuid4()
        id2 = uuid4()

        api_key = "shared-key"

        await repository.create(id1, "sonnet", owner_api_key=api_key)
        await repository.create(id2, "sonnet", owner_api_key=api_key)

        # Retrieve sessions
        stmt = select(Session).where(Session.id.in_([id1, id2]))
        result = await db_session.execute(stmt)
        sessions = result.scalars().all()

        hash1 = next(s.owner_api_key_hash for s in sessions if s.id == id1)
        hash2 = next(s.owner_api_key_hash for s in sessions if s.id == id2)

        # Both sessions should have identical hash
        assert hash1 == hash2
        assert hash1 == hash_api_key(api_key)
