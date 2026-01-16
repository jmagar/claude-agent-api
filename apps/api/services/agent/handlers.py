"""Message handlers for Agent SDK responses."""

import json
from typing import TYPE_CHECKING, Literal, cast

import structlog

from apps.api.schemas.messages import map_sdk_content_block, map_sdk_usage
from apps.api.schemas.responses import (
    ContentBlockSchema,
    ContentDeltaSchema,
    MessageEvent,
    MessageEventData,
    PartialMessageEvent,
    PartialMessageEventData,
    QuestionEvent,
    QuestionEventData,
    UsageSchema,
)

if TYPE_CHECKING:
    from apps.api.services.agent.types import StreamContext

logger = structlog.get_logger(__name__)


class MessageHandler:
    """Handler for SDK message processing and SSE formatting.

    This class is responsible for:
    - Mapping Claude Agent SDK messages to API SSE events
    - Extracting content blocks and usage information
    - Tracking file modifications for checkpointing
    - Handling special tool uses (AskUserQuestion, TodoWrite)
    - Formatting partial/streaming messages
    """

    def map_sdk_message(
        self, message: object, ctx: "StreamContext"
    ) -> dict[str, str] | None:
        """Map SDK message to SSE event dict.

        Args:
            message: SDK message.
            ctx: Stream context.

        Returns:
            SSE event dict with 'event' and 'data' keys, or None.
        """
        msg_type = type(message).__name__

        if msg_type == "SystemMessage":
            return None

        if msg_type == "UserMessage":
            return self._handle_user_message(message, ctx)

        if msg_type == "AssistantMessage":
            return self._handle_assistant_message(message, ctx)

        if msg_type == "ResultMessage":
            self._handle_result_message(message, ctx)
            return None

        # T118: Handle partial/streaming messages when include_partial_messages is enabled
        if msg_type == "StreamEvent" and ctx.include_partial_messages:
            # StreamEvent.event is a dict[str, object] containing raw Anthropic API stream event
            event_data = getattr(message, "event", None)
            if event_data and isinstance(event_data, dict):
                event_type = event_data.get("type")
                if event_type == "content_block_start":
                    return self._handle_partial_start(event_data, ctx)
                elif event_type == "content_block_delta":
                    return self._handle_partial_delta(event_data, ctx)
                elif event_type == "content_block_stop":
                    return self._handle_partial_stop(event_data, ctx)
            # Ignore StreamEvents without partial content data or other event types
            return None

        if msg_type == "ContentBlockStart" and ctx.include_partial_messages:
            return self._handle_partial_start(message, ctx)

        if msg_type == "ContentBlockDelta" and ctx.include_partial_messages:
            return self._handle_partial_delta(message, ctx)

        if msg_type == "ContentBlockStop" and ctx.include_partial_messages:
            return self._handle_partial_stop(message, ctx)

        return None

    def _handle_user_message(
        self, message: object, ctx: "StreamContext"
    ) -> dict[str, str]:
        """Handle UserMessage from SDK.

        Args:
            message: SDK UserMessage.
            ctx: Stream context.

        Returns:
            SSE event dict with 'event' and 'data' keys.
        """
        content_blocks = self._extract_content_blocks(message)

        # Track user message UUID for checkpointing (T104)
        user_uuid = getattr(message, "uuid", None)
        if ctx.enable_file_checkpointing and user_uuid:
            ctx.last_user_message_uuid = user_uuid

        event = MessageEvent(
            data=MessageEventData(
                type="user",
                content=content_blocks,
                uuid=user_uuid,
            )
        )
        return self.format_sse(event.event, event.data.model_dump())

    def _handle_assistant_message(
        self, message: object, ctx: "StreamContext"
    ) -> dict[str, str]:
        """Handle AssistantMessage from SDK.

        Args:
            message: SDK AssistantMessage.
            ctx: Stream context.

        Returns:
            SSE event dict with 'event' and 'data' keys.
        """
        content_blocks = self._extract_content_blocks(message)
        usage = self._extract_usage(message)

        # Track file modifications from Write/Edit tools for checkpointing (T104)
        if ctx.enable_file_checkpointing:
            self.track_file_modifications(content_blocks, ctx)

        # Check for special tool uses (AskUserQuestion, TodoWrite)
        special_event = self._check_special_tool_uses(content_blocks, ctx)
        if special_event:
            return special_event

        event = MessageEvent(
            data=MessageEventData(
                type="assistant",
                content=content_blocks,
                model=getattr(message, "model", ctx.model),
                usage=usage,
            )
        )
        return self.format_sse(event.event, event.data.model_dump())

    def _check_special_tool_uses(
        self, content_blocks: list[ContentBlockSchema], ctx: "StreamContext"
    ) -> dict[str, str] | None:
        """Check for special tool uses and return event if found.

        Args:
            content_blocks: Content blocks from message.
            ctx: Stream context.

        Returns:
            SSE event dict for special tool, or None.
        """
        for block in content_blocks:
            if block.type == "tool_use" and block.name == "AskUserQuestion":
                question = str(block.input.get("question", "")) if block.input else ""
                q_event = QuestionEvent(
                    data=QuestionEventData(
                        tool_use_id=block.id or "",
                        question=question,
                        session_id=ctx.session_id,
                    )
                )
                return self.format_sse(q_event.event, q_event.data.model_dump())

            # T116e: Log TodoWrite tool use for tracking
            if block.type == "tool_use" and block.name == "TodoWrite":
                todos_data = block.input.get("todos", []) if block.input else []
                if isinstance(todos_data, list):
                    logger.info(
                        "TodoWrite tool use detected",
                        session_id=ctx.session_id,
                        todos_count=len(todos_data),
                    )
        return None

    def _handle_result_message(self, message: object, ctx: "StreamContext") -> None:
        """Handle ResultMessage from SDK.

        Updates context with result data. Does not emit an event.

        Args:
            message: SDK ResultMessage.
            ctx: Stream context to update.
        """
        from typing import cast

        ctx.is_error = getattr(message, "is_error", False)
        ctx.num_turns = getattr(message, "num_turns", ctx.num_turns)
        ctx.total_cost_usd = getattr(message, "total_cost_usd", None)
        ctx.result_text = getattr(message, "result", None)

        # Extract model_usage if available (T110: Model Selection)
        raw_model_usage = getattr(message, "model_usage", None)
        if raw_model_usage is not None:
            if isinstance(raw_model_usage, dict):
                ctx.model_usage = cast("dict[str, dict[str, int]]", raw_model_usage)
            else:
                logger.warning(
                    "model_usage is not a dict",
                    session_id=ctx.session_id,
                    type=type(raw_model_usage).__name__,
                )

        # Extract structured output if available (US8: Structured Output)
        raw_structured = getattr(message, "structured_output", None)
        if raw_structured is not None:
            if isinstance(raw_structured, dict):
                ctx.structured_output = cast("dict[str, object]", raw_structured)
            else:
                logger.warning(
                    "structured_output is not a dict",
                    session_id=ctx.session_id,
                    type=type(raw_structured).__name__,
                )
                ctx.is_error = True

    def _handle_partial_start(
        self, message: object, _ctx: "StreamContext"
    ) -> dict[str, str]:
        """Handle ContentBlockStart for partial message streaming.

        Args:
            message: SDK ContentBlockStart message or dict from StreamEvent.
            _ctx: Stream context (unused, kept for API consistency).

        Returns:
            SSE event dict with 'event' and 'data' keys.
        """
        # Handle both dict (from StreamEvent) and object forms
        if isinstance(message, dict):
            message_dict = cast("dict[str, object]", message)
            index_value = message_dict.get("index", 0)
            index = index_value if isinstance(index_value, int) else 0
            content_block = message_dict.get("content_block")
        else:
            index = getattr(message, "index", 0)
            content_block = getattr(message, "content_block", None)

        block_schema: ContentBlockSchema | None = None
        if content_block:
            if isinstance(content_block, dict):
                content_block_dict = cast("dict[str, object]", content_block)
                block_type_value = content_block_dict.get("type")
                if isinstance(block_type_value, str) and block_type_value in (
                    "text",
                    "thinking",
                    "tool_use",
                    "tool_result",
                ):
                    block_type = cast(
                        "Literal['text', 'thinking', 'tool_use', 'tool_result']",
                        block_type_value,
                    )
                else:
                    block_type = "text"
                text_value = content_block_dict.get("text")
                text = text_value if isinstance(text_value, str) else None
                id_value = content_block_dict.get("id")
                block_id = id_value if isinstance(id_value, str) else None
                name_value = content_block_dict.get("name")
                name = name_value if isinstance(name_value, str) else None
                block_schema = ContentBlockSchema(
                    type=block_type,
                    text=text,
                    id=block_id,
                    name=name,
                )
            else:
                block_schema = ContentBlockSchema(
                    type=getattr(content_block, "type", "text"),
                    text=getattr(content_block, "text", None),
                    id=getattr(content_block, "id", None),
                    name=getattr(content_block, "name", None),
                )

        partial_start_event = PartialMessageEvent(
            data=PartialMessageEventData(
                type="content_block_start",
                index=index,
                content_block=block_schema,
            )
        )
        return self.format_sse(
            partial_start_event.event, partial_start_event.data.model_dump()
        )

    def _handle_partial_delta(
        self, message: object, _ctx: "StreamContext"
    ) -> dict[str, str]:
        """Handle ContentBlockDelta for partial message streaming.

        Args:
            message: SDK ContentBlockDelta message or dict from StreamEvent.
            _ctx: Stream context (unused, kept for API consistency).

        Returns:
            SSE event dict with 'event' and 'data' keys.
        """
        # Handle both dict (from StreamEvent) and object forms
        if isinstance(message, dict):
            message_dict = cast("dict[str, object]", message)
            index_value = message_dict.get("index", 0)
            index = index_value if isinstance(index_value, int) else 0
            delta = message_dict.get("delta")
        else:
            index = getattr(message, "index", 0)
            delta = getattr(message, "delta", None)

        delta_schema: ContentDeltaSchema | None = None
        if delta:
            if isinstance(delta, dict):
                delta_dict = cast("dict[str, object]", delta)
                delta_type_value = delta_dict.get("type")
                if isinstance(delta_type_value, str) and delta_type_value in (
                    "text_delta",
                    "thinking_delta",
                    "input_json_delta",
                ):
                    delta_type = cast(
                        "Literal['text_delta', 'thinking_delta', 'input_json_delta']",
                        delta_type_value,
                    )
                else:
                    delta_type = "text_delta"
                text_value = delta_dict.get("text")
                text = text_value if isinstance(text_value, str) else None
                thinking_value = delta_dict.get("thinking")
                thinking = thinking_value if isinstance(thinking_value, str) else None
                partial_json_value = delta_dict.get("partial_json")
                partial_json = (
                    partial_json_value if isinstance(partial_json_value, str) else None
                )
                delta_schema = ContentDeltaSchema(
                    type=delta_type,
                    text=text if delta_type == "text_delta" else None,
                    thinking=(
                        thinking if delta_type == "thinking_delta" else None
                    ),
                    partial_json=(
                        partial_json if delta_type == "input_json_delta" else None
                    ),
                )
            else:
                delta_type_value = getattr(delta, "type", "text_delta")
                delta_type = (
                    delta_type_value
                    if delta_type_value
                    in ("text_delta", "thinking_delta", "input_json_delta")
                    else "text_delta"
                )
                delta_schema = ContentDeltaSchema(
                    type=delta_type,
                    text=(
                        getattr(delta, "text", None)
                        if delta_type == "text_delta"
                        else None
                    ),
                    thinking=(
                        getattr(delta, "thinking", None)
                        if delta_type == "thinking_delta"
                        else None
                    ),
                    partial_json=(
                        getattr(delta, "partial_json", None)
                        if delta_type == "input_json_delta"
                        else None
                    ),
                )

        partial_delta_event = PartialMessageEvent(
            data=PartialMessageEventData(
                type="content_block_delta",
                index=index,
                delta=delta_schema,
            )
        )
        return self.format_sse(
            partial_delta_event.event, partial_delta_event.data.model_dump()
        )

    def _handle_partial_stop(
        self, message: object, _ctx: "StreamContext"
    ) -> dict[str, str]:
        """Handle ContentBlockStop for partial message streaming.

        Args:
            message: SDK ContentBlockStop message or dict from StreamEvent.
            _ctx: Stream context (unused, kept for API consistency).

        Returns:
            SSE event dict with 'event' and 'data' keys.
        """
        # Handle both dict (from StreamEvent) and object forms
        if isinstance(message, dict):
            message_dict = cast("dict[str, object]", message)
            index_value = message_dict.get("index", 0)
            index = index_value if isinstance(index_value, int) else 0
        else:
            index = getattr(message, "index", 0)

        partial_stop_event = PartialMessageEvent(
            data=PartialMessageEventData(
                type="content_block_stop",
                index=index,
            )
        )
        return self.format_sse(
            partial_stop_event.event, partial_stop_event.data.model_dump()
        )

    def track_file_modifications(
        self, content_blocks: list[ContentBlockSchema], ctx: "StreamContext"
    ) -> None:
        """Track file modifications from tool_use blocks (T104).

        Extracts file paths from Write and Edit tool invocations
        and adds them to the context's files_modified list.

        Args:
            content_blocks: List of content blocks from assistant message.
            ctx: Stream context to update.
        """
        for block in content_blocks:
            if block.type != "tool_use":
                continue

            if (
                block.name in ("Write", "Edit")
                and block.input
                and isinstance(block.input, dict)
            ):
                file_path = block.input.get("file_path")
                if (
                    file_path
                    and isinstance(file_path, str)
                    and file_path not in ctx.files_modified
                ):
                    ctx.files_modified.append(file_path)
                    logger.debug(
                        "Tracked file modification",
                        file_path=file_path,
                        tool=block.name,
                        session_id=ctx.session_id,
                    )

    def _extract_content_blocks(self, message: object) -> list[ContentBlockSchema]:
        """Extract content blocks from SDK message.

        Args:
            message: SDK message.

        Returns:
            List of content block schemas.
        """
        content = getattr(message, "content", [])
        if isinstance(content, str):
            return [ContentBlockSchema(type="text", text=content)]

        blocks = []
        for block in content:
            if isinstance(block, dict):
                mapped = map_sdk_content_block(block)
                blocks.append(ContentBlockSchema(**cast("dict[str, object]", mapped)))
            else:
                # Dataclass block
                block_dict = {
                    "type": getattr(block, "type", "text"),
                }
                if hasattr(block, "text"):
                    block_dict["text"] = block.text
                if hasattr(block, "thinking"):
                    block_dict["thinking"] = block.thinking
                if hasattr(block, "id"):
                    block_dict["id"] = block.id
                if hasattr(block, "name"):
                    block_dict["name"] = block.name
                if hasattr(block, "input"):
                    block_dict["input"] = block.input
                if hasattr(block, "tool_use_id"):
                    block_dict["tool_use_id"] = block.tool_use_id
                if hasattr(block, "content"):
                    block_dict["content"] = block.content
                if hasattr(block, "is_error"):
                    block_dict["is_error"] = block.is_error
                blocks.append(
                    ContentBlockSchema(**cast("dict[str, object]", block_dict))
                )

        return blocks

    def _extract_usage(self, message: object) -> UsageSchema | None:
        """Extract usage data from SDK message.

        Args:
            message: SDK message.

        Returns:
            Usage schema or None.
        """
        usage = getattr(message, "usage", None)
        if usage is None:
            return None

        if isinstance(usage, dict):
            mapped = map_sdk_usage(usage)
            if mapped:
                return UsageSchema(**mapped)
        else:
            return UsageSchema(
                input_tokens=getattr(usage, "input_tokens", 0),
                output_tokens=getattr(usage, "output_tokens", 0),
                cache_read_input_tokens=getattr(usage, "cache_read_input_tokens", 0),
                cache_creation_input_tokens=getattr(
                    usage, "cache_creation_input_tokens", 0
                ),
            )
        return None

    def format_sse(self, event_type: str, data: dict[str, object]) -> dict[str, str]:
        """Format data as SSE event dict for EventSourceResponse.

        Args:
            event_type: Event type name.
            data: Event data.

        Returns:
            Dict with event and data keys for SSE.
        """
        return {"event": event_type, "data": json.dumps(data)}
