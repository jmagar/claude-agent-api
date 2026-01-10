"""Unit tests for FileModificationTracker."""

from unittest.mock import MagicMock

from apps.api.schemas.responses import ContentBlockSchema
from apps.api.services.agent.file_modification_tracker import FileModificationTracker
from apps.api.services.agent.types import StreamContext


def test_file_modification_tracker_converts_dicts() -> None:
    handler = MagicMock()
    tracker = FileModificationTracker(handler)
    ctx = StreamContext(session_id="sid", model="sonnet", start_time=0.0)

    tracker.track([{"type": "text", "text": "hi"}], ctx)

    handler.track_file_modifications.assert_called_once()
    args, _ = handler.track_file_modifications.call_args
    assert isinstance(args[0][0], ContentBlockSchema)
    assert args[0][0].type == "text"
    assert args[0][0].text == "hi"
