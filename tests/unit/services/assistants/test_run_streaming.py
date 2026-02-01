"""Unit tests for run streaming adapter (TDD - RED phase)."""

import pytest


class TestRunStreamingImports:
    """Tests for run streaming imports."""

    def test_can_import_run_streaming_adapter(self) -> None:
        """RunStreamingAdapter can be imported."""
        from apps.api.services.assistants.run_streaming import RunStreamingAdapter

        assert RunStreamingAdapter is not None

    def test_can_import_streaming_event_types(self) -> None:
        """Streaming event TypedDicts can be imported."""
        from apps.api.services.assistants.run_streaming import (
            AssistantStreamEvent,
            MessageDeltaEvent,
            RunCreatedEvent,
            RunDeltaEvent,
            RunStepDeltaEvent,
        )

        assert AssistantStreamEvent is not None
        assert RunCreatedEvent is not None
        assert RunDeltaEvent is not None
        assert RunStepDeltaEvent is not None
        assert MessageDeltaEvent is not None


class TestRunStreamingAdapterCreation:
    """Tests for creating RunStreamingAdapter."""

    def test_create_with_run_id(self) -> None:
        """Create adapter with run_id."""
        from apps.api.services.assistants.run_streaming import RunStreamingAdapter

        adapter = RunStreamingAdapter(
            run_id="run_abc123",
            thread_id="thread_xyz789",
            assistant_id="asst_def456",
        )

        assert adapter.run_id == "run_abc123"
        assert adapter.thread_id == "thread_xyz789"
        assert adapter.assistant_id == "asst_def456"


class TestStreamRunCreatedEvent:
    """Tests for thread.run.created event."""

    @pytest.mark.anyio
    async def test_stream_run_created_event(self) -> None:
        """First event is thread.run.created."""
        from apps.api.services.assistants.run_service import Run
        from apps.api.services.assistants.run_streaming import RunStreamingAdapter

        run = Run(
            id="run_abc123",
            thread_id="thread_xyz789",
            assistant_id="asst_def456",
            created_at=1704067200,
            status="queued",
            model="gpt-4",
            tools=[],
            metadata={},
        )

        adapter = RunStreamingAdapter(
            run_id=run.id,
            thread_id=run.thread_id,
            assistant_id=run.assistant_id,
        )

        # Get created event
        event = await adapter.emit_run_created(run)

        assert event["event"] == "thread.run.created"
        assert event["data"]["id"] == "run_abc123"
        assert event["data"]["status"] == "queued"


class TestStreamRunInProgressEvent:
    """Tests for thread.run.in_progress event."""

    @pytest.mark.anyio
    async def test_stream_run_in_progress_event(self) -> None:
        """Emit thread.run.in_progress when run starts."""
        from apps.api.services.assistants.run_service import Run
        from apps.api.services.assistants.run_streaming import RunStreamingAdapter

        run = Run(
            id="run_abc123",
            thread_id="thread_xyz789",
            assistant_id="asst_def456",
            created_at=1704067200,
            status="in_progress",
            model="gpt-4",
            tools=[],
            metadata={},
        )

        adapter = RunStreamingAdapter(
            run_id=run.id,
            thread_id=run.thread_id,
            assistant_id=run.assistant_id,
        )

        event = await adapter.emit_run_in_progress(run)

        assert event["event"] == "thread.run.in_progress"
        assert event["data"]["status"] == "in_progress"


class TestStreamMessageDeltaEvent:
    """Tests for thread.message.delta event."""

    @pytest.mark.anyio
    async def test_stream_message_delta_text(self) -> None:
        """Emit thread.message.delta for text content."""
        from apps.api.services.assistants.run_streaming import RunStreamingAdapter

        adapter = RunStreamingAdapter(
            run_id="run_abc123",
            thread_id="thread_xyz789",
            assistant_id="asst_def456",
        )

        event = await adapter.emit_message_delta(
            message_id="msg_xyz789",
            content_delta="Hello, ",
        )

        assert event["event"] == "thread.message.delta"
        assert event["data"]["id"] == "msg_xyz789"
        assert event["data"]["delta"]["content"][0]["text"]["value"] == "Hello, "


class TestStreamRunCompletedEvent:
    """Tests for thread.run.completed event."""

    @pytest.mark.anyio
    async def test_stream_run_completed_event(self) -> None:
        """Emit thread.run.completed when run finishes."""
        from typing import cast

        from apps.api.services.assistants.run_service import Run
        from apps.api.services.assistants.run_streaming import RunStreamingAdapter

        run = Run(
            id="run_abc123",
            thread_id="thread_xyz789",
            assistant_id="asst_def456",
            created_at=1704067200,
            status="completed",
            model="gpt-4",
            tools=[],
            metadata={},
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

        adapter = RunStreamingAdapter(
            run_id=run.id,
            thread_id=run.thread_id,
            assistant_id=run.assistant_id,
        )

        event = await adapter.emit_run_completed(run)

        assert event["event"] == "thread.run.completed"
        data = event["data"]
        assert data["status"] == "completed"
        usage = data.get("usage")
        assert isinstance(usage, dict)
        usage_dict = cast("dict[str, int]", usage)
        assert usage_dict["total_tokens"] == 150


class TestStreamRunRequiresActionEvent:
    """Tests for thread.run.requires_action event."""

    @pytest.mark.anyio
    async def test_stream_run_requires_action_event(self) -> None:
        """Emit thread.run.requires_action for tool calls."""
        from apps.api.services.assistants.run_service import Run, ToolCall
        from apps.api.services.assistants.run_streaming import RunStreamingAdapter

        tool_calls: list[ToolCall] = [
            {
                "id": "call_abc123",
                "type": "function",
                "function": {"name": "get_weather", "arguments": '{"location": "NYC"}'},
            }
        ]

        run = Run(
            id="run_abc123",
            thread_id="thread_xyz789",
            assistant_id="asst_def456",
            created_at=1704067200,
            status="requires_action",
            model="gpt-4",
            tools=[],
            metadata={},
            required_action={
                "type": "submit_tool_outputs",
                "submit_tool_outputs": {"tool_calls": tool_calls},
            },
        )

        adapter = RunStreamingAdapter(
            run_id=run.id,
            thread_id=run.thread_id,
            assistant_id=run.assistant_id,
        )

        event = await adapter.emit_run_requires_action(run)

        assert event["event"] == "thread.run.requires_action"
        assert event["data"]["status"] == "requires_action"
        assert event["data"]["required_action"] is not None


class TestStreamRunFailedEvent:
    """Tests for thread.run.failed event."""

    @pytest.mark.anyio
    async def test_stream_run_failed_event(self) -> None:
        """Emit thread.run.failed when run errors."""
        from typing import cast

        from apps.api.services.assistants.run_service import Run
        from apps.api.services.assistants.run_streaming import RunStreamingAdapter

        run = Run(
            id="run_abc123",
            thread_id="thread_xyz789",
            assistant_id="asst_def456",
            created_at=1704067200,
            status="failed",
            model="gpt-4",
            tools=[],
            metadata={},
            last_error={"code": "server_error", "message": "Something went wrong"},
        )

        adapter = RunStreamingAdapter(
            run_id=run.id,
            thread_id=run.thread_id,
            assistant_id=run.assistant_id,
        )

        event = await adapter.emit_run_failed(run)

        assert event["event"] == "thread.run.failed"
        data = event["data"]
        assert data["status"] == "failed"
        last_error = data.get("last_error")
        assert isinstance(last_error, dict)
        last_error_dict = cast("dict[str, str]", last_error)
        assert last_error_dict["code"] == "server_error"


class TestStreamDoneMarker:
    """Tests for [DONE] marker."""

    @pytest.mark.anyio
    async def test_emit_done_marker(self) -> None:
        """Emit done marker at end of stream."""
        from apps.api.services.assistants.run_streaming import RunStreamingAdapter

        adapter = RunStreamingAdapter(
            run_id="run_abc123",
            thread_id="thread_xyz789",
            assistant_id="asst_def456",
        )

        done = await adapter.emit_done()

        assert done == "done"


class TestFormatSSEEvent:
    """Tests for SSE event formatting."""

    def test_format_event_as_sse(self) -> None:
        """Format event as SSE data line."""
        from apps.api.services.assistants.run_streaming import (
            RunCreatedEvent,
            format_sse_event,
        )

        event: RunCreatedEvent = {
            "event": "thread.run.created",
            "data": {"id": "run_abc123", "status": "queued"},
        }

        sse = format_sse_event(event)

        assert "event: thread.run.created" in sse
        assert "data:" in sse
        assert '"id": "run_abc123"' in sse

    def test_format_done_marker_as_sse(self) -> None:
        """Format done marker as SSE data line."""
        from apps.api.services.assistants.run_streaming import format_sse_event

        sse = format_sse_event("done")

        assert sse == "data: [DONE]\n\n"
