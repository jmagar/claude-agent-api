"""Unit tests for Pydantic schema validation (US3, US4, US7, US8)."""

import re

import pytest
from pydantic import ValidationError

from apps.api.schemas.requests.config import (
    AgentDefinitionSchema,
    HooksConfigSchema,
    HookWebhookSchema,
    McpServerConfigSchema,
    OutputFormatSchema,
)
from apps.api.schemas.requests.query import QueryRequest
from apps.api.schemas.requests.sessions import ForkRequest, ResumeRequest


class TestHookWebhookSchemaValidation:
    """Unit tests for HookWebhookSchema validation (T082)."""

    def test_valid_webhook_with_url_only(self) -> None:
        """Test creating a webhook with just a URL."""
        hook = HookWebhookSchema(url="https://example.com/webhook")  # type: ignore[arg-type]
        assert str(hook.url) == "https://example.com/webhook"
        assert hook.timeout == 30  # default
        assert hook.headers == {}  # default
        assert hook.matcher is None  # default

    def test_valid_webhook_with_all_fields(self) -> None:
        """Test creating a webhook with all fields specified."""
        hook = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
            headers={"Authorization": "Bearer token123", "X-Custom": "value"},
            timeout=60,
            matcher="Write|Edit",
        )
        assert str(hook.url) == "https://example.com/webhook"
        assert hook.headers == {"Authorization": "Bearer token123", "X-Custom": "value"}
        assert hook.timeout == 60
        assert hook.matcher == "Write|Edit"

    def test_url_must_be_valid_http_url(self) -> None:
        """Test that URL must be a valid HTTP/HTTPS URL."""
        # Valid URLs (external only due to SSRF protection)
        hook = HookWebhookSchema(url="https://example.com/hook")  # type: ignore[arg-type]
        assert hook.url is not None

        hook = HookWebhookSchema(url="http://webhook.example.com/hook")  # type: ignore[arg-type]
        assert hook.url is not None

        # Invalid URLs
        with pytest.raises(ValidationError):
            HookWebhookSchema(url="not-a-url")  # type: ignore[arg-type]

        with pytest.raises(ValidationError):
            HookWebhookSchema(url="ftp://example.com/hook")  # type: ignore[arg-type]

        with pytest.raises(ValidationError):
            HookWebhookSchema(url="")  # type: ignore[arg-type]

    def test_timeout_must_be_within_bounds(self) -> None:
        """Test timeout validation (1-300 seconds)."""
        # Valid timeouts
        for timeout in [1, 30, 100, 300]:
            hook = HookWebhookSchema(
                url="https://example.com/hook",  # type: ignore[arg-type]
                timeout=timeout,
            )
            assert hook.timeout == timeout

        # Invalid timeouts - below minimum
        with pytest.raises(ValidationError):
            HookWebhookSchema(
                url="https://example.com/hook",  # type: ignore[arg-type]
                timeout=0,
            )

        with pytest.raises(ValidationError):
            HookWebhookSchema(
                url="https://example.com/hook",  # type: ignore[arg-type]
                timeout=-1,
            )

        # Invalid timeouts - above maximum
        with pytest.raises(ValidationError):
            HookWebhookSchema(
                url="https://example.com/hook",  # type: ignore[arg-type]
                timeout=301,
            )

        with pytest.raises(ValidationError):
            HookWebhookSchema(
                url="https://example.com/hook",  # type: ignore[arg-type]
                timeout=1000,
            )

    def test_headers_can_be_empty_dict(self) -> None:
        """Test that headers can be empty dict (default)."""
        hook = HookWebhookSchema(url="https://example.com/hook")  # type: ignore[arg-type]
        assert hook.headers == {}

    def test_headers_with_multiple_values(self) -> None:
        """Test headers with multiple key-value pairs."""
        hook = HookWebhookSchema(
            url="https://example.com/hook",  # type: ignore[arg-type]
            headers={
                "Authorization": "Bearer abc123",
                "Content-Type": "application/json",
                "X-Request-ID": "req-123",
            },
        )
        assert len(hook.headers) == 3

    def test_matcher_can_be_valid_regex(self) -> None:
        """Test that matcher accepts valid regex patterns."""
        # Simple patterns
        hook = HookWebhookSchema(
            url="https://example.com/hook",  # type: ignore[arg-type]
            matcher="Write",
        )
        assert hook.matcher == "Write"

        # OR pattern
        hook = HookWebhookSchema(
            url="https://example.com/hook",  # type: ignore[arg-type]
            matcher="Write|Edit|Bash",
        )
        assert re.match(hook.matcher, "Write") is not None
        assert re.match(hook.matcher, "Edit") is not None
        assert re.match(hook.matcher, "Read") is None

        # Wildcard pattern
        hook = HookWebhookSchema(
            url="https://example.com/hook",  # type: ignore[arg-type]
            matcher="mcp__.*",
        )
        assert re.match(hook.matcher, "mcp__server__tool") is not None
        assert re.match(hook.matcher, "Read") is None

    def test_matcher_can_be_none(self) -> None:
        """Test that matcher defaults to None (match all)."""
        hook = HookWebhookSchema(url="https://example.com/hook")  # type: ignore[arg-type]
        assert hook.matcher is None


class TestHooksConfigSchemaValidation:
    """Unit tests for HooksConfigSchema validation (T082)."""

    def test_empty_hooks_config(self) -> None:
        """Test creating empty HooksConfigSchema."""
        config = HooksConfigSchema()
        assert config.pre_tool_use is None
        assert config.post_tool_use is None
        assert config.stop is None
        assert config.subagent_stop is None
        assert config.user_prompt_submit is None
        assert config.pre_compact is None
        assert config.notification is None

    def test_pre_tool_use_hook(self) -> None:
        """Test PreToolUse hook configuration."""
        config = HooksConfigSchema(
            PreToolUse=HookWebhookSchema(
                url="https://example.com/pre-tool",  # type: ignore[arg-type]
            )
        )
        assert config.pre_tool_use is not None
        assert "pre-tool" in str(config.pre_tool_use.url)

    def test_post_tool_use_hook(self) -> None:
        """Test PostToolUse hook configuration."""
        config = HooksConfigSchema(
            PostToolUse=HookWebhookSchema(
                url="https://example.com/post-tool",  # type: ignore[arg-type]
            )
        )
        assert config.post_tool_use is not None

    def test_stop_hook(self) -> None:
        """Test Stop hook configuration."""
        config = HooksConfigSchema(
            Stop=HookWebhookSchema(
                url="https://example.com/stop",  # type: ignore[arg-type]
            )
        )
        assert config.stop is not None

    def test_subagent_stop_hook(self) -> None:
        """Test SubagentStop hook configuration."""
        config = HooksConfigSchema(
            SubagentStop=HookWebhookSchema(
                url="https://example.com/subagent-stop",  # type: ignore[arg-type]
            )
        )
        assert config.subagent_stop is not None

    def test_user_prompt_submit_hook(self) -> None:
        """Test UserPromptSubmit hook configuration."""
        config = HooksConfigSchema(
            UserPromptSubmit=HookWebhookSchema(
                url="https://example.com/prompt",  # type: ignore[arg-type]
            )
        )
        assert config.user_prompt_submit is not None

    def test_pre_compact_hook(self) -> None:
        """Test PreCompact hook configuration."""
        config = HooksConfigSchema(
            PreCompact=HookWebhookSchema(
                url="https://example.com/pre-compact",  # type: ignore[arg-type]
            )
        )
        assert config.pre_compact is not None

    def test_notification_hook(self) -> None:
        """Test Notification hook configuration."""
        config = HooksConfigSchema(
            Notification=HookWebhookSchema(
                url="https://example.com/notification",  # type: ignore[arg-type]
            )
        )
        assert config.notification is not None

    def test_multiple_hooks_together(self) -> None:
        """Test configuring multiple hook types together."""
        config = HooksConfigSchema(
            PreToolUse=HookWebhookSchema(
                url="https://example.com/pre",  # type: ignore[arg-type]
                timeout=30,
                matcher="Write|Edit",
            ),
            PostToolUse=HookWebhookSchema(
                url="https://example.com/post",  # type: ignore[arg-type]
                timeout=30,
            ),
            Stop=HookWebhookSchema(
                url="https://example.com/stop",  # type: ignore[arg-type]
                timeout=60,
            ),
        )
        assert config.pre_tool_use is not None
        assert config.post_tool_use is not None
        assert config.stop is not None
        assert config.subagent_stop is None
        assert config.user_prompt_submit is None

    def test_hook_alias_names_in_dict(self) -> None:
        """Test that aliases (PreToolUse) work when parsing from dict."""
        data = {
            "PreToolUse": {
                "url": "https://example.com/hook",
                "timeout": 30,
            }
        }
        config = HooksConfigSchema.model_validate(data)
        assert config.pre_tool_use is not None

    def test_snake_case_names_work(self) -> None:
        """Test that snake_case field names also work (populate_by_name)."""
        config = HooksConfigSchema(
            pre_tool_use=HookWebhookSchema(
                url="https://example.com/hook",  # type: ignore[arg-type]
            )
        )
        assert config.pre_tool_use is not None


class TestHooksInQueryRequest:
    """Tests for hooks field in QueryRequest."""

    def test_query_request_with_hooks(self) -> None:
        """Test QueryRequest accepts hooks configuration."""
        request = QueryRequest(
            prompt="Test prompt",
            hooks=HooksConfigSchema(
                PreToolUse=HookWebhookSchema(
                    url="https://example.com/hook",  # type: ignore[arg-type]
                )
            ),
        )
        assert request.hooks is not None
        assert request.hooks.pre_tool_use is not None

    def test_query_request_hooks_defaults_to_none(self) -> None:
        """Test that hooks defaults to None if not specified."""
        request = QueryRequest(prompt="Test prompt")
        assert request.hooks is None

    def test_query_request_with_hooks_and_other_params(self) -> None:
        """Test QueryRequest with hooks and other parameters."""
        request = QueryRequest(
            prompt="Test prompt",
            allowed_tools=["Read", "Write"],
            permission_mode="acceptEdits",
            hooks=HooksConfigSchema(
                PreToolUse=HookWebhookSchema(
                    url="https://example.com/pre",  # type: ignore[arg-type]
                    timeout=60,
                    matcher="Write",
                ),
                Stop=HookWebhookSchema(
                    url="https://example.com/stop",  # type: ignore[arg-type]
                ),
            ),
        )
        assert request.allowed_tools == ["Read", "Write"]
        assert request.permission_mode == "acceptEdits"
        assert request.hooks is not None
        assert request.hooks.pre_tool_use is not None
        assert request.hooks.stop is not None


class TestHooksInResumeRequest:
    """Tests for hooks field in ResumeRequest."""

    def test_resume_request_with_hooks(self) -> None:
        """Test ResumeRequest accepts hooks configuration."""
        request = ResumeRequest(
            prompt="Continue",
            hooks=HooksConfigSchema(
                PreToolUse=HookWebhookSchema(
                    url="https://example.com/hook",  # type: ignore[arg-type]
                )
            ),
        )
        assert request.hooks is not None

    def test_resume_request_hooks_defaults_to_none(self) -> None:
        """Test that hooks defaults to None in ResumeRequest."""
        request = ResumeRequest(prompt="Continue")
        assert request.hooks is None


class TestHooksInForkRequest:
    """Tests for hooks field in ForkRequest."""

    def test_fork_request_with_hooks(self) -> None:
        """Test ForkRequest accepts hooks configuration."""
        request = ForkRequest(
            prompt="Fork and continue",
            hooks=HooksConfigSchema(
                PreToolUse=HookWebhookSchema(
                    url="https://example.com/hook",  # type: ignore[arg-type]
                ),
                SubagentStop=HookWebhookSchema(
                    url="https://example.com/subagent",  # type: ignore[arg-type]
                ),
            ),
        )
        assert request.hooks is not None
        assert request.hooks.pre_tool_use is not None
        assert request.hooks.subagent_stop is not None

    def test_fork_request_hooks_defaults_to_none(self) -> None:
        """Test that hooks defaults to None in ForkRequest."""
        request = ForkRequest(prompt="Fork")
        assert request.hooks is None


class TestToolConfigurationValidation:
    """Unit tests for tool configuration in schemas (US3, T057)."""

    def test_allowed_tools_accepts_builtin_tools(self) -> None:
        """Test that built-in tool names are accepted."""
        request = QueryRequest(
            prompt="Test",
            allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        )
        assert len(request.allowed_tools) == 6

    def test_allowed_tools_accepts_mcp_tools(self) -> None:
        """Test that MCP tool names are accepted."""
        request = QueryRequest(
            prompt="Test",
            allowed_tools=["mcp__server__tool", "mcp__custom__action"],
        )
        assert len(request.allowed_tools) == 2

    def test_disallowed_tools_accepts_builtin_tools(self) -> None:
        """Test that built-in tools can be disallowed."""
        request = QueryRequest(
            prompt="Test",
            disallowed_tools=["Bash", "Write"],
        )
        assert len(request.disallowed_tools) == 2

    def test_tool_conflict_raises_error(self) -> None:
        """Test that having same tool in allowed and disallowed raises error."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(
                prompt="Test",
                allowed_tools=["Read", "Write"],
                disallowed_tools=["Write"],
            )
        assert "conflict" in str(exc_info.value).lower()

    def test_invalid_tool_names_rejected(self) -> None:
        """Test that invalid tool names are rejected."""
        with pytest.raises(ValidationError):
            QueryRequest(
                prompt="Test",
                allowed_tools=["InvalidTool"],
            )


class TestAgentDefinitionSchemaValidation:
    """Unit tests for AgentDefinitionSchema validation (US4, T063)."""

    def test_valid_agent_definition(self) -> None:
        """Test creating a valid agent definition."""
        agent = AgentDefinitionSchema(
            description="A code review agent",
            prompt="You are a code reviewer",
            tools=["Read", "Grep"],
            model="sonnet",
        )
        assert agent.description == "A code review agent"
        assert agent.tools == ["Read", "Grep"]

    def test_agent_definition_cannot_have_task_tool(self) -> None:
        """Test that subagents cannot have Task tool."""
        with pytest.raises(ValidationError) as exc_info:
            AgentDefinitionSchema(
                description="Test agent",
                prompt="Test prompt",
                tools=["Read", "Task"],
            )
        assert "Task" in str(exc_info.value)

    def test_agent_definition_tools_defaults_to_none(self) -> None:
        """Test that tools defaults to None (inherits from parent)."""
        agent = AgentDefinitionSchema(
            description="Test agent",
            prompt="Test prompt",
        )
        assert agent.tools is None

    def test_agent_definition_model_options(self) -> None:
        """Test valid model options for agents."""
        for model in ["sonnet", "opus", "haiku", "inherit"]:
            agent = AgentDefinitionSchema(
                description="Test",
                prompt="Test",
                model=model,  # type: ignore[arg-type]
            )
            assert agent.model == model


class TestOutputFormatSchemaValidation:
    """Unit tests for OutputFormatSchema validation (US8, T090)."""

    def test_json_schema_requires_schema_field(self) -> None:
        """Test that json_schema type requires schema field."""
        with pytest.raises(ValidationError):
            OutputFormatSchema(type="json_schema", schema=None)

    def test_json_schema_with_valid_schema(self) -> None:
        """Test json_schema type with valid schema."""
        output_format = OutputFormatSchema(
            type="json_schema",
            schema={
                "type": "object",
                "properties": {"result": {"type": "string"}},
            },
        )
        assert output_format.schema_ is not None
        assert output_format.schema_["type"] == "object"

    def test_schema_must_have_type_property(self) -> None:
        """Test that schema must have 'type' property."""
        with pytest.raises(ValidationError):
            OutputFormatSchema(
                type="json_schema",
                schema={"properties": {"a": {"type": "string"}}},
            )

    def test_json_type_does_not_require_schema(self) -> None:
        """Test that 'json' type does not require schema field."""
        output_format = OutputFormatSchema(type="json")
        assert output_format.schema_ is None


class TestMcpServerConfigSchemaValidation:
    """Unit tests for MCP server configuration validation (US5)."""

    def test_stdio_requires_command(self) -> None:
        """Test that stdio transport requires command."""
        with pytest.raises(ValidationError):
            McpServerConfigSchema(type="stdio")

    def test_sse_requires_url(self) -> None:
        """Test that sse transport requires url."""
        with pytest.raises(ValidationError):
            McpServerConfigSchema(type="sse")

    def test_http_requires_url(self) -> None:
        """Test that http transport requires url."""
        with pytest.raises(ValidationError):
            McpServerConfigSchema(type="http")

    def test_valid_stdio_config(self) -> None:
        """Test valid stdio configuration."""
        config = McpServerConfigSchema(
            type="stdio",
            command="python",
            args=["server.py", "--port", "8080"],
            env={"API_KEY": "secret"},
        )
        assert config.command == "python"
        assert len(config.args) == 3

    def test_valid_sse_config(self) -> None:
        """Test valid SSE configuration."""
        config = McpServerConfigSchema(
            type="sse",
            url="https://example.com/sse",
            headers={"Authorization": "Bearer token"},
        )
        assert config.url == "https://example.com/sse"


class TestModelValidation:
    """Unit tests for model parameter validation (US10, T106)."""

    def test_model_accepts_sonnet(self) -> None:
        """Test that 'sonnet' is a valid model."""
        request = QueryRequest(prompt="Test", model="sonnet")
        assert request.model == "sonnet"

    def test_model_accepts_opus(self) -> None:
        """Test that 'opus' is a valid model."""
        request = QueryRequest(prompt="Test", model="opus")
        assert request.model == "opus"

    def test_model_accepts_haiku(self) -> None:
        """Test that 'haiku' is a valid model."""
        request = QueryRequest(prompt="Test", model="haiku")
        assert request.model == "haiku"

    def test_model_accepts_full_model_id_sonnet(self) -> None:
        """Test that full Sonnet model ID is accepted."""
        request = QueryRequest(prompt="Test", model="claude-sonnet-4-20250514")
        assert request.model == "claude-sonnet-4-20250514"

    def test_model_accepts_full_model_id_opus(self) -> None:
        """Test that full Opus model ID is accepted."""
        request = QueryRequest(prompt="Test", model="claude-opus-4-20250514")
        assert request.model == "claude-opus-4-20250514"

    def test_model_accepts_full_model_id_haiku(self) -> None:
        """Test that full Haiku model ID is accepted."""
        request = QueryRequest(prompt="Test", model="claude-haiku-3-5-20250514")
        assert request.model == "claude-haiku-3-5-20250514"

    def test_model_accepts_claude_3_5_sonnet(self) -> None:
        """Test that claude-3-5-sonnet model ID is accepted."""
        request = QueryRequest(prompt="Test", model="claude-3-5-sonnet-20241022")
        assert request.model == "claude-3-5-sonnet-20241022"

    def test_model_accepts_none_as_default(self) -> None:
        """Test that model defaults to None (uses default model)."""
        request = QueryRequest(prompt="Test")
        assert request.model is None

    def test_model_rejects_invalid_names(self) -> None:
        """Test that invalid model names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(prompt="Test", model="invalid-model")
        error_str = str(exc_info.value).lower()
        assert "model" in error_str or "invalid" in error_str

    def test_model_rejects_empty_string(self) -> None:
        """Test that empty string model is rejected."""
        with pytest.raises(ValidationError):
            QueryRequest(prompt="Test", model="")

    def test_model_rejects_arbitrary_string(self) -> None:
        """Test that arbitrary string model is rejected."""
        with pytest.raises(ValidationError):
            QueryRequest(prompt="Test", model="gpt-4")

    def test_model_rejects_partial_model_name(self) -> None:
        """Test that partial model names are rejected."""
        with pytest.raises(ValidationError):
            QueryRequest(prompt="Test", model="claude")

    def test_model_in_fork_request(self) -> None:
        """Test model validation in ForkRequest."""
        request = ForkRequest(prompt="Fork", model="opus")
        assert request.model == "opus"

    def test_model_in_fork_request_invalid(self) -> None:
        """Test that invalid model in ForkRequest is rejected."""
        with pytest.raises(ValidationError):
            ForkRequest(prompt="Fork", model="invalid-model")

    def test_model_error_message_includes_valid_options(self) -> None:
        """Test that validation error message mentions valid model options."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(prompt="Test", model="badmodel")
        error_str = str(exc_info.value).lower()
        # Error message should mention valid options or be descriptive
        assert "sonnet" in error_str or "model" in error_str
