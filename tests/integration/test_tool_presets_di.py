"""Integration tests for tool presets route dependency injection."""

import inspect

import pytest

from apps.api.routes import tool_presets


def test_list_tool_presets_uses_di_signature() -> None:
    """Verify list_tool_presets uses DI for tool_preset_service."""
    sig = inspect.signature(tool_presets.list_tool_presets)
    params = list(sig.parameters.keys())
    assert "tool_preset_service" in params
    assert "cache" not in params


def test_create_tool_preset_uses_di_signature() -> None:
    """Verify create_tool_preset uses DI for tool_preset_service."""
    sig = inspect.signature(tool_presets.create_tool_preset)
    params = list(sig.parameters.keys())
    assert "tool_preset_service" in params
    assert "cache" not in params


def test_get_tool_preset_uses_di_signature() -> None:
    """Verify get_tool_preset uses DI for tool_preset_service."""
    sig = inspect.signature(tool_presets.get_tool_preset)
    params = list(sig.parameters.keys())
    assert "tool_preset_service" in params
    assert "cache" not in params


def test_update_tool_preset_uses_di_signature() -> None:
    """Verify update_tool_preset uses DI for tool_preset_service."""
    sig = inspect.signature(tool_presets.update_tool_preset)
    params = list(sig.parameters.keys())
    assert "tool_preset_service" in params
    assert "cache" not in params


def test_delete_tool_preset_uses_di_signature() -> None:
    """Verify delete_tool_preset uses DI for tool_preset_service."""
    sig = inspect.signature(tool_presets.delete_tool_preset)
    params = list(sig.parameters.keys())
    assert "tool_preset_service" in params
    assert "cache" not in params
