"""Checkpoint management service (T101)."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, TypedDict, cast
from uuid import uuid4

import structlog

from apps.api.config import get_settings

if TYPE_CHECKING:
    from apps.api.protocols import Cache

logger = structlog.get_logger(__name__)


class CachedCheckpointData(TypedDict):
    """TypedDict for checkpoint data stored in Redis cache."""

    id: str
    session_id: str
    user_message_uuid: str
    created_at: str  # ISO format
    files_modified: list[str]


@dataclass
class Checkpoint:
    """Checkpoint data model."""

    id: str
    session_id: str
    user_message_uuid: str
    created_at: datetime
    files_modified: list[str]


class CheckpointService:
    """Service for managing file checkpoints."""

    def __init__(self, cache: "Cache | None" = None) -> None:
        """Initialize checkpoint service.

        Args:
            cache: Cache instance implementing Cache protocol.
        """
        self._cache = cache
        settings = get_settings()
        self._ttl = settings.redis_session_ttl

    def _checkpoints_key(self, session_id: str) -> str:
        """Generate cache key for session checkpoints list."""
        return f"checkpoints:{session_id}"

    def _checkpoint_key(self, checkpoint_id: str) -> str:
        """Generate cache key for individual checkpoint."""
        return f"checkpoint:{checkpoint_id}"

    def _uuid_index_key(self, user_message_uuid: str) -> str:
        """Generate cache key for user message UUID index."""
        return f"checkpoint_uuid_index:{user_message_uuid}"

    async def create_checkpoint(
        self,
        session_id: str,
        user_message_uuid: str,
        files_modified: list[str],
    ) -> Checkpoint:
        """Create a new checkpoint.

        Args:
            session_id: Session ID this checkpoint belongs to.
            user_message_uuid: UUID from the user message.
            files_modified: List of file paths modified at this checkpoint.

        Returns:
            Created checkpoint.

        Note:
            If cache is not configured, checkpoint will be created but not persisted.
        """
        if not self._cache:
            logger.warning(
                "CheckpointService has no cache configured - checkpoint will not be persisted",
                session_id=session_id,
                user_message_uuid=user_message_uuid,
            )

        now = datetime.now(UTC)
        checkpoint_id = str(uuid4())

        checkpoint = Checkpoint(
            id=checkpoint_id,
            session_id=session_id,
            user_message_uuid=user_message_uuid,
            created_at=now,
            files_modified=files_modified,
        )

        # Cache the checkpoint
        await self._cache_checkpoint(checkpoint)

        # Add to session checkpoints list
        await self._add_to_session_checkpoints(checkpoint)

        # Create UUID index for lookup by user_message_uuid
        await self._create_uuid_index(checkpoint)

        logger.info(
            "Checkpoint created",
            checkpoint_id=checkpoint_id,
            session_id=session_id,
            user_message_uuid=user_message_uuid,
            files_modified_count=len(files_modified),
        )

        return checkpoint

    async def get_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Get a checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint ID to retrieve.

        Returns:
            Checkpoint if found, None otherwise.
        """
        return await self._get_cached_checkpoint(checkpoint_id)

    async def get_checkpoint_by_user_message_uuid(
        self, user_message_uuid: str
    ) -> Checkpoint | None:
        """Get a checkpoint by user message UUID.

        Args:
            user_message_uuid: User message UUID to find checkpoint for.

        Returns:
            Checkpoint if found, None otherwise.
        """
        if not self._cache:
            return None

        # Look up checkpoint_id from UUID index
        index_key = self._uuid_index_key(user_message_uuid)
        checkpoint_id = await self._cache.get(index_key)

        if not checkpoint_id:
            return None

        return await self.get_checkpoint(checkpoint_id)

    async def list_checkpoints(self, session_id: str) -> list[Checkpoint]:
        """List all checkpoints for a session.

        Args:
            session_id: Session ID to get checkpoints for.

        Returns:
            List of checkpoints for the session.
        """
        if not self._cache:
            return []

        key = self._checkpoints_key(session_id)
        data = await self._cache.get_json(key)

        if not data:
            return []

        checkpoints_raw = data.get("checkpoints", [])
        if not isinstance(checkpoints_raw, list):
            return []

        checkpoints: list[Checkpoint] = []
        for checkpoint_data in checkpoints_raw:
            if not isinstance(checkpoint_data, dict):
                continue

            checkpoint = self._parse_checkpoint_data(checkpoint_data)
            if checkpoint:
                checkpoints.append(checkpoint)

        # Sort by created_at ascending (oldest first)
        checkpoints.sort(key=lambda c: c.created_at)

        return checkpoints

    async def validate_checkpoint(
        self, session_id: str, checkpoint_id: str
    ) -> bool:
        """Validate that a checkpoint exists and belongs to a session.

        Args:
            session_id: Session ID to validate against.
            checkpoint_id: Checkpoint ID to validate.

        Returns:
            True if checkpoint exists and belongs to session.
        """
        checkpoint = await self.get_checkpoint(checkpoint_id)

        if checkpoint is None:
            return False

        return checkpoint.session_id == session_id

    async def _cache_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Cache a checkpoint in Redis.

        Args:
            checkpoint: Checkpoint to cache.
        """
        if not self._cache:
            return

        key = self._checkpoint_key(checkpoint.id)
        data: CachedCheckpointData = {
            "id": checkpoint.id,
            "session_id": checkpoint.session_id,
            "user_message_uuid": checkpoint.user_message_uuid,
            "created_at": checkpoint.created_at.isoformat(),
            "files_modified": checkpoint.files_modified,
        }

        await self._cache.set_json(key, cast("dict[str, object]", data), self._ttl)

    async def _get_cached_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Get a checkpoint from cache.

        Args:
            checkpoint_id: Checkpoint ID to retrieve.

        Returns:
            Checkpoint if found in cache.
        """
        if not self._cache:
            return None

        key = self._checkpoint_key(checkpoint_id)
        parsed = await self._cache.get_json(key)

        if not parsed:
            return None

        return self._parse_checkpoint_data(parsed)

    async def _add_to_session_checkpoints(self, checkpoint: Checkpoint) -> None:
        """Add checkpoint to session checkpoints list.

        Args:
            checkpoint: Checkpoint to add.
        """
        if not self._cache:
            return

        key = self._checkpoints_key(checkpoint.session_id)
        data = await self._cache.get_json(key)

        if data is None:
            data = {"checkpoints": []}

        checkpoints_raw = data.get("checkpoints", [])
        if not isinstance(checkpoints_raw, list):
            checkpoints_raw = []

        checkpoint_data: CachedCheckpointData = {
            "id": checkpoint.id,
            "session_id": checkpoint.session_id,
            "user_message_uuid": checkpoint.user_message_uuid,
            "created_at": checkpoint.created_at.isoformat(),
            "files_modified": checkpoint.files_modified,
        }
        checkpoints_raw.append(checkpoint_data)

        data["checkpoints"] = checkpoints_raw
        await self._cache.set_json(key, data, self._ttl)

    async def _create_uuid_index(self, checkpoint: Checkpoint) -> None:
        """Create UUID index for checkpoint lookup.

        Args:
            checkpoint: Checkpoint to create index for.
        """
        if not self._cache:
            return

        index_key = self._uuid_index_key(checkpoint.user_message_uuid)
        await self._cache.cache_set(index_key, checkpoint.id, self._ttl)

    def _parse_checkpoint_data(
        self, data: dict[str, object]
    ) -> Checkpoint | None:
        """Parse checkpoint data from cache format.

        Args:
            data: Raw checkpoint data from cache.

        Returns:
            Parsed Checkpoint or None if invalid.
        """
        try:
            checkpoint_id = str(data["id"])
            session_id = str(data["session_id"])
            user_message_uuid = str(data["user_message_uuid"])
            created_at_str = str(data["created_at"])

            files_modified_raw = data.get("files_modified", [])
            if isinstance(files_modified_raw, list):
                files_modified = [str(f) for f in files_modified_raw]
            else:
                files_modified = []

            return Checkpoint(
                id=checkpoint_id,
                session_id=session_id,
                user_message_uuid=user_message_uuid,
                created_at=datetime.fromisoformat(created_at_str),
                files_modified=files_modified,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(
                "Failed to parse checkpoint data",
                error=str(e),
            )
            return None
