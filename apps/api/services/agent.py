"""Agent service wrapping Claude Agent SDK."""

import asyncio
import json
import os
import re
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, TypedDict, cast
from uuid import uuid4

import structlog

from apps.api.config import get_settings
from apps.api.exceptions import AgentError
from apps.api.schemas.messages import (
    map_sdk_content_block,
    map_sdk_usage,
)
from apps.api.schemas.requests import HooksConfigSchema, QueryRequest
from apps.api.schemas.responses import (
    ContentBlockSchema,
    ContentDeltaSchema,
    DoneEvent,
    DoneEventData,
    ErrorEvent,
    ErrorEventData,
    InitEvent,
    InitEventData,
    MessageEvent,
    MessageEventData,
    PartialMessageEvent,
    PartialMessageEventData,
    QuestionEvent,
    QuestionEventData,
    ResultEvent,
    ResultEventData,
    UsageSchema,
)
from apps.api.services.webhook import WebhookService

if TYPE_CHECKING:
    from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions
    from claude_agent_sdk.types import (
        McpHttpServerConfig,
        McpSdkServerConfig,
        McpSSEServerConfig,
        McpStdioServerConfig,
        SandboxSettings,
        SdkPluginConfig,
        SettingSource,
    )

    from apps.api.services.checkpoint import Checkpoint, CheckpointService

    # Union type for MCP server configs
    McpServerConfig = (
        McpStdioServerConfig
        | McpSSEServerConfig
        | McpHttpServerConfig
        | McpSdkServerConfig
    )

logger = structlog.get_logger(__name__)

# Pattern for ${VAR} or ${VAR:-default} environment variable syntax
_ENV_VAR_PATTERN = re.compile(r"\$\{([^}:]+)(?::-([^}]*))?\}")

# Pattern for slash command detection (T115a)
# Matches prompts starting with / followed by alphanumeric characters, dashes, or underscores
_SLASH_COMMAND_PATTERN = re.compile(r"^/([a-zA-Z][a-zA-Z0-9_-]*)")


def detect_slash_command(prompt: str) -> str | None:
    """Detect if a prompt starts with a slash command (T115a).

    Slash commands are prompts that start with / followed by a command name.
    Examples: /help, /clear, /commit, /review-pr

    Args:
        prompt: The user prompt to check.

    Returns:
        The command name (without /) if detected, None otherwise.
    """
    match = _SLASH_COMMAND_PATTERN.match(prompt.strip())
    return match.group(1) if match else None


def resolve_env_var(value: str) -> str:
    """Resolve environment variables in a string.

    Supports ${VAR} and ${VAR:-default} syntax.

    Args:
        value: String potentially containing env var references.

    Returns:
        String with environment variables resolved.
    """

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default = match.group(2)  # May be None if no default specified
        return os.environ.get(var_name, default if default is not None else "")

    return _ENV_VAR_PATTERN.sub(replacer, value)


def resolve_env_dict(env: dict[str, str]) -> dict[str, str]:
    """Resolve environment variables in a dict of strings.

    Args:
        env: Dictionary with string values that may contain env var references.

    Returns:
        Dictionary with all env vars resolved.
    """
    return {key: resolve_env_var(val) for key, val in env.items()}


class QueryResponseDict(TypedDict):
    """TypedDict for non-streaming query response."""

    session_id: str
    model: str
    content: list[dict[str, object]]
    is_error: bool
    duration_ms: int
    num_turns: int
    total_cost_usd: float | None
    usage: dict[str, int] | None
    result: str | None
    structured_output: dict[str, object] | None


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
    structured_output: dict[str, object] | None = None
    # Model usage tracking (T110)
    model_usage: dict[str, dict[str, int]] | None = None
    # Checkpoint tracking fields (T100, T104)
    enable_file_checkpointing: bool = False
    last_user_message_uuid: str | None = None
    files_modified: list[str] = field(default_factory=list)
    # Partial messages tracking (T118)
    include_partial_messages: bool = False


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

    @property
    def checkpoint_service(self) -> "CheckpointService | None":
        """Get the checkpoint service instance.

        Returns:
            CheckpointService instance or None if not configured.
        """
        return self._checkpoint_service

    async def query_stream(
        self,
        request: QueryRequest,
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
                plugin_names = [
                    p.name for p in request.plugins if p.enabled
                ]

            # Emit init event
            # Note: commands will be populated from SDK's SystemMessage init event
            # when the SDK provides available slash commands during connection
            init_event = InitEvent(
                data=InitEventData(
                    session_id=session_id,
                    model=model,
                    tools=request.allowed_tools or [],
                    mcp_servers=[],
                    plugins=plugin_names,
                    commands=[],  # Populated from SDK response if available
                    permission_mode=request.permission_mode,
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
            yield self._format_sse(result_event.event, result_event.data.model_dump())

            # Emit done event
            reason: Literal["completed", "interrupted", "error"]
            if self._active_sessions.get(session_id, asyncio.Event()).is_set():
                reason = "interrupted"
            elif ctx.is_error:
                reason = "error"
            else:
                reason = "completed"
            done_event = DoneEvent(data=DoneEventData(reason=reason))
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
            slash_command = detect_slash_command(request.prompt)
            if slash_command:
                logger.info(
                    "Slash command detected in prompt",
                    session_id=ctx.session_id,
                    command=slash_command,
                )

            # Import SDK here to avoid import errors if not installed
            from claude_agent_sdk import ClaudeSDKClient

            # Build options
            options = self._build_options(request)

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
            raise AgentError(
                f"Agent execution failed: {e}", original_error=str(e)
            ) from e

    def _build_mcp_configs(
        self, request: QueryRequest
    ) -> dict[str, dict[str, str | list[str] | dict[str, str] | None]] | None:
        """Build MCP server configurations from request.

        Args:
            request: Query request.

        Returns:
            MCP server configs dict or None.
        """
        if not request.mcp_servers:
            return None

        mcp_configs: dict[str, dict[str, str | list[str] | dict[str, str] | None]] = {}
        for name, config in request.mcp_servers.items():
            # Resolve ${VAR:-default} syntax in env and headers
            resolved_env = resolve_env_dict(config.env) if config.env else {}
            resolved_headers = (
                resolve_env_dict(config.headers) if config.headers else {}
            )
            mcp_configs[name] = {
                "command": config.command,
                "args": config.args,
                "type": config.type,
                "url": config.url,
                "headers": resolved_headers,
                "env": resolved_env,
            }
        return mcp_configs

    def _build_agent_defs(
        self, request: QueryRequest
    ) -> dict[str, dict[str, str | list[str] | None]] | None:
        """Build agent definitions from request.

        Args:
            request: Query request.

        Returns:
            Agent definitions dict or None.
        """
        if not request.agents:
            return None

        agent_defs: dict[str, dict[str, str | list[str] | None]] = {}
        for name, agent in request.agents.items():
            agent_defs[name] = {
                "description": agent.description,
                "prompt": agent.prompt,
                "tools": agent.tools,
                "model": agent.model,
            }
        return agent_defs

    def _build_output_format(
        self, request: QueryRequest
    ) -> dict[str, str | dict[str, object] | None] | None:
        """Build output format configuration from request.

        Args:
            request: Query request.

        Returns:
            Output format dict or None.
        """
        if not request.output_format:
            return None

        return {
            "type": request.output_format.type,
            "schema": request.output_format.schema_,
        }

    def _build_plugins(self, request: QueryRequest) -> list[dict[str, str | None]]:
        """Build plugins list from request.

        Args:
            request: Query request.

        Returns:
            List of plugin config dicts.
        """
        plugins_list: list[dict[str, str | None]] = []
        if request.plugins:
            for plugin_config in request.plugins:
                if plugin_config.enabled:  # Only include enabled plugins
                    plugins_list.append({
                        "name": plugin_config.name,
                        "path": plugin_config.path,
                    })
        return plugins_list

    def _build_sandbox_config(
        self, request: QueryRequest
    ) -> dict[str, bool | list[str]] | None:
        """Build sandbox configuration from request.

        Args:
            request: Query request.

        Returns:
            Sandbox config dict or None.
        """
        if not request.sandbox:
            return None

        return {
            "enabled": request.sandbox.enabled,
            "allowed_paths": request.sandbox.allowed_paths,
            "network_access": request.sandbox.network_access,
        }

    def _resolve_system_prompt(self, request: QueryRequest) -> str | None:
        """Resolve system prompt with optional append.

        Combines base system_prompt with system_prompt_append if both provided.

        Args:
            request: Query request.

        Returns:
            Resolved system prompt or None.
        """
        system_prompt = request.system_prompt if request.system_prompt else None

        if request.system_prompt_append:
            if system_prompt:
                return f"{system_prompt}\n\n{request.system_prompt_append}"
            return request.system_prompt_append

        return system_prompt

    def _build_options(self, request: QueryRequest) -> "ClaudeAgentOptions":
        """Build SDK options from request.

        Args:
            request: Query request.

        Returns:
            ClaudeAgentOptions instance.

        Note:
            The SDK has complex nested types that require dynamic construction.
            We use a typed approach with conditional building.
        """
        from claude_agent_sdk import ClaudeAgentOptions

        # Extract basic options from request
        allowed_tools = request.allowed_tools if request.allowed_tools else None
        disallowed_tools = (
            request.disallowed_tools if request.disallowed_tools else None
        )
        permission_mode = request.permission_mode if request.permission_mode else None
        permission_prompt_tool_name = (
            request.permission_prompt_tool_name
            if request.permission_prompt_tool_name
            else None
        )

        # Session resume configuration
        resume: str | None = None
        fork_session: bool | None = None
        if request.session_id and not request.fork_session:
            resume = request.session_id
        elif request.session_id and request.fork_session:
            resume = request.session_id
            fork_session = True

        # Setting sources for CLAUDE.md loading (T114)
        setting_sources_typed: list[str] | None = None
        if request.setting_sources:
            setting_sources_typed = list(request.setting_sources)

        # Build complex configs using helper methods
        mcp_configs = self._build_mcp_configs(request)
        agent_defs = self._build_agent_defs(request)
        output_format = self._build_output_format(request)
        plugins_list = self._build_plugins(request)
        sandbox_config = self._build_sandbox_config(request)
        final_system_prompt = self._resolve_system_prompt(request)

        # Note: mcp_servers, agents, plugins, setting_sources, and sandbox are cast
        # because SDK expects specific config types but accepts dict-like structures
        return ClaudeAgentOptions(
            allowed_tools=allowed_tools or [],
            disallowed_tools=disallowed_tools or [],
            permission_mode=permission_mode,
            permission_prompt_tool_name=permission_prompt_tool_name,
            model=request.model if request.model else None,
            max_turns=request.max_turns if request.max_turns else None,
            cwd=request.cwd if request.cwd else None,
            env=request.env or {},
            system_prompt=final_system_prompt,
            enable_file_checkpointing=bool(request.enable_file_checkpointing),
            resume=resume,
            fork_session=fork_session or False,
            mcp_servers=cast("dict[str, McpServerConfig]", mcp_configs or {}),
            agents=cast("dict[str, AgentDefinition] | None", agent_defs),
            output_format=output_format,
            plugins=cast("list[SdkPluginConfig]", plugins_list),
            setting_sources=cast("list[SettingSource] | None", setting_sources_typed),
            sandbox=cast("SandboxSettings | None", sandbox_config),
            include_partial_messages=request.include_partial_messages,
        )

    def _handle_user_message(
        self, message: object, ctx: StreamContext
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
        return self._format_sse(event.event, event.data.model_dump())

    def _handle_assistant_message(
        self, message: object, ctx: StreamContext
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
            self._track_file_modifications(content_blocks, ctx)

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
        return self._format_sse(event.event, event.data.model_dump())

    def _check_special_tool_uses(
        self, content_blocks: list[ContentBlockSchema], ctx: StreamContext
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
                question = block.input.get("question", "") if block.input else ""
                q_event = QuestionEvent(
                    data=QuestionEventData(
                        tool_use_id=block.id or "",
                        question=question,
                        session_id=ctx.session_id,
                    )
                )
                return self._format_sse(q_event.event, q_event.data.model_dump())

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

    def _handle_result_message(self, message: object, ctx: StreamContext) -> None:
        """Handle ResultMessage from SDK.

        Updates context with result data. Does not emit an event.

        Args:
            message: SDK ResultMessage.
            ctx: Stream context to update.
        """
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
        self, message: object, _ctx: StreamContext
    ) -> dict[str, str]:
        """Handle ContentBlockStart for partial message streaming.

        Args:
            message: SDK ContentBlockStart message.
            _ctx: Stream context (unused, kept for API consistency).

        Returns:
            SSE event dict with 'event' and 'data' keys.
        """
        index = getattr(message, "index", 0)
        content_block = getattr(message, "content_block", None)

        block_schema: ContentBlockSchema | None = None
        if content_block:
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
        return self._format_sse(
            partial_start_event.event, partial_start_event.data.model_dump()
        )

    def _handle_partial_delta(
        self, message: object, _ctx: StreamContext
    ) -> dict[str, str]:
        """Handle ContentBlockDelta for partial message streaming.

        Args:
            message: SDK ContentBlockDelta message.
            _ctx: Stream context (unused, kept for API consistency).

        Returns:
            SSE event dict with 'event' and 'data' keys.
        """
        index = getattr(message, "index", 0)
        delta = getattr(message, "delta", None)

        delta_schema: ContentDeltaSchema | None = None
        if delta:
            delta_type = getattr(delta, "type", "text_delta")
            delta_schema = ContentDeltaSchema(
                type=delta_type,
                text=getattr(delta, "text", None) if delta_type == "text_delta" else None,
                thinking=getattr(delta, "thinking", None) if delta_type == "thinking_delta" else None,
                partial_json=getattr(delta, "partial_json", None) if delta_type == "input_json_delta" else None,
            )

        partial_delta_event = PartialMessageEvent(
            data=PartialMessageEventData(
                type="content_block_delta",
                index=index,
                delta=delta_schema,
            )
        )
        return self._format_sse(
            partial_delta_event.event, partial_delta_event.data.model_dump()
        )

    def _handle_partial_stop(
        self, message: object, _ctx: StreamContext
    ) -> dict[str, str]:
        """Handle ContentBlockStop for partial message streaming.

        Args:
            message: SDK ContentBlockStop message.
            _ctx: Stream context (unused, kept for API consistency).

        Returns:
            SSE event dict with 'event' and 'data' keys.
        """
        index = getattr(message, "index", 0)

        partial_stop_event = PartialMessageEvent(
            data=PartialMessageEventData(
                type="content_block_stop",
                index=index,
            )
        )
        return self._format_sse(
            partial_stop_event.event, partial_stop_event.data.model_dump()
        )

    def _map_sdk_message(
        self, message: object, ctx: StreamContext
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
        if msg_type == "ContentBlockStart" and ctx.include_partial_messages:
            return self._handle_partial_start(message, ctx)

        if msg_type == "ContentBlockDelta" and ctx.include_partial_messages:
            return self._handle_partial_delta(message, ctx)

        if msg_type == "ContentBlockStop" and ctx.include_partial_messages:
            return self._handle_partial_stop(message, ctx)

        return None

    def _track_file_modifications(
        self, content_blocks: list[ContentBlockSchema], ctx: StreamContext
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

    async def _mock_response(
        self,
        request: QueryRequest,
        ctx: StreamContext,
    ) -> AsyncGenerator[dict[str, str], None]:
        """Generate mock response for development without SDK.

        Args:
            request: Query request.
            ctx: Stream context.

        Yields:
            SSE event dicts with 'event' and 'data' keys.
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

    def _format_sse(
        self, event_type: str, data: dict[str, object]
    ) -> dict[str, str]:
        """Format data as SSE event dict for EventSourceResponse.

        Args:
            event_type: Event type name.
            data: Event data.

        Returns:
            Dict with event and data keys for SSE.
        """
        return {"event": event_type, "data": json.dumps(data)}

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

    async def query_single(self, request: QueryRequest) -> QueryResponseDict:
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
        )

        try:
            async for _event in self._execute_query(request, ctx):
                # Parse event to extract content
                pass

            is_error = ctx.is_error
            num_turns = ctx.num_turns
            total_cost_usd = ctx.total_cost_usd
            result_text = ctx.result_text
            structured_output = ctx.structured_output

        except Exception as e:
            is_error = True
            content_blocks = [{"type": "text", "text": f"Error: {e}"}]

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        return QueryResponseDict(
            session_id=session_id,
            model=model,
            content=content_blocks,
            is_error=is_error,
            duration_ms=duration_ms,
            num_turns=num_turns,
            total_cost_usd=total_cost_usd,
            usage=usage_data,
            result=result_text,
            structured_output=structured_output,
        )

    # Hook execution methods for webhook-based hooks

    async def execute_pre_tool_use_hook(
        self,
        hooks_config: HooksConfigSchema | None,
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
        if not hooks_config or not hooks_config.pre_tool_use:
            return {"decision": "allow"}

        return await self._webhook_service.execute_hook(
            hook_event="PreToolUse",
            hook_config=hooks_config.pre_tool_use,
            session_id=session_id,
            tool_name=tool_name,
            tool_input=tool_input,
        )

    async def execute_post_tool_use_hook(
        self,
        hooks_config: HooksConfigSchema | None,
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
        if not hooks_config or not hooks_config.post_tool_use:
            return {"acknowledged": True}

        return await self._webhook_service.execute_hook(
            hook_event="PostToolUse",
            hook_config=hooks_config.post_tool_use,
            session_id=session_id,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_result=tool_result,
        )

    async def execute_stop_hook(
        self,
        hooks_config: HooksConfigSchema | None,
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
        if not hooks_config or not hooks_config.stop:
            return {"acknowledged": True}

        result_data: dict[str, object] = {
            "is_error": is_error,
            "duration_ms": duration_ms,
        }
        if result:
            result_data["result"] = result

        return await self._webhook_service.execute_hook(
            hook_event="Stop",
            hook_config=hooks_config.stop,
            session_id=session_id,
            result_data=result_data,
        )

    async def execute_subagent_stop_hook(
        self,
        hooks_config: HooksConfigSchema | None,
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
        if not hooks_config or not hooks_config.subagent_stop:
            return {"acknowledged": True}

        result_data: dict[str, object] = {
            "subagent_name": subagent_name,
            "is_error": is_error,
        }
        if result:
            result_data["result"] = result

        return await self._webhook_service.execute_hook(
            hook_event="SubagentStop",
            hook_config=hooks_config.subagent_stop,
            session_id=session_id,
            result_data=result_data,
        )

    async def execute_user_prompt_submit_hook(
        self,
        hooks_config: HooksConfigSchema | None,
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
        if not hooks_config or not hooks_config.user_prompt_submit:
            return {"decision": "allow"}

        return await self._webhook_service.execute_hook(
            hook_event="UserPromptSubmit",
            hook_config=hooks_config.user_prompt_submit,
            session_id=session_id,
            tool_input={"prompt": prompt},
        )
