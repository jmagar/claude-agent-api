"""Unit tests for slash commands service."""

from pathlib import Path

from apps.api.services.commands import CommandsService


class TestCommandsDiscovery:
    """Test command discovery from filesystem."""

    def test_discover_commands_from_directory(self, tmp_path: Path) -> None:
        """Test discovering commands from .claude/commands/ directory."""
        # Create test command file
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        command_file = commands_dir / "test.md"
        command_file.write_text("""# Test Command

This is a test command.

Arguments: $ARGUMENTS
""")

        # Discover commands
        service = CommandsService(project_path=tmp_path)
        commands = service.discover_commands()

        # Assertions
        assert len(commands) == 1
        assert commands[0]["name"] == "test"
        assert commands[0]["path"] == str(command_file)

    def test_discover_commands_returns_empty_when_no_directory(
        self, tmp_path: Path
    ) -> None:
        """Test discovering commands when .claude/commands/ doesn't exist."""
        service = CommandsService(project_path=tmp_path)
        commands = service.discover_commands()
        assert commands == []


class TestCommandExecution:
    """Test command execution logic."""

    def test_parse_command_with_arguments(self) -> None:
        """Test parsing slash command with arguments."""
        service = CommandsService(project_path=Path.cwd())

        result = service.parse_command("/test arg1 arg2")

        assert result is not None
        assert result["command"] == "test"
        assert result["args"] == "arg1 arg2"

    def test_parse_command_without_arguments(self) -> None:
        """Test parsing slash command without arguments."""
        service = CommandsService(project_path=Path.cwd())

        result = service.parse_command("/test")

        assert result is not None
        assert result["command"] == "test"
        assert result["args"] == ""

    def test_parse_command_returns_none_for_non_command(self) -> None:
        """Test parsing non-command string returns None."""
        service = CommandsService(project_path=Path.cwd())

        result = service.parse_command("regular prompt")

        assert result is None
