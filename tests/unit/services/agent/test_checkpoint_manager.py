"""Unit tests for CheckpointManager."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.services.agent.checkpoint_manager import CheckpointManager
from apps.api.services.agent.types import StreamContext


@pytest.mark.anyio
async def test_checkpoint_manager_skips_when_disabled() -> None:
    checkpoint_service = AsyncMock()
    manager = CheckpointManager(checkpoint_service=checkpoint_service)
    ctx = StreamContext(session_id="sid", model="sonnet", start_time=0.0)

    result = await manager.create_from_context(ctx)

    assert result is None
    checkpoint_service.create_checkpoint.assert_not_called()


@pytest.mark.anyio
async def test_checkpoint_manager_creates_checkpoint_when_enabled() -> None:
    checkpoint_service = AsyncMock()
    checkpoint_service.create_checkpoint.return_value = MagicMock(id="chk-1")
    manager = CheckpointManager(checkpoint_service=checkpoint_service)
    ctx = StreamContext(
        session_id="sid",
        model="sonnet",
        start_time=0.0,
        enable_file_checkpointing=True,
    )
    ctx.last_user_message_uuid = "uuid-1"
    ctx.files_modified = ["a.txt"]

    result = await manager.create_from_context(ctx)

    assert result is not None
    checkpoint_service.create_checkpoint.assert_called_once_with(
        session_id="sid",
        user_message_uuid="uuid-1",
        files_modified=["a.txt"],
    )
