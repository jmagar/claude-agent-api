"""Tests for memory protocol interface."""
import pytest
from apps.api.protocols import MemoryProtocol


def test_memory_protocol_has_required_methods() -> None:
    """Memory protocol must define search, add, get_all, delete methods."""
    assert hasattr(MemoryProtocol, "search")
    assert hasattr(MemoryProtocol, "add")
    assert hasattr(MemoryProtocol, "get_all")
    assert hasattr(MemoryProtocol, "delete")
    assert hasattr(MemoryProtocol, "delete_all")
