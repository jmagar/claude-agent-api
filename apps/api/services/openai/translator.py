"""Request translator for OpenAI to Claude Agent SDK format conversion."""

import structlog

from apps.api.schemas.openai.requests import ChatCompletionRequest, OpenAIMessage
from apps.api.schemas.requests.query import QueryRequest
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

    def translate(self, request: ChatCompletionRequest) -> QueryRequest:
        """Translate OpenAI ChatCompletionRequest to Claude QueryRequest.

        Args:
            request: OpenAI chat completion request

        Returns:
            QueryRequest suitable for Claude Agent SDK

        Raises:
            ValueError: If the model name is not recognized
        """
        # Map model name
        claude_model = self._model_mapper.to_claude(request.model)

        # Log warning for max_tokens (unsupported - incompatible with max_turns semantics)
        if request.max_tokens is not None:
            self._log_unsupported_parameter("max_tokens")

        # Separate system messages from user/assistant messages
        system_prompt, conversation_messages = self._separate_system_messages(
            request.messages
        )

        # Concatenate user/assistant messages with role prefixes
        prompt_parts = []
        for msg in conversation_messages:
            role_upper = msg.role.upper()
            prompt_parts.append(f"{role_upper}: {msg.content}\n\n")

        prompt = "".join(prompt_parts)

        # Create QueryRequest with system_prompt if present
        # NOTE: We do NOT set max_turns when max_tokens is present because they have
        # incompatible semantics: max_tokens limits output tokens, max_turns limits
        # conversation turns. There's no reliable conversion between them.
        return QueryRequest(
            prompt=prompt,
            model=claude_model,
            system_prompt=system_prompt,
        )
