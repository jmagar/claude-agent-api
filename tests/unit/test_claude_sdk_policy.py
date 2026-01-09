"""Tests for Claude SDK mocking policy."""

from unittest.mock import MagicMock

import claude_agent_sdk


def test_claude_sdk_is_mocked_by_default() -> None:
    """Ensure Claude SDK client is mocked for non-e2e tests."""
    assert isinstance(claude_agent_sdk.ClaudeSDKClient, MagicMock)
