"""<summary>Run streaming queries for AgentService.</summary>"""

import time
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

import structlog

from apps.api.services.agent.query_executor import QueryExecutor
from apps.api.services.agent.session_tracker import AgentSessionTracker
from apps.api.services.agent.stream_orchestrator import StreamOrchestrator
from apps.api.services.agent.types import StreamContext

if TYPE_CHECKING:
    from apps.api.schemas.requests.query import QueryRequest
    from apps.api.services.commands import CommandsService

logger = structlog.get_logger(__name__)


class StreamQueryRunner:
    """<summary>Handles the streaming query flow.</summary>"""

    def __init__(
        self,
        session_tracker: AgentSessionTracker | None = None,
        query_executor: QueryExecutor | None = None,
        stream_orchestrator: StreamOrchestrator | None = None,
    ) -> None:
        """<summary>Initialize dependencies.</summary>"""
        self._session_tracker = session_tracker
        self._query_executor = query_executor
        self._stream_orchestrator = stream_orchestrator

    async def run(
        self,
        request: "QueryRequest",
        commands_service: "CommandsService",
        session_id_override: str | None = None,
    ) -> AsyncGenerator[dict[str, str], None]:
        """<summary>Execute the streaming query flow.</summary>"""
        if (
            not self._session_tracker
            or not self._query_executor
            or not self._stream_orchestrator
        ):
            raise RuntimeError("StreamQueryRunner dependencies not configured")

        session_id = session_id_override or request.session_id or str(uuid4())
        model = request.model or "sonnet"
        ctx = StreamContext(
            session_id=session_id,
            model=model,
            start_time=time.perf_counter(),
            enable_file_checkpointing=request.enable_file_checkpointing,
            include_partial_messages=request.include_partial_messages,
        )

        await self._session_tracker.register(session_id)

        try:
            async for event in self._query_executor.execute(
                request, ctx, commands_service
            ):
                yield event
                if await self._session_tracker.is_interrupted(session_id):
                    duration_ms = int((time.perf_counter() - ctx.start_time) * 1000)
                    yield self._stream_orchestrator.build_result_event(
                        ctx=ctx,
                        duration_ms=duration_ms,
                    )
                    yield self._stream_orchestrator.build_done_event(
                        reason="interrupted",
                    )
                    return

            duration_ms = int((time.perf_counter() - ctx.start_time) * 1000)
            yield self._stream_orchestrator.build_result_event(
                ctx=ctx,
                duration_ms=duration_ms,
            )
            reason: Literal["completed", "error"] = (
                "error" if ctx.is_error else "completed"
            )
            yield self._stream_orchestrator.build_done_event(reason=reason)
        except Exception as exc:
            logger.exception(
                "Stream query execution failed",
                session_id=session_id,
                error=str(exc),
            )
            yield self._stream_orchestrator.build_error_event(
                "AGENT_ERROR",
                "Internal error",
            )
            yield self._stream_orchestrator.build_done_event(reason="error")
        finally:
            await self._session_tracker.unregister(session_id)
