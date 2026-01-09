"""Unit tests for StreamOrchestrator."""

import pytest

from apps.api.services.agent.handlers import MessageHandler
from apps.api.services.agent.stream_orchestrator import StreamOrchestrator


@pytest.mark.anyio
async def test_stream_orchestrator_builds_init_and_done_events() -> None:
    """Test init and done events are formatted correctly."""
    orchestrator = StreamOrchestrator(message_handler=MessageHandler())
    init_event = orchestrator.build_init_event(
        session_id="sid",
        model="sonnet",
        tools=["Read"],
        plugins=[],
        commands=[],
        permission_mode="default",
    )
    done_event = orchestrator.build_done_event(reason="completed")

    assert init_event["event"] == "init"
    assert done_event["event"] == "done"
