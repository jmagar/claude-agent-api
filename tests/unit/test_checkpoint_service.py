"""Unit tests for CheckpointService (T098)."""

from typing import TYPE_CHECKING, cast
from uuid import uuid4

import pytest

from apps.api.services.checkpoint import CheckpointService

if TYPE_CHECKING:
    from apps.api.protocols import Cache


class MockCache:
    """Mock cache that stores data in memory.

    Implements the Cache protocol for testing purposes.
    """

    def __init__(self) -> None:
        self._json_store: dict[str, dict[str, object]] = {}
        self._string_store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        """Get string value from cache."""
        return self._string_store.get(key)

    async def cache_set(self, key: str, value: str, _ttl: int | None = None) -> bool:
        """Set string value in cache."""
        self._string_store[key] = value
        return True

    async def get_json(self, key: str) -> dict[str, object] | None:
        """Get JSON value from cache."""
        return self._json_store.get(key)

    async def set_json(
        self, key: str, value: dict[str, object], _ttl: int | None = None
    ) -> bool:
        """Set JSON value in cache."""
        self._json_store[key] = value
        return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        deleted = False
        if key in self._json_store:
            del self._json_store[key]
            deleted = True
        if key in self._string_store:
            del self._string_store[key]
            deleted = True
        return deleted

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._json_store or key in self._string_store

    async def scan_keys(self, pattern: str) -> list[str]:
        """Scan for keys matching pattern."""
        prefix = pattern.replace("*", "")
        all_keys = list(self._json_store.keys()) + list(self._string_store.keys())
        return [k for k in all_keys if k.startswith(prefix)]

    async def add_to_set(self, _key: str, _value: str) -> bool:
        """Add value to set (not implemented for tests)."""
        return True

    async def remove_from_set(self, _key: str, _value: str) -> bool:
        """Remove value from set (not implemented for tests)."""
        return True

    async def set_members(self, _key: str) -> set[str]:
        """Get set members (not implemented for tests)."""
        return set()

    async def acquire_lock(self, _key: str, _ttl: int = 300) -> bool:
        """Acquire lock (not implemented for tests)."""
        return True

    async def release_lock(self, _key: str) -> bool:
        """Release lock (not implemented for tests)."""
        return True

    async def ping(self) -> bool:
        """Check connectivity."""
        return True


@pytest.fixture
def mock_cache() -> MockCache:
    """Create mock cache for testing."""
    return MockCache()


@pytest.fixture
def checkpoint_service(mock_cache: MockCache) -> CheckpointService:
    """Create CheckpointService with mocked cache.

    MockCache implements the Cache protocol required by CheckpointService.
    """
    service = CheckpointService(cache=cast("Cache", mock_cache))
    return service


class TestCheckpointServiceCreate:
    """Tests for checkpoint creation."""

    @pytest.mark.anyio
    async def test_create_checkpoint_returns_checkpoint_data(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that create_checkpoint returns checkpoint data."""
        session_id = str(uuid4())
        user_message_uuid = f"msg-{uuid4().hex[:8]}"
        files_modified = ["/path/to/file1.py", "/path/to/file2.py"]

        checkpoint = await checkpoint_service.create_checkpoint(
            session_id=session_id,
            user_message_uuid=user_message_uuid,
            files_modified=files_modified,
        )

        assert checkpoint.id is not None
        assert checkpoint.session_id == session_id
        assert checkpoint.user_message_uuid == user_message_uuid
        assert checkpoint.files_modified == files_modified
        assert checkpoint.created_at is not None

    @pytest.mark.anyio
    async def test_create_checkpoint_with_empty_files_list(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that checkpoint can be created with empty files list."""
        session_id = str(uuid4())
        user_message_uuid = f"msg-{uuid4().hex[:8]}"

        checkpoint = await checkpoint_service.create_checkpoint(
            session_id=session_id,
            user_message_uuid=user_message_uuid,
            files_modified=[],
        )

        assert checkpoint.id is not None
        assert checkpoint.files_modified == []


class TestCheckpointServiceGet:
    """Tests for checkpoint retrieval."""

    @pytest.mark.anyio
    async def test_get_checkpoint_returns_existing_checkpoint(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that get_checkpoint returns an existing checkpoint."""
        session_id = str(uuid4())
        user_message_uuid = f"msg-{uuid4().hex[:8]}"
        files_modified = ["/path/to/file.py"]

        # Create a checkpoint first
        created = await checkpoint_service.create_checkpoint(
            session_id=session_id,
            user_message_uuid=user_message_uuid,
            files_modified=files_modified,
        )

        # Retrieve it
        retrieved = await checkpoint_service.get_checkpoint(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.session_id == created.session_id
        assert retrieved.user_message_uuid == created.user_message_uuid

    @pytest.mark.anyio
    async def test_get_checkpoint_returns_none_for_unknown(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that get_checkpoint returns None for unknown checkpoint."""
        result = await checkpoint_service.get_checkpoint("nonexistent-checkpoint")
        assert result is None


class TestCheckpointServiceList:
    """Tests for checkpoint listing."""

    @pytest.mark.anyio
    async def test_list_checkpoints_returns_empty_when_no_checkpoints(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that list_checkpoints returns empty list when no checkpoints."""
        session_id = str(uuid4())
        result = await checkpoint_service.list_checkpoints(session_id=session_id)

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.anyio
    async def test_list_checkpoints_returns_checkpoints_for_session(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that list_checkpoints returns checkpoints for session."""
        session_id = str(uuid4())

        # Create multiple checkpoints
        for i in range(3):
            await checkpoint_service.create_checkpoint(
                session_id=session_id,
                user_message_uuid=f"msg-{i}",
                files_modified=[f"/path/to/file{i}.py"],
            )

        result = await checkpoint_service.list_checkpoints(session_id=session_id)

        assert isinstance(result, list)
        assert len(result) == 3

    @pytest.mark.anyio
    async def test_list_checkpoints_only_returns_session_checkpoints(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that list_checkpoints only returns checkpoints for the given session."""
        session_id_1 = str(uuid4())
        session_id_2 = str(uuid4())

        # Create checkpoints for session 1
        for i in range(2):
            await checkpoint_service.create_checkpoint(
                session_id=session_id_1,
                user_message_uuid=f"msg-1-{i}",
                files_modified=[f"/path/1/file{i}.py"],
            )

        # Create checkpoints for session 2
        for i in range(3):
            await checkpoint_service.create_checkpoint(
                session_id=session_id_2,
                user_message_uuid=f"msg-2-{i}",
                files_modified=[f"/path/2/file{i}.py"],
            )

        # List checkpoints for session 1
        result_1 = await checkpoint_service.list_checkpoints(session_id=session_id_1)
        assert len(result_1) == 2

        # List checkpoints for session 2
        result_2 = await checkpoint_service.list_checkpoints(session_id=session_id_2)
        assert len(result_2) == 3


class TestCheckpointServiceValidate:
    """Tests for checkpoint validation."""

    @pytest.mark.anyio
    async def test_validate_checkpoint_returns_true_for_valid(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that validate_checkpoint returns True for valid checkpoint."""
        session_id = str(uuid4())
        user_message_uuid = f"msg-{uuid4().hex[:8]}"

        checkpoint = await checkpoint_service.create_checkpoint(
            session_id=session_id,
            user_message_uuid=user_message_uuid,
            files_modified=["/path/to/file.py"],
        )

        is_valid = await checkpoint_service.validate_checkpoint(
            session_id=session_id,
            checkpoint_id=checkpoint.id,
        )

        assert is_valid is True

    @pytest.mark.anyio
    async def test_validate_checkpoint_returns_false_for_unknown(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that validate_checkpoint returns False for unknown checkpoint."""
        session_id = str(uuid4())

        is_valid = await checkpoint_service.validate_checkpoint(
            session_id=session_id,
            checkpoint_id="nonexistent-checkpoint",
        )

        assert is_valid is False

    @pytest.mark.anyio
    async def test_validate_checkpoint_returns_false_for_wrong_session(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that validate_checkpoint returns False for checkpoint from other session."""
        session_id_1 = str(uuid4())
        session_id_2 = str(uuid4())

        # Create checkpoint for session 1
        checkpoint = await checkpoint_service.create_checkpoint(
            session_id=session_id_1,
            user_message_uuid=f"msg-{uuid4().hex[:8]}",
            files_modified=["/path/to/file.py"],
        )

        # Try to validate using session 2
        is_valid = await checkpoint_service.validate_checkpoint(
            session_id=session_id_2,
            checkpoint_id=checkpoint.id,
        )

        assert is_valid is False


class TestCheckpointServiceGetByUserMessageUuid:
    """Tests for getting checkpoint by user message UUID."""

    @pytest.mark.anyio
    async def test_get_by_user_message_uuid_returns_checkpoint(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that get_checkpoint_by_user_message_uuid returns checkpoint."""
        session_id = str(uuid4())
        user_message_uuid = f"msg-{uuid4().hex[:8]}"

        created = await checkpoint_service.create_checkpoint(
            session_id=session_id,
            user_message_uuid=user_message_uuid,
            files_modified=["/path/to/file.py"],
        )

        result = await checkpoint_service.get_checkpoint_by_user_message_uuid(
            user_message_uuid=user_message_uuid,
        )

        assert result is not None
        assert result.id == created.id
        assert result.user_message_uuid == user_message_uuid

    @pytest.mark.anyio
    async def test_get_by_user_message_uuid_returns_none_for_unknown(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that get_checkpoint_by_user_message_uuid returns None for unknown."""
        result = await checkpoint_service.get_checkpoint_by_user_message_uuid(
            user_message_uuid="nonexistent-uuid",
        )

        assert result is None
