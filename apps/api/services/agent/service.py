"""Agent service wrapping Claude Agent SDK."""

import asyncio
import json
import time
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

import structlog

from apps.api.config import get_settings
from apps.api.exceptions import AgentError
from apps.api.schemas.responses import (
    CommandInfoSchema,
    DoneEvent,
    DoneEventData,
    ErrorEvent,
    ErrorEventData,
    InitEvent,
    InitEventData,
    ResultEvent,
    ResultEventData,
    UsageSchema,
)
from apps.api.services.agent.handlers import MessageHandler
from apps.api.services.agent.hooks import HookExecutor
from apps.api.services.agent.options import OptionsBuilder
from apps.api.services.agent.types import QueryResponseDict, StreamContext
from apps.api.services.webhook import WebhookService

if TYPE_CHECKING:
    from apps.api.schemas.requests.config import HooksConfigSchema
    from apps.api.schemas.requests.query import QueryRequest
    from apps.api.services.checkpoint import Checkpoint, CheckpointService

logger = structlog.get_logger(__name__)


class AgentService:
    """Service for interacting with Claude Agent SDK."""

    def __init__(
        self,
        webhook_service: WebhookService | None = None,
        checkpoint_service: "CheckpointService | None" = None,
    ) -> None:
        """Initialize agent service.

        Args:
            webhook_service: Optional WebhookService for hook callbacks.
                           If not provided, a default instance is created.
            checkpoint_service: Optional CheckpointService for file checkpointing.
                              Required for enable_file_checkpointing functionality.
        """
        self._settings = get_settings()
        self._active_sessions: dict[str, asyncio.Event] = {}
        self._webhook_service = webhook_service or WebhookService()
        self._checkpoint_service = checkpoint_service
        self._message_handler = MessageHandler()
        self._hook_executor = HookExecutor(self._webhook_service)

    @property
    def checkpoint_service(self) -> "CheckpointService | None":
        """Get the checkpoint service instance.

        Returns:
            CheckpointService instance or None if not configured.
        """
        return self._checkpoint_service

    async def query_stream(
        self, request: "QueryRequest"
    ) -> AsyncGenerator[dict[str, str], None]:
        """Stream a query to the agent.

        Args:
            request: Query request.

        Yields:
            SSE event dicts with 'event' and 'data' keys.
        """
        session_id = request.session_id or str(uuid4())
        model = request.model or "sonnet"
        ctx = StreamContext(
            session_id=session_id,
            model=model,
            start_time=time.perf_counter(),
            enable_file_checkpointing=request.enable_file_checkpointing,
            include_partial_messages=request.include_partial_messages,
        )

        # Create interrupt event for this session
        self._active_sessions[session_id] = asyncio.Event()

        try:
            # Extract plugin names for InitEvent (T115)
            plugin_names: list[str] = []
            if request.plugins:
                plugin_names = [p.name for p in request.plugins if p.enabled]

            # Discover slash commands from project directory (T115)
            from pathlib import Path

            from apps.api.services.commands import CommandsService

            project_path = Path(request.cwd) if request.cwd else Path.cwd()
            commands_service = CommandsService(project_path=project_path)
            discovered_commands = commands_service.discover_commands()

            # Convert to schema objects
            command_schemas: list[CommandInfoSchema] = [
                CommandInfoSchema(name=cmd["name"], path=cmd["path"])
                for cmd in discovered_commands
            ]

            # Emit init event
            init_event = InitEvent(
                data=InitEventData(
                    session_id=session_id,
                    model=model,
                    tools=request.allowed_tools or [],
                    mcp_servers=[],
                    plugins=plugin_names,
                    commands=command_schemas,
                    permission_mode=request.permission_mode,
                )
            )
            yield self._message_handler.format_sse(
                init_event.event, init_event.data.model_dump()
            )

            # Execute query using SDK
            async for event in self._execute_query(request, ctx):
                yield event

                # Check for interrupt
                interrupt_event = self._active_sessions.get(session_id)
                if interrupt_event and interrupt_event.is_set():
                    ctx.is_error = False
                    break

            # Emit result event
            duration_ms = int((time.perf_counter() - ctx.start_time) * 1000)

            # Convert model_usage to UsageSchema format (T110)
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
                    session_id=session_id,
                    is_error=ctx.is_error,
                    duration_ms=duration_ms,
                    num_turns=ctx.num_turns,
                    total_cost_usd=ctx.total_cost_usd,
                    model_usage=model_usage_converted,
                    result=ctx.result_text,
                    structured_output=ctx.structured_output,
                )
            )
            yield self._message_handler.format_sse(
                result_event.event, result_event.data.model_dump()
            )

            # Emit done event
            reason: Literal["completed", "interrupted", "error"]
            interrupt_event = self._active_sessions.get(session_id)
            if interrupt_event and interrupt_event.is_set():
                reason = "interrupted"
            elif ctx.is_error:
                reason = "error"
            else:
                reason = "completed"
            done_event = DoneEvent(data=DoneEventData(reason=reason))
            yield self._message_handler.format_sse(
                done_event.event, done_event.data.model_dump()
            )

        except Exception as e:
            logger.exception("Query stream error", session_id=session_id, error=str(e))
            # Emit error event
            error_event = ErrorEvent(
                data=ErrorEventData(
                    code="AGENT_ERROR",
                    message=str(e),
                )
            )
            yield self._message_handler.format_sse(
                error_event.event, error_event.data.model_dump()
            )

            # Emit done with error
            done_event = DoneEvent(data=DoneEventData(reason="error"))
            yield self._message_handler.format_sse(
                done_event.event, done_event.data.model_dump()
            )

        finally:
            # Cleanup
            self._active_sessions.pop(session_id, None)

    async def _execute_query(
        self,
        request: "QueryRequest",
        ctx: StreamContext,
    ) -> AsyncGenerator[dict[str, str], None]:
        """Execute query using Claude Agent SDK.

        Args:
            request: Query request.
            ctx: Stream context.

        Yields:
            SSE event dicts with 'event' and 'data' keys.
        """
        try:
            # Detect slash commands in prompt (T115a)
            # Use CommandsService for full parsing including arguments
            from pathlib import Path

            from apps.api.services.commands import CommandsService

            project_path = Path(request.cwd) if request.cwd else Path.cwd()
            commands_service = CommandsService(project_path=project_path)
            parsed_command = commands_service.parse_command(request.prompt)

            if parsed_command:
                # Slash command detected - SDK will handle execution
                # Just log for observability
                logger.info(
                    "slash_command_detected",
                    session_id=ctx.session_id,
                    command=parsed_command["command"],
                    args=parsed_command["args"],
                )

            # Import SDK here to avoid import errors if not installed
            from claude_agent_sdk import ClaudeSDKClient

            # Build options using OptionsBuilder
            options = OptionsBuilder(request).build()

            # Create client and execute query
            # Note: Only pass session_id to SDK when resuming an existing SDK session
            # For new conversations, use the default "default" session_id
            async with ClaudeSDKClient(options) as client:
                # T122: Build query content with images if provided
                # SDK accepts images as part of multimodal content
                if request.images:
                    # Build multimodal content: text + images
                    content: list[dict[str, str | dict[str, str]]] = []

                    # Add text prompt
                    content.append({"type": "text", "text": request.prompt})

                    # Add images
                    for image in request.images:
                        if image.type == "base64":
                            content.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image.media_type,
                                    "data": image.data,
                                },
                            })
                        else:
                            # URL type
                            content.append({
                                "type": "image",
                                "source": {
                                    "type": "url",
                                    "url": image.data,
                                },
                            })

                    logger.info(
                        "Multimodal query with images",
                        session_id=ctx.session_id,
                        image_count=len(request.images),
                    )
                    # Pass multimodal content to SDK
                    await client.query(content)  # type: ignore[arg-type]
                else:
                    # Standard text-only prompt
                    await client.query(request.prompt)

                async for message in client.receive_response():
                    # Update context
                    ctx.num_turns += 1

                    # Map SDK message to API event using MessageHandler
                    event_str = self._message_handler.map_sdk_message(message, ctx)
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
            raise AgentError(
                f"Agent execution failed: {e}", original_error=str(e)
            ) from e

    async def _mock_response(
        self,
        request: "QueryRequest",
        ctx: StreamContext,
    ) -> AsyncGenerator[dict[str, str], None]:
        """Generate mock response for development without SDK.

        Args:
            request: Query request.
            ctx: Stream context.

        Yields:
            SSE event dicts with 'event' and 'data' keys.
        """
        from apps.api.schemas.responses import (
            ContentBlockSchema,
            MessageEvent,
            MessageEventData,
        )

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
        yield self._message_handler.format_sse(event.event, event.data.model_dump())

        ctx.result_text = "Mock response completed"
        ctx.total_cost_usd = 0.001

        # Generate mock structured output if output_format was specified
        if request.output_format:
            if request.output_format.type == "json":
                # For json type, return a simple mock JSON object
                ctx.structured_output = {
                    "message": "Mock structured response",
                    "status": "success",
                }
            elif request.output_format.type == "json_schema":
                # For json_schema, generate a mock response matching the schema
                # In production, the SDK would validate against the schema
                ctx.structured_output = {
                    "message": "Mock structured response matching schema",
                    "validated": True,
                }

    async def query_single(self, request: "QueryRequest") -> "QueryResponseDict":
        """Execute non-streaming query.

        Args:
            request: Query request.

        Returns:
            Complete response dictionary.
        """
        session_id = request.session_id or str(uuid4())
        model = request.model or "sonnet"
        start_time = time.perf_counter()

        content_blocks: list[dict[str, object]] = []
        is_error = False
        num_turns = 0
        total_cost_usd: float | None = None
        result_text: str | None = None
        usage_data: dict[str, int] | None = None
        structured_output: dict[str, object] | None = None

        # Collect all events from stream
        ctx = StreamContext(
            session_id=session_id,
            model=model,
            start_time=start_time,
            enable_file_checkpointing=request.enable_file_checkpointing,
            include_partial_messages=request.include_partial_messages,
        )

        try:
            async for event in self._execute_query(request, ctx):
                event_type = event.get("event")
                if event_type == "message":
                    try:
                        event_data = json.loads(event.get("data", "{}"))
                        # Accumulate assistant message content
                        if event_data.get("type") == "assistant":
                            content_blocks.extend(event_data.get("content", []))
                            # Track usage (typically latest message has cumulative or we sum)
                            if event_data.get("usage"):
                                msg_usage = event_data["usage"]
                                if usage_data is None:
                                    usage_data = msg_usage.copy()
                                else:
                                    # Accumulate tokens across turns
                                    for k, v in msg_usage.items():
                                        if isinstance(v, int):
                                            usage_data[k] = usage_data.get(k, 0) + v
                    except json.JSONDecodeError:
                        logger.error("Failed to parse event data", event=event)
                elif event_type == "error":
                    is_error = True

            is_error = is_error or ctx.is_error
            num_turns = ctx.num_turns
            total_cost_usd = ctx.total_cost_usd
            result_text = ctx.result_text
            structured_output = ctx.structured_output

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
            "structured_output": structured_output,
        }

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

    async def submit_answer(self, session_id: str, answer: str) -> bool:
        """Submit an answer to a pending AskUserQuestion.

        Args:
            session_id: Session that has a pending question.
            answer: The user's answer.

        Returns:
            True if the answer was accepted, False if session not found.
        """
        # Check if session exists and is active
        if session_id not in self._active_sessions:
            return False

        # Store the answer for the session to pick up
        # In a full implementation, this would communicate with the SDK
        # For now, we just acknowledge the answer was received
        logger.info(
            "Answer submitted for session",
            session_id=session_id,
            answer_length=len(answer),
        )

        # TODO: Implement SDK answer submission when SDK supports it
        # This would typically involve calling a method on the client
        # to inject the user's response into the conversation

        return True

    async def update_permission_mode(
        self,
        session_id: str,
        permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"],
    ) -> bool:
        """Update permission mode for an active session (FR-015).

        Allows dynamic permission mode changes during streaming.

        Args:
            session_id: Session to update.
            permission_mode: New permission mode to apply.

        Returns:
            True if update was accepted, False if session not found/active.
        """
        # Check if session exists and is active
        if session_id not in self._active_sessions:
            return False

        # Log the permission mode change
        logger.info(
            "Permission mode updated for session",
            session_id=session_id,
            new_permission_mode=permission_mode,
        )

        # TODO: When SDK supports dynamic permission mode changes,
        # call the appropriate SDK method here to update the mode
        # for subsequent tool calls in the active session

        return True

    async def create_checkpoint_from_context(
        self, ctx: StreamContext
    ) -> "Checkpoint | None":
        """Create a checkpoint from tracked context data (T104).

        Creates a checkpoint if file checkpointing is enabled, a user message
        UUID has been tracked, and the checkpoint service is available.

        Args:
            ctx: Stream context with tracked checkpoint data.

        Returns:
            Created Checkpoint if successful, None otherwise.
        """
        # Skip if checkpointing not enabled
        if not ctx.enable_file_checkpointing:
            return None

        # Skip if no user message UUID to associate checkpoint with
        if not ctx.last_user_message_uuid:
            return None

        # Skip if checkpoint service not available
        if not self._checkpoint_service:
            logger.warning(
                "Cannot create checkpoint: checkpoint_service not configured",
                session_id=ctx.session_id,
            )
            return None

        try:
            checkpoint = await self._checkpoint_service.create_checkpoint(
                session_id=ctx.session_id,
                user_message_uuid=ctx.last_user_message_uuid,
                files_modified=ctx.files_modified.copy(),
            )
            logger.info(
                "Created checkpoint from context",
                checkpoint_id=checkpoint.id,
                session_id=ctx.session_id,
                user_message_uuid=ctx.last_user_message_uuid,
                files_count=len(ctx.files_modified),
            )
            return checkpoint
        except Exception as e:
            logger.error(
                "Failed to create checkpoint from context",
                session_id=ctx.session_id,
                error=str(e),
            )
            return None

    async def execute_pre_tool_use_hook(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        tool_name: str,
        tool_input: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Execute PreToolUse webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            tool_name: Name of tool being executed.
            tool_input: Tool input parameters.

        Returns:
            Webhook response with decision (allow/deny/ask).
        """
        return await self._hook_executor.execute_pre_tool_use(
            hooks_config, session_id, tool_name, tool_input
        )

    async def execute_post_tool_use_hook(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        tool_name: str,
        tool_input: dict[str, object] | None = None,
        tool_result: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Execute PostToolUse webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            tool_name: Name of tool that was executed.
            tool_input: Tool input parameters.
            tool_result: Result from tool execution.

        Returns:
            Webhook response.
        """
        return await self._hook_executor.execute_post_tool_use(
            hooks_config, session_id, tool_name, tool_input, tool_result
        )

    async def execute_stop_hook(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        is_error: bool = False,
        duration_ms: int = 0,
        result: str | None = None,
    ) -> dict[str, object]:
        """Execute Stop webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            is_error: Whether session ended with error.
            duration_ms: Session duration in milliseconds.
            result: Final result text.

        Returns:
            Webhook response.
        """
        return await self._hook_executor.execute_stop(
            hooks_config, session_id, is_error, duration_ms, result
        )

    async def execute_subagent_stop_hook(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        subagent_name: str,
        is_error: bool = False,
        result: str | None = None,
    ) -> dict[str, object]:
        """Execute SubagentStop webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            subagent_name: Name of subagent that stopped.
            is_error: Whether subagent ended with error.
            result: Subagent result.

        Returns:
            Webhook response.
        """
        return await self._hook_executor.execute_subagent_stop(
            hooks_config, session_id, subagent_name, is_error, result
        )

    async def execute_user_prompt_submit_hook(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        prompt: str,
    ) -> dict[str, object]:
        """Execute UserPromptSubmit webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            prompt: User prompt being submitted.

        Returns:
            Webhook response with potential modified prompt.
        """
        return await self._hook_executor.execute_user_prompt_submit(
            hooks_config, session_id, prompt
        )

    # Private delegation methods for testing compatibility

    def _build_options(self, request: "QueryRequest") -> object:
        """Build SDK options - delegates to OptionsBuilder for testing."""
        return OptionsBuilder(request).build()

    def _map_sdk_message(self, message: object, ctx: StreamContext) -> dict[str, str] | None:
        """Map SDK message to SSE event - delegates to MessageHandler for testing."""
        return self._message_handler.map_sdk_message(message, ctx)

    def _track_file_modifications(
        self, content_blocks: list[object], ctx: StreamContext
    ) -> None:
        """Track file modifications - delegates to MessageHandler for testing."""
        from apps.api.schemas.responses import ContentBlockSchema

        # Convert generic objects to ContentBlockSchema for handler
        typed_blocks: list[ContentBlockSchema] = []
        for block in content_blocks:
            if isinstance(block, ContentBlockSchema):
                typed_blocks.append(block)
            elif isinstance(block, dict):
                typed_blocks.append(ContentBlockSchema(**block))
            else:
                # Skip non-dict, non-schema blocks
                continue

        self._message_handler.track_file_modifications(typed_blocks, ctx)
