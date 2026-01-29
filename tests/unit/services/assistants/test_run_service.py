"""Unit tests for RunService (TDD - RED phase)."""

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


@pytest.fixture
def mock_db_repo() -> AsyncMock:
    """Create mock database repository."""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get = AsyncMock(return_value=None)
    repo.list_runs = AsyncMock(return_value=([], 0))
    repo.update = AsyncMock()
    return repo


class TestRunServiceImport:
    """Tests for RunService import."""

    def test_can_import_service(self) -> None:
        """Service can be imported from the module."""
        from apps.api.services.assistants.run_service import RunService

        assert RunService is not None

    def test_can_import_run_dataclass(self) -> None:
        """Run dataclass can be imported."""
        from apps.api.services.assistants.run_service import Run

        assert Run is not None

    def test_can_import_run_status_type(self) -> None:
        """RunStatus type can be imported."""
        from apps.api.services.assistants.run_service import RunStatus

        assert RunStatus is not None


class TestRunServiceCreate:
    """Tests for creating runs."""

    @pytest.mark.anyio
    async def test_create_run(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Create a new run."""
        from apps.api.services.assistants.run_service import RunService

        service = RunService(cache=mock_cache, db_repo=mock_db_repo)

        run = await service.create_run(
            thread_id="thread_abc123",
            assistant_id="asst_abc123",
            model="gpt-4",
        )

        assert run is not None
        assert run.id.startswith("run_")
        assert run.thread_id == "thread_abc123"
        assert run.assistant_id == "asst_abc123"
        assert run.status == "queued"

    @pytest.mark.anyio
    async def test_create_run_with_instructions(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Create run with custom instructions."""
        from apps.api.services.assistants.run_service import RunService

        service = RunService(cache=mock_cache, db_repo=mock_db_repo)

        run = await service.create_run(
            thread_id="thread_abc123",
            assistant_id="asst_abc123",
            model="gpt-4",
            instructions="Custom instructions",
        )

        assert run.instructions == "Custom instructions"


class TestRunServiceGet:
    """Tests for getting runs."""

    @pytest.mark.anyio
    async def test_get_run(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Get run by ID."""
        from apps.api.services.assistants.run_service import RunService

        cached_data = {
            "id": "run_abc123",
            "thread_id": "thread_abc123",
            "assistant_id": "asst_abc123",
            "created_at": 1704067200,
            "status": "queued",
            "model": "gpt-4",
            "instructions": None,
            "tools": [],
            "metadata": {},
        }
        mock_cache.get_json = AsyncMock(return_value=cached_data)

        service = RunService(cache=mock_cache, db_repo=mock_db_repo)
        run = await service.get_run("thread_abc123", "run_abc123")

        assert run is not None
        assert run.id == "run_abc123"
        assert run.status == "queued"

    @pytest.mark.anyio
    async def test_get_run_not_found(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Get run returns None when not found."""
        from apps.api.services.assistants.run_service import RunService

        mock_cache.get_json = AsyncMock(return_value=None)

        service = RunService(cache=mock_cache, db_repo=mock_db_repo)
        run = await service.get_run("thread_abc123", "run_nonexistent")

        assert run is None


class TestRunServiceList:
    """Tests for listing runs."""

    @pytest.mark.anyio
    async def test_list_runs_empty(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """List runs returns empty when none exist."""
        from apps.api.services.assistants.run_service import RunService

        mock_cache.scan_keys = AsyncMock(return_value=[])

        service = RunService(cache=mock_cache, db_repo=mock_db_repo)
        result = await service.list_runs("thread_abc123")

        assert result.data == []
        assert result.has_more is False


class TestRunServiceStatusTransitions:
    """Tests for run status transitions."""

    @pytest.mark.anyio
    async def test_start_run_transitions_to_in_progress(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Starting a run transitions from queued to in_progress."""
        from apps.api.services.assistants.run_service import RunService

        cached_data = {
            "id": "run_abc123",
            "thread_id": "thread_abc123",
            "assistant_id": "asst_abc123",
            "created_at": 1704067200,
            "status": "queued",
            "model": "gpt-4",
            "instructions": None,
            "tools": [],
            "metadata": {},
        }
        mock_cache.get_json = AsyncMock(return_value=cached_data)

        service = RunService(cache=mock_cache, db_repo=mock_db_repo)
        run = await service.start_run("thread_abc123", "run_abc123")

        assert run is not None
        assert run.status == "in_progress"

    @pytest.mark.anyio
    async def test_complete_run(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Completing a run transitions to completed."""
        from apps.api.services.assistants.run_service import RunService

        cached_data = {
            "id": "run_abc123",
            "thread_id": "thread_abc123",
            "assistant_id": "asst_abc123",
            "created_at": 1704067200,
            "status": "in_progress",
            "model": "gpt-4",
            "instructions": None,
            "tools": [],
            "metadata": {},
        }
        mock_cache.get_json = AsyncMock(return_value=cached_data)

        service = RunService(cache=mock_cache, db_repo=mock_db_repo)
        run = await service.complete_run("thread_abc123", "run_abc123")

        assert run is not None
        assert run.status == "completed"

    @pytest.mark.anyio
    async def test_cancel_run(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Cancelling a run transitions to cancelled."""
        from apps.api.services.assistants.run_service import RunService

        cached_data = {
            "id": "run_abc123",
            "thread_id": "thread_abc123",
            "assistant_id": "asst_abc123",
            "created_at": 1704067200,
            "status": "in_progress",
            "model": "gpt-4",
            "instructions": None,
            "tools": [],
            "metadata": {},
        }
        mock_cache.get_json = AsyncMock(return_value=cached_data)

        service = RunService(cache=mock_cache, db_repo=mock_db_repo)
        run = await service.cancel_run("thread_abc123", "run_abc123")

        assert run is not None
        assert run.status == "cancelled"

    @pytest.mark.anyio
    async def test_require_action(
        self,
        mock_cache: AsyncMock,
        mock_db_repo: AsyncMock,
    ) -> None:
        """Setting required action transitions to requires_action."""
        from apps.api.services.assistants.run_service import RunService

        cached_data = {
            "id": "run_abc123",
            "thread_id": "thread_abc123",
            "assistant_id": "asst_abc123",
            "created_at": 1704067200,
            "status": "in_progress",
            "model": "gpt-4",
            "instructions": None,
            "tools": [],
            "metadata": {},
        }
        mock_cache.get_json = AsyncMock(return_value=cached_data)

        service = RunService(cache=mock_cache, db_repo=mock_db_repo)
        run = await service.require_action(
            "thread_abc123",
            "run_abc123",
            tool_calls=[
                {
                    "id": "call_abc123",
                    "type": "function",
                    "function": {"name": "get_weather", "arguments": "{}"},
                }
            ],
        )

        assert run is not None
        assert run.status == "requires_action"
        assert run.required_action is not None


class TestRunIdGeneration:
    """Tests for run ID generation."""

    def test_generate_run_id(self) -> None:
        """generate_run_id creates valid run IDs."""
        from apps.api.services.assistants.run_service import generate_run_id

        id1 = generate_run_id()
        id2 = generate_run_id()

        assert id1.startswith("run_")
        assert id2.startswith("run_")
        assert id1 != id2
        assert len(id1) > 10
