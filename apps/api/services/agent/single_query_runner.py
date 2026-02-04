"""<summary>Run single-shot queries for AgentService.</summary>"""

import time
from typing import TYPE_CHECKING
from uuid import uuid4

import structlog

from apps.api.services.agent.query_executor import QueryExecutor
from apps.api.services.agent.single_query_aggregator import SingleQueryAggregator
from apps.api.services.agent.types import StreamContext

if TYPE_CHECKING:
    from apps.api.schemas.requests.query import QueryRequest
    from apps.api.services.agent.types import QueryResponseDict
    from apps.api.services.commands import CommandsService
    from apps.api.services.memory import MemoryService

logger = structlog.get_logger(__name__)


class SingleQueryRunner:
    """<summary>Handles the single query flow.</summary>"""

    def __init__(self, query_executor: QueryExecutor | None = None) -> None:
        """<summary>Initialize dependencies.</summary>"""
        self._query_executor = query_executor

    async def run(
        self,
        request: "QueryRequest",
        commands_service: "CommandsService",
        memory_service: "MemoryService | None" = None,
        api_key: str = "",
    ) -> "QueryResponseDict":
        """<summary>Execute a single query and aggregate results with memory integration.</summary>

        Args:
            request: Query request.
            commands_service: Commands service for slash command detection.
            memory_service: Optional MemoryService for memory injection/extraction.
            api_key: API key for memory multi-tenant isolation.

        Returns:
            Complete query response dict.
        """
        if not self._query_executor:
            raise RuntimeError("SingleQueryRunner dependency not configured")

        session_id = request.session_id or str(uuid4())
        model = request.model or "sonnet"
        start_time = time.perf_counter()
        aggregator = SingleQueryAggregator()

        ctx = StreamContext(
            session_id=session_id,
            model=model,
            start_time=start_time,
            enable_file_checkpointing=request.enable_file_checkpointing,
            include_partial_messages=request.include_partial_messages,
        )

        try:
            async for event in self._query_executor.execute(
                request, ctx, commands_service, memory_service, api_key
            ):
                aggregator.handle_event(event)
        except Exception as exc:
            logger.error(
                "Single query execution failed",
                session_id=session_id,
                error=str(exc),
            )
            ctx.is_error = True
            aggregator.content_blocks.clear()
            aggregator.content_blocks.append(
                {"type": "text", "text": "Error: Internal error"}
            )

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        return aggregator.finalize(
            session_id=session_id,
            model=model,
            ctx=ctx,
            duration_ms=duration_ms,
        )
