"""<summary>Create checkpoints from stream context data.</summary>"""

from typing import TYPE_CHECKING

import structlog

from apps.api.services.agent.types import StreamContext

if TYPE_CHECKING:
    from apps.api.services.checkpoint import Checkpoint, CheckpointService

logger = structlog.get_logger(__name__)


class CheckpointManager:
    """<summary>Manages checkpoint creation from a stream context.</summary>"""

    def __init__(self, checkpoint_service: "CheckpointService | None") -> None:
        """<summary>Initialize with a checkpoint service.</summary>"""
        self._checkpoint_service = checkpoint_service

    async def create_from_context(self, ctx: StreamContext) -> "Checkpoint | None":
        """<summary>Create a checkpoint using stream context data.</summary>"""
        if not ctx.enable_file_checkpointing:
            return None
        if not ctx.last_user_message_uuid:
            return None
        if not self._checkpoint_service:
            logger.warning(
                "Cannot create checkpoint: checkpoint_service not configured",
                session_id=ctx.session_id,
            )
            return None

        try:
            checkpoint = await self._checkpoint_service.create_checkpoint(
                session_id=ctx.session_id,
                user_message_uuid=ctx.last_user_message_uuid,
                files_modified=ctx.files_modified.copy(),
            )
            logger.info(
                "Created checkpoint from context",
                checkpoint_id=checkpoint.id,
                session_id=ctx.session_id,
                user_message_uuid=ctx.last_user_message_uuid,
                files_count=len(ctx.files_modified),
            )
            return checkpoint
        except Exception as exc:
            logger.error(
                "Failed to create checkpoint from context",
                session_id=ctx.session_id,
                error=str(exc),
            )
            return None
