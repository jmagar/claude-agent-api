"""Unit tests for agent service."""

import pytest

from apps.api.schemas.requests import QueryRequest


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
