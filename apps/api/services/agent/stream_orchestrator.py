"""<summary>Stream event orchestration helpers for AgentService.</summary>"""

from typing import TYPE_CHECKING, Literal

from apps.api.schemas.responses import (
    CommandInfoSchema,
    DoneEvent,
    DoneEventData,
    InitEvent,
    InitEventData,
    ResultEvent,
    ResultEventData,
    UsageSchema,
)

if TYPE_CHECKING:
    from apps.api.services.agent.handlers import MessageHandler
    from apps.api.services.agent.types import StreamContext


class StreamOrchestrator:
    """<summary>Builds init/result/done events for streaming responses.</summary>"""

    def __init__(self, message_handler: "MessageHandler") -> None:
        """<summary>Initialize orchestrator.</summary>"""
        self._message_handler = message_handler

    def build_init_event(
        self,
        session_id: str,
        model: str,
        tools: list[str],
        plugins: list[str],
        commands: list[CommandInfoSchema],
        permission_mode: str | None,
        mcp_servers: list[dict[str, object]] | None = None,
    ) -> dict[str, str]:
        """<summary>Build init event SSE payload.</summary>"""
        init_event = InitEvent(
            data=InitEventData(
                session_id=session_id,
                model=model,
                tools=tools,
                mcp_servers=mcp_servers or [],
                plugins=plugins,
                commands=commands,
                permission_mode=permission_mode,
            )
        )
        return self._message_handler.format_sse(
            init_event.event, init_event.data.model_dump()
        )

    def build_result_event(
        self,
        ctx: "StreamContext",
        duration_ms: int,
    ) -> dict[str, str]:
        """<summary>Build result event SSE payload.</summary>"""
        model_usage_converted: dict[str, UsageSchema] | None = None
        if ctx.model_usage:
            model_usage_converted = {}
            for model_name, usage_dict in ctx.model_usage.items():
                if isinstance(usage_dict, dict):
                    model_usage_converted[model_name] = UsageSchema(
                        input_tokens=usage_dict.get("input_tokens", 0),
                        output_tokens=usage_dict.get("output_tokens", 0),
                        cache_read_input_tokens=usage_dict.get(
                            "cache_read_input_tokens", 0
                        ),
                        cache_creation_input_tokens=usage_dict.get(
                            "cache_creation_input_tokens", 0
                        ),
                    )

        result_event = ResultEvent(
            data=ResultEventData(
                session_id=ctx.session_id,
                is_error=ctx.is_error,
                duration_ms=duration_ms,
                num_turns=ctx.num_turns,
                total_cost_usd=ctx.total_cost_usd,
                model_usage=model_usage_converted,
                result=ctx.result_text,
                structured_output=ctx.structured_output,
            )
        )
        return self._message_handler.format_sse(
            result_event.event, result_event.data.model_dump()
        )

    def build_done_event(
        self,
        reason: Literal["completed", "interrupted", "error"],
    ) -> dict[str, str]:
        """<summary>Build done event SSE payload.</summary>"""
        done_event = DoneEvent(data=DoneEventData(reason=reason))
        return self._message_handler.format_sse(
            done_event.event, done_event.data.model_dump()
        )
