"""Unit tests for security validation (T128)."""

import pytest
from pydantic import ValidationError

from apps.api.schemas.requests.config import HookWebhookSchema, McpServerConfigSchema
from apps.api.schemas.requests.query import QueryRequest


class TestPathTraversalValidation:
    """Tests for path traversal prevention."""

    def test_cwd_rejects_path_traversal(self) -> None:
        """Test cwd rejects path traversal attempts."""
        with pytest.raises(ValidationError, match="Path traversal"):
            QueryRequest(prompt="test", cwd="../etc/passwd")

    def test_cwd_rejects_encoded_traversal(self) -> None:
        """Test cwd rejects URL-encoded path traversal."""
        with pytest.raises(ValidationError, match="Path traversal"):
            QueryRequest(prompt="test", cwd="%2e%2e/etc/passwd")

    def test_cwd_allows_valid_paths(self) -> None:
        """Test cwd allows valid absolute paths."""
        request = QueryRequest(prompt="test", cwd="/home/user/project")
        assert request.cwd == "/home/user/project"

    def test_add_dirs_rejects_path_traversal(self) -> None:
        """Test add_dirs rejects path traversal attempts."""
        with pytest.raises(ValidationError, match="Path traversal"):
            QueryRequest(prompt="test", add_dirs=["../secret"])

    def test_add_dirs_allows_valid_paths(self) -> None:
        """Test add_dirs allows valid paths."""
        request = QueryRequest(prompt="test", add_dirs=["/home/user/docs"])
        assert request.add_dirs == ["/home/user/docs"]


class TestNullByteValidation:
    """Tests for null byte prevention."""

    def test_cwd_rejects_null_bytes(self) -> None:
        """Test cwd rejects null bytes."""
        with pytest.raises(ValidationError, match="Null bytes"):
            QueryRequest(prompt="test", cwd="/home/user\x00/project")

    def test_env_key_rejects_null_bytes(self) -> None:
        """Test env key rejects null bytes."""
        with pytest.raises(ValidationError, match="Null bytes"):
            QueryRequest(prompt="test", env={"KEY\x00": "value"})

    def test_env_value_rejects_null_bytes(self) -> None:
        """Test env value rejects null bytes."""
        with pytest.raises(ValidationError, match="Null bytes"):
            QueryRequest(prompt="test", env={"KEY": "value\x00"})


class TestEnvVariableValidation:
    """Tests for dangerous environment variable prevention."""

    def test_rejects_ld_preload(self) -> None:
        """Test env rejects LD_PRELOAD."""
        with pytest.raises(ValidationError, match="LD_PRELOAD"):
            QueryRequest(prompt="test", env={"LD_PRELOAD": "/evil.so"})

    def test_rejects_ld_library_path(self) -> None:
        """Test env rejects LD_LIBRARY_PATH."""
        with pytest.raises(ValidationError, match="LD_LIBRARY_PATH"):
            QueryRequest(prompt="test", env={"LD_LIBRARY_PATH": "/evil"})

    def test_rejects_path(self) -> None:
        """Test env rejects PATH modification."""
        with pytest.raises(ValidationError, match="PATH"):
            QueryRequest(prompt="test", env={"PATH": "/evil/bin"})

    def test_allows_safe_env_vars(self) -> None:
        """Test env allows safe variables."""
        request = QueryRequest(
            prompt="test",
            env={"MY_VAR": "value", "ANOTHER": "test"},
        )
        assert request.env == {"MY_VAR": "value", "ANOTHER": "test"}


class TestMcpServerSecurityValidation:
    """Tests for MCP server command injection prevention."""

    def test_command_rejects_shell_metacharacters(self) -> None:
        """Test command rejects shell metacharacters."""
        with pytest.raises(ValidationError, match="Shell metacharacters"):
            McpServerConfigSchema(type="stdio", command="node; rm -rf /")

    def test_command_rejects_pipes(self) -> None:
        """Test command rejects pipe characters."""
        with pytest.raises(ValidationError, match="Shell metacharacters"):
            McpServerConfigSchema(type="stdio", command="cat | bash")

    def test_command_rejects_command_substitution(self) -> None:
        """Test command rejects command substitution."""
        with pytest.raises(ValidationError, match="Shell metacharacters"):
            McpServerConfigSchema(type="stdio", command="$(whoami)")

    def test_command_allows_valid_commands(self) -> None:
        """Test command allows valid simple commands."""
        config = McpServerConfigSchema(type="stdio", command="node")
        assert config.command == "node"

    def test_args_reject_null_bytes(self) -> None:
        """Test args rejects null bytes."""
        with pytest.raises(ValidationError, match="Null bytes"):
            McpServerConfigSchema(
                type="stdio",
                command="node",
                args=["--arg\x00"],
            )

    def test_url_rejects_localhost(self) -> None:
        """Test URL rejects localhost (SSRF prevention)."""
        with pytest.raises(ValidationError, match="internal resources"):
            McpServerConfigSchema(type="sse", url="http://localhost:8080/sse")

    def test_url_rejects_private_ip(self) -> None:
        """Test URL rejects private IP addresses (SSRF prevention)."""
        with pytest.raises(ValidationError, match="internal resources"):
            McpServerConfigSchema(type="http", url="http://192.168.1.1/api")

    def test_url_rejects_metadata_endpoints(self) -> None:
        """Test URL rejects cloud metadata endpoints (SSRF prevention)."""
        with pytest.raises(ValidationError, match="internal resources"):
            McpServerConfigSchema(
                type="http",
                url="http://metadata.google.internal/computeMetadata/v1/",
            )

    def test_url_allows_external(self) -> None:
        """Test URL allows external endpoints."""
        config = McpServerConfigSchema(
            type="sse",
            url="https://api.example.com/mcp/sse",
        )
        assert config.url == "https://api.example.com/mcp/sse"


class TestHookWebhookSecurityValidation:
    """Tests for webhook URL SSRF prevention."""

    def test_url_rejects_localhost(self) -> None:
        """Test webhook URL rejects localhost."""
        with pytest.raises(ValidationError, match="internal resources"):
            HookWebhookSchema(url="http://localhost:9000/hook")

    def test_url_rejects_private_ip(self) -> None:
        """Test webhook URL rejects private IPs."""
        with pytest.raises(ValidationError, match="internal resources"):
            HookWebhookSchema(url="http://10.0.0.1/webhook")

    def test_url_rejects_loopback(self) -> None:
        """Test webhook URL rejects loopback."""
        with pytest.raises(ValidationError, match="internal resources"):
            HookWebhookSchema(url="http://127.0.0.1:8080/hook")

    def test_url_allows_external(self) -> None:
        """Test webhook URL allows external endpoints."""
        schema = HookWebhookSchema(url="https://hooks.example.com/webhook")
        assert str(schema.url) == "https://hooks.example.com/webhook"


class TestPromptValidation:
    """Tests for prompt validation."""

    def test_prompt_length_validation(self) -> None:
        """Test prompt respects max length."""
        with pytest.raises(ValidationError):
            # max_length is 100000
            QueryRequest(prompt="x" * 100001)

    def test_prompt_min_length_validation(self) -> None:
        """Test prompt requires minimum length."""
        with pytest.raises(ValidationError):
            QueryRequest(prompt="")

    def test_valid_prompt(self) -> None:
        """Test valid prompt is accepted."""
        request = QueryRequest(prompt="Hello, Claude!")
        assert request.prompt == "Hello, Claude!"
