"""Aggregates streaming events for single-query responses."""

import json
from typing import TYPE_CHECKING

import structlog

from apps.api.services.agent.types import StreamContext

if TYPE_CHECKING:
    from apps.api.services.agent.types import QueryResponseDict

logger = structlog.get_logger(__name__)


class SingleQueryAggregator:
    """Collects events and builds single-query response payloads."""

    def __init__(self) -> None:
        """Initialize aggregator state."""
        self._content_blocks: list[dict[str, object]] = []
        self._usage_data: dict[str, int] | None = None
        self._is_error = False

    @property
    def content_blocks(self) -> list[dict[str, object]]:
        """Return collected content blocks."""
        return self._content_blocks

    @property
    def usage_data(self) -> dict[str, int] | None:
        """Return collected usage data."""
        return self._usage_data

    @property
    def is_error(self) -> bool:
        """Return True if an error event was observed."""
        return self._is_error

    def handle_event(self, event: dict[str, str]) -> None:
        """Handle a streaming event.

        Processes 'message' events for content aggregation, 'result' events
        for final usage statistics, and 'error' events for error state tracking.

        Args:
            event: SSE event dict with 'event' and 'data' keys.
        """
        event_type = event.get("event")
        if event_type == "message":
            try:
                event_data = json.loads(event.get("data", "{}"))
                if event_data.get("type") == "assistant":
                    self._content_blocks.extend(event_data.get("content", []))
                    self._accumulate_usage(event_data.get("usage"))
            except json.JSONDecodeError:
                logger.error("Failed to parse event data", event=event)
        elif event_type == "result":
            # Result event contains final usage statistics
            try:
                event_data = json.loads(event.get("data", "{}"))
                self._accumulate_usage(event_data.get("usage"))
            except json.JSONDecodeError:
                logger.error("Failed to parse result event data", event=event)
        elif event_type == "error":
            self._is_error = True

    def _accumulate_usage(self, usage: dict[str, int] | None) -> None:
        """Accumulate usage statistics.

        Args:
            usage: Usage dict with input_tokens, output_tokens, etc.
        """
        if not usage:
            return
        if self._usage_data is None:
            self._usage_data = usage.copy()
        else:
            for key, value in usage.items():
                if isinstance(value, int):
                    self._usage_data[key] = self._usage_data.get(key, 0) + value

    def finalize(
        self,
        session_id: str,
        model: str,
        ctx: StreamContext,
        duration_ms: int,
    ) -> "QueryResponseDict":
        """Build the final single-query response payload.

        Args:
            session_id: The session identifier.
            model: The model name used for the query.
            ctx: Stream context containing aggregated metadata.
            duration_ms: Total query duration in milliseconds.

        Returns:
            A dictionary containing the complete query response.
        """
        # Prefer ctx.usage (from SDK ResultMessage) over aggregated event usage
        usage = ctx.usage if ctx.usage else self._usage_data

        return {
            "session_id": session_id,
            "model": model,
            "content": self._content_blocks,
            "is_error": self._is_error or ctx.is_error,
            "duration_ms": duration_ms,
            "num_turns": ctx.num_turns,
            "total_cost_usd": ctx.total_cost_usd,
            "usage": usage,
            "result": ctx.result_text,
            "structured_output": ctx.structured_output,
        }
