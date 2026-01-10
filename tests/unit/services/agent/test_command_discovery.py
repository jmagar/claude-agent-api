"""Unit tests for CommandDiscovery."""

from pathlib import Path

from apps.api.services.agent.command_discovery import CommandDiscovery


def test_command_discovery_returns_schema_objects(tmp_path: Path) -> None:
    discovery = CommandDiscovery(project_path=tmp_path)
    commands_service = discovery.commands_service
    assert commands_service.project_path == tmp_path
    assert discovery.discover_commands() == []
