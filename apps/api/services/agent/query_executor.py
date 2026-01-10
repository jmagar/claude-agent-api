"""Query execution helpers for AgentService."""

import asyncio
from collections.abc import AsyncGenerator, AsyncIterable
from typing import TYPE_CHECKING, cast

import structlog

from apps.api.exceptions import AgentError
from apps.api.services.agent.options import OptionsBuilder
from apps.api.services.agent.types import StreamContext

if TYPE_CHECKING:
    from apps.api.schemas.requests.query import QueryRequest
    from apps.api.services.agent.handlers import MessageHandler
    from apps.api.services.commands import CommandsService

logger = structlog.get_logger(__name__)


class QueryExecutor:
    """Executes queries against the Claude Agent SDK."""

    def __init__(self, message_handler: "MessageHandler") -> None:
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
    ) -> AsyncGenerator[dict[str, str], None]:
        """Execute query using Claude Agent SDK.

        Args:
            request: Query request containing prompt and options.
            ctx: Stream context for tracking execution state.
            commands_service: Service for parsing slash commands.

        Yields:
            SSE-formatted event dictionaries.

        Raises:
            AgentError: If SDK execution fails.
        """
        try:
            # Detect slash commands in prompt for observability logging
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
            from claude_agent_sdk import (
                ClaudeSDKClient,
                ClaudeSDKError,
                CLIConnectionError,
                CLIJSONDecodeError,
                CLINotFoundError,
                ProcessError,
            )

            # Build options using OptionsBuilder
            options = OptionsBuilder(request).build()

            logger.info(
                "Creating SDK client",
                session_id=ctx.session_id,
                model=ctx.model,
                enable_file_checkpointing=request.enable_file_checkpointing,
                permission_mode=request.permission_mode,
            )

            # Create client and execute query
            # Note: Only pass session_id to SDK when resuming an existing SDK session
            # For new conversations, use the default "default" session_id
            async with ClaudeSDKClient(options) as client:
                logger.debug("SDK client connected", session_id=ctx.session_id)
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

                    logger.info(
                        "Multimodal query with images",
                        session_id=ctx.session_id,
                        image_count=len(request.images),
                    )
                    # Pass multimodal content to SDK
                    # SDK type hints require AsyncIterable but accepts lists at runtime
                    multimodal_content = cast(
                        "AsyncIterable[dict[str, str | dict[str, str]]]",
                        content,
                    )
                    await client.query(multimodal_content)
                else:
                    # Standard text-only prompt
                    await client.query(request.prompt)

                logger.debug("Query sent to SDK", session_id=ctx.session_id)

                async for message in client.receive_response():
                    # Update context
                    ctx.num_turns += 1

                    logger.debug(
                        "Received SDK message",
                        session_id=ctx.session_id,
                        message_type=type(message).__name__,
                    )

                    # Map SDK message to API event using MessageHandler
                    event_str = self._message_handler.map_sdk_message(message, ctx)
                    if event_str:
                        yield event_str

                logger.debug("SDK client disconnecting", session_id=ctx.session_id)

        except ImportError:
            # SDK not installed - emit mock response for development
            logger.warning("Claude Agent SDK not installed, using mock response")
            async for event in self.mock_response(request, ctx):
                yield event

        except CLINotFoundError as e:
            logger.error("Claude Code CLI not found", error=str(e))
            ctx.is_error = True
            # Store full error details in original_error for logging
            # but use generic message for security
            raise AgentError(
                "Claude Code CLI is not installed",
                original_error=str(e),
            ) from e

        except CLIConnectionError as e:
            logger.error("Failed to connect to Claude Code", error=str(e))
            ctx.is_error = True
            # Store full error details in original_error for logging
            # but use generic message for security
            raise AgentError(
                "Connection to Claude Code failed", original_error=str(e)
            ) from e

        except ProcessError as e:
            exit_code = getattr(e, "exit_code", None)
            stderr = getattr(e, "stderr", None)
            logger.error(
                "Claude Code process failed", exit_code=exit_code, stderr=stderr
            )
            ctx.is_error = True
            # Store full error details in original_error for logging
            # but use generic message for security
            raise AgentError("Process failed", original_error=str(e)) from e

        except CLIJSONDecodeError as e:
            line = getattr(e, "line", None)
            logger.error("Failed to parse SDK response", line=line)
            ctx.is_error = True
            # Store full error details in original_error for logging
            # but use generic message for security
            raise AgentError(
                "SDK response parsing failed", original_error=str(e)
            ) from e

        except ClaudeSDKError as e:
            logger.error("SDK error", error=str(e))
            ctx.is_error = True
            # Store full error details in original_error for logging
            # but use generic message for security
            raise AgentError("SDK error", original_error=str(e)) from e

        except asyncio.CancelledError:
            logger.info("SDK execution cancelled", session_id=ctx.session_id)
            raise

        except Exception as e:
            logger.error("SDK execution error", error=str(e))
            ctx.is_error = True
            # Store full error details in original_error for logging
            # but use generic message for security
            raise AgentError("Agent execution failed", original_error=str(e)) from e

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
