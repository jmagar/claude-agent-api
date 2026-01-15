"""Model mapping service for OpenAI compatibility."""

from apps.api.schemas.openai.responses import OpenAIModelInfo


class ModelMapper:
    """Maps between OpenAI model names and Claude model names."""

    def __init__(self, mapping: dict[str, str]) -> None:
        """Initialize ModelMapper with bidirectional mapping.

        Args:
            mapping: Dictionary mapping OpenAI model names to Claude model names.
                    Example: {"gpt-4": "sonnet", "gpt-3.5-turbo": "haiku"}
        """
        self._openai_to_claude = mapping
        self._claude_to_openai = {v: k for k, v in mapping.items()}

    def to_claude(self, openai_model: str) -> str:
        """Convert OpenAI model name to Claude model name.

        Args:
            openai_model: OpenAI model name (e.g., "gpt-4")

        Returns:
            Claude model name (e.g., "sonnet")

        Raises:
            ValueError: If the OpenAI model is not recognized
        """
        if openai_model not in self._openai_to_claude:
            raise ValueError(f"Unknown OpenAI model: {openai_model}")
        return self._openai_to_claude[openai_model]

    def to_openai(self, claude_model: str) -> str:
        """Convert Claude model name to OpenAI model name.

        Args:
            claude_model: Claude model name (e.g., "sonnet")

        Returns:
            OpenAI model name (e.g., "gpt-4")

        Raises:
            ValueError: If the Claude model is not recognized
        """
        if claude_model not in self._claude_to_openai:
            raise ValueError(f"Unknown Claude model: {claude_model}")
        return self._claude_to_openai[claude_model]

    def list_models(self) -> list[OpenAIModelInfo]:
        """List all available OpenAI-compatible models.

        Returns:
            List of model information dictionaries with OpenAI format:
            - id: Model identifier (OpenAI model name)
            - object: Always "model"
            - created: Unix timestamp (static value)
            - owned_by: Owner identifier (static value)
        """
        return [
            OpenAIModelInfo(
                id=openai_model,
                object="model",
                created=1700000000,
                owned_by="claude-agent-api",
            )
            for openai_model in self._openai_to_claude
        ]
