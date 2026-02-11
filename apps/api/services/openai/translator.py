"""Request translator for OpenAI to Claude Agent SDK format conversion."""

import time
import uuid
from typing import Literal, cast

import structlog

from apps.api.exceptions.base import APIError
from apps.api.protocols import ModelMapper
from apps.api.schemas.openai.requests import (
    ChatCompletionRequest,
    OpenAIContentPart,
    OpenAIMessage,
)
from apps.api.schemas.openai.responses import (
    OpenAIChatCompletion,
    OpenAIChoice,
    OpenAIResponseMessage,
    OpenAIUsage,
)
from apps.api.schemas.requests.query import QueryRequest
from apps.api.schemas.responses import SingleQueryResponse
from apps.api.services.openai.tools import ToolTranslator

logger = structlog.get_logger(__name__)

# Singleton tool translator instance
_tool_translator = ToolTranslator()


def _extract_text_content(content: str | list[OpenAIContentPart] | None) -> str:
    """Extract text from message content regardless of format.

    Args:
        content: Message content (string or array of content parts)

    Returns:
        Text content as a string (empty string if None)
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    # Array of content parts - extract text from text parts
    text_parts: list[str] = []
    for part in content:
        if part.type == "text" and part.text:
            text_parts.append(part.text)
    return "\n".join(text_parts)


class RequestTranslator:
    """Translates OpenAI chat completion requests to Claude Agent SDK QueryRequest format."""

    def __init__(self, model_mapper: ModelMapper) -> None:
        """Initialize RequestTranslator with model mapping.

        Args:
            model_mapper: ModelMapper instance for converting model names
        """
        self._model_mapper = model_mapper

    def _log_unsupported_parameter(self, parameter_name: str) -> None:
        """Log WARNING for unsupported OpenAI parameter.

        Helper function to log structured warnings when OpenAI parameters
        are not supported by Claude Agent SDK.

        Args:
            parameter_name: Name of the unsupported parameter
        """
        logger.warning(
            "Parameter not supported by Claude Agent SDK, ignoring",
            parameter=parameter_name,
        )

    def _separate_system_messages(
        self, messages: list[OpenAIMessage]
    ) -> tuple[str | None, list[OpenAIMessage]]:
        """Separate system messages from conversation messages.

        Extracts all system role messages and combines them into a single system_prompt.
        Returns remaining user/assistant/tool messages for conversation prompt.

        Args:
            messages: List of OpenAI messages

        Returns:
            Tuple of (system_prompt, conversation_messages)
            - system_prompt: Combined system messages joined with "\n\n", or None if no system messages
            - conversation_messages: List of non-system messages (user/assistant/tool)
        """
        system_messages: list[str] = []
        conversation_messages: list[OpenAIMessage] = []

        for msg in messages:
            if msg.role == "system":
                text = _extract_text_content(msg.content)
                if text:
                    system_messages.append(text)
            else:
                conversation_messages.append(msg)

        # Build system_prompt from system messages
        system_prompt = None
        if system_messages:
            system_prompt = "\n\n".join(system_messages)

        return system_prompt, conversation_messages

    def _concatenate_messages(self, messages: list[OpenAIMessage]) -> str:
        """Concatenate user/assistant/tool messages with role prefixes.

        Converts list of OpenAI messages into a single prompt string with role prefixes.
        Each message is formatted as "ROLE: content\n\n".

        Strategy:
        - User messages → "USER: content\n\n"
        - Assistant messages → "ASSISTANT: content\n\n"
        - Tool messages → "TOOL_RESULT: content\n\n"
        - Assistant messages with tool_calls → formatted tool call representation
        - System messages should be filtered out before calling

        Edge cases handled:
        - Empty message list returns empty string
        - Empty content in message is preserved as "ROLE: \n\n"
        - Role is uppercased for consistency
        - Tool calls are formatted as function invocations

        Args:
            messages: List of OpenAI messages (user/assistant/tool only)

        Returns:
            Concatenated prompt string with role prefixes
        """
        # Handle edge case: empty message list
        if not messages:
            return ""

        # Concatenate messages with role prefixes
        prompt_parts: list[str] = []
        for msg in messages:
            if msg.role == "tool":
                # Tool result message
                tool_id = msg.tool_call_id or "unknown"
                func_name = msg.name or "unknown"
                content_text = _extract_text_content(msg.content)
                prompt_parts.append(
                    f"TOOL_RESULT ({func_name}, id={tool_id}): {content_text}\n\n"
                )
            elif msg.role == "assistant" and msg.tool_calls:
                # Assistant message with tool calls
                tool_call_strs: list[str] = []
                for tc in msg.tool_calls:
                    tool_call_strs.append(
                        f"  - {tc.function.name}(id={tc.id}): {tc.function.arguments}"
                    )
                tool_calls_text = "\n".join(tool_call_strs)
                content_text = _extract_text_content(msg.content)
                prompt_parts.append(
                    f"ASSISTANT: {content_text}\n[Tool Calls]\n{tool_calls_text}\n\n"
                )
            else:
                # Regular user or assistant message
                role_upper = msg.role.upper()
                content_text = _extract_text_content(msg.content)
                prompt_parts.append(f"{role_upper}: {content_text}\n\n")

        return "".join(prompt_parts)

    def translate(
        self,
        request: ChatCompletionRequest,
        permission_mode: str | None = None,
    ) -> QueryRequest:
        """Translate OpenAI ChatCompletionRequest to Claude QueryRequest.

        Args:
            request: OpenAI chat completion request
            permission_mode: Optional permission mode override from X-Permission-Mode header

        Returns:
            QueryRequest suitable for Claude Agent SDK

        Raises:
            APIError: If the model name is not recognized
        """
        logger.debug(
            "Starting request translation",
            openai_model=request.model,
            message_count=len(request.messages),
            stream=request.stream,
        )

        # Map model name
        try:
            claude_model = self._model_mapper.to_claude(request.model)
        except ValueError as exc:
            raise APIError(
                message=str(exc),
                code="MODEL_NOT_FOUND",
                status_code=400,
            ) from exc

        # Log warnings for unsupported parameters (SDK doesn't support sampling controls)
        if request.max_tokens is not None:
            self._log_unsupported_parameter("max_tokens")

        if request.temperature is not None:
            self._log_unsupported_parameter("temperature")

        if request.top_p is not None:
            self._log_unsupported_parameter("top_p")

        if request.stop is not None:
            self._log_unsupported_parameter("stop")

        # Separate system messages from user/assistant messages
        system_prompt, conversation_messages = self._separate_system_messages(
            request.messages
        )

        # Concatenate user/assistant messages with role prefixes
        prompt = self._concatenate_messages(conversation_messages)

        if not prompt:
            raise APIError(
                message="At least one user or assistant message is required",
                code="VALIDATION_ERROR",
                status_code=400,
            )

        # Create QueryRequest with system_prompt if present
        # NOTE: We do NOT set max_turns when max_tokens is present because they have
        # incompatible semantics: max_tokens limits output tokens, max_turns limits
        # conversation turns. There's no reliable conversion between them.

        # Use provided permission_mode or default to "default" for OpenAI compatibility
        final_permission_mode: Literal[
            "default", "acceptEdits", "plan", "bypassPermissions"
        ] = "default"
        if permission_mode in ("default", "acceptEdits", "plan", "bypassPermissions"):
            final_permission_mode = cast(
                "Literal['default', 'acceptEdits', 'plan', 'bypassPermissions']",
                permission_mode,
            )

        query_request = QueryRequest(
            prompt=prompt,
            model=claude_model,
            system_prompt=system_prompt,
            user=request.user,  # SUPPORTED: User identifier for tracking
            permission_mode=final_permission_mode,
            # setting_sources defaults to None - allows explicit mcp_servers without auto-loading
        )

        logger.info(
            "Request translation complete",
            claude_model=claude_model,
            has_system_prompt=system_prompt is not None,
            conversation_message_count=len(conversation_messages),
        )

        return query_request


class ResponseTranslator:
    """Translates Claude Agent SDK responses to OpenAI chat completion format."""

    def _map_stop_reason(
        self, stop_reason: str | None, has_tool_calls: bool = False
    ) -> Literal["stop", "length", "tool_calls", "error"]:
        """Map Claude Agent SDK stop_reason to OpenAI finish_reason.

        Args:
            stop_reason: Claude Agent SDK stop_reason value
            has_tool_calls: Whether the response contains tool_use blocks

        Returns:
            OpenAI finish_reason: "stop", "length", "tool_calls", or "error"

        Mapping:
            - completed → stop (or tool_calls if has_tool_calls)
            - max_turns_reached → length
            - interrupted → stop
            - error → error
            - None → stop (default)
        """
        # If response has tool calls, finish_reason should be "tool_calls"
        if has_tool_calls:
            return "tool_calls"

        if stop_reason == "completed":
            return "stop"
        if stop_reason == "max_turns_reached":
            return "length"
        if stop_reason == "interrupted":
            return "stop"
        if stop_reason == "error":
            return "error"
        # Default to "stop" if unknown
        return "stop"

    def translate(
        self, response: SingleQueryResponse, original_model: str
    ) -> OpenAIChatCompletion:
        """Translate SingleQueryResponse to OpenAI ChatCompletion format.

        Args:
            response: Claude Agent SDK SingleQueryResponse
            original_model: Original OpenAI model name requested (e.g., "gpt-4")

        Returns:
            OpenAIChatCompletion dict with OpenAI-compatible structure
        """
        logger.debug(
            "Starting response translation",
            claude_model=response.model,
            content_block_count=len(response.content),
            stop_reason=response.stop_reason,
        )

        # Generate unique completion ID
        completion_id = f"chatcmpl-{uuid.uuid4()}"

        # Convert content blocks to dicts for tool translator
        content_dicts: list[dict[str, object]] = []
        for block in response.content:
            block_dict: dict[str, object] = {"type": block.type}
            if block.text:
                block_dict["text"] = block.text
            if block.id:
                block_dict["id"] = block.id
            if block.name:
                block_dict["name"] = block.name
            if block.input:
                block_dict["input"] = block.input
            content_dicts.append(block_dict)

        # Check for tool calls and translate them
        has_tool_calls = _tool_translator.has_tool_calls(content_dicts)
        tool_calls = None
        if has_tool_calls:
            tool_calls = _tool_translator.translate_claude_tool_use_to_openai(
                content_dicts
            )

        # Extract text content from content blocks (only type="text")
        text_parts: list[str] = []
        for block in response.content:
            if block.type == "text" and block.text:
                text_parts.append(block.text)

        # Concatenate text blocks with space separator for OpenAI-compatible output
        content = " ".join(text_parts) if text_parts else None

        # Map stop_reason to finish_reason
        finish_reason = self._map_stop_reason(response.stop_reason, has_tool_calls)

        # Build response message
        message: OpenAIResponseMessage = {
            "role": "assistant",
        }
        # Only include content if present (may be None with tool_calls)
        if content is not None:
            message["content"] = content
        else:
            message["content"] = None
        # Include tool_calls if present
        if tool_calls:
            message["tool_calls"] = tool_calls

        # Build choice object
        choice: OpenAIChoice = {
            "index": 0,
            "message": message,
            "finish_reason": finish_reason,
        }

        # Build usage object
        usage: OpenAIUsage = {
            "prompt_tokens": response.usage.input_tokens if response.usage else 0,
            "completion_tokens": response.usage.output_tokens if response.usage else 0,
            "total_tokens": (
                (response.usage.input_tokens + response.usage.output_tokens)
                if response.usage
                else 0
            ),
        }

        # Return the Claude model name from the actual response, not the OpenAI model name
        # The response.model field contains the actual Claude model used (e.g., "sonnet")
        model_name = response.model if response.model else original_model

        # Build OpenAI ChatCompletion response
        completion = OpenAIChatCompletion(
            id=completion_id,
            object="chat.completion",
            created=int(time.time()),
            model=model_name,
            choices=[choice],
            usage=usage,
        )

        logger.info(
            "Response translation complete",
            completion_id=completion_id,
            content_length=len(content) if content else 0,
            finish_reason=finish_reason,
            tool_call_count=len(tool_calls) if tool_calls else 0,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
        )

        return completion
