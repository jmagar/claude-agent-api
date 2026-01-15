"""Request translator for OpenAI to Claude Agent SDK format conversion."""

from apps.api.schemas.openai.requests import ChatCompletionRequest
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

        # Concatenate messages with role prefixes
        prompt_parts = []
        for msg in request.messages:
            role_upper = msg.role.upper()
            prompt_parts.append(f"{role_upper}: {msg.content}\n\n")

        prompt = "".join(prompt_parts)

        # Create QueryRequest with minimal required fields
        return QueryRequest(
            prompt=prompt,
            model=claude_model,
        )
