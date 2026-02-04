"""Query execution helpers for AgentService."""

import asyncio
from collections.abc import AsyncGenerator
from enum import Enum
from typing import TYPE_CHECKING

import structlog

from apps.api.exceptions import AgentError
from apps.api.services.agent.options import OptionsBuilder
from apps.api.services.agent.types import StreamContext

if TYPE_CHECKING:
    from apps.api.schemas.requests.query import QueryRequest
    from apps.api.services.agent.handlers import MessageHandler
    from apps.api.services.commands import CommandsService
    from apps.api.services.memory import MemoryService

logger = structlog.get_logger(__name__)


class MessageRole(str, Enum):
    """Message role types."""

    ASSISTANT = "assistant"
    USER = "user"


class ContentType(str, Enum):
    """Content block types."""

    TEXT = "text"
    IMAGE = "image"


class QueryExecutor:
    """Executes queries against the Claude Agent SDK with memory integration."""

    def __init__(
        self,
        message_handler: "MessageHandler",
    ) -> None:
        """Initialize query executor.

        Args:
            message_handler: MessageHandler instance for SDK message mapping.
        """
        self._message_handler = message_handler

    async def execute(
        self,
        request: "QueryRequest",
        ctx: StreamContext,
        commands_service: "CommandsService",
        memory_service: "MemoryService | None" = None,
        api_key: str = "",
    ) -> AsyncGenerator[dict[str, str], None]:
        """Execute query using Claude Agent SDK with memory integration.

        Args:
            request: Query request containing prompt and options.
            ctx: Stream context for tracking execution state.
            commands_service: Service for parsing slash commands.
            memory_service: Optional MemoryService for memory injection/extraction.
            api_key: API key for memory multi-tenant isolation.

        Yields:
            SSE-formatted event dictionaries.

        Raises:
            AgentError: If SDK execution fails.
        """
        # Track assistant responses for memory extraction
        assistant_responses: list[str] = []

        try:
            async for event in self._execute_with_sdk(
                request, ctx, commands_service, memory_service, api_key, assistant_responses
            ):
                yield event
        except ImportError:
            # SDK not installed - emit mock response for development
            logger.warning("Claude Agent SDK not installed, using mock response")
            async for event in self.mock_response(request, ctx):
                yield event
        except Exception as e:
            # Handle SDK-specific errors
            async for event in self._handle_sdk_error(e, ctx):
                yield event

    async def _execute_with_sdk(
        self,
        request: "QueryRequest",
        ctx: StreamContext,
        commands_service: "CommandsService",
        memory_service: "MemoryService | None",
        api_key: str,
        assistant_responses: list[str],
    ) -> AsyncGenerator[dict[str, str], None]:
        """Execute query with SDK client.

        Args:
            request: Query request.
            ctx: Stream context.
            commands_service: Commands service.
            memory_service: Optional memory service.
            api_key: API key for memory isolation.
            assistant_responses: List to track responses.

        Yields:
            SSE event dicts.
        """
        # Import SDK here to avoid import errors if not installed
        from claude_agent_sdk import ClaudeSDKClient

        # Detect slash commands for observability
        parsed_command = commands_service.parse_command(request.prompt)
        if parsed_command:
            logger.debug(
                "slash_command_detected",
                session_id=ctx.session_id,
                command=parsed_command["command"],
                args=parsed_command["args"],
            )

        # Inject memory context
        if memory_service and api_key:
            request = await self._inject_memory_context(
                request, memory_service, api_key, ctx.session_id
            )

        # Build SDK options
        options = OptionsBuilder(request).build()

        logger.info(
            "Creating SDK client",
            session_id=ctx.session_id,
            model=ctx.model,
            enable_file_checkpointing=request.enable_file_checkpointing,
            permission_mode=request.permission_mode,
        )

        # Execute query
        async with ClaudeSDKClient(options) as client:
            logger.debug("SDK client connected", session_id=ctx.session_id)

            # Send query (text or multimodal)
            if request.images:
                await self._send_multimodal_query(client, request, ctx)
            else:
                await client.query(request.prompt)

            logger.debug("Query sent to SDK", session_id=ctx.session_id)

            # Process responses
            async for message in client.receive_response():
                ctx.num_turns += 1

                logger.debug(
                    "Received SDK message",
                    session_id=ctx.session_id,
                    message_type=type(message).__name__,
                )

                # Track assistant responses (type-safe)
                self._track_assistant_responses(message, assistant_responses)

                # Map SDK message to API event
                event_str = self._message_handler.map_sdk_message(message, ctx)
                if event_str:
                    yield event_str

            logger.debug("SDK client disconnecting", session_id=ctx.session_id)

        # Extract memories after completion
        if memory_service and api_key:
            await self._extract_memory(
                request, assistant_responses, memory_service, api_key, ctx.session_id
            )

    async def _send_multimodal_query(
        self,
        client: object,
        request: "QueryRequest",
        ctx: StreamContext,
    ) -> None:
        """Send multimodal query with images to SDK client.

        Args:
            client: SDK client instance.
            request: Query request with images.
            ctx: Stream context for logging.
        """
        content = self._build_multimodal_content(request)

        logger.info(
            "Multimodal query with images",
            session_id=ctx.session_id,
            image_count=len(request.images) if request.images else 0,
        )

        # SDK requires AsyncIterable for multimodal content
        async def content_generator() -> AsyncGenerator[dict[str, object], None]:
            for item in content:
                yield item

        # Type ignore needed because client is typed as object
        await client.query(content_generator())  # type: ignore[attr-defined]

    async def _handle_sdk_error(
        self, error: Exception, ctx: StreamContext
    ) -> AsyncGenerator[dict[str, str], None]:
        """Handle SDK-specific errors with appropriate error messages.

        Args:
            error: The exception that was raised.
            ctx: Stream context to update error state.

        Yields:
            Nothing (always raises AgentError).

        Raises:
            AgentError: Translated error with user-friendly message.
        """
        from claude_agent_sdk import (
            ClaudeSDKError,
            CLIConnectionError,
            CLIJSONDecodeError,
            CLINotFoundError,
            ProcessError,
        )

        ctx.is_error = True

        if isinstance(error, CLINotFoundError):
            logger.error("Claude Code CLI not found", error=str(error))
            raise AgentError(
                "Claude Code CLI is not installed",
                original_error=str(error),
            ) from error

        if isinstance(error, CLIConnectionError):
            logger.error("Failed to connect to Claude Code", error=str(error))
            raise AgentError(
                "Connection to Claude Code failed", original_error=str(error)
            ) from error

        if isinstance(error, ProcessError):
            exit_code = getattr(error, "exit_code", None)
            stderr = getattr(error, "stderr", None)
            logger.error(
                "Claude Code process failed", exit_code=exit_code, stderr=stderr
            )
            raise AgentError("Process failed", original_error=str(error)) from error

        if isinstance(error, CLIJSONDecodeError):
            line = getattr(error, "line", None)
            logger.error("Failed to parse SDK response", line=line)
            raise AgentError(
                "SDK response parsing failed", original_error=str(error)
            ) from error

        if isinstance(error, ClaudeSDKError):
            logger.error("SDK error", error=str(error))
            raise AgentError("SDK error", original_error=str(error)) from error

        if isinstance(error, asyncio.CancelledError):
            logger.info("SDK execution cancelled", session_id=ctx.session_id)
            raise

        # Generic error
        logger.error("SDK execution error", error=str(error))
        raise AgentError("Agent execution failed", original_error=str(error)) from error

        # Make this a generator (unreachable but satisfies type checker)
        yield {}  # pragma: no cover

    async def _inject_memory_context(
        self,
        request: "QueryRequest",
        memory_service: "MemoryService",
        api_key: str,
        session_id: str,
    ) -> "QueryRequest":
        """Inject memory context into system prompt.

        Args:
            request: Original query request.
            memory_service: Memory service for retrieving context.
            api_key: API key for multi-tenant isolation.
            session_id: Session ID for logging.

        Returns:
            Modified request with memory context injected (immutable copy).
        """
        try:
            memory_context = await memory_service.format_memory_context(
                query=request.prompt,
                user_id=api_key,
            )

            # Enhance system prompt with memory context if memories found
            if memory_context:
                original_system_prompt = request.system_prompt or ""
                enhanced_system_prompt = (
                    f"{original_system_prompt}\n\n{memory_context}".strip()
                )
                # Create immutable copy with updated system prompt
                request = request.model_copy(
                    update={"system_prompt": enhanced_system_prompt}
                )

                logger.debug(
                    "memory_context_injected",
                    session_id=session_id,
                    user_id=api_key,
                    memory_count=memory_context.count("\n- "),
                )
        except Exception as exc:
            logger.warning(
                "memory_injection_failed",
                session_id=session_id,
                user_id=api_key,
                error=str(exc),
            )
            # Continue without memory context

        return request

    def _build_multimodal_content(
        self, request: "QueryRequest"
    ) -> list[dict[str, object]]:
        """Build multimodal content list from request.

        Args:
            request: Query request with optional images.

        Returns:
            List of content blocks (text + images).
        """
        content: list[dict[str, object]] = []

        # Add text prompt
        content.append({"type": "text", "text": request.prompt})

        # Add images if provided
        if request.images:
            for image in request.images:
                if image.type == "base64":
                    content.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image.media_type,
                                "data": image.data,
                            },
                        }
                    )
                else:
                    # URL type
                    content.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "url",
                                "url": image.data,
                            },
                        }
                    )

        return content

    def _track_assistant_responses(
        self, message: object, assistant_responses: list[str]
    ) -> None:
        """Track assistant message responses for memory extraction.

        Args:
            message: SDK message object.
            assistant_responses: List to append responses to.
        """
        if not hasattr(message, "type") or message.type != MessageRole.ASSISTANT:
            return

        if not hasattr(message, "content"):
            return

        # Type-safe iteration: check if content is a list before iterating
        content = getattr(message, "content", [])
        if not isinstance(content, list):
            return

        for content_block in content:
            if (
                hasattr(content_block, "type")
                and content_block.type == ContentType.TEXT
                and hasattr(content_block, "text")
            ):
                assistant_responses.append(content_block.text)

    async def _extract_memory(
        self,
        request: "QueryRequest",
        assistant_responses: list[str],
        memory_service: "MemoryService",
        api_key: str,
        session_id: str,
    ) -> None:
        """Extract and store memories from conversation.

        Args:
            request: Original query request.
            assistant_responses: List of assistant response texts.
            memory_service: Memory service for storing memories.
            api_key: API key for multi-tenant isolation.
            session_id: Session ID for metadata.
        """
        try:
            # Format conversation for memory extraction
            if assistant_responses:
                assistant_text = " ".join(assistant_responses)
                conversation = f"User: {request.prompt}\n\nAssistant: {assistant_text}"
            else:
                # Even without responses, store the user prompt
                conversation = f"User: {request.prompt}"

            await memory_service.add_memory(
                messages=conversation,
                user_id=api_key,
                metadata={
                    "session_id": session_id,
                    "source": "query",
                },
            )
            logger.debug(
                "memory_extracted",
                session_id=session_id,
                user_id=api_key,
                has_response=bool(assistant_responses),
            )
        except Exception as exc:
            logger.warning(
                "memory_extraction_failed",
                session_id=session_id,
                user_id=api_key,
                error=str(exc),
            )

    async def mock_response(
        self,
        request: "QueryRequest",
        ctx: StreamContext,
    ) -> AsyncGenerator[dict[str, str], None]:
        """Generate mock response for development without SDK.

        Args:
            request: Query request containing prompt and options.
            ctx: Stream context for tracking execution state.

        Yields:
            SSE-formatted event dictionaries.
        """
        from apps.api.schemas.responses import (
            ContentBlockSchema,
            MessageEvent,
            MessageEventData,
            UsageSchema,
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
