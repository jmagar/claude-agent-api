"""Unit tests for SessionRepository (Priority 2).

Tests all CRUD operations, relationships, cascades, and error conditions
for the session repository layer.
"""

from collections.abc import AsyncGenerator
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.adapters.session_repo import SessionRepository
from apps.api.dependencies import get_db
from apps.api.exceptions.session import SessionNotFoundError
from apps.api.models.session import Checkpoint, Session, SessionMessage


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


@pytest.fixture
def repository(db_session: AsyncSession) -> SessionRepository:
    """Create SessionRepository with test database.

    Args:
        db_session: Test database session.

    Returns:
        SessionRepository instance.
    """
    return SessionRepository(db_session)


class TestSessionCreate:
    """Tests for session creation."""

    @pytest.mark.anyio
    async def test_create_session_persists_to_database(
        self,
        repository: SessionRepository,
        db_session: AsyncSession,
    ) -> None:
        """Test that creating a session persists to database.

        GREEN: This test verifies basic session creation.
        """
        session_id = uuid4()
        model = "sonnet"

        session = await repository.create(session_id, model)

        assert session.id == session_id
        assert session.model == model
        assert session.status == "active"
        assert session.total_turns == 0
        assert session.created_at is not None

        # Verify in database
        stmt = select(Session).where(Session.id == session_id)
        result = await db_session.execute(stmt)
        db_session_record = result.scalar_one_or_none()
        assert db_session_record is not None
        assert db_session_record.id == session_id

    @pytest.mark.anyio
    async def test_create_session_with_parent_id(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test creating a session with parent relationship.

        GREEN: This test verifies session forking/parent relationships.
        """
        # Create parent session
        parent_id = uuid4()
        await repository.create(parent_id, "sonnet")

        # Create child session
        child_id = uuid4()
        child = await repository.create(
            child_id,
            "sonnet",
            parent_session_id=parent_id,
        )

        assert child.parent_session_id == parent_id

    @pytest.mark.anyio
    async def test_create_session_with_metadata(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test creating a session with custom metadata.

        GREEN: This test verifies metadata storage.
        """
        session_id = uuid4()
        metadata: dict[str, object] = {
            "user": "test@example.com",
            "tags": ["production", "demo"],
        }

        session = await repository.create(
            session_id,
            "sonnet",
            metadata=metadata,
        )

        assert session.metadata_ == metadata


class TestSessionGet:
    """Tests for session retrieval."""

    @pytest.mark.anyio
    async def test_get_returns_session_by_id(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test retrieving an existing session.

        GREEN: This test verifies session retrieval.
        """
        session_id = uuid4()
        await repository.create(session_id, "sonnet")

        result = await repository.get(session_id)

        assert result is not None
        assert result.id == session_id

    @pytest.mark.anyio
    async def test_get_returns_none_for_nonexistent(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test handling of missing session.

        GREEN: This test verifies None is returned for missing sessions.
        """
        nonexistent_id = uuid4()

        result = await repository.get(nonexistent_id)

        assert result is None


class TestSessionUpdate:
    """Tests for session updates."""

    @pytest.mark.anyio
    async def test_update_session_status(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test updating session fields.

        GREEN: This test verifies session updates work correctly.
        """
        session_id = uuid4()
        await repository.create(session_id, "sonnet")

        updated = await repository.update(
            session_id,
            status="completed",
            total_turns=5,
            total_cost_usd=0.05,
        )

        assert updated is not None
        assert updated.status == "completed"
        assert updated.total_turns == 5
        assert updated.total_cost_usd == Decimal("0.05")

    @pytest.mark.anyio
    async def test_update_session_atomic_returning(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test update uses atomic RETURNING clause.

        GREEN: This test verifies the update returns the updated row.
        """
        session_id = uuid4()
        await repository.create(session_id, "sonnet")

        # Update should return the updated session in one query
        updated = await repository.update(session_id, status="error")

        # Should get back the updated session without additional query
        assert updated is not None
        assert updated.status == "error"
        assert updated.updated_at is not None


class TestSessionList:
    """Tests for session listing."""

    @pytest.mark.anyio
    async def test_list_sessions_pagination(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test paginated session listing.

        GREEN: This test verifies pagination works correctly.
        """
        # Get initial count
        _, initial_total = await repository.list_sessions(limit=1, offset=0)

        # Create multiple sessions
        created_ids = []
        for _ in range(5):
            session = await repository.create(uuid4(), "sonnet")
            created_ids.append(session.id)

        # Get first 3 from all sessions
        sessions, total = await repository.list_sessions(limit=3, offset=0)

        assert len(sessions) == 3
        # Total should be at least initial + our 5 sessions (may be more due to parallel tests)
        assert total >= initial_total + 5

        # Get next batch
        sessions, total = await repository.list_sessions(limit=3, offset=3)

        assert len(sessions) >= 2  # At least our 2 remaining sessions
        assert total >= initial_total + 5

        # Verify our created sessions exist in the database
        for session_id in created_ids:
            found = await repository.get(session_id)
            assert found is not None
            assert found.id == session_id

    @pytest.mark.anyio
    async def test_list_sessions_filter_by_status(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test filtering sessions by status.

        GREEN: This test verifies status filtering.
        """
        # Get initial completed count
        _, initial_completed = await repository.list_sessions(
            status="completed", limit=1, offset=0
        )

        # Create sessions with different statuses
        id1 = uuid4()
        id2 = uuid4()
        id3 = uuid4()

        await repository.create(id1, "sonnet")
        await repository.create(id2, "sonnet")
        await repository.create(id3, "sonnet")

        # Update some to completed
        await repository.update(id1, status="completed")
        await repository.update(id2, status="completed")

        # Filter by completed with large limit to ensure our sessions are included
        sessions, total = await repository.list_sessions(status="completed", limit=1000)

        # Total may be higher due to parallel tests, but should be at least initial + 2
        assert total >= initial_completed + 2
        assert all(s.status == "completed" for s in sessions)
        # Verify our specific sessions are in the results
        completed_ids = {s.id for s in sessions}
        assert id1 in completed_ids
        assert id2 in completed_ids
        assert id3 not in completed_ids

    @pytest.mark.anyio
    async def test_list_sessions_filter_by_owner_api_key(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test filtering sessions by owner API key."""
        owner_a = "owner-a"
        owner_b = "owner-b"

        id1 = uuid4()
        id2 = uuid4()
        id3 = uuid4()

        await repository.create(id1, "sonnet", owner_api_key=owner_a)
        await repository.create(id2, "sonnet", owner_api_key=owner_a)
        await repository.create(id3, "sonnet", owner_api_key=owner_b)

        sessions, total = await repository.list_sessions(
            owner_api_key=owner_a,
            limit=1000,
        )

        assert total >= 2
        assert all(s.owner_api_key == owner_a for s in sessions)
        found_ids = {s.id for s in sessions}
        assert id1 in found_ids
        assert id2 in found_ids
        assert id3 not in found_ids


class TestSessionMessages:
    """Tests for session message operations."""

    @pytest.mark.anyio
    async def test_add_message_to_session(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test adding a message to a session.

        GREEN: This test verifies message creation.
        """
        session_id = uuid4()
        await repository.create(session_id, "sonnet")

        content: dict[str, object] = {"type": "text", "text": "Hello"}
        message = await repository.add_message(
            session_id,
            "user",
            content,
        )

        assert message.session_id == session_id
        assert message.message_type == "user"
        assert message.content == content

    @pytest.mark.anyio
    async def test_add_message_raises_for_nonexistent_session(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test error handling when adding message to missing session.

        GREEN: This test verifies proper error handling.
        """
        nonexistent_id = uuid4()
        content: dict[str, object] = {"text": "Hello"}

        with pytest.raises(SessionNotFoundError):
            await repository.add_message(
                nonexistent_id,
                "user",
                content,
            )

    @pytest.mark.anyio
    async def test_get_messages_ordered_by_created_at(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test message ordering by creation time.

        GREEN: This test verifies messages are returned in correct order.
        """
        session_id = uuid4()
        await repository.create(session_id, "sonnet")

        # Add multiple messages
        content1: dict[str, object] = {"text": "First"}
        content2: dict[str, object] = {"text": "Second"}
        content3: dict[str, object] = {"text": "Third"}
        msg1 = await repository.add_message(session_id, "user", content1)
        msg2 = await repository.add_message(session_id, "assistant", content2)
        msg3 = await repository.add_message(session_id, "user", content3)

        # Get messages
        messages = await repository.get_messages(session_id)

        assert len(messages) == 3
        assert messages[0].id == msg1.id
        assert messages[1].id == msg2.id
        assert messages[2].id == msg3.id


class TestSessionCheckpoints:
    """Tests for checkpoint operations."""

    @pytest.mark.anyio
    async def test_add_checkpoint(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test checkpoint creation.

        GREEN: This test verifies checkpoint creation.
        """
        session_id = uuid4()
        await repository.create(session_id, "sonnet")

        files = ["/path/to/file1.py", "/path/to/file2.py"]
        message_uuid = str(uuid4())
        checkpoint = await repository.add_checkpoint(
            session_id,
            message_uuid,
            files,
        )

        assert checkpoint.session_id == session_id
        assert checkpoint.user_message_uuid == message_uuid
        assert checkpoint.files_modified == files

    @pytest.mark.anyio
    async def test_get_checkpoints(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test checkpoint retrieval.

        GREEN: This test verifies checkpoint listing.
        """
        session_id = uuid4()
        await repository.create(session_id, "sonnet")

        # Add multiple checkpoints
        uuid1 = str(uuid4())
        uuid2 = str(uuid4())
        await repository.add_checkpoint(session_id, uuid1, ["/file1.py"])
        await repository.add_checkpoint(session_id, uuid2, ["/file2.py"])

        # Get checkpoints
        checkpoints = await repository.get_checkpoints(session_id)

        assert len(checkpoints) == 2
        assert checkpoints[0].user_message_uuid == uuid1
        assert checkpoints[1].user_message_uuid == uuid2


class TestSessionDelete:
    """Tests for session deletion."""

    @pytest.mark.anyio
    async def test_delete_session_cascades(
        self,
        repository: SessionRepository,
        db_session: AsyncSession,
    ) -> None:
        """Test session deletion cascades to messages and checkpoints.

        GREEN: This test verifies cascade deletion works correctly.
        """
        session_id = uuid4()
        await repository.create(session_id, "sonnet")

        # Add message and checkpoint
        content: dict[str, object] = {"text": "Hello"}
        await repository.add_message(session_id, "user", content)
        checkpoint_uuid = str(uuid4())
        await repository.add_checkpoint(session_id, checkpoint_uuid, ["/file.py"])

        # Delete session
        deleted = await repository.delete_session(session_id)

        assert deleted is True

        # Verify session is gone
        session = await repository.get(session_id)
        assert session is None

        # Verify messages are gone
        msg_stmt = select(SessionMessage).where(SessionMessage.session_id == session_id)
        msg_result = await db_session.execute(msg_stmt)
        messages = msg_result.scalars().all()
        assert len(messages) == 0

        # Verify checkpoints are gone
        cp_stmt = select(Checkpoint).where(Checkpoint.session_id == session_id)
        cp_result = await db_session.execute(cp_stmt)
        checkpoints = cp_result.scalars().all()
        assert len(checkpoints) == 0
