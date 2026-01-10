"""Unit tests for StreamQueryRunner delegation."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.schemas.requests.query import QueryRequest
from apps.api.services.agent.stream_query_runner import StreamQueryRunner


@pytest.mark.anyio
async def test_stream_query_runner_executes_query() -> None:
    session_tracker = AsyncMock()
    session_tracker.is_interrupted.return_value = False
    query_executor = MagicMock()
    stream_orchestrator = MagicMock()
    stream_orchestrator.build_result_event.return_value = {
        "event": "result",
        "data": "{}",
    }
    stream_orchestrator.build_done_event.return_value = {
        "event": "done",
        "data": "{}",
    }

    async def _execute(
        _request: QueryRequest, _ctx: object, _commands: object
    ) -> AsyncGenerator[dict[str, str], None]:
        yield {"event": "message", "data": "{}"}

    query_executor.execute.side_effect = _execute

    commands_service = MagicMock()
    runner = StreamQueryRunner(
        session_tracker=session_tracker,
        query_executor=query_executor,
        stream_orchestrator=stream_orchestrator,
    )
    request = QueryRequest(prompt="test")

    events = []
    async for event in runner.run(request, commands_service):
        events.append(event)

    assert {"event": "message", "data": "{}"} in events
    query_executor.execute.assert_called_once()


@pytest.mark.anyio
async def test_stream_query_runner_interrupts_session() -> None:
    session_tracker = AsyncMock()
    session_tracker.is_interrupted.return_value = True
    query_executor = MagicMock()
    stream_orchestrator = MagicMock()
    stream_orchestrator.build_result_event.return_value = {
        "event": "result",
        "data": "{}",
    }
    stream_orchestrator.build_done_event.return_value = {
        "event": "done",
        "data": "{}",
    }

    async def _execute(
        _request: QueryRequest, _ctx: object, _commands: object
    ) -> AsyncGenerator[dict[str, str], None]:
        yield {"event": "message", "data": "{}"}

    query_executor.execute.side_effect = _execute

    commands_service = MagicMock()
    runner = StreamQueryRunner(
        session_tracker=session_tracker,
        query_executor=query_executor,
        stream_orchestrator=stream_orchestrator,
    )
    request = QueryRequest(prompt="test")

    events = []
    async for event in runner.run(request, commands_service):
        events.append(event)

    assert events[-1]["event"] == "done"
    stream_orchestrator.build_done_event.assert_called_once_with(reason="interrupted")


@pytest.mark.anyio
async def test_stream_query_runner_emits_error_on_exception() -> None:
    session_tracker = AsyncMock()
    session_tracker.is_interrupted.return_value = False
    query_executor = MagicMock()
    stream_orchestrator = MagicMock()
    stream_orchestrator.build_done_event.return_value = {
        "event": "done",
        "data": "{}",
    }
    stream_orchestrator.build_error_event.return_value = {
        "event": "error",
        "data": "{}",
    }

    async def _execute(
        _request: QueryRequest, _ctx: object, _commands: object
    ) -> AsyncGenerator[dict[str, str], None]:
        raise RuntimeError("boom")
        yield {"event": "never", "data": "{}"}

    query_executor.execute.side_effect = _execute

    commands_service = MagicMock()
    runner = StreamQueryRunner(
        session_tracker=session_tracker,
        query_executor=query_executor,
        stream_orchestrator=stream_orchestrator,
    )
    request = QueryRequest(prompt="test")

    events = []
    async for event in runner.run(request, commands_service):
        events.append(event)

    assert events[-1]["event"] == "done"
    assert {"event": "error", "data": "{}"} in events
