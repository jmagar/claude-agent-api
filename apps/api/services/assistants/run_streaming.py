"""Run streaming adapter for OpenAI Assistants API SSE events.

Emits Server-Sent Events (SSE) for run state changes, message deltas,
and step updates following OpenAI's Assistants API streaming protocol.
"""

import json
from typing import Literal, Required, TypedDict

import structlog

from apps.api.services.assistants.run_service import Run

logger = structlog.get_logger(__name__)


# =============================================================================
# SSE Event Types
# =============================================================================

# Event type literals
EventType = Literal[
    "thread.run.created",
    "thread.run.queued",
    "thread.run.in_progress",
    "thread.run.requires_action",
    "thread.run.completed",
    "thread.run.failed",
    "thread.run.cancelling",
    "thread.run.cancelled",
    "thread.run.expired",
    "thread.run.step.created",
    "thread.run.step.in_progress",
    "thread.run.step.delta",
    "thread.run.step.completed",
    "thread.run.step.failed",
    "thread.run.step.cancelled",
    "thread.run.step.expired",
    "thread.message.created",
    "thread.message.in_progress",
    "thread.message.delta",
    "thread.message.completed",
    "thread.message.incomplete",
]


class TextDeltaContent(TypedDict):
    """Text delta content block."""

    value: Required[str]


class ContentDeltaBlock(TypedDict):
    """Content delta block."""

    type: Literal["text"]
    text: TextDeltaContent


class MessageDelta(TypedDict):
    """Message delta object."""

    content: Required[list[ContentDeltaBlock]]


class MessageDeltaData(TypedDict):
    """Message delta event data."""

    id: Required[str]
    object: Required[Literal["thread.message.delta"]]
    delta: Required[MessageDelta]


class RunCreatedEvent(TypedDict):
    """thread.run.created event."""

    event: Required[Literal["thread.run.created"]]
    data: Required[dict[str, object]]


class RunDeltaEvent(TypedDict):
    """thread.run.* status change events."""

    event: Required[EventType]
    data: Required[dict[str, object]]


class RunStepDeltaEvent(TypedDict):
    """thread.run.step.* events."""

    event: Required[EventType]
    data: Required[dict[str, object]]


class MessageDeltaEvent(TypedDict):
    """thread.message.delta event."""

    event: Required[Literal["thread.message.delta"]]
    data: Required[MessageDeltaData]


# Union type for all assistant stream events
AssistantStreamEvent = (
    RunCreatedEvent | RunDeltaEvent | RunStepDeltaEvent | MessageDeltaEvent
)


# =============================================================================
# Run Streaming Adapter
# =============================================================================


class RunStreamingAdapter:
    """Adapter for emitting OpenAI Assistants API streaming events.

    Transforms run state changes and content updates into SSE events
    following OpenAI's streaming protocol.

    Event sequence for a typical run:
    1. thread.run.created
    2. thread.run.queued
    3. thread.run.in_progress
    4. thread.run.step.created (message_creation)
    5. thread.message.created
    6. thread.message.in_progress
    7. thread.message.delta (multiple)
    8. thread.message.completed
    9. thread.run.step.completed
    10. thread.run.completed
    """

    def __init__(
        self,
        run_id: str,
        thread_id: str,
        assistant_id: str,
    ) -> None:
        """Initialize streaming adapter.

        Args:
            run_id: The run ID.
            thread_id: The thread ID.
            assistant_id: The assistant ID.
        """
        self.run_id = run_id
        self.thread_id = thread_id
        self.assistant_id = assistant_id

    def _run_to_dict(self, run: Run) -> dict[str, object]:
        """Convert Run to dictionary for event data.

        Args:
            run: Run object to convert.

        Returns:
            Dictionary representation of run.
        """
        data: dict[str, object] = {
            "id": run.id,
            "object": "thread.run",
            "created_at": run.created_at,
            "thread_id": run.thread_id,
            "assistant_id": run.assistant_id,
            "status": run.status,
            "model": run.model,
            "instructions": run.instructions,
            "tools": run.tools,
            "metadata": run.metadata,
            "started_at": run.started_at,
            "expires_at": run.expires_at,
            "cancelled_at": run.cancelled_at,
            "failed_at": run.failed_at,
            "completed_at": run.completed_at,
        }

        # Add optional fields
        if run.required_action is not None:
            data["required_action"] = dict(run.required_action)
        else:
            data["required_action"] = None

        if run.last_error is not None:
            data["last_error"] = dict(run.last_error)
        else:
            data["last_error"] = None

        if run.usage is not None:
            data["usage"] = dict(run.usage)
        else:
            data["usage"] = None

        return data

    async def emit_run_created(self, run: Run) -> RunCreatedEvent:
        """Emit thread.run.created event.

        Args:
            run: The created run.

        Returns:
            SSE event for run creation.
        """
        logger.debug(
            "Emitting run created event",
            run_id=run.id,
            thread_id=run.thread_id,
        )

        return RunCreatedEvent(
            event="thread.run.created",
            data=self._run_to_dict(run),
        )

    async def emit_run_in_progress(self, run: Run) -> RunDeltaEvent:
        """Emit thread.run.in_progress event.

        Args:
            run: The run in progress.

        Returns:
            SSE event for run in progress.
        """
        logger.debug(
            "Emitting run in_progress event",
            run_id=run.id,
        )

        return RunDeltaEvent(
            event="thread.run.in_progress",
            data=self._run_to_dict(run),
        )

    async def emit_run_completed(self, run: Run) -> RunDeltaEvent:
        """Emit thread.run.completed event.

        Args:
            run: The completed run.

        Returns:
            SSE event for run completion.
        """
        logger.debug(
            "Emitting run completed event",
            run_id=run.id,
            usage=run.usage,
        )

        return RunDeltaEvent(
            event="thread.run.completed",
            data=self._run_to_dict(run),
        )

    async def emit_run_failed(self, run: Run) -> RunDeltaEvent:
        """Emit thread.run.failed event.

        Args:
            run: The failed run.

        Returns:
            SSE event for run failure.
        """
        logger.debug(
            "Emitting run failed event",
            run_id=run.id,
            error=run.last_error,
        )

        return RunDeltaEvent(
            event="thread.run.failed",
            data=self._run_to_dict(run),
        )

    async def emit_run_requires_action(self, run: Run) -> RunDeltaEvent:
        """Emit thread.run.requires_action event.

        Args:
            run: The run requiring action.

        Returns:
            SSE event for requires action.
        """
        logger.debug(
            "Emitting run requires_action event",
            run_id=run.id,
            required_action=run.required_action,
        )

        return RunDeltaEvent(
            event="thread.run.requires_action",
            data=self._run_to_dict(run),
        )

    async def emit_run_cancelled(self, run: Run) -> RunDeltaEvent:
        """Emit thread.run.cancelled event.

        Args:
            run: The cancelled run.

        Returns:
            SSE event for run cancellation.
        """
        logger.debug(
            "Emitting run cancelled event",
            run_id=run.id,
        )

        return RunDeltaEvent(
            event="thread.run.cancelled",
            data=self._run_to_dict(run),
        )

    async def emit_message_delta(
        self,
        message_id: str,
        content_delta: str,
    ) -> MessageDeltaEvent:
        """Emit thread.message.delta event.

        Args:
            message_id: The message ID.
            content_delta: The text content delta.

        Returns:
            SSE event for message delta.
        """
        logger.debug(
            "Emitting message delta event",
            message_id=message_id,
            delta_length=len(content_delta),
        )

        return MessageDeltaEvent(
            event="thread.message.delta",
            data=MessageDeltaData(
                id=message_id,
                object="thread.message.delta",
                delta=MessageDelta(
                    content=[
                        ContentDeltaBlock(
                            type="text",
                            text=TextDeltaContent(value=content_delta),
                        )
                    ]
                ),
            ),
        )

    async def emit_done(self) -> str:
        """Emit done marker.

        Returns:
            Done marker string.
        """
        logger.debug("Emitting done marker", run_id=self.run_id)
        return "done"


# =============================================================================
# SSE Formatting
# =============================================================================


def format_sse_event(event: AssistantStreamEvent | str) -> str:
    """Format an event as an SSE data line.

    Args:
        event: Event to format (dict or "done" string).

    Returns:
        SSE-formatted string.
    """
    if event == "done":
        return "data: [DONE]\n\n"

    if isinstance(event, dict):
        event_type = event.get("event", "")
        data = event.get("data", {})
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    # Fallback for unknown types
    return f"data: {json.dumps(event)}\n\n"
