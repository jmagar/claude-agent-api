"""Unit tests for SessionService (T042)."""

import pytest

from apps.api.exceptions import SessionNotFoundError
from apps.api.services.session import SessionService
from apps.api.types import JsonValue


class MockCache:
    """Mock cache that stores data in memory.

    Implements the Cache protocol for testing purposes.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, JsonValue]] = {}
        self.get_many_calls = 0

    async def get(self, key: str) -> str | None:
        """Get string value from cache."""
        value = self._store.get(key)
        if value is None:
            return None
        import json

        return json.dumps(value)

    async def cache_set(self, key: str, value: str, ttl: int | None = None) -> bool:
        """Set string value in cache."""
        import json

        self._store[key] = json.loads(value)
        return True

    async def get_json(self, key: str) -> dict[str, JsonValue] | None:
        """Get JSON value from cache."""
        return self._store.get(key)

    async def set_json(
        self, key: str, value: dict[str, JsonValue], ttl: int | None = None
    ) -> bool:
        """Set JSON value in cache."""
        self._store[key] = value
        return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._store

    async def scan_keys(self, pattern: str) -> list[str]:
        """Scan for keys matching pattern."""
        # Simple pattern matching for session:* pattern
        if pattern == "session:*":
            return [k for k in self._store if k.startswith("session:")]
        return list(self._store.keys())

    async def clear(self) -> bool:
        """Clear all cached values."""
        self._store.clear()
        return True

    async def add_to_set(self, key: str, value: str) -> bool:
        """Add value to set (not implemented for tests)."""
        return True

    async def remove_from_set(self, key: str, value: str) -> bool:
        """Remove value from set (not implemented for tests)."""
        return True

    async def set_members(self, key: str) -> set[str]:
        """Get set members (not implemented for tests)."""
        return set()

    async def acquire_lock(
        self, key: str, ttl: int = 300, value: str | None = None
    ) -> str | None:
        """Acquire lock (not implemented for tests)."""
        return "mock-lock-value"

    async def release_lock(self, key: str, value: str) -> bool:
        """Release lock (not implemented for tests)."""
        return True

    async def ping(self) -> bool:
        """Check connectivity."""
        return True

    async def get_many_json(
        self, keys: list[str]
    ) -> list[dict[str, JsonValue] | None]:
        """Get multiple JSON values (tracks call count)."""
        self.get_many_calls += 1
        return [self._store.get(key) for key in keys]


@pytest.fixture
def mock_cache() -> MockCache:
    """Create mock cache for testing."""
    return MockCache()


@pytest.fixture
def session_service(mock_cache: MockCache) -> SessionService:
    """Create SessionService with mocked cache.

    MockCache implements the Cache protocol required by SessionService.
    """
    # MockCache implements all required Cache protocol methods
    service = SessionService(cache=mock_cache)
    return service


class TestSessionServiceCreate:
    """Tests for session creation."""

    @pytest.mark.anyio
    async def test_create_session_returns_session_data(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that create_session returns session data."""
        session = await session_service.create_session(
            model="sonnet",
        )

        assert session.id is not None
        assert session.model == "sonnet"
        assert session.status == "active"
        assert session.created_at is not None

    @pytest.mark.anyio
    async def test_create_session_with_custom_id(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that create_session can use a custom ID."""
        custom_id = "custom-session-id-123"
        session = await session_service.create_session(
            session_id=custom_id,
            model="opus",
        )

        assert session.id == custom_id
        assert session.model == "opus"


class TestSessionServiceGet:
    """Tests for session retrieval."""

    @pytest.mark.anyio
    async def test_get_session_returns_existing_session(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that get_session returns an existing session."""
        # Create a session first
        created = await session_service.create_session(model="sonnet")

        # Retrieve it
        retrieved = await session_service.get_session(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.model == created.model

    @pytest.mark.anyio
    async def test_get_session_returns_none_for_unknown(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that get_session returns None for unknown session."""
        result = await session_service.get_session("nonexistent-session")
        assert result is None

    @pytest.mark.anyio
    async def test_get_session_raises_for_owner_mismatch(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that get_session hides sessions owned by other API keys."""
        session = await session_service.create_session(
            model="sonnet",
            owner_api_key="owner-key",
        )

        with pytest.raises(SessionNotFoundError):
            await session_service.get_session(
                session.id,
                current_api_key="other-key",
            )


class TestSessionServiceList:
    """Tests for session listing."""

    @pytest.mark.anyio
    async def test_list_sessions_returns_empty_when_no_sessions(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that list_sessions returns empty list when no sessions."""
        result = await session_service.list_sessions(page=1, page_size=10)

        assert result.total == 0
        assert result.page == 1
        assert result.page_size == 10
        assert len(result.sessions) == 0


class TestSessionServiceUpdate:
    """Tests for session updates."""

    @pytest.mark.anyio
    async def test_update_session_status(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that session status can be updated."""
        session = await session_service.create_session(model="sonnet")
        assert session.status == "active"

        updated = await session_service.update_session(
            session.id,
            status="completed",
        )

        assert updated is not None
        assert updated.status == "completed"
        assert updated.updated_at >= session.created_at

    @pytest.mark.anyio
    async def test_update_session_returns_none_for_unknown(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that update returns None for unknown session."""
        result = await session_service.update_session(
            "nonexistent",
            status="completed",
        )
        assert result is None


class TestSessionServiceDelete:
    """Tests for session deletion."""

    @pytest.mark.anyio
    async def test_delete_session_removes_session(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that delete_session removes the session."""
        session = await session_service.create_session(model="sonnet")

        # Verify it exists
        assert await session_service.get_session(session.id) is not None

        # Delete it
        result = await session_service.delete_session(session.id)
        assert result is True

        # Verify it's gone
        assert await session_service.get_session(session.id) is None

    @pytest.mark.anyio
    async def test_delete_session_returns_false_for_unknown(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that delete returns False for unknown session."""
        result = await session_service.delete_session("nonexistent")
        assert result is False


@pytest.mark.unit
@pytest.mark.anyio
async def test_session_service_accepts_db_repo_parameter() -> None:
    """Test that SessionService can be initialized with db_repo dependency."""
    from unittest.mock import MagicMock

    from apps.api.adapters.session_repo import SessionRepository

    mock_cache = MagicMock()
    mock_repo = MagicMock(spec=SessionRepository)
    service = SessionService(cache=mock_cache, db_repo=mock_repo)

    assert service._db_repo is mock_repo


class TestSessionServiceExists:
    """Tests for session existence check."""

    @pytest.mark.anyio
    async def test_session_exists_returns_true_for_existing(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that session_exists returns True for existing session."""
        session = await session_service.create_session(model="sonnet")
        assert await session_service.session_exists(session.id) is True

    @pytest.mark.anyio
    async def test_session_exists_returns_false_for_unknown(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that session_exists returns False for unknown session."""
        assert await session_service.session_exists("nonexistent") is False


class TestSessionServiceEdgeCases:
    """Edge case tests for SessionService (Priority 9)."""

    @pytest.mark.anyio
    async def test_create_session_stores_metadata_correctly(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that session metadata is properly stored."""
        session = await session_service.create_session(
            model="sonnet",
            session_id="test-metadata-session",
            parent_session_id="parent-session-123",
        )

        assert session.parent_session_id == "parent-session-123"
        assert session.total_turns == 0
        assert session.total_cost_usd is None

        # Verify it persists
        retrieved = await session_service.get_session(session.id)
        assert retrieved is not None
        assert retrieved.parent_session_id == "parent-session-123"

    @pytest.mark.anyio
    async def test_update_session_updates_status(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that status transitions work correctly."""
        session = await session_service.create_session(model="sonnet")
        assert session.status == "active"

        # Update to completed
        updated = await session_service.update_session(
            session.id,
            status="completed",
        )
        assert updated is not None
        assert updated.status == "completed"

        # Update to error
        updated = await session_service.update_session(
            session.id,
            status="error",
        )
        assert updated is not None
        assert updated.status == "error"

    @pytest.mark.anyio
    async def test_update_session_returns_updated_session(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that update returns the updated session with correct values."""
        session = await session_service.create_session(model="sonnet")

        updated = await session_service.update_session(
            session.id,
            status="completed",
            total_turns=5,
            total_cost_usd=0.25,
        )

        assert updated is not None
        assert updated.status == "completed"
        assert updated.total_turns == 5
        assert updated.total_cost_usd == 0.25
        assert updated.updated_at >= session.created_at

    @pytest.mark.anyio
    async def test_delete_session_removes_from_cache(
        self,
        session_service: SessionService,
        mock_cache: MockCache,
    ) -> None:
        """Test that delete removes session from cache."""
        session = await session_service.create_session(model="sonnet")
        cache_key = f"session:{session.id}"

        # Verify it's in cache
        assert await mock_cache.exists(cache_key) is True

        # Delete session
        result = await session_service.delete_session(session.id)
        assert result is True

        # Verify it's removed from cache
        assert await mock_cache.exists(cache_key) is False

    @pytest.mark.anyio
    async def test_get_session_cache_hit(
        self,
        session_service: SessionService,
    ) -> None:
        """Test cache hit path returns session from cache."""
        # Create session (stores in cache)
        session = await session_service.create_session(model="sonnet")

        # Get session (should hit cache)
        retrieved = await session_service.get_session(session.id)

        assert retrieved is not None
        assert retrieved.id == session.id
        assert retrieved.model == session.model
        assert retrieved.status == session.status

    @pytest.mark.anyio
    async def test_list_sessions_pagination_works(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that pagination works correctly."""
        # Create 5 sessions
        session_ids = []
        for i in range(5):
            session = await session_service.create_session(
                model="sonnet",
                session_id=f"session-{i}",
            )
            session_ids.append(session.id)

        # Get first page (2 items)
        page1 = await session_service.list_sessions(page=1, page_size=2)
        assert page1.total == 5
        assert len(page1.sessions) == 2
        assert page1.page == 1
        assert page1.page_size == 2

        # Get second page (2 items)
        page2 = await session_service.list_sessions(page=2, page_size=2)
        assert page2.total == 5
        assert len(page2.sessions) == 2
        assert page2.page == 2

        # Get third page (1 item)
        page3 = await session_service.list_sessions(page=3, page_size=2)
        assert page3.total == 5
        assert len(page3.sessions) == 1
        assert page3.page == 3

    @pytest.mark.anyio
    async def test_list_sessions_returns_ordered_by_created_at(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that sessions are returned in descending created_at order."""
        import asyncio

        # Create 3 sessions with small delays
        session1 = await session_service.create_session(
            model="sonnet",
            session_id="session-1",
        )
        await asyncio.sleep(0.01)  # Small delay to ensure different timestamps

        session2 = await session_service.create_session(
            model="sonnet",
            session_id="session-2",
        )
        await asyncio.sleep(0.01)

        session3 = await session_service.create_session(
            model="sonnet",
            session_id="session-3",
        )

        # List sessions
        result = await session_service.list_sessions(page=1, page_size=10)

        assert len(result.sessions) == 3
        # Most recent first (session-3, session-2, session-1)
        assert result.sessions[0].id == session3.id
        assert result.sessions[1].id == session2.id
        assert result.sessions[2].id == session1.id

    @pytest.mark.anyio
    async def test_update_session_updates_timestamp(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that update_session updates the updated_at timestamp."""
        import asyncio

        session = await session_service.create_session(model="sonnet")
        original_updated = session.updated_at

        # Wait a bit then update
        await asyncio.sleep(0.01)

        updated = await session_service.update_session(
            session.id,
            total_turns=1,
        )

        assert updated is not None
        assert updated.updated_at > original_updated

    @pytest.mark.anyio
    async def test_create_session_generates_uuid_if_not_provided(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that create_session generates a UUID when session_id is None."""
        session = await session_service.create_session(model="sonnet")

        # Check that ID is a valid UUID format
        assert session.id is not None
        assert len(session.id) > 0
        # UUID format check (8-4-4-4-12)
        parts = session.id.split("-")
        assert len(parts) == 5

    @pytest.mark.anyio
    async def test_update_session_partial_updates(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that update_session can do partial updates."""
        session = await session_service.create_session(model="sonnet")

        # Update only total_turns
        updated1 = await session_service.update_session(
            session.id,
            total_turns=3,
        )
        assert updated1 is not None
        assert updated1.total_turns == 3
        assert updated1.status == "active"  # Should remain unchanged
        assert updated1.total_cost_usd is None  # Should remain unchanged

        # Update only total_cost_usd
        updated2 = await session_service.update_session(
            session.id,
            total_cost_usd=0.15,
        )
        assert updated2 is not None
        assert updated2.total_cost_usd == 0.15
        assert updated2.total_turns == 3  # Should remain from previous update
        assert updated2.status == "active"  # Should remain unchanged

    @pytest.mark.anyio
    async def test_list_sessions_uses_bulk_cache_reads(
        self,
        session_service: SessionService,
        mock_cache: MockCache,
    ) -> None:
        """Test that list_sessions uses bulk cache read instead of N individual reads."""
        # Create 3 sessions
        for i in range(3):
            await session_service.create_session(
                model="sonnet",
                session_id=f"session-{i}",
            )

        # Reset counter after creation
        mock_cache.get_many_calls = 0

        # List sessions
        result = await session_service.list_sessions(page=1, page_size=10)

        # Should make exactly 1 bulk cache call (not 3 individual calls)
        assert result.total == 3
        assert mock_cache.get_many_calls == 1
