"""Model mapping service for Claude API compatibility."""

from apps.api.schemas.openai.responses import OpenAIModelInfo

# Claude model definitions with full names
# Short aliases map to the actual model identifiers used by Claude Code CLI
# See: https://code.claude.com/docs/en/model-config
CLAUDE_MODELS: dict[str, str] = {
    "claude-sonnet-4-5-20250929": "sonnet",  # Sonnet 4.5
    "claude-opus-4-5-20251101": "opus",  # Opus 4.5
    "claude-haiku-4-5-20251001": "haiku",  # Haiku 4.5
}

# Reverse lookup: short name -> full name
CLAUDE_ALIASES: dict[str, str] = {v: k for k, v in CLAUDE_MODELS.items()}


class ModelMapper:
    """Maps model names to Claude model identifiers."""

    def __init__(self, models: dict[str, str] | None = None) -> None:
        """Initialize ModelMapper with Claude models.

        Args:
            models: Optional custom model mapping. If not provided, uses
                   default Claude models.
        """
        self._models = models if models is not None else CLAUDE_MODELS
        self._aliases = {v: k for k, v in self._models.items()}
        # All valid model names (both full and short)
        self._valid_names = set(self._models.keys()) | set(self._aliases.keys())

    def to_claude(self, model: str) -> str:
        """Get the Claude CLI model identifier for a model name.

        Accepts both full model names (e.g., "claude-sonnet-4-5-20250929")
        and short aliases (e.g., "sonnet"). Returns the short alias that
        the Claude Code CLI expects.

        Args:
            model: Model name (full or alias)

        Returns:
            Claude CLI model identifier (e.g., "sonnet")

        Raises:
            ValueError: If the model is not recognized
        """
        # If it's a full model name, return the alias
        if model in self._models:
            return self._models[model]

        # If it's already an alias, return as-is
        if model in self._aliases:
            return model

        raise ValueError(f"Unknown model: {model}")

    def to_full_name(self, model: str) -> str:
        """Get the full model name for any model identifier.

        Args:
            model: Model name (full or alias)

        Returns:
            Full model name (e.g., "claude-sonnet-4-5-20250929")

        Raises:
            ValueError: If the model is not recognized
        """
        # If it's already a full name, return as-is
        if model in self._models:
            return model

        # If it's an alias, look up the full name
        if model in self._aliases:
            return self._aliases[model]

        raise ValueError(f"Unknown model: {model}")

    def list_models(self) -> list[OpenAIModelInfo]:
        """List all available Claude models.

        Returns:
            List of model information in OpenAI-compatible format.
        """
        return [
            OpenAIModelInfo(
                id=full_name,
                object="model",
                created=1700000000,
                owned_by="anthropic",
            )
            for full_name in self._models.keys()
        ]

    def get_model_info(self, model: str) -> OpenAIModelInfo:
        """Get model information for a specific model.

        Accepts both full names and short aliases.

        Args:
            model: Model name (full or alias)

        Returns:
            OpenAI-formatted model information.

        Raises:
            ValueError: If the model is not recognized
        """
        full_name = self.to_full_name(model)
        return OpenAIModelInfo(
            id=full_name,
            object="model",
            created=1700000000,
            owned_by="anthropic",
        )
