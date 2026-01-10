"""<summary>Discover slash commands for agent sessions.</summary>"""

from pathlib import Path

from apps.api.schemas.responses import CommandInfoSchema
from apps.api.services.commands import CommandsService


class CommandDiscovery:
    """<summary>Discovers slash commands and exposes the CommandsService.</summary>"""

    def __init__(self, project_path: Path) -> None:
        """<summary>Initialize with a project path.</summary>"""
        self._commands_service = CommandsService(project_path=project_path)

    @property
    def commands_service(self) -> CommandsService:
        """<summary>Return the commands service instance.</summary>"""
        return self._commands_service

    def discover_commands(self) -> list[CommandInfoSchema]:
        """<summary>Return discovered commands as schema objects.</summary>"""
        discovered = self._commands_service.discover_commands()
        return [
            CommandInfoSchema(name=cmd["name"], path=cmd["path"]) for cmd in discovered
        ]
