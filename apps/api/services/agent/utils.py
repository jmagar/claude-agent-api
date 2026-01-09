"""Utility functions for agent service."""

import os
import re

# Pattern for ${VAR} or ${VAR:-default} environment variable syntax
_ENV_VAR_PATTERN = re.compile(r"\$\{([^}:]+)(?::-([^}]*))?\}")

# Pattern for slash command detection (T115a)
# Matches prompts starting with / followed by alphanumeric characters, dashes, or underscores
_SLASH_COMMAND_PATTERN = re.compile(r"^/([a-zA-Z][a-zA-Z0-9_-]*)")


def resolve_env_var(value: str) -> str:
    """Resolve environment variables in a string.

    Supports ${VAR} and ${VAR:-default} syntax.

    Args:
        value: String that may contain environment variable references.

    Returns:
        String with environment variables resolved.
    """

    def replace_match(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default_value = match.group(2) if match.group(2) is not None else ""
        return os.environ.get(var_name, default_value)

    return _ENV_VAR_PATTERN.sub(replace_match, value)


def resolve_env_dict(env: dict[str, str]) -> dict[str, str]:
    """Resolve environment variables in all values of a dictionary.

    Args:
        env: Dictionary with values that may contain environment variable references.

    Returns:
        Dictionary with all values resolved.
    """
    return {key: resolve_env_var(value) for key, value in env.items()}


def detect_slash_command(prompt: str) -> str | None:
    """Detect if a prompt starts with a slash command (T115a).

    Slash commands are prompts that start with / followed by a command name.
    Examples: /help, /clear, /commit, /review-pr

    Args:
        prompt: The user prompt to check.

    Returns:
        The command name (without /) if detected, None otherwise.
    """
    match = _SLASH_COMMAND_PATTERN.match(prompt.strip())
    return match.group(1) if match else None
