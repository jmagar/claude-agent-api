"""Unit tests for StreamOrchestrator."""

import json

import pytest

from apps.api.services.agent.handlers import MessageHandler
from apps.api.services.agent.stream_orchestrator import StreamOrchestrator
from apps.api.services.agent.types import StreamContext


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
    init_data = json.loads(init_event["data"])
    assert init_data["session_id"] == "sid"
    assert init_data["model"] == "sonnet"
    assert init_data["tools"] == ["Read"]
    assert init_data["plugins"] == []
    assert init_data["commands"] == []
    assert init_data["permission_mode"] == "default"
    assert init_data["mcp_servers"] == []

    assert done_event["event"] == "done"
    done_data = json.loads(done_event["data"])
    assert done_data["reason"] == "completed"


@pytest.mark.parametrize("reason", ["completed", "interrupted", "error"])
def test_stream_orchestrator_builds_done_event_reasons(reason: str) -> None:
    """Test done events include expected reason values."""
    orchestrator = StreamOrchestrator(message_handler=MessageHandler())
    done_event = orchestrator.build_done_event(reason=reason)

    assert done_event["event"] == "done"
    done_data = json.loads(done_event["data"])
    assert done_data["reason"] == reason


def test_stream_orchestrator_builds_result_event_payload() -> None:
    """Test result event payload includes expected fields."""
    orchestrator = StreamOrchestrator(message_handler=MessageHandler())
    ctx = StreamContext(session_id="sid", model="sonnet", start_time=0.0)
    ctx.num_turns = 2
    ctx.total_cost_usd = 1.23
    ctx.model_usage = {
        "sonnet": {
            "input_tokens": 10,
            "output_tokens": 5,
            "cache_read_input_tokens": 1,
            "cache_creation_input_tokens": 2,
        }
    }
    ctx.result_text = "done"
    ctx.structured_output = {"answer": "ok"}

    result_event = orchestrator.build_result_event(ctx=ctx, duration_ms=11)

    assert result_event["event"] == "result"
    result_data = json.loads(result_event["data"])
    assert result_data["session_id"] == "sid"
    assert result_data["is_error"] is False
    assert result_data["duration_ms"] == 11
    assert result_data["num_turns"] == 2
    assert result_data["total_cost_usd"] == 1.23
    assert result_data["result"] == "done"
    assert result_data["structured_output"] == {"answer": "ok"}
    assert result_data["model_usage"]["sonnet"]["input_tokens"] == 10
    assert result_data["model_usage"]["sonnet"]["output_tokens"] == 5
    assert result_data["model_usage"]["sonnet"]["cache_read_input_tokens"] == 1
    assert result_data["model_usage"]["sonnet"]["cache_creation_input_tokens"] == 2
