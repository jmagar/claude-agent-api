"""Tests for QueryRequest schema."""

from typing import cast

import pytest
from pydantic import HttpUrl, ValidationError

from apps.api.schemas.requests.config import HooksConfigSchema, HookWebhookSchema
from apps.api.schemas.requests.query import QueryRequest


class TestQueryRequest:
    """Tests for QueryRequest schema."""

    def test_valid_minimal_query(self) -> None:
        """Test valid minimal query."""
        query = QueryRequest(prompt="Hello")
        assert query.prompt == "Hello"
        assert query.session_id is None

    def test_valid_query_with_model(self) -> None:
        """Test valid query with model."""
        query = QueryRequest(prompt="Hello", model="sonnet")
        assert query.model == "sonnet"

    def test_invalid_empty_prompt(self) -> None:
        """Test empty prompt is invalid."""
        with pytest.raises(ValidationError):
            QueryRequest(prompt="")

    def test_invalid_model(self) -> None:
        """Test invalid model raises error."""
        with pytest.raises(ValidationError, match="Invalid model"):
            QueryRequest(prompt="Hello", model="gpt-4")

    def test_valid_allowed_tools(self) -> None:
        """Test valid allowed tools."""
        query = QueryRequest(
            prompt="Hello", allowed_tools=["Read", "Write", "mcp__server__tool"]
        )
        assert len(query.allowed_tools) == 3

    def test_invalid_allowed_tools(self) -> None:
        """Test invalid tool names."""
        with pytest.raises(ValidationError, match="Invalid tool names"):
            QueryRequest(prompt="Hello", allowed_tools=["InvalidTool"])

    def test_tool_conflict(self) -> None:
        """Test conflict between allowed and disallowed tools."""
        with pytest.raises(ValidationError, match="Tool conflict"):
            QueryRequest(
                prompt="Hello", allowed_tools=["Read"], disallowed_tools=["Read"]
            )

    def test_query_with_hooks(self) -> None:
        """Test query with hooks configuration."""
        query = QueryRequest(
            prompt="Hello",
            hooks=HooksConfigSchema(
                PreToolUse=HookWebhookSchema(
                    url=cast("HttpUrl", "https://example.com/hook")
                )
            ),
        )
        assert query.hooks is not None
        assert query.hooks.pre_tool_use is not None

    def test_cwd_path_traversal_rejected(self) -> None:
        """Test path traversal in cwd is rejected (T128)."""
        with pytest.raises(ValidationError, match="Path traversal"):
            QueryRequest(prompt="Hello", cwd="../etc/passwd")

    def test_cwd_null_byte_rejected(self) -> None:
        """Test null bytes in cwd are rejected (T128)."""
        with pytest.raises(ValidationError, match="Null bytes"):
            QueryRequest(prompt="Hello", cwd="/safe/path\x00/inject")

    def test_add_dirs_path_traversal_rejected(self) -> None:
        """Test path traversal in add_dirs is rejected (T128)."""
        with pytest.raises(ValidationError, match="Path traversal"):
            QueryRequest(prompt="Hello", add_dirs=["../sensitive"])

    def test_add_dirs_null_byte_rejected(self) -> None:
        """Test null bytes in add_dirs are rejected (T128)."""
        with pytest.raises(ValidationError, match="Null bytes"):
            QueryRequest(prompt="Hello", add_dirs=["/path\x00/inject"])

    def test_env_null_byte_rejected(self) -> None:
        """Test null bytes in env are rejected (T128)."""
        with pytest.raises(ValidationError, match="Null bytes"):
            QueryRequest(prompt="Hello", env={"KEY\x00": "value"})

    def test_env_dangerous_var_rejected(self) -> None:
        """Test dangerous env vars are rejected (T128)."""
        with pytest.raises(ValidationError, match="LD_PRELOAD"):
            QueryRequest(prompt="Hello", env={"LD_PRELOAD": "/lib/malicious.so"})

    def test_env_path_var_rejected(self) -> None:
        """Test PATH env var is rejected (T128)."""
        with pytest.raises(ValidationError, match="PATH"):
            QueryRequest(prompt="Hello", env={"PATH": "/malicious/bin"})
