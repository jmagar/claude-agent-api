"""Agent service wrapping Claude Agent SDK."""

import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

import structlog

from apps.api.config import get_settings
from apps.api.schemas.responses import (
    CommandInfoSchema,
    ErrorEvent,
    ErrorEventData,
)
from apps.api.services.agent.handlers import MessageHandler
from apps.api.services.agent.hook_facade import HookFacade
from apps.api.services.agent.hooks import HookExecutor
from apps.api.services.agent.options import OptionsBuilder
from apps.api.services.agent.query_executor import QueryExecutor
from apps.api.services.agent.session_tracker import AgentSessionTracker
from apps.api.services.agent.single_query_aggregator import SingleQueryAggregator
from apps.api.services.agent.stream_orchestrator import StreamOrchestrator
from apps.api.services.agent.types import QueryResponseDict, StreamContext
from apps.api.services.commands import CommandsService
from apps.api.services.webhook import WebhookService

if TYPE_CHECKING:
    from apps.api.protocols import Cache
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
        cache: "Cache | None" = None,
        session_tracker: AgentSessionTracker | None = None,
        query_executor: QueryExecutor | None = None,
    ) -> None:
        """Initialize agent service.

        Args:
            webhook_service: Optional WebhookService for hook callbacks.
                           If not provided, a default instance is created.
            checkpoint_service: Optional CheckpointService for file checkpointing.
                              Required for enable_file_checkpointing functionality.
            cache: Optional Cache instance for distributed session tracking.
                   Required for horizontal scaling across multiple instances.
        """
        self._settings = get_settings()
        self._webhook_service = webhook_service or WebhookService()
        self._checkpoint_service = checkpoint_service
        self._cache = cache
        self._session_tracker = session_tracker or AgentSessionTracker(cache=cache)
        self._message_handler = MessageHandler()
        self._hook_executor = HookExecutor(self._webhook_service)
        self._hook_facade = HookFacade(self._hook_executor)
        self._query_executor = query_executor or QueryExecutor(self._message_handler)
        self._stream_orchestrator = StreamOrchestrator(self._message_handler)

    async def _register_active_session(self, session_id: str) -> None:
        """Register session as active in Redis for distributed tracking.

        Args:
            session_id: The session ID to register.

        Raises:
            RuntimeError: If cache is not configured (required for distributed sessions).

        This replaces the in-memory dict approach and enables horizontal scaling.
        Sessions are tracked with a TTL to auto-cleanup stale entries.
        Redis is REQUIRED - no in-memory fallback to prevent split-brain in multi-instance.
        """
        await self._session_tracker.register(session_id)

    async def _is_session_active(self, session_id: str) -> bool:
        """Check if session is active across all instances.

        Args:
            session_id: The session ID to check.

        Returns:
            True if session is active in Redis.

        Raises:
            RuntimeError: If cache is not configured.
        """
        return await self._session_tracker.is_active(session_id)

    async def _unregister_active_session(self, session_id: str) -> None:
        """Remove session from active tracking.

        Args:
            session_id: The session ID to unregister.

        Raises:
            RuntimeError: If cache is not configured.
        """
        await self._session_tracker.unregister(session_id)

    async def _check_interrupt(self, session_id: str) -> bool:
        """Check if session was interrupted (works across instances).

        Args:
            session_id: The session ID to check.

        Returns:
            True if session has been interrupted.

        Raises:
            RuntimeError: If cache is not configured.
        """
        return await self._session_tracker.is_interrupted(session_id)

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
        """Stream a query to the agent (distributed-aware).

        This method now uses Redis-backed session tracking instead of
        in-memory dict, enabling horizontal scaling.

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

        # Register session as active using distributed tracking (replaces in-memory dict)
        await self._register_active_session(session_id)

        try:
            # Extract plugin names for InitEvent (T115)
            plugin_names: list[str] = []
            if request.plugins:
                plugin_names = [p.name for p in request.plugins if p.enabled]

            # Discover slash commands from project directory (T115)
            project_path = Path(request.cwd) if request.cwd else Path.cwd()
            commands_service = CommandsService(project_path=project_path)
            discovered_commands = commands_service.discover_commands()

            # Convert to schema objects
            command_schemas: list[CommandInfoSchema] = [
                CommandInfoSchema(name=cmd["name"], path=cmd["path"])
                for cmd in discovered_commands
            ]

            # Emit init event
            init_event = self._stream_orchestrator.build_init_event(
                session_id=session_id,
                model=model,
                tools=request.allowed_tools or [],
                plugins=plugin_names,
                commands=command_schemas,
                permission_mode=request.permission_mode,
                mcp_servers=[],
            )
            yield init_event

            # Execute query using SDK
            async for event in self._execute_query(request, ctx, commands_service):
                yield event

                # Check for interrupt using Redis-backed check
                if await self._check_interrupt(session_id):
                    logger.info("Session interrupted", session_id=session_id)
                    ctx.is_error = False
                    break

            # Emit result event
            duration_ms = int((time.perf_counter() - ctx.start_time) * 1000)

            result_event = self._stream_orchestrator.build_result_event(
                ctx=ctx,
                duration_ms=duration_ms,
            )
            yield result_event

            # Emit done event
            reason: Literal["completed", "interrupted", "error"]
            if await self._check_interrupt(session_id):
                reason = "interrupted"
            elif ctx.is_error:
                reason = "error"
            else:
                reason = "completed"
            done_event = self._stream_orchestrator.build_done_event(reason=reason)
            yield done_event

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
            yield self._stream_orchestrator.build_done_event(reason="error")

        finally:
            # Cleanup: unregister from Redis
            await self._unregister_active_session(session_id)

    async def _execute_query(
        self,
        request: "QueryRequest",
        ctx: StreamContext,
        commands_service: CommandsService,
    ) -> AsyncGenerator[dict[str, str], None]:
        """Execute query using Claude Agent SDK.

        Args:
            request: Query request.
            ctx: Stream context.
            commands_service: Commands service for slash command detection.

        Yields:
            SSE event dicts with 'event' and 'data' keys.
        """
        async for event in self._query_executor.execute(request, ctx, commands_service):
            yield event

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
        async for event in self._query_executor.mock_response(request, ctx):
            yield event

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
        aggregator = SingleQueryAggregator()

        # Collect all events from stream
        ctx = StreamContext(
            session_id=session_id,
            model=model,
            start_time=start_time,
            enable_file_checkpointing=request.enable_file_checkpointing,
            include_partial_messages=request.include_partial_messages,
        )

        # Initialize commands service for slash command detection
        project_path = Path(request.cwd) if request.cwd else Path.cwd()
        commands_service = CommandsService(project_path=project_path)

        try:
            async for event in self._execute_query(request, ctx, commands_service):
                aggregator.handle_event(event)
        except Exception as e:
            ctx.is_error = True
            aggregator.content_blocks.clear()
            aggregator.content_blocks.append({"type": "text", "text": f"Error: {e}"})

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        return aggregator.finalize(
            session_id=session_id,
            model=model,
            ctx=ctx,
            duration_ms=duration_ms,
        )

    async def interrupt(self, session_id: str) -> bool:
        """Interrupt a running agent session (distributed).

        Args:
            session_id: The session ID to interrupt.

        Returns:
            True if interrupt signal was sent successfully, False if session not active.

        Raises:
            RuntimeError: If cache is not configured.

        This now works across multiple API instances via Redis.
        Redis is REQUIRED - no in-memory fallback to prevent split-brain.
        """
        # Check if session is active (across all instances)
        is_active = await self._is_session_active(session_id)
        if not is_active:
            logger.info(
                "Cannot interrupt inactive session",
                session_id=session_id,
            )
            return False

        logger.info("Interrupting session", session_id=session_id)

        # Mark session as interrupted in Redis (visible to all instances)
        await self._session_tracker.mark_interrupted(session_id)

        logger.info(
            "Interrupt signal sent",
            session_id=session_id,
            storage="redis",
            distributed=True,
        )

        return True

    async def submit_answer(self, session_id: str, answer: str) -> bool:
        """Submit an answer to a pending AskUserQuestion.

        Args:
            session_id: Session that has a pending question.
            answer: The user's answer.

        Returns:
            True if the answer was accepted, False if session not found.
        """
        # Check if session exists and is active using distributed tracking
        is_active = await self._is_session_active(session_id)
        if not is_active:
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
        # Check if session exists and is active using distributed tracking
        is_active = await self._is_session_active(session_id)
        if not is_active:
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
        return await self._hook_facade.execute_pre_tool_use(
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
        return await self._hook_facade.execute_post_tool_use(
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
        return await self._hook_facade.execute_stop(
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
        return await self._hook_facade.execute_subagent_stop(
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
        return await self._hook_facade.execute_user_prompt_submit(
            hooks_config, session_id, prompt
        )

    # Private delegation methods for testing compatibility

    def _build_options(self, request: "QueryRequest") -> object:
        """Build SDK options - delegates to OptionsBuilder for testing."""
        return OptionsBuilder(request).build()

    def _map_sdk_message(
        self, message: object, ctx: StreamContext
    ) -> dict[str, str] | None:
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
