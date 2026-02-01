"""Unit tests for MessageService (TDD - RED phase)."""

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_cache() -> AsyncMock:
    """Create mock cache instance."""
    cache = AsyncMock()
    cache.get_json = AsyncMock(return_value=None)
    cache.set_json = AsyncMock()
    cache.delete = AsyncMock(return_value=True)
    cache.scan_keys = AsyncMock(return_value=[])
    cache.get_many_json = AsyncMock(return_value=[])
    return cache


class TestMessageServiceImport:
    """Tests for MessageService import."""

    def test_can_import_service(self) -> None:
        """Service can be imported from the module."""
        from apps.api.services.assistants.message_service import MessageService

        assert MessageService is not None

    def test_can_import_message_dataclass(self) -> None:
        """Message dataclass can be imported."""
        from apps.api.services.assistants.message_service import Message

        assert Message is not None


class TestMessageServiceCreate:
    """Tests for creating messages."""

    @pytest.mark.anyio
    async def test_create_user_message(
        self,
        mock_cache: AsyncMock,
    ) -> None:
        """Create user message."""
        from apps.api.services.assistants.message_service import MessageService

        service = MessageService(cache=mock_cache)

        message = await service.create_message(
            thread_id="thread_abc123",
            role="user",
            content="Hello!",
        )

        assert message is not None
        assert message.id.startswith("msg_")
        assert message.thread_id == "thread_abc123"
        assert message.role == "user"
        assert len(message.content) == 1
        assert message.content[0]["type"] == "text"

    @pytest.mark.anyio
    async def test_create_message_with_metadata(
        self,
        mock_cache: AsyncMock,
    ) -> None:
        """Create message with metadata."""
        from apps.api.services.assistants.message_service import MessageService

        service = MessageService(cache=mock_cache)

        message = await service.create_message(
            thread_id="thread_abc123",
            role="user",
            content="Hello!",
            metadata={"key": "value"},
        )

        assert message.metadata == {"key": "value"}


class TestMessageServiceGet:
    """Tests for getting messages."""

    @pytest.mark.anyio
    async def test_get_message(
        self,
        mock_cache: AsyncMock,
    ) -> None:
        """Get message by ID."""
        from apps.api.services.assistants.message_service import MessageService

        cached_data = {
            "id": "msg_abc123",
            "thread_id": "thread_abc123",
            "created_at": 1704067200,
            "role": "user",
            "content": [
                {"type": "text", "text": {"value": "Hello!", "annotations": []}}
            ],
            "metadata": {},
        }
        mock_cache.get_json = AsyncMock(return_value=cached_data)

        service = MessageService(cache=mock_cache)
        message = await service.get_message("thread_abc123", "msg_abc123")

        assert message is not None
        assert message.id == "msg_abc123"
        assert message.role == "user"

    @pytest.mark.anyio
    async def test_get_message_not_found(
        self,
        mock_cache: AsyncMock,
    ) -> None:
        """Get message returns None when not found."""
        from apps.api.services.assistants.message_service import MessageService

        mock_cache.get_json = AsyncMock(return_value=None)

        service = MessageService(cache=mock_cache)
        message = await service.get_message("thread_abc123", "msg_nonexistent")

        assert message is None


class TestMessageServiceList:
    """Tests for listing messages."""

    @pytest.mark.anyio
    async def test_list_messages_empty(
        self,
        mock_cache: AsyncMock,
    ) -> None:
        """List messages returns empty when none exist."""
        from apps.api.services.assistants.message_service import MessageService

        mock_cache.scan_keys = AsyncMock(return_value=[])

        service = MessageService(cache=mock_cache)
        result = await service.list_messages("thread_abc123")

        assert result.data == []
        assert result.has_more is False

    @pytest.mark.anyio
    async def test_list_messages_with_results(
        self,
        mock_cache: AsyncMock,
    ) -> None:
        """List messages returns available messages."""
        from apps.api.services.assistants.message_service import MessageService

        mock_cache.scan_keys = AsyncMock(return_value=["message:thread_abc123:msg_1"])
        mock_cache.get_many_json = AsyncMock(
            return_value=[
                {
                    "id": "msg_1",
                    "thread_id": "thread_abc123",
                    "created_at": 1704067200,
                    "role": "user",
                    "content": [
                        {"type": "text", "text": {"value": "Hello!", "annotations": []}}
                    ],
                    "metadata": {},
                }
            ]
        )

        service = MessageService(cache=mock_cache)
        result = await service.list_messages("thread_abc123")

        assert len(result.data) == 1
        assert result.data[0].id == "msg_1"


class TestMessageServiceModify:
    """Tests for modifying messages."""

    @pytest.mark.anyio
    async def test_modify_message_metadata(
        self,
        mock_cache: AsyncMock,
    ) -> None:
        """Modify message updates metadata."""
        from apps.api.services.assistants.message_service import MessageService

        cached_data = {
            "id": "msg_abc123",
            "thread_id": "thread_abc123",
            "created_at": 1704067200,
            "role": "user",
            "content": [
                {"type": "text", "text": {"value": "Hello!", "annotations": []}}
            ],
            "metadata": {"old": "value"},
        }
        mock_cache.get_json = AsyncMock(return_value=cached_data)

        service = MessageService(cache=mock_cache)
        message = await service.modify_message(
            "thread_abc123",
            "msg_abc123",
            metadata={"new": "value"},
        )

        assert message is not None
        assert message.metadata == {"new": "value"}

    @pytest.mark.anyio
    async def test_modify_message_not_found(
        self,
        mock_cache: AsyncMock,
    ) -> None:
        """Modify message returns None when not found."""
        from apps.api.services.assistants.message_service import MessageService

        mock_cache.get_json = AsyncMock(return_value=None)

        service = MessageService(cache=mock_cache)
        message = await service.modify_message(
            "thread_abc123",
            "msg_nonexistent",
            metadata={"key": "value"},
        )

        assert message is None


class TestMessageIdGeneration:
    """Tests for message ID generation."""

    def test_generate_message_id(self) -> None:
        """generate_message_id creates valid message IDs."""
        from apps.api.services.assistants.message_service import generate_message_id

        id1 = generate_message_id()
        id2 = generate_message_id()

        assert id1.startswith("msg_")
        assert id2.startswith("msg_")
        assert id1 != id2
        assert len(id1) > 10
