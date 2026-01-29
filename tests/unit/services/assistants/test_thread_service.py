"""Unit tests for ThreadService (TDD - RED phase)."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_session_service() -> AsyncMock:
    """Create mock session service."""
    service = AsyncMock()
    service.create_session = AsyncMock()
    service.get_session = AsyncMock(return_value=None)
    service.update_session = AsyncMock()
    service.delete_session = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_cache() -> AsyncMock:
    """Create mock cache instance."""
    cache = AsyncMock()
    cache.get_json = AsyncMock(return_value=None)
    cache.set_json = AsyncMock()
    cache.delete = AsyncMock(return_value=True)
    return cache


class TestThreadServiceImport:
    """Tests for ThreadService import."""

    def test_can_import_service(self) -> None:
        """Service can be imported from the module."""
        from apps.api.services.assistants.thread_service import ThreadService

        assert ThreadService is not None

    def test_can_import_thread_dataclass(self) -> None:
        """Thread dataclass can be imported."""
        from apps.api.services.assistants.thread_service import Thread

        assert Thread is not None


class TestThreadServiceCreate:
    """Tests for creating threads."""

    @pytest.mark.anyio
    async def test_create_thread_minimal(
        self,
        mock_session_service: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        """Create thread with minimal parameters."""
        from apps.api.services.assistants.thread_service import ThreadService

        mock_session = MagicMock()
        mock_session.id = "sess_abc123"
        mock_session.created_at = MagicMock()
        mock_session.created_at.timestamp.return_value = 1704067200
        mock_session_service.create_session = AsyncMock(return_value=mock_session)

        service = ThreadService(
            session_service=mock_session_service,
            cache=mock_cache,
        )

        thread = await service.create_thread()

        assert thread is not None
        assert thread.id.startswith("thread_")
        assert thread.metadata == {}

    @pytest.mark.anyio
    async def test_create_thread_with_metadata(
        self,
        mock_session_service: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        """Create thread with metadata."""
        from apps.api.services.assistants.thread_service import ThreadService

        mock_session = MagicMock()
        mock_session.id = "sess_abc123"
        mock_session.created_at = MagicMock()
        mock_session.created_at.timestamp.return_value = 1704067200
        mock_session_service.create_session = AsyncMock(return_value=mock_session)

        service = ThreadService(
            session_service=mock_session_service,
            cache=mock_cache,
        )

        thread = await service.create_thread(metadata={"key": "value"})

        assert thread.metadata == {"key": "value"}

    @pytest.mark.anyio
    async def test_create_thread_stores_in_cache(
        self,
        mock_session_service: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        """Create thread writes to cache."""
        from apps.api.services.assistants.thread_service import ThreadService

        mock_session = MagicMock()
        mock_session.id = "sess_abc123"
        mock_session.created_at = MagicMock()
        mock_session.created_at.timestamp.return_value = 1704067200
        mock_session_service.create_session = AsyncMock(return_value=mock_session)

        service = ThreadService(
            session_service=mock_session_service,
            cache=mock_cache,
        )

        thread = await service.create_thread()

        mock_cache.set_json.assert_called()
        cache_key = mock_cache.set_json.call_args[0][0]
        assert cache_key == f"thread:{thread.id}"


class TestThreadServiceGet:
    """Tests for getting threads."""

    @pytest.mark.anyio
    async def test_get_thread_from_cache(
        self,
        mock_session_service: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        """Get thread retrieves from cache first."""
        from apps.api.services.assistants.thread_service import ThreadService

        cached_data = {
            "id": "thread_abc123",
            "session_id": "sess_abc123",
            "created_at": 1704067200,
            "metadata": {"key": "value"},
        }
        mock_cache.get_json = AsyncMock(return_value=cached_data)

        service = ThreadService(
            session_service=mock_session_service,
            cache=mock_cache,
        )

        thread = await service.get_thread("thread_abc123")

        assert thread is not None
        assert thread.id == "thread_abc123"
        assert thread.metadata == {"key": "value"}

    @pytest.mark.anyio
    async def test_get_thread_not_found(
        self,
        mock_session_service: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        """Get thread returns None when not found."""
        from apps.api.services.assistants.thread_service import ThreadService

        mock_cache.get_json = AsyncMock(return_value=None)

        service = ThreadService(
            session_service=mock_session_service,
            cache=mock_cache,
        )

        thread = await service.get_thread("thread_nonexistent")

        assert thread is None


class TestThreadServiceModify:
    """Tests for modifying threads."""

    @pytest.mark.anyio
    async def test_modify_thread_metadata(
        self,
        mock_session_service: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        """Modify thread updates metadata."""
        from apps.api.services.assistants.thread_service import ThreadService

        cached_data = {
            "id": "thread_abc123",
            "session_id": "sess_abc123",
            "created_at": 1704067200,
            "metadata": {"old": "value"},
        }
        mock_cache.get_json = AsyncMock(return_value=cached_data)

        service = ThreadService(
            session_service=mock_session_service,
            cache=mock_cache,
        )

        thread = await service.modify_thread(
            "thread_abc123",
            metadata={"new": "value"},
        )

        assert thread is not None
        assert thread.metadata == {"new": "value"}

    @pytest.mark.anyio
    async def test_modify_thread_not_found(
        self,
        mock_session_service: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        """Modify thread returns None when not found."""
        from apps.api.services.assistants.thread_service import ThreadService

        mock_cache.get_json = AsyncMock(return_value=None)

        service = ThreadService(
            session_service=mock_session_service,
            cache=mock_cache,
        )

        thread = await service.modify_thread(
            "thread_nonexistent",
            metadata={"key": "value"},
        )

        assert thread is None


class TestThreadServiceDelete:
    """Tests for deleting threads."""

    @pytest.mark.anyio
    async def test_delete_thread(
        self,
        mock_session_service: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        """Delete thread removes from cache and session service."""
        from apps.api.services.assistants.thread_service import ThreadService

        cached_data = {
            "id": "thread_abc123",
            "session_id": "sess_abc123",
            "created_at": 1704067200,
            "metadata": {},
        }
        mock_cache.get_json = AsyncMock(return_value=cached_data)
        mock_cache.delete = AsyncMock(return_value=True)

        service = ThreadService(
            session_service=mock_session_service,
            cache=mock_cache,
        )

        result = await service.delete_thread("thread_abc123")

        assert result is True
        mock_cache.delete.assert_called()

    @pytest.mark.anyio
    async def test_delete_thread_not_found(
        self,
        mock_session_service: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        """Delete thread returns False when not found."""
        from apps.api.services.assistants.thread_service import ThreadService

        mock_cache.get_json = AsyncMock(return_value=None)

        service = ThreadService(
            session_service=mock_session_service,
            cache=mock_cache,
        )

        result = await service.delete_thread("thread_nonexistent")

        assert result is False


class TestThreadIdGeneration:
    """Tests for thread ID generation."""

    def test_generate_thread_id(self) -> None:
        """generate_thread_id creates valid thread IDs."""
        from apps.api.services.assistants.thread_service import generate_thread_id

        id1 = generate_thread_id()
        id2 = generate_thread_id()

        assert id1.startswith("thread_")
        assert id2.startswith("thread_")
        assert id1 != id2
        assert len(id1) > 10
