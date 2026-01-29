"""Unit tests for CheckpointService (T098)."""

import asyncio
from typing import TYPE_CHECKING, cast
from uuid import uuid4

import pytest

from apps.api.services.checkpoint import CheckpointService
from apps.api.types import JsonValue

if TYPE_CHECKING:
    from apps.api.protocols import Cache


class MockCache:
    """Mock cache that stores data in memory.

    Implements the Cache protocol for testing purposes.
    """

    def __init__(self) -> None:
        self._json_store: dict[str, dict[str, JsonValue]] = {}
        self._string_store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        """Get string value from cache."""
        return self._string_store.get(key)

    async def cache_set(self, key: str, value: str, ttl: int | None = None) -> bool:
        """Set string value in cache."""
        self._string_store[key] = value
        return True

    async def get_json(self, key: str) -> dict[str, JsonValue] | None:
        """Get JSON value from cache."""
        return self._json_store.get(key)

    async def set_json(
        self, key: str, value: dict[str, JsonValue], ttl: int | None = None
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

    async def scan_keys(self, pattern: str, max_keys: int = 1000) -> list[str]:
        """Scan for keys matching pattern."""
        prefix = pattern.replace("*", "")
        all_keys = list(self._json_store.keys()) + list(self._string_store.keys())
        matching = [k for k in all_keys if k.startswith(prefix)]
        return matching[:max_keys]

    async def clear(self) -> bool:
        """Clear all cached values."""
        self._json_store.clear()
        self._string_store.clear()
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

    async def get_many_json(self, keys: list[str]) -> list[dict[str, JsonValue] | None]:
        """Get multiple JSON values from cache."""
        return [await self.get_json(key) for key in keys]


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


class TestCheckpointServiceEdgeCases:
    """Edge case tests for CheckpointService (Priority 10)."""

    @pytest.mark.anyio
    async def test_create_checkpoint_generates_uuid(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that create_checkpoint generates a UUID for the checkpoint ID."""
        session_id = str(uuid4())
        user_message_uuid = f"msg-{uuid4().hex[:8]}"

        checkpoint = await checkpoint_service.create_checkpoint(
            session_id=session_id,
            user_message_uuid=user_message_uuid,
            files_modified=["/path/to/file.py"],
        )

        # Check that ID is a valid UUID format (8-4-4-4-12)
        assert checkpoint.id is not None
        parts = checkpoint.id.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    @pytest.mark.anyio
    async def test_create_checkpoint_persists_to_cache(
        self,
        checkpoint_service: CheckpointService,
        mock_cache: MockCache,
    ) -> None:
        """Test that checkpoint is persisted to cache."""
        session_id = str(uuid4())
        user_message_uuid = f"msg-{uuid4().hex[:8]}"

        checkpoint = await checkpoint_service.create_checkpoint(
            session_id=session_id,
            user_message_uuid=user_message_uuid,
            files_modified=["/path/to/file.py"],
        )

        # Verify it's in cache
        checkpoint_key = f"checkpoint:{checkpoint.id}"
        assert await mock_cache.exists(checkpoint_key) is True

        # Verify index is created
        index_key = f"checkpoint_uuid_index:{user_message_uuid}"
        assert await mock_cache.exists(index_key) is True

    @pytest.mark.anyio
    async def test_create_checkpoint_with_metadata(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that checkpoint stores all metadata correctly."""
        session_id = str(uuid4())
        user_message_uuid = f"msg-{uuid4().hex[:8]}"
        files_modified = [
            "/path/to/file1.py",
            "/path/to/file2.py",
            "/path/to/file3.py",
        ]

        checkpoint = await checkpoint_service.create_checkpoint(
            session_id=session_id,
            user_message_uuid=user_message_uuid,
            files_modified=files_modified,
        )

        assert checkpoint.session_id == session_id
        assert checkpoint.user_message_uuid == user_message_uuid
        assert checkpoint.files_modified == files_modified
        assert checkpoint.created_at is not None

        # Verify retrieval maintains data integrity
        retrieved = await checkpoint_service.get_checkpoint(checkpoint.id)
        assert retrieved is not None
        assert retrieved.files_modified == files_modified

    @pytest.mark.anyio
    async def test_list_checkpoints_returns_ordered_list(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that checkpoints are returned in ascending created_at order."""
        session_id = str(uuid4())

        # Create 3 checkpoints with small delays
        checkpoint1 = await checkpoint_service.create_checkpoint(
            session_id=session_id,
            user_message_uuid=f"msg-1-{uuid4().hex[:8]}",
            files_modified=["/path/1.py"],
        )
        await asyncio.sleep(0.01)

        checkpoint2 = await checkpoint_service.create_checkpoint(
            session_id=session_id,
            user_message_uuid=f"msg-2-{uuid4().hex[:8]}",
            files_modified=["/path/2.py"],
        )
        await asyncio.sleep(0.01)

        checkpoint3 = await checkpoint_service.create_checkpoint(
            session_id=session_id,
            user_message_uuid=f"msg-3-{uuid4().hex[:8]}",
            files_modified=["/path/3.py"],
        )

        # List checkpoints
        result = await checkpoint_service.list_checkpoints(session_id=session_id)

        assert len(result) == 3
        # Oldest first (checkpoint1, checkpoint2, checkpoint3)
        assert result[0].id == checkpoint1.id
        assert result[1].id == checkpoint2.id
        assert result[2].id == checkpoint3.id

    @pytest.mark.anyio
    async def test_get_checkpoint_by_uuid(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test UUID index lookup works correctly."""
        session_id = str(uuid4())
        user_message_uuid = f"msg-{uuid4().hex[:8]}"

        checkpoint = await checkpoint_service.create_checkpoint(
            session_id=session_id,
            user_message_uuid=user_message_uuid,
            files_modified=["/path/to/file.py"],
        )

        # Retrieve by UUID
        retrieved = await checkpoint_service.get_checkpoint_by_user_message_uuid(
            user_message_uuid=user_message_uuid,
        )

        assert retrieved is not None
        assert retrieved.id == checkpoint.id
        assert retrieved.user_message_uuid == user_message_uuid

    @pytest.mark.anyio
    async def test_get_checkpoint_returns_none_for_nonexistent(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that get_checkpoint returns None for nonexistent checkpoint."""
        result = await checkpoint_service.get_checkpoint("nonexistent-id-12345")
        assert result is None

    @pytest.mark.anyio
    async def test_validate_checkpoint_with_valid_checkpoint(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test checkpoint validation with valid checkpoint."""
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
    async def test_validate_checkpoint_rejects_wrong_session(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that validate_checkpoint rejects checkpoint from wrong session."""
        session_id_1 = str(uuid4())
        session_id_2 = str(uuid4())

        checkpoint = await checkpoint_service.create_checkpoint(
            session_id=session_id_1,
            user_message_uuid=f"msg-{uuid4().hex[:8]}",
            files_modified=["/path/to/file.py"],
        )

        # Try to validate with different session
        is_valid = await checkpoint_service.validate_checkpoint(
            session_id=session_id_2,
            checkpoint_id=checkpoint.id,
        )

        assert is_valid is False

    @pytest.mark.anyio
    async def test_list_checkpoints_handles_empty_session(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that list_checkpoints handles sessions with no checkpoints."""
        session_id = str(uuid4())

        result = await checkpoint_service.list_checkpoints(session_id=session_id)

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.anyio
    async def test_checkpoint_stores_multiple_files(
        self,
        checkpoint_service: CheckpointService,
    ) -> None:
        """Test that checkpoint can store multiple modified file paths."""
        session_id = str(uuid4())
        user_message_uuid = f"msg-{uuid4().hex[:8]}"
        files = [
            "/path/to/file1.py",
            "/path/to/file2.py",
            "/path/to/file3.py",
            "/path/to/nested/file4.py",
            "/path/to/nested/deep/file5.py",
        ]

        checkpoint = await checkpoint_service.create_checkpoint(
            session_id=session_id,
            user_message_uuid=user_message_uuid,
            files_modified=files,
        )

        assert checkpoint.files_modified == files

        # Verify persistence
        retrieved = await checkpoint_service.get_checkpoint(checkpoint.id)
        assert retrieved is not None
        assert len(retrieved.files_modified) == 5
        assert retrieved.files_modified == files
