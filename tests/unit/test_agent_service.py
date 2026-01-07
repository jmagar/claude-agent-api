"""Unit tests for agent service."""

import pytest

from apps.api.schemas.requests import QueryRequest
from apps.api.services.agent import resolve_env_dict, resolve_env_var


class TestAgentService:
    """Tests for AgentService class."""

    def test_query_request_validation(self) -> None:
        """Test QueryRequest schema validation."""
        # Valid request
        request = QueryRequest(prompt="Test prompt")
        assert request.prompt == "Test prompt"
        assert request.allowed_tools == []
        assert request.permission_mode == "default"

    def test_query_request_with_tools(self) -> None:
        """Test QueryRequest with tool configuration."""
        request = QueryRequest(
            prompt="Test prompt",
            allowed_tools=["Read", "Write"],
            disallowed_tools=["Bash"],
        )
        assert request.allowed_tools == ["Read", "Write"]
        assert request.disallowed_tools == ["Bash"]

    def test_query_request_max_turns_validation(self) -> None:
        """Test max_turns bounds validation."""
        # Valid
        request = QueryRequest(prompt="Test", max_turns=10)
        assert request.max_turns == 10

        # Too low
        with pytest.raises(ValueError):
            QueryRequest(prompt="Test", max_turns=0)

        # Too high
        with pytest.raises(ValueError):
            QueryRequest(prompt="Test", max_turns=1001)

    def test_query_request_permission_modes(self) -> None:
        """Test all permission modes are accepted."""
        modes = ["default", "acceptEdits", "plan", "bypassPermissions"]
        for mode in modes:
            request = QueryRequest(
                prompt="Test",
                permission_mode=mode,  # type: ignore
            )
            assert request.permission_mode == mode

    def test_query_request_with_mcp_servers(self) -> None:
        """Test QueryRequest with MCP server configuration."""
        from apps.api.schemas.requests import McpServerConfigSchema

        request = QueryRequest(
            prompt="Test",
            mcp_servers={
                "custom": McpServerConfigSchema(
                    command="python",
                    args=["server.py"],
                )
            },
        )
        assert "custom" in request.mcp_servers  # type: ignore

    def test_query_request_with_subagents(self) -> None:
        """Test QueryRequest with subagent definitions."""
        from apps.api.schemas.requests import AgentDefinitionSchema

        request = QueryRequest(
            prompt="Test",
            agents={
                "reviewer": AgentDefinitionSchema(
                    description="Code review agent",
                    prompt="You are a code reviewer",
                    tools=["Read", "Grep"],
                )
            },
        )
        assert "reviewer" in request.agents  # type: ignore

    def test_subagent_no_task_tool(self) -> None:
        """Test that subagents cannot have Task tool."""
        from apps.api.schemas.requests import AgentDefinitionSchema

        with pytest.raises(ValueError) as exc_info:
            AgentDefinitionSchema(
                description="Test agent",
                prompt="Test prompt",
                tools=["Read", "Task"],
            )
        assert "Task" in str(exc_info.value)

    def test_query_request_with_hooks(self) -> None:
        """Test QueryRequest with webhook hooks."""
        from apps.api.schemas.requests import HooksConfigSchema, HookWebhookSchema

        request = QueryRequest(
            prompt="Test",
            hooks=HooksConfigSchema(
                PreToolUse=HookWebhookSchema(
                    url="https://example.com/hook",  # type: ignore
                    timeout=30,
                )
            ),
        )
        assert request.hooks is not None
        assert request.hooks.pre_tool_use is not None

    def test_query_request_with_output_format(self) -> None:
        """Test QueryRequest with structured output format."""
        from apps.api.schemas.requests import OutputFormatSchema

        request = QueryRequest(
            prompt="Test",
            output_format=OutputFormatSchema(
                type="json_schema",
                schema={
                    "type": "object",
                    "properties": {"result": {"type": "string"}},
                },
            ),
        )
        assert request.output_format is not None
        assert request.output_format.type == "json_schema"

    def test_output_format_requires_schema(self) -> None:
        """Test that json_schema type requires schema field."""
        from apps.api.schemas.requests import OutputFormatSchema

        with pytest.raises(ValueError):
            OutputFormatSchema(type="json_schema", schema=None)

    def test_mcp_server_stdio_requires_command(self) -> None:
        """Test that stdio transport requires command."""
        from apps.api.schemas.requests import McpServerConfigSchema

        with pytest.raises(ValueError):
            McpServerConfigSchema(type="stdio")

    def test_mcp_server_sse_requires_url(self) -> None:
        """Test that sse transport requires url."""
        from apps.api.schemas.requests import McpServerConfigSchema

        with pytest.raises(ValueError):
            McpServerConfigSchema(type="sse")

    def test_mcp_server_http_requires_url(self) -> None:
        """Test that http transport requires url."""
        from apps.api.schemas.requests import McpServerConfigSchema

        with pytest.raises(ValueError):
            McpServerConfigSchema(type="http")

    def test_mcp_server_stdio_with_args(self) -> None:
        """Test stdio transport with command and args."""
        from apps.api.schemas.requests import McpServerConfigSchema

        config = McpServerConfigSchema(
            type="stdio",
            command="python",
            args=["server.py", "--port", "8080"],
        )
        assert config.command == "python"
        assert config.args == ["server.py", "--port", "8080"]
        assert config.type == "stdio"

    def test_mcp_server_sse_with_headers(self) -> None:
        """Test SSE transport with headers."""
        from apps.api.schemas.requests import McpServerConfigSchema

        config = McpServerConfigSchema(
            type="sse",
            url="https://example.com/sse",
            headers={"Authorization": "Bearer token123"},
        )
        assert config.url == "https://example.com/sse"
        assert config.headers == {"Authorization": "Bearer token123"}

    def test_mcp_server_http_with_headers(self) -> None:
        """Test HTTP transport with headers."""
        from apps.api.schemas.requests import McpServerConfigSchema

        config = McpServerConfigSchema(
            type="http",
            url="https://example.com/mcp",
            headers={"X-API-Key": "secret"},
        )
        assert config.url == "https://example.com/mcp"
        assert config.type == "http"

    def test_mcp_server_env_vars(self) -> None:
        """Test MCP server with environment variables."""
        from apps.api.schemas.requests import McpServerConfigSchema

        config = McpServerConfigSchema(
            type="stdio",
            command="python",
            args=["server.py"],
            env={
                "API_KEY": "${API_KEY:-default}",
                "DEBUG": "true",
            },
        )
        assert config.env["API_KEY"] == "${API_KEY:-default}"
        assert config.env["DEBUG"] == "true"

    def test_mcp_server_default_type_is_stdio(self) -> None:
        """Test that default transport type is stdio."""
        from apps.api.schemas.requests import McpServerConfigSchema

        config = McpServerConfigSchema(command="python")
        assert config.type == "stdio"

    def test_mcp_server_default_empty_args(self) -> None:
        """Test that args defaults to empty list."""
        from apps.api.schemas.requests import McpServerConfigSchema

        config = McpServerConfigSchema(command="python")
        assert config.args == []

    def test_mcp_server_default_empty_headers(self) -> None:
        """Test that headers defaults to empty dict."""
        from apps.api.schemas.requests import McpServerConfigSchema

        config = McpServerConfigSchema(type="sse", url="https://example.com/sse")
        assert config.headers == {}

    def test_mcp_server_default_empty_env(self) -> None:
        """Test that env defaults to empty dict."""
        from apps.api.schemas.requests import McpServerConfigSchema

        config = McpServerConfigSchema(command="python")
        assert config.env == {}

    def test_multiple_mcp_servers_in_request(self) -> None:
        """Test multiple MCP servers in a single request."""
        from apps.api.schemas.requests import McpServerConfigSchema

        request = QueryRequest(
            prompt="Test",
            mcp_servers={
                "stdio-server": McpServerConfigSchema(
                    type="stdio",
                    command="python",
                    args=["server.py"],
                ),
                "sse-server": McpServerConfigSchema(
                    type="sse",
                    url="https://example.com/sse",
                ),
                "http-server": McpServerConfigSchema(
                    type="http",
                    url="https://example.com/mcp",
                ),
            },
        )
        assert request.mcp_servers is not None
        assert len(request.mcp_servers) == 3
        assert "stdio-server" in request.mcp_servers
        assert "sse-server" in request.mcp_servers
        assert "http-server" in request.mcp_servers


class TestEnvVarResolution:
    """Tests for environment variable resolution functions."""

    def test_resolve_env_var_simple(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test resolving a simple ${VAR} reference."""
        monkeypatch.setenv("MY_VAR", "my_value")
        result = resolve_env_var("${MY_VAR}")
        assert result == "my_value"

    def test_resolve_env_var_with_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test resolving ${VAR:-default} with default value."""
        # Variable not set, should use default
        monkeypatch.delenv("UNSET_VAR", raising=False)
        result = resolve_env_var("${UNSET_VAR:-default_value}")
        assert result == "default_value"

    def test_resolve_env_var_with_default_when_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test resolving ${VAR:-default} when variable is set."""
        monkeypatch.setenv("SET_VAR", "actual_value")
        result = resolve_env_var("${SET_VAR:-default_value}")
        assert result == "actual_value"

    def test_resolve_env_var_missing_no_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test resolving ${VAR} when variable is not set and no default."""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        result = resolve_env_var("${MISSING_VAR}")
        assert result == ""

    def test_resolve_env_var_in_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test resolving env var embedded in a larger string."""
        monkeypatch.setenv("API_KEY", "secret123")
        result = resolve_env_var("Bearer ${API_KEY}")
        assert result == "Bearer secret123"

    def test_resolve_env_var_multiple(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test resolving multiple env vars in one string."""
        monkeypatch.setenv("HOST", "localhost")
        monkeypatch.setenv("PORT", "8080")
        result = resolve_env_var("http://${HOST}:${PORT}/api")
        assert result == "http://localhost:8080/api"

    def test_resolve_env_var_no_substitution(self) -> None:
        """Test string with no env vars passes through unchanged."""
        result = resolve_env_var("plain_string")
        assert result == "plain_string"

    def test_resolve_env_var_empty_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test ${VAR:-} with empty default."""
        monkeypatch.delenv("EMPTY_DEFAULT_VAR", raising=False)
        result = resolve_env_var("${EMPTY_DEFAULT_VAR:-}")
        assert result == ""

    def test_resolve_env_dict_all_resolved(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test resolving all values in a dictionary."""
        monkeypatch.setenv("KEY1", "value1")
        monkeypatch.setenv("KEY2", "value2")

        env = {
            "VAR1": "${KEY1}",
            "VAR2": "${KEY2:-default}",
            "VAR3": "static",
        }
        result = resolve_env_dict(env)

        assert result["VAR1"] == "value1"
        assert result["VAR2"] == "value2"
        assert result["VAR3"] == "static"

    def test_resolve_env_dict_with_missing_vars(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test resolving dict with some missing variables."""
        monkeypatch.delenv("MISSING", raising=False)

        env = {
            "KEY": "${MISSING:-fallback}",
        }
        result = resolve_env_dict(env)

        assert result["KEY"] == "fallback"

    def test_resolve_env_dict_empty(self) -> None:
        """Test resolving empty dictionary."""
        result = resolve_env_dict({})
        assert result == {}
