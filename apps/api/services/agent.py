"""Agent service wrapping Claude Agent SDK."""

import asyncio
import json
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import structlog

from apps.api.config import get_settings
from apps.api.exceptions import AgentError
from apps.api.schemas.messages import (
    map_sdk_content_block,
    map_sdk_usage,
)
from apps.api.schemas.requests import QueryRequest
from apps.api.schemas.responses import (
    ContentBlockSchema,
    DoneEvent,
    DoneEventData,
    ErrorEvent,
    ErrorEventData,
    InitEvent,
    InitEventData,
    MessageEvent,
    MessageEventData,
    QuestionEvent,
    QuestionEventData,
    ResultEvent,
    ResultEventData,
    UsageSchema,
)

logger = structlog.get_logger(__name__)


@dataclass
class StreamContext:
    """Context for a streaming query."""

    session_id: str
    model: str
    start_time: float
    num_turns: int = 0
    total_cost_usd: float | None = None
    is_error: bool = False
    result_text: str | None = None
    structured_output: dict[str, Any] | None = None


class AgentService:
    """Service for interacting with Claude Agent SDK."""

    def __init__(self) -> None:
        """Initialize agent service."""
        self._settings = get_settings()
        self._active_sessions: dict[str, asyncio.Event] = {}

    async def query_stream(
        self,
        request: QueryRequest,
    ) -> AsyncGenerator[str, None]:
        """Stream a query to the agent.

        Args:
            request: Query request.

        Yields:
            SSE formatted events.
        """
        session_id = request.session_id or str(uuid4())
        model = request.model or "sonnet"
        ctx = StreamContext(
            session_id=session_id,
            model=model,
            start_time=time.perf_counter(),
        )

        # Create interrupt event for this session
        self._active_sessions[session_id] = asyncio.Event()

        try:
            # Emit init event
            init_event = InitEvent(
                data=InitEventData(
                    session_id=session_id,
                    model=model,
                    tools=request.allowed_tools or [],
                    mcp_servers=[],
                    plugins=[],
                    commands=[],
                )
            )
            yield self._format_sse(init_event.event, init_event.data.model_dump())

            # Execute query using SDK
            async for event in self._execute_query(request, ctx):
                yield event

                # Check for interrupt
                if self._active_sessions.get(session_id, asyncio.Event()).is_set():
                    ctx.is_error = False
                    break

            # Emit result event
            duration_ms = int((time.perf_counter() - ctx.start_time) * 1000)
            result_event = ResultEvent(
                data=ResultEventData(
                    session_id=session_id,
                    is_error=ctx.is_error,
                    duration_ms=duration_ms,
                    num_turns=ctx.num_turns,
                    total_cost_usd=ctx.total_cost_usd,
                    result=ctx.result_text,
                    structured_output=ctx.structured_output,
                )
            )
            yield self._format_sse(result_event.event, result_event.data.model_dump())

            # Emit done event
            reason = "interrupted" if self._active_sessions.get(
                session_id, asyncio.Event()
            ).is_set() else ("error" if ctx.is_error else "completed")
            done_event = DoneEvent(data=DoneEventData(reason=reason))  # type: ignore
            yield self._format_sse(done_event.event, done_event.data.model_dump())

        except Exception as e:
            logger.exception("Query stream error", session_id=session_id, error=str(e))
            # Emit error event
            error_event = ErrorEvent(
                data=ErrorEventData(
                    code="AGENT_ERROR",
                    message=str(e),
                )
            )
            yield self._format_sse(error_event.event, error_event.data.model_dump())

            # Emit done with error
            done_event = DoneEvent(data=DoneEventData(reason="error"))
            yield self._format_sse(done_event.event, done_event.data.model_dump())

        finally:
            # Cleanup
            self._active_sessions.pop(session_id, None)

    async def _execute_query(
        self,
        request: QueryRequest,
        ctx: StreamContext,
    ) -> AsyncGenerator[str, None]:
        """Execute query using Claude Agent SDK.

        Args:
            request: Query request.
            ctx: Stream context.

        Yields:
            SSE formatted message events.
        """
        try:
            # Import SDK here to avoid import errors if not installed
            from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

            # Build options
            options = self._build_options(request)

            # Create client and execute query
            async with ClaudeSDKClient(options) as client:
                await client.query(request.prompt, session_id=ctx.session_id)

                async for message in client.receive_messages():
                    # Update context
                    ctx.num_turns += 1

                    # Map SDK message to API event
                    event_str = self._map_sdk_message(message, ctx)
                    if event_str:
                        yield event_str

        except ImportError:
            # SDK not installed - emit mock response for development
            logger.warning("Claude Agent SDK not installed, using mock response")
            async for event in self._mock_response(request, ctx):
                yield event

        except Exception as e:
            logger.error("SDK execution error", error=str(e))
            ctx.is_error = True
            raise AgentError(f"Agent execution failed: {e}", original_error=str(e)) from e

    def _build_options(self, request: QueryRequest) -> Any:
        """Build SDK options from request.

        Args:
            request: Query request.

        Returns:
            ClaudeAgentOptions instance.
        """
        from claude_agent_sdk import ClaudeAgentOptions

        options_dict: dict[str, Any] = {}

        if request.allowed_tools:
            options_dict["allowed_tools"] = request.allowed_tools
        if request.disallowed_tools:
            options_dict["disallowed_tools"] = request.disallowed_tools
        if request.permission_mode:
            options_dict["permission_mode"] = request.permission_mode
        if request.model:
            options_dict["model"] = request.model
        if request.max_turns:
            options_dict["max_turns"] = request.max_turns
        if request.cwd:
            options_dict["cwd"] = request.cwd
        if request.env:
            options_dict["env"] = request.env
        if request.system_prompt:
            options_dict["system_prompt"] = request.system_prompt
        if request.enable_file_checkpointing:
            options_dict["enable_file_checkpointing"] = True

        # Session resume
        if request.session_id and not request.fork_session:
            options_dict["resume"] = request.session_id
        elif request.session_id and request.fork_session:
            options_dict["resume"] = request.session_id
            options_dict["fork_session"] = True

        # MCP servers
        if request.mcp_servers:
            from claude_agent_sdk import McpServerConfig

            mcp_configs = {}
            for name, config in request.mcp_servers.items():
                mcp_configs[name] = McpServerConfig(
                    command=config.command,
                    args=config.args,
                    type=config.type,
                    url=config.url,
                    headers=config.headers,
                    env=config.env,
                )
            options_dict["mcp_servers"] = mcp_configs

        # Subagents
        if request.agents:
            from claude_agent_sdk import AgentDefinition

            agent_defs = {}
            for name, agent in request.agents.items():
                agent_defs[name] = AgentDefinition(
                    description=agent.description,
                    prompt=agent.prompt,
                    tools=agent.tools,
                    model=agent.model,
                )
            options_dict["agents"] = agent_defs

        # Output format
        if request.output_format:
            from claude_agent_sdk import OutputFormat

            options_dict["output_format"] = OutputFormat(
                type=request.output_format.type,
                schema=request.output_format.schema_,
            )

        return ClaudeAgentOptions(**options_dict)

    def _map_sdk_message(self, message: Any, ctx: StreamContext) -> str | None:
        """Map SDK message to SSE event string.

        Args:
            message: SDK message.
            ctx: Stream context.

        Returns:
            SSE formatted string or None.
        """
        msg_type = type(message).__name__

        if msg_type == "SystemMessage":
            # Handle system messages (init, etc.)
            return None

        elif msg_type == "UserMessage":
            content_blocks = self._extract_content_blocks(message)
            event = MessageEvent(
                data=MessageEventData(
                    type="user",
                    content=content_blocks,
                    uuid=getattr(message, "uuid", None),
                )
            )
            return self._format_sse(event.event, event.data.model_dump())

        elif msg_type == "AssistantMessage":
            content_blocks = self._extract_content_blocks(message)
            usage = self._extract_usage(message)

            # Check for AskUserQuestion
            for block in content_blocks:
                if block.type == "tool_use" and block.name == "AskUserQuestion":
                    question = block.input.get("question", "") if block.input else ""
                    q_event = QuestionEvent(
                        data=QuestionEventData(
                            tool_use_id=block.id or "",
                            question=question,
                            session_id=ctx.session_id,
                        )
                    )
                    return self._format_sse(q_event.event, q_event.data.model_dump())

            event = MessageEvent(
                data=MessageEventData(
                    type="assistant",
                    content=content_blocks,
                    model=getattr(message, "model", ctx.model),
                    usage=usage,
                )
            )
            return self._format_sse(event.event, event.data.model_dump())

        elif msg_type == "ResultMessage":
            # Update context from result
            ctx.is_error = getattr(message, "is_error", False)
            ctx.num_turns = getattr(message, "num_turns", ctx.num_turns)
            ctx.total_cost_usd = getattr(message, "total_cost_usd", None)
            ctx.result_text = getattr(message, "result", None)
            return None

        return None

    def _extract_content_blocks(self, message: Any) -> list[ContentBlockSchema]:
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
                blocks.append(ContentBlockSchema(**mapped))
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
                blocks.append(ContentBlockSchema(**block_dict))

        return blocks

    def _extract_usage(self, message: Any) -> UsageSchema | None:
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

    async def _mock_response(
        self,
        request: QueryRequest,
        ctx: StreamContext,
    ) -> AsyncGenerator[str, None]:
        """Generate mock response for development without SDK.

        Args:
            request: Query request.
            ctx: Stream context.

        Yields:
            SSE formatted events.
        """
        # Simulate thinking delay
        await asyncio.sleep(0.1)

        # Emit assistant message
        ctx.num_turns = 1
        event = MessageEvent(
            data=MessageEventData(
                type="assistant",
                content=[
                    ContentBlockSchema(
                        type="text",
                        text=f"[Mock Response] Received prompt: {request.prompt[:100]}...",
                    )
                ],
                model=ctx.model,
                usage=UsageSchema(
                    input_tokens=100,
                    output_tokens=50,
                ),
            )
        )
        yield self._format_sse(event.event, event.data.model_dump())

        ctx.result_text = "Mock response completed"
        ctx.total_cost_usd = 0.001

    def _format_sse(self, event_type: str, data: dict[str, Any]) -> str:
        """Format data as SSE event.

        Args:
            event_type: Event type name.
            data: Event data.

        Returns:
            SSE formatted string.
        """
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    async def interrupt(self, session_id: str) -> bool:
        """Interrupt a running query.

        Args:
            session_id: Session to interrupt.

        Returns:
            True if session was interrupted.
        """
        if session_id in self._active_sessions:
            self._active_sessions[session_id].set()
            return True
        return False

    async def query_single(self, request: QueryRequest) -> dict[str, Any]:
        """Execute non-streaming query.

        Args:
            request: Query request.

        Returns:
            Complete response dictionary.
        """
        session_id = request.session_id or str(uuid4())
        model = request.model or "sonnet"
        start_time = time.perf_counter()

        content_blocks: list[dict[str, Any]] = []
        is_error = False
        num_turns = 0
        total_cost_usd: float | None = None
        result_text: str | None = None
        usage_data: dict[str, int] | None = None

        # Collect all events from stream
        ctx = StreamContext(
            session_id=session_id,
            model=model,
            start_time=start_time,
        )

        try:
            async for _event in self._execute_query(request, ctx):
                # Parse event to extract content
                pass

            is_error = ctx.is_error
            num_turns = ctx.num_turns
            total_cost_usd = ctx.total_cost_usd
            result_text = ctx.result_text

        except Exception as e:
            is_error = True
            content_blocks = [{"type": "text", "text": f"Error: {e}"}]

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "session_id": session_id,
            "model": model,
            "content": content_blocks,
            "is_error": is_error,
            "duration_ms": duration_ms,
            "num_turns": num_turns,
            "total_cost_usd": total_cost_usd,
            "usage": usage_data,
            "result": result_text,
        }
