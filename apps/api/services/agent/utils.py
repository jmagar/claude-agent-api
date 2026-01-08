"""Utility functions for agent service."""

import os
import re

# Pattern for ${VAR} or ${VAR:-default} environment variable syntax
_ENV_VAR_PATTERN = re.compile(r"\$\{([^}:]+)(?::-([^}]*))?\}")

# Pattern for slash command detection (T115a)
# Matches prompts starting with / followed by alphanumeric characters, dashes, or underscores
_SLASH_COMMAND_PATTERN = re.compile(r"^/([a-zA-Z][a-zA-Z0-9_-]*)")


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


def resolve_env_var(value: str) -> str:
    """Resolve environment variables in a string.

    Supports ${VAR} and ${VAR:-default} syntax.

    Args:
        value: String potentially containing env var references.

    Returns:
        String with environment variables resolved.
    """

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default = match.group(2)  # May be None if no default specified
        return os.environ.get(var_name, default if default is not None else "")

    return _ENV_VAR_PATTERN.sub(replacer, value)


def resolve_env_dict(env: dict[str, str]) -> dict[str, str]:
    """Resolve environment variables in a dict of strings.

    Args:
        env: Dictionary with string values that may contain env var references.

    Returns:
        Dictionary with all env vars resolved.
    """
    return {key: resolve_env_var(val) for key, val in env.items()}
