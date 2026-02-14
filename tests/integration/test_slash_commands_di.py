"""Integration tests for slash commands route dependency injection."""

import inspect

from apps.api.routes import slash_commands


def test_list_slash_commands_uses_di_signature() -> None:
    """Verify list_slash_commands uses DI for slash_command_service."""
    sig = inspect.signature(slash_commands.list_slash_commands)
    params = list(sig.parameters.keys())
    assert "slash_command_service" in params
    assert "cache" not in params


def test_create_slash_command_uses_di_signature() -> None:
    """Verify create_slash_command uses DI for slash_command_service."""
    sig = inspect.signature(slash_commands.create_slash_command)
    params = list(sig.parameters.keys())
    assert "slash_command_service" in params
    assert "cache" not in params


def test_get_slash_command_uses_di_signature() -> None:
    """Verify get_slash_command uses DI for slash_command_service."""
    sig = inspect.signature(slash_commands.get_slash_command)
    params = list(sig.parameters.keys())
    assert "slash_command_service" in params
    assert "cache" not in params


def test_update_slash_command_uses_di_signature() -> None:
    """Verify update_slash_command uses DI for slash_command_service."""
    sig = inspect.signature(slash_commands.update_slash_command)
    params = list(sig.parameters.keys())
    assert "slash_command_service" in params
    assert "cache" not in params


def test_delete_slash_command_uses_di_signature() -> None:
    """Verify delete_slash_command uses DI for slash_command_service."""
    sig = inspect.signature(slash_commands.delete_slash_command)
    params = list(sig.parameters.keys())
    assert "slash_command_service" in params
    assert "cache" not in params
