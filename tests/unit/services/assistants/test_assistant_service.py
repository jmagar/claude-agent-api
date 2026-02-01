"""Unit tests for AssistantService (TDD - RED phase)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

if TYPE_CHECKING:
    from apps.api.types import JsonValue


@pytest.fixture
def mock_cache() -> AsyncMock:
    """Create mock cache instance."""
    cache = AsyncMock()
    cache.get_json = AsyncMock(return_value=None)
    cache.set_json = AsyncMock()
    cache.delete = AsyncMock(return_value=True)
    cache.exists = AsyncMock(return_value=False)
    cache.scan_keys = AsyncMock(return_value=[])
    cache.get_many_json = AsyncMock(return_value=[])
    return cache


@pytest.fixture
def mock_db_repo() -> AsyncMock:
    """Create mock database repository."""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get = AsyncMock(return_value=None)
    repo.list_assistants = AsyncMock(return_value=([], 0))
    repo.update = AsyncMock()
    repo.delete = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_model_mapper() -> MagicMock:
    """Create mock model mapper."""
    mapper = MagicMock()
    mapper.to_claude = MagicMock(return_value="sonnet")
    mapper.validate_model = MagicMock(return_value=True)
    return mapper


class TestAssistantServiceImport:
    """Tests for AssistantService import."""

    def test_can_import_service(self) -> None:
        """Service can be imported from the module."""
        from apps.api.services.assistants.assistant_service import AssistantService

        assert AssistantService is not None

    def test_can_import_assistant_dataclass(self) -> None:
        """Assistant dataclass can be imported."""
        from apps.api.services.assistants.assistant_service import Assistant

        assert Assistant is not None


class TestAssistantServiceCreate:
    """Tests for creating assistants."""

    @pytest.mark.anyio
    async def test_create_assistant_minimal(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Create assistant with minimal parameters."""
        from apps.api.services.assistants.assistant_service import AssistantService

        service = AssistantService(cache=mock_cache, db_repo=mock_db_repo)

        assistant = await service.create_assistant(model="gpt-4")

        assert assistant is not None
        assert assistant.id.startswith("asst_")
        assert assistant.model == "gpt-4"
        assert assistant.name is None
        assert assistant.tools == []

    @pytest.mark.anyio
    async def test_create_assistant_full(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Create assistant with all parameters."""
        from apps.api.services.assistants.assistant_service import AssistantService

        service = AssistantService(cache=mock_cache, db_repo=mock_db_repo)

        assistant = await service.create_assistant(
            model="gpt-4",
            name="Test Assistant",
            description="A test assistant",
            instructions="You are helpful.",
            tools=[{"type": "code_interpreter"}],
            metadata={"key": "value"},
            owner_api_key="test-api-key",
        )

        assert assistant.name == "Test Assistant"
        assert assistant.description == "A test assistant"
        assert assistant.instructions == "You are helpful."
        assert assistant.tools == [{"type": "code_interpreter"}]
        assert assistant.metadata == {"key": "value"}

    @pytest.mark.anyio
    async def test_create_assistant_writes_to_db(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Create assistant writes to database."""
        from apps.api.services.assistants.assistant_service import AssistantService

        service = AssistantService(cache=mock_cache, db_repo=mock_db_repo)

        await service.create_assistant(model="gpt-4")

        mock_db_repo.create.assert_called_once()
        call_kwargs = mock_db_repo.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4"

    @pytest.mark.anyio
    async def test_create_assistant_caches_result(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Create assistant writes to cache."""
        from apps.api.services.assistants.assistant_service import AssistantService

        service = AssistantService(cache=mock_cache, db_repo=mock_db_repo)

        assistant = await service.create_assistant(model="gpt-4")

        mock_cache.set_json.assert_called_once()
        cache_key = mock_cache.set_json.call_args[0][0]
        assert cache_key == f"assistant:{assistant.id}"


class TestAssistantServiceGet:
    """Tests for getting assistants."""

    @pytest.mark.anyio
    async def test_get_assistant_from_cache(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Get assistant retrieves from cache first."""
        from apps.api.services.assistants.assistant_service import AssistantService

        cached_data: dict[str, JsonValue] = {
            "id": "asst_abc123",
            "model": "gpt-4",
            "name": "Cached Assistant",
            "description": None,
            "instructions": None,
            "tools": [],
            "metadata": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "owner_api_key": None,
        }
        mock_cache.get_json = AsyncMock(return_value=cached_data)

        service = AssistantService(cache=mock_cache, db_repo=mock_db_repo)
        assistant = await service.get_assistant("asst_abc123")

        assert assistant is not None
        assert assistant.id == "asst_abc123"
        assert assistant.name == "Cached Assistant"
        mock_db_repo.get.assert_not_called()

    @pytest.mark.anyio
    async def test_get_assistant_falls_back_to_db(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Get assistant falls back to database on cache miss."""
        from apps.api.services.assistants.assistant_service import AssistantService

        mock_cache.get_json = AsyncMock(return_value=None)

        # Create mock DB model
        db_assistant = MagicMock()
        db_assistant.id = "asst_abc123"
        db_assistant.model = "gpt-4"
        db_assistant.name = "DB Assistant"
        db_assistant.description = None
        db_assistant.instructions = None
        db_assistant.tools = []
        db_assistant.metadata_ = {}
        db_assistant.owner_api_key = None
        db_assistant.created_at = MagicMock()
        db_assistant.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        db_assistant.updated_at = MagicMock()
        db_assistant.updated_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_db_repo.get = AsyncMock(return_value=db_assistant)

        service = AssistantService(cache=mock_cache, db_repo=mock_db_repo)
        assistant = await service.get_assistant("asst_abc123")

        assert assistant is not None
        assert assistant.id == "asst_abc123"
        assert assistant.name == "DB Assistant"
        mock_db_repo.get.assert_called_once_with("asst_abc123")

    @pytest.mark.anyio
    async def test_get_assistant_not_found(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Get assistant returns None when not found."""
        from apps.api.services.assistants.assistant_service import AssistantService

        mock_cache.get_json = AsyncMock(return_value=None)
        mock_db_repo.get = AsyncMock(return_value=None)

        service = AssistantService(cache=mock_cache, db_repo=mock_db_repo)
        assistant = await service.get_assistant("asst_nonexistent")

        assert assistant is None


class TestAssistantServiceList:
    """Tests for listing assistants."""

    @pytest.mark.anyio
    async def test_list_assistants_empty(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """List assistants returns empty list when none exist."""
        from apps.api.services.assistants.assistant_service import AssistantService

        mock_db_repo.list_assistants = AsyncMock(return_value=([], 0))

        service = AssistantService(cache=mock_cache, db_repo=mock_db_repo)
        result = await service.list_assistants()

        assert result.data == []
        assert result.has_more is False

    @pytest.mark.anyio
    async def test_list_assistants_with_pagination(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """List assistants supports pagination."""
        from apps.api.services.assistants.assistant_service import AssistantService

        # Create mock assistants
        mock_assistants = []
        for i in range(3):
            assistant = MagicMock()
            assistant.id = f"asst_{i}"
            assistant.model = "gpt-4"
            assistant.name = f"Assistant {i}"
            assistant.description = None
            assistant.instructions = None
            assistant.tools = []
            assistant.metadata_ = {}
            assistant.owner_api_key = None
            assistant.created_at = MagicMock()
            assistant.created_at.isoformat.return_value = "2024-01-01T00:00:00"
            assistant.updated_at = MagicMock()
            assistant.updated_at.isoformat.return_value = "2024-01-01T00:00:00"
            mock_assistants.append(assistant)

        # Service requests limit+1 to detect has_more, so return 3 items when limit=2
        mock_db_repo.list_assistants = AsyncMock(return_value=(mock_assistants, 3))

        service = AssistantService(cache=mock_cache, db_repo=mock_db_repo)
        result = await service.list_assistants(limit=2)

        assert len(result.data) == 2  # Should be truncated to limit
        assert result.has_more is True  # Because we got 3 items (more than limit)

    @pytest.mark.anyio
    async def test_list_assistants_by_owner(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """List assistants filters by owner API key."""
        from apps.api.services.assistants.assistant_service import AssistantService

        mock_db_repo.list_assistants = AsyncMock(return_value=([], 0))

        service = AssistantService(cache=mock_cache, db_repo=mock_db_repo)
        await service.list_assistants(owner_api_key="test-key")

        mock_db_repo.list_assistants.assert_called_once()
        call_kwargs = mock_db_repo.list_assistants.call_args.kwargs
        assert call_kwargs["owner_api_key"] == "test-key"


class TestAssistantServiceUpdate:
    """Tests for updating assistants."""

    @pytest.mark.anyio
    async def test_update_assistant(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Update assistant modifies fields."""
        from apps.api.services.assistants.assistant_service import AssistantService

        # Setup existing assistant
        cached_data: dict[str, JsonValue] = {
            "id": "asst_abc123",
            "model": "gpt-4",
            "name": "Original Name",
            "description": None,
            "instructions": None,
            "tools": [],
            "metadata": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "owner_api_key": None,
        }
        mock_cache.get_json = AsyncMock(return_value=cached_data)

        service = AssistantService(cache=mock_cache, db_repo=mock_db_repo)
        assistant = await service.update_assistant(
            "asst_abc123",
            name="Updated Name",
            instructions="New instructions",
        )

        assert assistant is not None
        assert assistant.name == "Updated Name"
        assert assistant.instructions == "New instructions"

    @pytest.mark.anyio
    async def test_update_assistant_not_found(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Update assistant returns None when not found."""
        from apps.api.services.assistants.assistant_service import AssistantService

        mock_cache.get_json = AsyncMock(return_value=None)
        mock_db_repo.get = AsyncMock(return_value=None)

        service = AssistantService(cache=mock_cache, db_repo=mock_db_repo)
        assistant = await service.update_assistant("asst_nonexistent", name="New")

        assert assistant is None


class TestAssistantServiceDelete:
    """Tests for deleting assistants."""

    @pytest.mark.anyio
    async def test_delete_assistant(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Delete assistant removes from DB and cache."""
        from apps.api.services.assistants.assistant_service import AssistantService

        mock_db_repo.delete = AsyncMock(return_value=True)
        mock_cache.delete = AsyncMock(return_value=True)

        service = AssistantService(cache=mock_cache, db_repo=mock_db_repo)
        result = await service.delete_assistant("asst_abc123")

        assert result is True
        mock_db_repo.delete.assert_called_once_with("asst_abc123")
        mock_cache.delete.assert_called_once()

    @pytest.mark.anyio
    async def test_delete_assistant_not_found(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Delete assistant returns False when not found."""
        from apps.api.services.assistants.assistant_service import AssistantService

        mock_db_repo.delete = AsyncMock(return_value=False)

        service = AssistantService(cache=mock_cache, db_repo=mock_db_repo)
        result = await service.delete_assistant("asst_nonexistent")

        assert result is False
