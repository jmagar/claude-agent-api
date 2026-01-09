"""Utility functions for agent service."""

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
