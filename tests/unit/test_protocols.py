"""Unit tests for protocol interfaces."""

from typing import get_origin

from apps.api.protocols import SessionRepository


def test_session_repository_protocol_is_protocol() -> None:
    """Ensure SessionRepository is a typing.Protocol."""
    # Check if SessionRepository is a Protocol by checking its _is_protocol attribute
    assert getattr(SessionRepository, "_is_protocol", False) is True
