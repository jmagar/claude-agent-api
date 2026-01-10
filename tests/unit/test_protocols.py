"""Unit tests for protocol interfaces."""

from typing import Protocol

from apps.api.protocols import SessionRepositoryProtocol


def test_session_repository_protocol_is_protocol() -> None:
    """Ensure SessionRepositoryProtocol is a typing.Protocol."""
    assert issubclass(SessionRepositoryProtocol, Protocol)
