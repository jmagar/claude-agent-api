"""Type definitions for agent service."""

from dataclasses import dataclass, field
from typing import TypedDict


class QueryResponseDict(TypedDict):
    """TypedDict for non-streaming query response.

    Contains the complete response data for a non-streaming query,
    including session info, content, usage statistics, and results.
    """

    session_id: str
    model: str
    content: list[dict[str, object]]
    is_error: bool
    duration_ms: int
    num_turns: int
    total_cost_usd: float | None
    usage: dict[str, int] | None
    result: str | None
    structured_output: dict[str, object] | None


@dataclass
class StreamContext:
    """Context for a streaming query.

    Maintains state throughout a streaming query session, including:
    - Session metadata (ID, model, timing)
    - Query progress (turns, cost, errors)
    - Checkpoint tracking (file modifications, message UUIDs)
    - Partial message configuration
    """

    session_id: str
    model: str
    start_time: float
    num_turns: int = 0
    total_cost_usd: float | None = None
    is_error: bool = False
    result_text: str | None = None
    structured_output: dict[str, object] | None = None
    # Model usage tracking (T110)
    model_usage: dict[str, dict[str, int]] | None = None
    # Checkpoint tracking fields (T100, T104)
    enable_file_checkpointing: bool = False
    last_user_message_uuid: str | None = None
    files_modified: list[str] = field(default_factory=list)
    # Partial messages tracking (T118)
    include_partial_messages: bool = False
