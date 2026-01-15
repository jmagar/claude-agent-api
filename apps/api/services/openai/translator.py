"""Request translator for OpenAI to Claude Agent SDK format conversion."""

import time
import uuid
from typing import Literal

import structlog

from apps.api.schemas.openai.requests import ChatCompletionRequest, OpenAIMessage
from apps.api.schemas.openai.responses import (
    OpenAIChatCompletion,
    OpenAIChoice,
    OpenAIResponseMessage,
    OpenAIUsage,
)
from apps.api.schemas.requests.query import QueryRequest
from apps.api.schemas.responses import SingleQueryResponse
from apps.api.services.openai.models import ModelMapper

logger = structlog.get_logger(__name__)


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
        Returns remaining user/assistant messages for conversation prompt.

        Args:
            messages: List of OpenAI messages

        Returns:
            Tuple of (system_prompt, conversation_messages)
            - system_prompt: Combined system messages joined with "\n\n", or None if no system messages
            - conversation_messages: List of non-system messages (user/assistant)
        """
        system_messages = []
        conversation_messages = []

        for msg in messages:
            if msg.role == "system":
                system_messages.append(msg.content)
            else:
                conversation_messages.append(msg)

        # Build system_prompt from system messages
        system_prompt = None
        if system_messages:
            system_prompt = "\n\n".join(system_messages)

        return system_prompt, conversation_messages

    def _concatenate_messages(self, messages: list[OpenAIMessage]) -> str:
        """Concatenate user/assistant messages with role prefixes.

        Converts list of OpenAI messages (user/assistant roles) into a single prompt
        string with role prefixes. Each message is formatted as "ROLE: content\n\n".

        Strategy:
        - User messages → "USER: content\n\n"
        - Assistant messages → "ASSISTANT: content\n\n"
        - System messages should be filtered out before calling (use _separate_system_messages)

        Edge cases handled:
        - Empty message list returns empty string
        - Empty content in message is preserved as "ROLE: \n\n"
        - Role is uppercased for consistency

        Args:
            messages: List of OpenAI messages (typically user/assistant only)

        Returns:
            Concatenated prompt string with role prefixes
        """
        # Handle edge case: empty message list
        if not messages:
            return ""

        # Concatenate messages with role prefixes
        prompt_parts = []
        for msg in messages:
            role_upper = msg.role.upper()
            prompt_parts.append(f"{role_upper}: {msg.content}\n\n")

        return "".join(prompt_parts)

    def translate(self, request: ChatCompletionRequest) -> QueryRequest:
        """Translate OpenAI ChatCompletionRequest to Claude QueryRequest.

        Args:
            request: OpenAI chat completion request

        Returns:
            QueryRequest suitable for Claude Agent SDK

        Raises:
            ValueError: If the model name is not recognized
        """
        logger.debug(
            "Starting request translation",
            openai_model=request.model,
            message_count=len(request.messages),
            stream=request.stream,
        )

        # Map model name
        claude_model = self._model_mapper.to_claude(request.model)

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

        # Create QueryRequest with system_prompt if present
        # NOTE: We do NOT set max_turns when max_tokens is present because they have
        # incompatible semantics: max_tokens limits output tokens, max_turns limits
        # conversation turns. There's no reliable conversion between them.
        query_request = QueryRequest(
            prompt=prompt,
            model=claude_model,
            system_prompt=system_prompt,
            user=request.user,  # SUPPORTED: User identifier for tracking
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
        self, stop_reason: str | None
    ) -> Literal["stop", "length", "error"]:
        """Map Claude Agent SDK stop_reason to OpenAI finish_reason.

        Args:
            stop_reason: Claude Agent SDK stop_reason value

        Returns:
            OpenAI finish_reason: "stop", "length", or "error"

        Mapping:
            - completed → stop
            - max_turns_reached → length
            - interrupted → stop
            - error → error
            - None → stop (default)
        """
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

        # Extract text content from content blocks (only type="text")
        text_parts = []
        for block in response.content:
            if block.type == "text" and block.text:
                text_parts.append(block.text)

        # Concatenate text blocks with space separator
        content = " ".join(text_parts)

        # Map stop_reason to finish_reason
        finish_reason = self._map_stop_reason(response.stop_reason)

        # Build response message
        message: OpenAIResponseMessage = {
            "role": "assistant",
            "content": content,
        }

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
            content_length=len(content),
            finish_reason=finish_reason,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
        )

        return completion
