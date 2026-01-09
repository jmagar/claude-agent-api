"""<summary>Aggregates streaming events for single-query responses.</summary>"""

import json
from typing import TYPE_CHECKING

import structlog

from apps.api.services.agent.types import StreamContext

if TYPE_CHECKING:
    from apps.api.services.agent.types import QueryResponseDict

logger = structlog.get_logger(__name__)


class SingleQueryAggregator:
    """<summary>Collects events and builds single-query response payloads.</summary>"""

    def __init__(self) -> None:
        """<summary>Initialize aggregator state.</summary>"""
        self._content_blocks: list[dict[str, object]] = []
        self._usage_data: dict[str, int] | None = None
        self._is_error = False

    @property
    def content_blocks(self) -> list[dict[str, object]]:
        """<summary>Return collected content blocks.</summary>"""
        return self._content_blocks

    @property
    def usage_data(self) -> dict[str, int] | None:
        """<summary>Return collected usage data.</summary>"""
        return self._usage_data

    @property
    def is_error(self) -> bool:
        """<summary>Return True if an error event was observed.</summary>"""
        return self._is_error

    def handle_event(self, event: dict[str, str]) -> None:
        """<summary>Handle a streaming event.</summary>"""
        event_type = event.get("event")
        if event_type == "message":
            try:
                event_data = json.loads(event.get("data", "{}"))
                if event_data.get("type") == "assistant":
                    self._content_blocks.extend(event_data.get("content", []))
                    if event_data.get("usage"):
                        msg_usage = event_data["usage"]
                        if self._usage_data is None:
                            self._usage_data = msg_usage.copy()
                        else:
                            for key, value in msg_usage.items():
                                if isinstance(value, int):
                                    self._usage_data[key] = (
                                        self._usage_data.get(key, 0) + value
                                    )
            except json.JSONDecodeError:
                logger.error("Failed to parse event data", event=event)
        elif event_type == "error":
            self._is_error = True

    def finalize(
        self,
        session_id: str,
        model: str,
        ctx: StreamContext,
        duration_ms: int,
    ) -> "QueryResponseDict":
        """<summary>Build the final single-query response payload.</summary>"""
        return {
            "session_id": session_id,
            "model": model,
            "content": self._content_blocks,
            "is_error": self._is_error or ctx.is_error,
            "duration_ms": duration_ms,
            "num_turns": ctx.num_turns,
            "total_cost_usd": ctx.total_cost_usd,
            "usage": self._usage_data,
            "result": ctx.result_text,
            "structured_output": ctx.structured_output,
        }
