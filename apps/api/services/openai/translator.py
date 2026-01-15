"""Request translator for OpenAI to Claude Agent SDK format conversion."""

from apps.api.schemas.openai.requests import ChatCompletionRequest, OpenAIMessage
from apps.api.schemas.requests.query import QueryRequest
from apps.api.services.openai.models import ModelMapper


class RequestTranslator:
    """Translates OpenAI chat completion requests to Claude Agent SDK QueryRequest format."""

    def __init__(self, model_mapper: ModelMapper) -> None:
        """Initialize RequestTranslator with model mapping.

        Args:
            model_mapper: ModelMapper instance for converting model names
        """
        self._model_mapper = model_mapper

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
        return QueryRequest(
            prompt=prompt,
            model=claude_model,
            system_prompt=system_prompt,
        )
