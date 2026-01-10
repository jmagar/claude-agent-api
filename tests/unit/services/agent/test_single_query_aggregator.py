"""Unit tests for SingleQueryAggregator."""

from apps.api.services.agent.single_query_aggregator import SingleQueryAggregator
from apps.api.services.agent.types import StreamContext


def test_single_query_aggregator_finalizes_result() -> None:
    """Test aggregator builds a minimal result payload."""
    aggregator = SingleQueryAggregator()
    ctx = StreamContext(session_id="sid", model="sonnet", start_time=0.0)

    result = aggregator.finalize(
        session_id="sid",
        model="sonnet",
        ctx=ctx,
        duration_ms=10,
    )

    assert result["session_id"] == "sid"
    assert result["model"] == "sonnet"
    assert result["duration_ms"] == 10
    assert result["num_turns"] == 0
    assert result["is_error"] is False
    assert result["content"] == []
    assert result["usage"] is None
    assert result["total_cost_usd"] is None
    assert result["result"] is None
    assert result["structured_output"] is None
