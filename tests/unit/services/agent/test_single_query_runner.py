"""Unit tests for SingleQueryRunner delegation."""

from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest

from apps.api.schemas.requests.query import QueryRequest
from apps.api.services.agent.single_query_runner import SingleQueryRunner


@pytest.mark.anyio
async def test_single_query_runner_aggregates_assistant_content() -> None:
    query_executor = MagicMock()

    async def _execute(
        _request: QueryRequest, _ctx: object, _commands: object
    ) -> AsyncGenerator[dict[str, str], None]:
        yield {
            "event": "message",
            "data": '{"type": "assistant", "content": [{"type": "text", "text": "hi"}]}',
        }

    query_executor.execute.side_effect = _execute

    commands_service = MagicMock()
    runner = SingleQueryRunner(query_executor=query_executor)
    request = QueryRequest(prompt="test")
    result = await runner.run(request, commands_service)

    assert result["content"] == [{"type": "text", "text": "hi"}]
    assert result["is_error"] is False


@pytest.mark.anyio
async def test_single_query_runner_handles_executor_error() -> None:
    query_executor = MagicMock()

    async def _execute(
        _request: QueryRequest, _ctx: object, _commands: object
    ) -> AsyncGenerator[dict[str, str], None]:
        raise RuntimeError("boom")
        yield {"event": "never", "data": "{}"}

    query_executor.execute.side_effect = _execute

    commands_service = MagicMock()
    runner = SingleQueryRunner(query_executor=query_executor)
    request = QueryRequest(prompt="test")
    result = await runner.run(request, commands_service)

    assert result["is_error"] is True
    assert result["content"] == [{"type": "text", "text": "Error: Internal error"}]
