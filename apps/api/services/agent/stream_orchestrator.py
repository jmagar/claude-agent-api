"""Stream event orchestration helpers for AgentService."""

from typing import TYPE_CHECKING, Literal, cast

from apps.api.schemas.responses import (
    CommandInfoSchema,
    DoneEvent,
    DoneEventData,
    ErrorEvent,
    ErrorEventData,
    InitEvent,
    InitEventData,
    McpServerStatusSchema,
    ResultEvent,
    ResultEventData,
    UsageSchema,
)

if TYPE_CHECKING:
    from apps.api.services.agent.handlers import MessageHandler
    from apps.api.services.agent.types import StreamContext


class StreamOrchestrator:
    """Builds init/result/done events for streaming responses."""

    def __init__(self, message_handler: "MessageHandler") -> None:
        """Initialize orchestrator.

        Args:
            message_handler: Handler for formatting SSE messages.
        """
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
        """Build init event SSE payload.

        Args:
            session_id: The session identifier.
            model: The model name.
            tools: List of available tool names.
            plugins: List of enabled plugin names.
            commands: List of available command schemas.
            permission_mode: Permission mode setting, if any.
            mcp_servers: Optional list of MCP server configurations.

        Returns:
            SSE-formatted dict with event type and JSON data.
        """
        init_event = InitEvent(
            data=InitEventData(
                session_id=session_id,
                model=model,
                tools=tools,
                mcp_servers=cast("list[McpServerStatusSchema]", mcp_servers or []),
                plugins=plugins,
                commands=commands,
                permission_mode=cast(
                    "Literal['default', 'acceptEdits', 'plan', 'bypassPermissions']",
                    permission_mode,
                ),
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
        """Build result event SSE payload.

        Args:
            ctx: Stream context containing session metadata and usage stats.
            duration_ms: Total duration in milliseconds.

        Returns:
            SSE-formatted dict with event type and JSON data.
        """
        # Convert per-model usage and aggregate total usage
        model_usage_converted: dict[str, UsageSchema] | None = None
        aggregated_usage: UsageSchema | None = None

        # First, check if ctx.usage has aggregated usage from SDK ResultMessage
        if ctx.usage:
            aggregated_usage = UsageSchema(
                input_tokens=ctx.usage.get("input_tokens", 0),
                output_tokens=ctx.usage.get("output_tokens", 0),
                cache_read_input_tokens=ctx.usage.get("cache_read_input_tokens", 0),
                cache_creation_input_tokens=ctx.usage.get(
                    "cache_creation_input_tokens", 0
                ),
            )

        # Also process model_usage for per-model breakdown
        if ctx.model_usage:
            model_usage_converted = {}
            total_input = 0
            total_output = 0
            total_cache_read = 0
            total_cache_creation = 0

            for model_name, usage_dict in ctx.model_usage.items():
                if isinstance(usage_dict, dict):
                    input_tokens = usage_dict.get("input_tokens", 0)
                    output_tokens = usage_dict.get("output_tokens", 0)
                    cache_read = usage_dict.get("cache_read_input_tokens", 0)
                    cache_creation = usage_dict.get("cache_creation_input_tokens", 0)

                    model_usage_converted[model_name] = UsageSchema(
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cache_read_input_tokens=cache_read,
                        cache_creation_input_tokens=cache_creation,
                    )

                    total_input += input_tokens
                    total_output += output_tokens
                    total_cache_read += cache_read
                    total_cache_creation += cache_creation

            # Fallback: aggregate from model_usage if ctx.usage wasn't set
            if aggregated_usage is None:
                aggregated_usage = UsageSchema(
                    input_tokens=total_input,
                    output_tokens=total_output,
                    cache_read_input_tokens=total_cache_read,
                    cache_creation_input_tokens=total_cache_creation,
                )

        result_event = ResultEvent(
            data=ResultEventData(
                session_id=ctx.session_id,
                is_error=ctx.is_error,
                duration_ms=duration_ms,
                num_turns=ctx.num_turns,
                total_cost_usd=ctx.total_cost_usd,
                usage=aggregated_usage,
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
        """Build done event SSE payload.

        Args:
            reason: Completion reason (completed, interrupted, or error).

        Returns:
            SSE-formatted dict with event type and JSON data.
        """
        done_event = DoneEvent(data=DoneEventData(reason=reason))
        return self._message_handler.format_sse(
            done_event.event, done_event.data.model_dump()
        )

    def build_error_event(self, code: str, message: str) -> dict[str, str]:
        """Build error event SSE payload.

        Args:
            code: Error code identifier.
            message: Error message to surface.

        Returns:
            SSE-formatted dict with event type and JSON data.
        """
        error_event = ErrorEvent(data=ErrorEventData(code=code, message=message))
        return self._message_handler.format_sse(
            error_event.event, error_event.data.model_dump()
        )
