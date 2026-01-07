"""Unit tests for SessionService (T042)."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.services.session import Session, SessionService


class MockCache:
    """Mock cache that stores data in memory."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        # Mock the underlying _client for list_sessions scan
        self._client = MagicMock()
        self._client.scan = AsyncMock(return_value=(0, []))

    async def get_json(self, key: str) -> dict[str, Any] | None:
        return self._store.get(key)

    async def set_json(
        self, key: str, value: dict[str, Any], ttl: int | None = None
    ) -> bool:
        self._store[key] = value
        return True

    async def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        return key in self._store


@pytest.fixture
def mock_cache() -> MockCache:
    """Create mock cache for testing."""
    return MockCache()


@pytest.fixture
def session_service(mock_cache: MockCache) -> SessionService:
    """Create SessionService with mocked cache."""
    service = SessionService(cache=mock_cache)  # type: ignore[arg-type]
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
