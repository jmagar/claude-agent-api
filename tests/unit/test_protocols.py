"""Unit tests for protocol interfaces."""

from typing import Protocol

from apps.api.protocols import SessionRepository


def test_session_repository_protocol_is_protocol() -> None:
    """Ensure SessionRepository is a typing.Protocol."""
    assert issubclass(SessionRepository, Protocol)
