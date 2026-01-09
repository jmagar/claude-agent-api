"""Slash commands discovery and execution service."""

import re
from pathlib import Path
from typing import TypedDict

import structlog

logger = structlog.get_logger(__name__)


class CommandInfo(TypedDict):
    """Information about a discovered command."""

    name: str
    path: str


class ParsedCommand(TypedDict):
    """Parsed command with name and arguments."""

    command: str
    args: str


class CommandsService:
    """Service for discovering and executing slash commands."""

    def __init__(self, project_path: Path | str) -> None:
        """Initialize commands service.

        Args:
            project_path: Path to project root containing .claude/commands/
        """
        self.project_path = Path(project_path)
        self.commands_dir = self.project_path / ".claude" / "commands"

    def discover_commands(self) -> list[CommandInfo]:
        """Discover commands from .claude/commands/ directory.

        Returns:
            List of command info dicts with name and path
        """
        if not self.commands_dir.exists():
            return []

        commands: list[CommandInfo] = []
        for command_file in self.commands_dir.glob("*.md"):
            try:
                commands.append(
                    CommandInfo(
                        name=command_file.stem,
                        path=str(command_file)
                    )
                )
            except (OSError, UnicodeDecodeError, ValueError) as e:
                logger.error(
                    "command_file_discovery_error",
                    file_path=str(command_file),
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                # Continue processing other files
                continue

        return commands

    def parse_command(self, prompt: str) -> ParsedCommand | None:
        """Parse slash command from prompt string.

        Args:
            prompt: User prompt that may start with /command

        Returns:
            ParsedCommand dict or None if not a slash command
        """
        # Use existing detection logic from utils.py to check if it's a slash command
        from apps.api.services.agent.utils import detect_slash_command

        command_name = detect_slash_command(prompt)
        if not command_name:
            return None

        # Extract arguments: everything after the command name
        # Pattern: /command_name followed by optional whitespace and args
        pattern = re.compile(r"^/[a-zA-Z][a-zA-Z0-9_-]*\s*(.*)", re.DOTALL)
        match = pattern.match(prompt.strip())

        args = ""
        if match:
            args = match.group(1).strip()

        return ParsedCommand(
            command=command_name,
            args=args
        )
