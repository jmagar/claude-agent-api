"""Tests for schema validators."""

import pytest

from apps.api.schemas.validators import (
    BLOCKED_URL_PATTERNS,
    NULL_BYTE_PATTERN,
    PATH_TRAVERSAL_PATTERN,
    SHELL_METACHAR_PATTERN,
    validate_model_name,
    validate_no_null_bytes,
    validate_no_path_traversal,
    validate_tool_name,
    validate_url_not_internal,
)


class TestSecurityPatterns:
    """Tests for security regex patterns."""

    def test_shell_metachar_pattern(self) -> None:
        """Test shell metacharacter pattern."""
        assert SHELL_METACHAR_PATTERN.search(";echo") is not None
        assert SHELL_METACHAR_PATTERN.search("|cat") is not None
        assert SHELL_METACHAR_PATTERN.search("$(cmd)") is not None
        assert SHELL_METACHAR_PATTERN.search("safe_command") is None

    def test_path_traversal_pattern(self) -> None:
        """Test path traversal pattern."""
        assert PATH_TRAVERSAL_PATTERN.search("../etc/passwd") is not None
        assert PATH_TRAVERSAL_PATTERN.search("%2e%2e%2f") is not None
        assert PATH_TRAVERSAL_PATTERN.search("/safe/path") is None

    def test_null_byte_pattern(self) -> None:
        """Test null byte pattern."""
        assert NULL_BYTE_PATTERN.search("test\x00inject") is not None
        assert NULL_BYTE_PATTERN.search("safe_string") is None

    def test_blocked_url_patterns(self) -> None:
        """Test blocked URL patterns tuple."""
        assert "localhost" in BLOCKED_URL_PATTERNS
        assert "127.0.0.1" in BLOCKED_URL_PATTERNS
        assert "169.254." in BLOCKED_URL_PATTERNS
        assert "metadata.google.internal" in BLOCKED_URL_PATTERNS


class TestValidateNoNullBytes:
    """Tests for validate_no_null_bytes function."""

    def test_valid_string(self) -> None:
        """Test valid string passes."""
        result = validate_no_null_bytes("safe_string", "test_field")
        assert result == "safe_string"

    def test_null_byte_raises(self) -> None:
        """Test null bytes raise ValueError."""
        with pytest.raises(ValueError, match="Null bytes not allowed in test_field"):
            validate_no_null_bytes("test\x00inject", "test_field")


class TestValidateNoPathTraversal:
    """Tests for validate_no_path_traversal function."""

    def test_valid_path(self) -> None:
        """Test valid path passes."""
        result = validate_no_path_traversal("/safe/path", "test_field")
        assert result == "/safe/path"

    def test_path_traversal_raises(self) -> None:
        """Test path traversal raises ValueError."""
        with pytest.raises(ValueError, match="Path traversal not allowed"):
            validate_no_path_traversal("../etc/passwd", "test_field")

    def test_encoded_path_traversal_raises(self) -> None:
        """Test encoded path traversal raises ValueError."""
        with pytest.raises(ValueError, match="Path traversal not allowed"):
            validate_no_path_traversal("%2e%2e%2fetc/passwd", "test_field")


class TestValidateUrlNotInternal:
    """Tests for validate_url_not_internal function."""

    def test_valid_external_url(self) -> None:
        """Test valid external URL passes."""
        result = validate_url_not_internal("https://example.com/api")
        assert result == "https://example.com/api"

    def test_localhost_raises(self) -> None:
        """Test localhost raises ValueError."""
        with pytest.raises(ValueError, match="internal resources"):
            validate_url_not_internal("http://localhost:8080")

    def test_private_ip_raises(self) -> None:
        """Test private IPs raise ValueError."""
        with pytest.raises(ValueError, match="internal resources"):
            validate_url_not_internal("http://192.168.1.1/api")

    def test_metadata_url_raises(self) -> None:
        """Test cloud metadata URLs raise ValueError."""
        with pytest.raises(ValueError, match="internal resources"):
            validate_url_not_internal("http://metadata.google.internal/")


class TestValidateToolName:
    """Tests for validate_tool_name function."""

    def test_valid_built_in_tool(self) -> None:
        """Test built-in tools are valid."""
        assert validate_tool_name("Read") is True
        assert validate_tool_name("Write") is True
        assert validate_tool_name("Bash") is True

    def test_valid_mcp_tool(self) -> None:
        """Test MCP tools with mcp__ prefix are valid."""
        assert validate_tool_name("mcp__server__tool") is True
        assert validate_tool_name("mcp__github__create_issue") is True

    def test_invalid_tool(self) -> None:
        """Test invalid tool names."""
        assert validate_tool_name("InvalidTool") is False
        assert validate_tool_name("random_tool") is False


class TestValidateModelName:
    """Tests for validate_model_name function."""

    def test_none_model(self) -> None:
        """Test None is valid."""
        assert validate_model_name(None) is None

    def test_short_model_names(self) -> None:
        """Test short model names are valid."""
        assert validate_model_name("sonnet") == "sonnet"
        assert validate_model_name("opus") == "opus"
        assert validate_model_name("haiku") == "haiku"

    def test_full_model_ids(self) -> None:
        """Test full model IDs are valid."""
        assert validate_model_name("claude-sonnet-4-20250514") == "claude-sonnet-4-20250514"
        assert validate_model_name("claude-3-5-sonnet-20241022") == "claude-3-5-sonnet-20241022"

    def test_invalid_empty_string(self) -> None:
        """Test empty string raises ValueError."""
        with pytest.raises(ValueError, match="Model cannot be empty"):
            validate_model_name("")

    def test_invalid_model_name(self) -> None:
        """Test invalid model names raise ValueError."""
        with pytest.raises(ValueError, match="Invalid model"):
            validate_model_name("gpt-4")
