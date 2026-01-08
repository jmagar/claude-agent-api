"""Tests for control request schemas."""

import pytest
from pydantic import ValidationError

from apps.api.schemas.requests.control import ControlRequest, RewindRequest


class TestRewindRequest:
    """Tests for RewindRequest schema."""

    def test_valid_rewind(self) -> None:
        """Test valid rewind request."""
        req = RewindRequest(checkpoint_id="chk_123")
        assert req.checkpoint_id == "chk_123"

    def test_empty_checkpoint_id_invalid(self) -> None:
        """Test empty checkpoint_id is invalid."""
        with pytest.raises(ValidationError):
            RewindRequest(checkpoint_id="")


class TestControlRequest:
    """Tests for ControlRequest schema."""

    def test_valid_permission_mode_change(self) -> None:
        """Test valid permission mode change."""
        req = ControlRequest(
            type="permission_mode_change",
            permission_mode="bypassPermissions"
        )
        assert req.type == "permission_mode_change"
        assert req.permission_mode == "bypassPermissions"

    def test_permission_mode_change_requires_mode(self) -> None:
        """Test permission_mode_change requires permission_mode."""
        with pytest.raises(ValidationError, match="permission_mode is required"):
            ControlRequest(type="permission_mode_change")
