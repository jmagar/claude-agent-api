"""Run executor for OpenAI-compatible assistant runs.

Orchestrates Claude Agent SDK execution for the Assistants API.
Handles tool calls, creates assistant messages, and manages run lifecycle.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypedDict

import structlog

from apps.api.services.assistants.run_service import RunUsage, ToolCall

if TYPE_CHECKING:
    from apps.api.services.assistants.assistant_service import AssistantService
    from apps.api.services.assistants.message_service import Message, MessageService
    from apps.api.services.assistants.run_service import RunService
    from apps.api.services.assistants.thread_service import ThreadService

logger = structlog.get_logger(__name__)


# =============================================================================
# Types
# =============================================================================


class ToolOutput(TypedDict):
    """Tool output from client."""

    tool_call_id: str
    output: str


class UsageDict(TypedDict):
    """Token usage statistics."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ExecutionResult:
    """Result of run execution."""

    response_text: str | None
    tool_calls: list[dict[str, object]] = field(default_factory=list)
    usage: dict[str, int] | None = None


def _extract_tool_call(tc: dict[str, object]) -> ToolCall:
    """Extract ToolCall from a dict with proper type handling.

    Args:
        tc: Tool call dict from execution result.

    Returns:
        Properly typed ToolCall.
    """
    tc_id = str(tc.get("id", ""))

    # Extract function data
    func_raw = tc.get("function")
    func_name = ""
    func_args = "{}"

    if isinstance(func_raw, dict):
        # Access dict items directly since we know it's a dict
        for key, val in func_raw.items():
            if key == "name" and val is not None:
                func_name = str(val)
            elif key == "arguments" and val is not None:
                func_args = str(val)

    return {
        "id": tc_id,
        "type": "function",
        "function": {
            "name": func_name,
            "arguments": func_args,
        },
    }


# =============================================================================
# Run Executor
# =============================================================================


class RunExecutor:
    """Executes runs using Claude Agent SDK.

    Orchestrates the execution flow:
    1. Starts the run (queued → in_progress)
    2. Gathers thread messages for context
    3. Calls Claude SDK with context and assistant instructions
    4. Handles tool calls (transitions to requires_action if needed)
    5. Creates assistant message with response
    6. Completes the run (or fails/cancels)
    """

    def __init__(
        self,
        run_service: "RunService",
        message_service: "MessageService",
        assistant_service: "AssistantService",
        thread_service: "ThreadService",
    ) -> None:
        """Initialize run executor.

        Args:
            run_service: Service for run lifecycle management.
            message_service: Service for message operations.
            assistant_service: Service for assistant retrieval.
            thread_service: Service for thread retrieval.
        """
        self._run_service = run_service
        self._message_service = message_service
        self._assistant_service = assistant_service
        self._thread_service = thread_service

    async def execute_run(
        self,
        thread_id: str,
        run_id: str,
    ) -> ExecutionResult | None:
        """Execute a run.

        Args:
            thread_id: Thread ID containing the run.
            run_id: Run ID to execute.

        Returns:
            Execution result or None if run not found.
        """
        # Start the run (queued → in_progress)
        run = await self._run_service.start_run(thread_id, run_id)
        if not run:
            logger.warning(
                "Run not found",
                thread_id=thread_id,
                run_id=run_id,
            )
            return None

        # Get assistant for instructions and tools
        assistant = await self._assistant_service.get_assistant(run.assistant_id)
        if not assistant:
            logger.error(
                "Assistant not found for run",
                assistant_id=run.assistant_id,
                run_id=run_id,
            )
            await self._run_service.fail_run(
                thread_id,
                run_id,
                error={"code": "assistant_not_found", "message": "Assistant not found"},
            )
            return None

        try:
            # Execute with SDK
            result = await self._execute_with_sdk(thread_id, run, assistant)

            if result.tool_calls:
                # Transition to requires_action
                tool_calls: list[ToolCall] = []
                for tc in result.tool_calls:
                    if isinstance(tc, dict):
                        tool_calls.append(_extract_tool_call(tc))

                await self._run_service.require_action(
                    thread_id,
                    run_id,
                    tool_calls=tool_calls,
                )

                logger.info(
                    "Run requires tool outputs",
                    run_id=run_id,
                    tool_call_count=len(tool_calls),
                )
            else:
                # Create assistant message
                if result.response_text:
                    await self._message_service.create_message(
                        thread_id=thread_id,
                        role="assistant",
                        content=result.response_text,
                        assistant_id=assistant.id,
                        run_id=run_id,
                    )

                # Complete the run
                usage: RunUsage | None = None
                if result.usage:
                    usage = {
                        "prompt_tokens": result.usage.get("prompt_tokens", 0),
                        "completion_tokens": result.usage.get("completion_tokens", 0),
                        "total_tokens": result.usage.get("total_tokens", 0),
                    }

                await self._run_service.complete_run(
                    thread_id,
                    run_id,
                    usage=usage,
                )

                logger.info("Run completed", run_id=run_id)

            return result

        except Exception as e:
            logger.error(
                "Run execution failed",
                run_id=run_id,
                error=str(e),
                exc_info=True,
            )

            await self._run_service.fail_run(
                thread_id,
                run_id,
                error={"code": "execution_error", "message": str(e)},
            )

            return None

    async def submit_tool_outputs(
        self,
        thread_id: str,
        run_id: str,
        tool_outputs: list[ToolOutput],
    ) -> ExecutionResult | None:
        """Submit tool outputs and continue execution.

        Args:
            thread_id: Thread ID containing the run.
            run_id: Run ID to continue.
            tool_outputs: Tool outputs from client.

        Returns:
            Execution result or None if run not found.
        """
        # Resume the run
        run = await self._run_service.submit_tool_outputs(thread_id, run_id)
        if not run:
            logger.warning(
                "Run not found for tool outputs",
                thread_id=thread_id,
                run_id=run_id,
            )
            return None

        # Get assistant
        assistant = await self._assistant_service.get_assistant(run.assistant_id)
        if not assistant:
            logger.error(
                "Assistant not found for run",
                assistant_id=run.assistant_id,
                run_id=run_id,
            )
            await self._run_service.fail_run(
                thread_id,
                run_id,
                error={"code": "assistant_not_found", "message": "Assistant not found"},
            )
            return None

        try:
            # Continue execution with tool outputs
            result = await self._execute_with_sdk(
                thread_id,
                run,
                assistant,
                tool_outputs=tool_outputs,
            )

            if result.tool_calls:
                # More tool calls needed
                tool_calls: list[ToolCall] = []
                for tc in result.tool_calls:
                    if isinstance(tc, dict):
                        tool_calls.append(_extract_tool_call(tc))

                await self._run_service.require_action(
                    thread_id,
                    run_id,
                    tool_calls=tool_calls,
                )
            else:
                # Create assistant message
                if result.response_text:
                    await self._message_service.create_message(
                        thread_id=thread_id,
                        role="assistant",
                        content=result.response_text,
                        assistant_id=assistant.id,
                        run_id=run_id,
                    )

                # Complete the run
                usage: RunUsage | None = None
                if result.usage:
                    usage = {
                        "prompt_tokens": result.usage.get("prompt_tokens", 0),
                        "completion_tokens": result.usage.get("completion_tokens", 0),
                        "total_tokens": result.usage.get("total_tokens", 0),
                    }

                await self._run_service.complete_run(
                    thread_id,
                    run_id,
                    usage=usage,
                )

            return result

        except Exception as e:
            logger.error(
                "Run continuation failed",
                run_id=run_id,
                error=str(e),
                exc_info=True,
            )

            await self._run_service.fail_run(
                thread_id,
                run_id,
                error={"code": "execution_error", "message": str(e)},
            )

            return None

    async def stream_run(
        self,
        thread_id: str,
        run_id: str,
    ) -> AsyncIterator[dict[str, object]]:
        """Stream run execution.

        Args:
            thread_id: Thread ID containing the run.
            run_id: Run ID to execute.

        Yields:
            SSE events for the run execution.
        """
        # Start the run
        run = await self._run_service.start_run(thread_id, run_id)
        if not run:
            logger.warning(
                "Run not found",
                thread_id=thread_id,
                run_id=run_id,
            )
            return

        # Get assistant
        assistant = await self._assistant_service.get_assistant(run.assistant_id)
        if not assistant:
            logger.error(
                "Assistant not found for run",
                assistant_id=run.assistant_id,
                run_id=run_id,
            )
            yield {"type": "error", "error": "Assistant not found"}
            return

        try:
            # Stream from SDK
            async for event in self._stream_with_sdk(thread_id, run, assistant):
                yield event

        except Exception as e:
            logger.error(
                "Streaming execution failed",
                run_id=run_id,
                error=str(e),
                exc_info=True,
            )

            await self._run_service.fail_run(
                thread_id,
                run_id,
                error={"code": "execution_error", "message": str(e)},
            )

            yield {"type": "error", "error": str(e)}

    async def _get_thread_messages(
        self,
        thread_id: str,
    ) -> list["Message"]:
        """Get thread messages for context.

        Args:
            thread_id: Thread ID to get messages from.

        Returns:
            List of messages in chronological order.
        """
        result = await self._message_service.list_messages(
            thread_id,
            limit=100,
            order="asc",
        )
        return result.data

    async def _execute_with_sdk(
        self,
        thread_id: str,
        run: object,
        assistant: object,
        tool_outputs: list[ToolOutput] | None = None,
    ) -> ExecutionResult:
        """Execute with Claude Agent SDK.

        This method should be mocked in tests.
        In production, it calls the actual Claude Agent SDK.

        Args:
            thread_id: Thread ID for context.
            run: Run object.
            assistant: Assistant object.
            tool_outputs: Optional tool outputs to continue with.

        Returns:
            Execution result.
        """
        # Get thread messages for context
        messages = await self._get_thread_messages(thread_id)

        # Build prompt from messages
        prompt_parts: list[str] = []
        for msg in messages:
            role = getattr(msg, "role", "user")
            content = getattr(msg, "content", [])
            text = ""
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_data = block.get("text", {})
                    if isinstance(text_data, dict):
                        text = text_data.get("value", "")
                    break
            if text:
                prompt_parts.append(f"{role.upper()}: {text}")

        # Build prompt from message parts
        # Note: prompt, system_prompt, tools are prepared for SDK integration
        _ = "\n\n".join(prompt_parts)  # prompt (for SDK)

        # Get instructions from assistant or run override
        instructions = getattr(run, "instructions", None) or getattr(
            assistant, "instructions", None
        )

        # Build system prompt (for SDK)
        _ = instructions or ""  # system_prompt

        # Get tools from assistant (for SDK)
        tools = getattr(assistant, "tools", [])

        logger.info(
            "Executing with SDK",
            thread_id=thread_id,
            run_id=getattr(run, "id", ""),
            message_count=len(messages),
            has_tools=len(tools) > 0,
            has_tool_outputs=tool_outputs is not None,
        )

        # In production, this would call the actual Claude Agent SDK
        # For now, return a mock result that indicates SDK should be called
        # The actual SDK integration will be done when we wire up the routes

        # This is a placeholder that will be replaced by actual SDK calls
        # Tests mock this method to control the execution flow
        raise NotImplementedError(
            "SDK execution not implemented. "
            "This method should be mocked in tests or implemented with actual SDK calls."
        )

    async def _stream_with_sdk(
        self,
        thread_id: str,
        run: object,
        assistant: object,
    ) -> AsyncIterator[dict[str, object]]:
        """Stream execution with Claude Agent SDK.

        This method should be mocked in tests.
        In production, it streams from the actual Claude Agent SDK.

        Args:
            thread_id: Thread ID for context.
            run: Run object.
            assistant: Assistant object.

        Yields:
            SSE events from SDK execution.
        """
        # Mark parameters as used for type checker
        _ = (thread_id, run, assistant)

        # This is a placeholder that will be replaced by actual SDK streaming
        # Tests mock this method to control the execution flow
        # Yield an error event and then raise to indicate not implemented
        yield {"type": "error", "error": "SDK streaming not implemented"}
        raise NotImplementedError(
            "SDK streaming not implemented. "
            "This method should be mocked in tests or implemented with actual SDK calls."
        )
