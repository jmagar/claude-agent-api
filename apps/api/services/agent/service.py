"""Agent service wrapping Claude Agent SDK."""

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypedDict
from uuid import uuid4

import structlog

from apps.api.config import get_settings
from apps.api.services.agent.checkpoint_manager import CheckpointManager
from apps.api.services.agent.command_discovery import CommandDiscovery
from apps.api.services.agent.config import AgentServiceConfig
from apps.api.services.agent.file_modification_tracker import FileModificationTracker
from apps.api.services.agent.handlers import MessageHandler
from apps.api.services.agent.hook_facade import HookFacade
from apps.api.services.agent.hooks import HookExecutor
from apps.api.services.agent.options import OptionsBuilder
from apps.api.services.agent.query_executor import QueryExecutor
from apps.api.services.agent.session_control import SessionControl
from apps.api.services.agent.session_tracker import AgentSessionTracker
from apps.api.services.agent.single_query_runner import SingleQueryRunner
from apps.api.services.agent.stream_orchestrator import StreamOrchestrator
from apps.api.services.agent.stream_query_runner import StreamQueryRunner
from apps.api.services.agent.types import QueryResponseDict, StreamContext
from apps.api.services.webhook import WebhookService

if TYPE_CHECKING:
    from apps.api.protocols import Cache
    from apps.api.schemas.requests.config import HooksConfigSchema
    from apps.api.schemas.requests.query import QueryRequest
    from apps.api.services.checkpoint import Checkpoint, CheckpointService
    from apps.api.services.commands import CommandsService
    from apps.api.services.mcp_config_injector import McpConfigInjector
    from apps.api.services.memory import MemoryService

logger = structlog.get_logger(__name__)


class _StreamRunnerKwargs(TypedDict, total=False):
    """Keyword arguments for StreamQueryRunner.run().

    Uses total=False to allow optional fields without type errors.
    """

    session_id_override: str
    api_key: str
    memory_service: "MemoryService | None"


class _SingleRunnerKwargs(TypedDict, total=False):
    """Keyword arguments for SingleQueryRunner.run().

    Uses total=False to allow optional fields without type errors.
    """

    api_key: str
    memory_service: "MemoryService | None"


class AgentService:
    """Service for interacting with Claude Agent SDK."""

    def __init__(
        self,
        config: AgentServiceConfig | None = None,
        session_tracker: AgentSessionTracker | None = None,
        query_executor: QueryExecutor | None = None,
        stream_runner: StreamQueryRunner | None = None,
        single_query_runner: SingleQueryRunner | None = None,
        session_control: SessionControl | None = None,
        checkpoint_manager: CheckpointManager | None = None,
        file_modification_tracker: FileModificationTracker | None = None,
        **deprecated_kwargs: object,
    ) -> None:
        """Initialize agent service.

        Args:
            config: Configuration for optional dependencies (webhook, checkpoint, cache, MCP, memory).
                    If not provided, defaults to empty config.
            session_tracker: Optional AgentSessionTracker (created with cache from config if not provided).
            query_executor: Optional QueryExecutor (created with default MessageHandler if not provided).
            stream_runner: Optional StreamQueryRunner (created if not provided).
            single_query_runner: Optional SingleQueryRunner (created if not provided).
            session_control: Optional SessionControl (created if not provided).
            checkpoint_manager: Optional CheckpointManager (created if not provided).
            file_modification_tracker: Optional FileModificationTracker (created if not provided).
            **deprecated_kwargs: Deprecated individual service parameters (cache, checkpoint_service, etc.).
                                 Use config parameter instead. Support retained for backward compatibility.
        """
        import warnings

        self._settings = get_settings()

        # Handle deprecated kwargs by building config if needed
        if deprecated_kwargs:
            warnings.warn(
                "Passing cache, checkpoint_service, memory_service, mcp_config_injector, "
                "or webhook_service directly to AgentService is deprecated. "
                "Use AgentServiceConfig instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if config is None:
                config = AgentServiceConfig(
                    cache=deprecated_kwargs.get("cache"),  # type: ignore[arg-type]
                    checkpoint_service=deprecated_kwargs.get("checkpoint_service"),  # type: ignore[arg-type]
                    memory_service=deprecated_kwargs.get("memory_service"),  # type: ignore[arg-type]
                    mcp_config_injector=deprecated_kwargs.get("mcp_config_injector"),  # type: ignore[arg-type]
                    webhook_service=deprecated_kwargs.get("webhook_service"),  # type: ignore[arg-type]
                )

        self._config = config or AgentServiceConfig()

        # Extract config values for backward compatibility
        self._webhook_service = self._config.webhook_service or WebhookService()
        self._checkpoint_service = self._config.checkpoint_service
        self._cache = self._config.cache
        self._mcp_config_injector = self._config.mcp_config_injector
        self._memory_service = self._config.memory_service

        # Initialize core components
        self._session_tracker = session_tracker or AgentSessionTracker(
            cache=self._cache
        )
        self._message_handler = MessageHandler()
        self._hook_executor = HookExecutor(self._webhook_service)
        self._hook_facade = HookFacade(self._hook_executor)
        self._query_executor = query_executor or QueryExecutor(self._message_handler)
        self._stream_orchestrator = StreamOrchestrator(self._message_handler)
        self._stream_runner = stream_runner or StreamQueryRunner(
            session_tracker=self._session_tracker,
            query_executor=self._query_executor,
            stream_orchestrator=self._stream_orchestrator,
        )
        self._single_query_runner = single_query_runner or SingleQueryRunner(
            query_executor=self._query_executor,
        )
        self._session_control = session_control or SessionControl(self._session_tracker)
        self._checkpoint_manager = checkpoint_manager or CheckpointManager(
            self._checkpoint_service
        )
        self._file_modification_tracker = (
            file_modification_tracker or FileModificationTracker(self._message_handler)
        )

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
        logger.debug(
            "Registered active session in distributed cache",
            session_id=session_id,
            storage="redis",
        )

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
    def checkpoint_service(self) -> object | None:
        """Get the checkpoint service instance.

        Returns:
            CheckpointService instance or None if not configured.
        """
        return self._checkpoint_service

    async def query_stream(
        self, request: "QueryRequest", api_key: str = ""
    ) -> AsyncGenerator[dict[str, str], None]:
        """Stream a query to the agent (distributed-aware).

        This method now uses Redis-backed session tracking instead of
        in-memory dict, enabling horizontal scaling.

        Args:
            request: Query request.
            api_key: API key for scoped MCP server configuration. Empty string disables injection.

        Yields:
            SSE event dicts with 'event' and 'data' keys.
        """
        # Inject server-side MCP configuration before execution
        if self._mcp_config_injector and api_key:
            request = await self._mcp_config_injector.inject(request, api_key)

        session_id = request.session_id or str(uuid4())
        model = request.model or "sonnet"

        # Extract plugin names for InitEvent (T115)
        plugin_names: list[str] = []
        if request.plugins:
            plugin_names = [p.name for p in request.plugins if p.enabled]

        # Discover slash commands from project directory (T115)
        project_path = Path(request.cwd) if request.cwd else Path.cwd()
        discovery = CommandDiscovery(project_path=project_path)
        command_schemas = discovery.discover_commands()

        # Build MCP server status list for init event
        mcp_server_status: list[dict[str, object]] = []
        if request.mcp_servers:
            for name, config in request.mcp_servers.items():
                mcp_server_status.append(
                    {
                        "name": name,
                        "type": config.type,
                        "status": "connected",  # Status is set to connected for display
                    }
                )

        # Emit init event
        init_event = self._stream_orchestrator.build_init_event(
            session_id=session_id,
            model=model,
            tools=request.allowed_tools or [],
            plugins=plugin_names,
            commands=command_schemas,
            permission_mode=request.permission_mode,
            mcp_servers=mcp_server_status,
        )
        yield init_event

        # Build kwargs for SDK runner (all params supported in SDK >= 0.1.19)
        stream_kwargs = _StreamRunnerKwargs(
            session_id_override=session_id,
            api_key=api_key,
            memory_service=self._memory_service,
        )

        # Invoke runner with typed kwargs
        async for event in self._stream_runner.run(
            request,
            discovery.commands_service,
            **stream_kwargs,
        ):
            yield event

    async def _execute_query(
        self,
        request: "QueryRequest",
        ctx: StreamContext,
        commands_service: "CommandsService",
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

    async def query_single(
        self, request: "QueryRequest", api_key: str = ""
    ) -> "QueryResponseDict":
        """Execute non-streaming query.

        Args:
            request: Query request.
            api_key: API key for scoped MCP server configuration. Empty string disables injection.

        Returns:
            Complete response dictionary.
        """
        # Inject server-side MCP configuration before execution
        if self._mcp_config_injector and api_key:
            request = await self._mcp_config_injector.inject(request, api_key)

        project_path = Path(request.cwd) if request.cwd else Path.cwd()
        discovery = CommandDiscovery(project_path=project_path)

        # Build kwargs for SDK runner (all params supported in SDK >= 0.1.19)
        single_kwargs = _SingleRunnerKwargs(
            api_key=api_key,
            memory_service=self._memory_service,
        )

        # Invoke runner with typed kwargs
        return await self._single_query_runner.run(
            request,
            discovery.commands_service,
            **single_kwargs,
        )

    async def interrupt(self, session_id: str) -> bool:
        """Interrupt a running agent session (distributed).

        Args:
            session_id: The session ID to interrupt.

        Returns:
            True if interrupt signal was sent successfully.

        Raises:
            RuntimeError: If cache is not configured.

        This now works across multiple API instances via Redis.
        Redis is REQUIRED - no in-memory fallback to prevent split-brain.

        Note: Only active sessions are marked as interrupted to avoid stale signals.
        """
        return await self._session_control.interrupt(session_id)

    async def submit_answer(self, session_id: str, answer: str) -> bool:
        """Submit an answer to a pending AskUserQuestion.

        Args:
            session_id: Session that has a pending question.
            answer: The user's answer.

        Returns:
            True if the answer was accepted, False if session not found.
        """
        return await self._session_control.submit_answer(session_id, answer)

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
        return await self._session_control.update_permission_mode(
            session_id, permission_mode
        )

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
        return await self._checkpoint_manager.create_from_context(ctx)

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
        """Track file modifications - delegates to FileModificationTracker for testing."""
        self._file_modification_tracker.track(content_blocks, ctx)
