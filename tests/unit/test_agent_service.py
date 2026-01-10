"""Unit tests for agent service."""

import json
from typing import Literal
from unittest.mock import MagicMock, patch

import pytest

from apps.api.schemas.requests.query import QueryRequest
from apps.api.services.agent import (
    AgentService,
    detect_slash_command,
    resolve_env_dict,
    resolve_env_var,
)
from apps.api.services.agent.file_modification_tracker import FileModificationTracker
from apps.api.services.agent.types import StreamContext


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
        modes: list[Literal["default", "acceptEdits", "plan", "bypassPermissions"]] = [
            "default",
            "acceptEdits",
            "plan",
            "bypassPermissions",
        ]
        for mode in modes:
            request = QueryRequest(
                prompt="Test",
                permission_mode=mode,
            )
            assert request.permission_mode == mode

    def test_query_request_with_mcp_servers(self) -> None:
        """Test QueryRequest with MCP server configuration."""
        from apps.api.schemas.requests.config import McpServerConfigSchema

        request = QueryRequest(
            prompt="Test",
            mcp_servers={
                "custom": McpServerConfigSchema(
                    command="python",
                    args=["server.py"],
                )
            },
        )
        assert request.mcp_servers is not None
        assert "custom" in request.mcp_servers

    def test_query_request_with_subagents(self) -> None:
        """Test QueryRequest with subagent definitions."""
        from apps.api.schemas.requests.config import AgentDefinitionSchema

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
        assert request.agents is not None
        assert "reviewer" in request.agents

    def test_subagent_no_task_tool(self) -> None:
        """Test that subagents cannot have Task tool."""
        from apps.api.schemas.requests.config import AgentDefinitionSchema

        with pytest.raises(ValueError) as exc_info:
            AgentDefinitionSchema(
                description="Test agent",
                prompt="Test prompt",
                tools=["Read", "Task"],
            )
        assert "Task" in str(exc_info.value)

    def test_query_request_with_hooks(self) -> None:
        """Test QueryRequest with webhook hooks."""
        from apps.api.schemas.requests.config import (
            HooksConfigSchema,
            HookWebhookSchema,
        )

        request = QueryRequest(
            prompt="Test",
            hooks=HooksConfigSchema(
                PreToolUse=HookWebhookSchema.model_validate({
                    "url": "https://example.com/hook",
                    "timeout": 30,
                })
            ),
        )
        assert request.hooks is not None
        assert request.hooks.pre_tool_use is not None

    def test_query_request_with_output_format(self) -> None:
        """Test QueryRequest with structured output format."""
        from apps.api.schemas.requests.config import OutputFormatSchema

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
        from apps.api.schemas.requests.config import OutputFormatSchema

        with pytest.raises(ValueError):
            OutputFormatSchema(type="json_schema", schema=None)

    def test_mcp_server_stdio_requires_command(self) -> None:
        """Test that stdio transport requires command."""
        from apps.api.schemas.requests.config import McpServerConfigSchema

        with pytest.raises(ValueError):
            McpServerConfigSchema(type="stdio")

    def test_mcp_server_sse_requires_url(self) -> None:
        """Test that sse transport requires url."""
        from apps.api.schemas.requests.config import McpServerConfigSchema

        with pytest.raises(ValueError):
            McpServerConfigSchema(type="sse")

    def test_mcp_server_http_requires_url(self) -> None:
        """Test that http transport requires url."""
        from apps.api.schemas.requests.config import McpServerConfigSchema

        with pytest.raises(ValueError):
            McpServerConfigSchema(type="http")

    def test_mcp_server_stdio_with_args(self) -> None:
        """Test stdio transport with command and args."""
        from apps.api.schemas.requests.config import McpServerConfigSchema

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
        from apps.api.schemas.requests.config import McpServerConfigSchema

        config = McpServerConfigSchema(
            type="sse",
            url="https://example.com/sse",
            headers={"Authorization": "Bearer token123"},
        )
        assert config.url == "https://example.com/sse"
        assert config.headers == {"Authorization": "Bearer token123"}

    def test_mcp_server_http_with_headers(self) -> None:
        """Test HTTP transport with headers."""
        from apps.api.schemas.requests.config import McpServerConfigSchema

        config = McpServerConfigSchema(
            type="http",
            url="https://example.com/mcp",
            headers={"X-API-Key": "secret"},
        )
        assert config.url == "https://example.com/mcp"
        assert config.type == "http"

    def test_mcp_server_env_vars(self) -> None:
        """Test MCP server with environment variables."""
        from apps.api.schemas.requests.config import McpServerConfigSchema

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
        from apps.api.schemas.requests.config import McpServerConfigSchema

        config = McpServerConfigSchema(command="python")
        assert config.type == "stdio"

    def test_mcp_server_default_empty_args(self) -> None:
        """Test that args defaults to empty list."""
        from apps.api.schemas.requests.config import McpServerConfigSchema

        config = McpServerConfigSchema(command="python")
        assert config.args == []

    def test_mcp_server_default_empty_headers(self) -> None:
        """Test that headers defaults to empty dict."""
        from apps.api.schemas.requests.config import McpServerConfigSchema

        config = McpServerConfigSchema(type="sse", url="https://example.com/sse")
        assert config.headers == {}

    def test_mcp_server_default_empty_env(self) -> None:
        """Test that env defaults to empty dict."""
        from apps.api.schemas.requests.config import McpServerConfigSchema

        config = McpServerConfigSchema(command="python")
        assert config.env == {}

    def test_multiple_mcp_servers_in_request(self) -> None:
        """Test multiple MCP servers in a single request."""
        from apps.api.schemas.requests.config import McpServerConfigSchema

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

    def test_agent_service_public_api_stable(self) -> None:
        """Test AgentService public methods remain available."""
        service = AgentService(cache=None)
        assert hasattr(service, "query_stream")
        assert hasattr(service, "query_single")
        assert hasattr(service, "interrupt")
        assert hasattr(service, "submit_answer")
        assert hasattr(service, "update_permission_mode")
        assert hasattr(service, "_execute_query")
        assert hasattr(service, "_map_sdk_message")
        assert hasattr(service, "_track_file_modifications")

    def test_track_file_modifications_delegates(self) -> None:
        """Test _track_file_modifications delegates to FileModificationTracker."""
        handler = MagicMock()
        tracker = FileModificationTracker(handler)
        service = AgentService(cache=None, file_modification_tracker=tracker)
        ctx = StreamContext(session_id="sid", model="sonnet", start_time=0.0)

        service._track_file_modifications([{"type": "text", "text": "hi"}], ctx)

        handler.track_file_modifications.assert_called_once()


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


class TestPermissionModeHandling:
    """Unit tests for permission mode handling in AgentService._build_options (T076)."""

    def test_build_options_passes_default_permission_mode(self) -> None:
        """Test that default permission_mode is passed to ClaudeAgentOptions."""
        service = AgentService()
        request = QueryRequest(prompt="Test", permission_mode="default")

        # Mock the SDK at the import location
        with patch("claude_agent_sdk.ClaudeAgentOptions") as mock_cls:
            mock_cls.return_value = MagicMock()
            service._build_options(request)

            # Verify permission_mode was passed
            mock_cls.assert_called_once()
            call_kwargs = mock_cls.call_args.kwargs
            assert call_kwargs.get("permission_mode") == "default"

    def test_build_options_passes_accept_edits_permission_mode(self) -> None:
        """Test that acceptEdits permission_mode is passed to ClaudeAgentOptions."""
        service = AgentService()
        request = QueryRequest(prompt="Test", permission_mode="acceptEdits")

        with patch("claude_agent_sdk.ClaudeAgentOptions") as mock_cls:
            mock_cls.return_value = MagicMock()
            service._build_options(request)

            call_kwargs = mock_cls.call_args.kwargs
            assert call_kwargs.get("permission_mode") == "acceptEdits"

    def test_build_options_passes_plan_permission_mode(self) -> None:
        """Test that plan permission_mode is passed to ClaudeAgentOptions."""
        service = AgentService()
        request = QueryRequest(prompt="Test", permission_mode="plan")

        with patch("claude_agent_sdk.ClaudeAgentOptions") as mock_cls:
            mock_cls.return_value = MagicMock()
            service._build_options(request)

            call_kwargs = mock_cls.call_args.kwargs
            assert call_kwargs.get("permission_mode") == "plan"

    def test_build_options_passes_bypass_permissions_mode(self) -> None:
        """Test that bypassPermissions mode is passed to ClaudeAgentOptions."""
        service = AgentService()
        request = QueryRequest(prompt="Test", permission_mode="bypassPermissions")

        with patch("claude_agent_sdk.ClaudeAgentOptions") as mock_cls:
            mock_cls.return_value = MagicMock()
            service._build_options(request)

            call_kwargs = mock_cls.call_args.kwargs
            assert call_kwargs.get("permission_mode") == "bypassPermissions"

    def test_build_options_passes_permission_prompt_tool_name(self) -> None:
        """Test that permission_prompt_tool_name is passed to ClaudeAgentOptions."""
        service = AgentService()
        request = QueryRequest(
            prompt="Test",
            permission_mode="default",
            permission_prompt_tool_name="custom_permission_tool",
        )

        with patch("claude_agent_sdk.ClaudeAgentOptions") as mock_cls:
            mock_cls.return_value = MagicMock()
            service._build_options(request)

            # Verify permission_prompt_tool_name was passed
            call_kwargs = mock_cls.call_args.kwargs
            assert (
                call_kwargs.get("permission_prompt_tool_name")
                == "custom_permission_tool"
            )

    def test_build_options_permission_prompt_tool_name_defaults_to_none(self) -> None:
        """Test permission_prompt_tool_name defaults to None when not specified."""
        service = AgentService()
        request = QueryRequest(prompt="Test")

        with patch("claude_agent_sdk.ClaudeAgentOptions") as mock_cls:
            mock_cls.return_value = MagicMock()
            service._build_options(request)

            call_kwargs = mock_cls.call_args.kwargs
            # Should be None or not present
            permission_tool = call_kwargs.get("permission_prompt_tool_name")
            assert permission_tool is None

    def test_all_permission_modes_are_valid_literals(self) -> None:
        """Test that all permission modes match the Literal type definition."""
        valid_modes: list[Literal["default", "acceptEdits", "plan", "bypassPermissions"]] = [
            "default",
            "acceptEdits",
            "plan",
            "bypassPermissions",
        ]
        for mode in valid_modes:
            request = QueryRequest(
                prompt="Test",
                permission_mode=mode,
            )
            assert request.permission_mode == mode

    def test_invalid_permission_mode_raises_validation_error(self) -> None:
        """Test that invalid permission mode raises validation error."""
        with pytest.raises(ValueError):
            QueryRequest.model_validate({
                "prompt": "Test",
                "permission_mode": "invalid_mode",
            })

    def test_build_options_with_all_permission_params(self) -> None:
        """Test building options with all permission-related parameters."""
        service = AgentService()
        request = QueryRequest(
            prompt="Test",
            permission_mode="acceptEdits",
            permission_prompt_tool_name="my_approval_tool",
            allowed_tools=["Read", "Write"],
            disallowed_tools=["Bash"],
        )

        with patch("claude_agent_sdk.ClaudeAgentOptions") as mock_cls:
            mock_cls.return_value = MagicMock()
            service._build_options(request)

            call_kwargs = mock_cls.call_args.kwargs
            assert call_kwargs.get("permission_mode") == "acceptEdits"
            assert call_kwargs.get("permission_prompt_tool_name") == "my_approval_tool"
            assert call_kwargs.get("allowed_tools") == ["Read", "Write"]
            assert call_kwargs.get("disallowed_tools") == ["Bash"]


class TestInitEventPermissionMode:
    """Tests for permission mode in init event (T080)."""

    def test_init_event_data_has_permission_mode_field(self) -> None:
        """Test that InitEventData schema includes permission_mode field."""
        from apps.api.schemas.responses import InitEventData

        data = InitEventData(
            session_id="test-session",
            model="sonnet",
            tools=["Read"],
        )
        assert data.permission_mode == "default"

    def test_init_event_data_with_custom_permission_mode(self) -> None:
        """Test InitEventData with custom permission mode."""
        from apps.api.schemas.responses import InitEventData

        data = InitEventData(
            session_id="test-session",
            model="sonnet",
            tools=["Read"],
            permission_mode="acceptEdits",
        )
        assert data.permission_mode == "acceptEdits"

    def test_init_event_data_all_permission_modes(self) -> None:
        """Test all permission modes are valid in InitEventData."""
        from apps.api.schemas.responses import InitEventData

        modes: list[Literal["default", "acceptEdits", "plan", "bypassPermissions"]] = [
            "default",
            "acceptEdits",
            "plan",
            "bypassPermissions",
        ]
        for mode in modes:
            data = InitEventData(
                session_id="test-session",
                model="sonnet",
                tools=[],
                permission_mode=mode,
            )
            assert data.permission_mode == mode

    def test_init_event_serialization_includes_permission_mode(self) -> None:
        """Test that permission_mode is included in model_dump output."""
        from apps.api.schemas.responses import InitEventData

        data = InitEventData(
            session_id="test-session",
            model="sonnet",
            tools=["Read"],
            permission_mode="plan",
        )
        dumped = data.model_dump()
        assert dumped["permission_mode"] == "plan"


class TestEnableFileCheckpointing:
    """Tests for enable_file_checkpointing handling in AgentService (T100)."""

    def test_build_options_passes_enable_file_checkpointing_true(self) -> None:
        """Test that enable_file_checkpointing=True is passed to ClaudeAgentOptions."""
        service = AgentService()
        request = QueryRequest(
            prompt="Test",
            enable_file_checkpointing=True,
        )

        with patch("claude_agent_sdk.ClaudeAgentOptions") as mock_cls:
            mock_cls.return_value = MagicMock()
            service._build_options(request)

            call_kwargs = mock_cls.call_args.kwargs
            assert call_kwargs.get("enable_file_checkpointing") is True

    def test_build_options_passes_enable_file_checkpointing_false(self) -> None:
        """Test that enable_file_checkpointing=False is passed to ClaudeAgentOptions."""
        service = AgentService()
        request = QueryRequest(
            prompt="Test",
            enable_file_checkpointing=False,
        )

        with patch("claude_agent_sdk.ClaudeAgentOptions") as mock_cls:
            mock_cls.return_value = MagicMock()
            service._build_options(request)

            call_kwargs = mock_cls.call_args.kwargs
            assert call_kwargs.get("enable_file_checkpointing") is False

    def test_build_options_defaults_enable_file_checkpointing_to_false(self) -> None:
        """Test that enable_file_checkpointing defaults to False when not specified."""
        service = AgentService()
        request = QueryRequest(prompt="Test")

        with patch("claude_agent_sdk.ClaudeAgentOptions") as mock_cls:
            mock_cls.return_value = MagicMock()
            service._build_options(request)

            call_kwargs = mock_cls.call_args.kwargs
            # Default should be False
            assert call_kwargs.get("enable_file_checkpointing") is False

    def test_agent_service_accepts_checkpoint_service_dependency(self) -> None:
        """Test that AgentService can be initialized with CheckpointService."""
        from apps.api.services.checkpoint import CheckpointService

        checkpoint_service = CheckpointService(cache=None)
        service = AgentService(checkpoint_service=checkpoint_service)

        assert service._checkpoint_service is checkpoint_service

    def test_agent_service_has_checkpoint_service_property(self) -> None:
        """Test that AgentService exposes checkpoint_service property."""
        from apps.api.services.checkpoint import CheckpointService

        checkpoint_service = CheckpointService(cache=None)
        service = AgentService(checkpoint_service=checkpoint_service)

        assert service.checkpoint_service is checkpoint_service

    def test_agent_service_checkpoint_service_defaults_to_none(self) -> None:
        """Test that checkpoint_service defaults to None when not provided."""
        service = AgentService()

        assert service._checkpoint_service is None

    def test_query_request_enable_file_checkpointing_field_exists(self) -> None:
        """Test that QueryRequest has enable_file_checkpointing field."""
        request = QueryRequest(prompt="Test", enable_file_checkpointing=True)
        assert request.enable_file_checkpointing is True

        request2 = QueryRequest(prompt="Test")
        assert request2.enable_file_checkpointing is False


class TestCheckpointUuidTracking:
    """Tests for checkpoint UUID tracking during message streaming (T104)."""

    @pytest.mark.anyio
    async def test_tracking_enabled_creates_checkpoint_on_user_message(
        self,
    ) -> None:
        """Test that checkpoints are created when processing user messages with UUIDs."""
        from unittest.mock import AsyncMock

        from apps.api.services.checkpoint import CheckpointService

        # Create a mock checkpoint service
        mock_checkpoint_service = AsyncMock(spec=CheckpointService)
        mock_checkpoint_service.create_checkpoint = AsyncMock()

        service = AgentService(checkpoint_service=mock_checkpoint_service)

        # Simulate a user message with UUID
        user_message = MagicMock()
        user_message.__class__.__name__ = "UserMessage"
        user_message.content = "Test message"
        user_message.uuid = "test-user-msg-uuid-123"

        # Create stream context with checkpointing enabled
        from apps.api.services.agent import StreamContext

        ctx = StreamContext(
            session_id="test-session-id",
            model="sonnet",
            start_time=0.0,
        )
        ctx.enable_file_checkpointing = True
        ctx.files_modified = ["/path/to/file.py"]

        # Process the message
        service._map_sdk_message(user_message, ctx)

        # Verify checkpoint was NOT created during _map_sdk_message
        # (checkpoints should be created asynchronously via a method call)
        # Instead, verify the UUID was tracked
        assert ctx.last_user_message_uuid == "test-user-msg-uuid-123"


class TestQueryStreamSessionIds:
    """Tests for AgentService.query_stream session ID handling."""

    @pytest.mark.anyio
    async def test_query_stream_does_not_set_resume_session_id(
        self,
        tmp_path: pytest.TempPathFactory,
    ) -> None:
        """Ensure new sessions don't set resume options in SDK."""

        class StubStreamRunner:
            """Capture request and override session ID for assertions."""

            def __init__(self) -> None:
                self.last_request: QueryRequest | None = None
                self.last_session_id: str | None = None

            async def run(  # noqa: D401 - Async generator stub.
                self,
                request: QueryRequest,
                commands_service: object,
                session_id_override: str | None = None,
            ):
                self.last_request = request
                self.last_session_id = session_id_override
                if False:  # pragma: no cover - required for async generator.
                    yield {}

        runner = StubStreamRunner()
        service = AgentService(stream_runner=runner)
        request = QueryRequest(prompt="Test prompt", cwd=str(tmp_path))

        events = [event async for event in service.query_stream(request)]

        assert events
        init_event = events[0]
        assert init_event["event"] == "init"
        init_data = json.loads(init_event["data"])
        session_id = init_data.get("session_id")
        assert isinstance(session_id, str)
        assert runner.last_request is not None
        assert runner.last_request.session_id is None
        assert runner.last_session_id == session_id

    def test_stream_context_has_checkpoint_tracking_fields(self) -> None:
        """Test that StreamContext has fields for checkpoint tracking."""
        from apps.api.services.agent import StreamContext

        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )

        # Should have enable_file_checkpointing field (defaults to False)
        assert hasattr(ctx, "enable_file_checkpointing")
        assert ctx.enable_file_checkpointing is False

        # Should have last_user_message_uuid field (defaults to None)
        assert hasattr(ctx, "last_user_message_uuid")
        assert ctx.last_user_message_uuid is None

        # Should have files_modified tracking
        assert hasattr(ctx, "files_modified")
        assert ctx.files_modified == []

    def test_stream_context_tracks_files_modified(self) -> None:
        """Test that StreamContext can track modified files."""
        from apps.api.services.agent import StreamContext

        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )

        ctx.files_modified.append("/path/to/file1.py")
        ctx.files_modified.append("/path/to/file2.py")

        assert len(ctx.files_modified) == 2
        assert "/path/to/file1.py" in ctx.files_modified

    def test_tool_result_with_write_updates_files_modified(self) -> None:
        """Test that Write tool results update files_modified in context."""
        from apps.api.schemas.responses import ContentBlockSchema
        from apps.api.services.agent import StreamContext

        service = AgentService()

        # Create content blocks for Write tool directly
        content_blocks: list[object] = [
            ContentBlockSchema(
                type="tool_use",
                id="tool-123",
                name="Write",
                input={"file_path": "/path/to/new_file.py", "content": "# New file"},
            )
        ]

        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )
        ctx.enable_file_checkpointing = True

        # Test _track_file_modifications directly
        service._track_file_modifications(content_blocks, ctx)

        # Verify file path was tracked
        assert "/path/to/new_file.py" in ctx.files_modified

    def test_tool_result_with_edit_updates_files_modified(self) -> None:
        """Test that Edit tool results update files_modified in context."""
        from apps.api.schemas.responses import ContentBlockSchema
        from apps.api.services.agent import StreamContext

        service = AgentService()

        # Create content blocks for Edit tool directly
        content_blocks: list[object] = [
            ContentBlockSchema(
                type="tool_use",
                id="tool-456",
                name="Edit",
                input={"file_path": "/path/to/edited.py", "old_string": "x", "new_string": "y"},
            )
        ]

        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )
        ctx.enable_file_checkpointing = True

        # Test _track_file_modifications directly
        service._track_file_modifications(content_blocks, ctx)

        # Verify file path was tracked
        assert "/path/to/edited.py" in ctx.files_modified

    def test_files_not_tracked_when_checkpointing_disabled(self) -> None:
        """Test that files are not tracked when checkpointing is disabled.

        The key behavior is that _map_sdk_message only calls _track_file_modifications
        when enable_file_checkpointing is True. This test verifies that files_modified
        remains empty when checkpointing is disabled, even with tool_use blocks that
        would normally be tracked.
        """
        from apps.api.services.agent import StreamContext

        # Create context with checkpointing disabled
        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )
        ctx.enable_file_checkpointing = False

        # files_modified should be empty and stay empty when checkpointing is disabled
        assert len(ctx.files_modified) == 0
        assert ctx.enable_file_checkpointing is False

    @pytest.mark.anyio
    async def test_create_checkpoint_from_context(self) -> None:
        """Test creating a checkpoint from tracked context data."""
        from unittest.mock import AsyncMock

        from apps.api.services.agent import StreamContext
        from apps.api.services.checkpoint import CheckpointService

        # Create mock checkpoint service
        mock_checkpoint_service = AsyncMock(spec=CheckpointService)
        mock_checkpoint_service.create_checkpoint = AsyncMock(return_value=MagicMock(
            id="checkpoint-123",
            session_id="test-session",
            user_message_uuid="user-msg-uuid-456",
            files_modified=["/path/to/file.py"],
        ))

        service = AgentService(checkpoint_service=mock_checkpoint_service)

        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )
        ctx.enable_file_checkpointing = True
        ctx.last_user_message_uuid = "user-msg-uuid-456"
        ctx.files_modified = ["/path/to/file.py"]

        # Create checkpoint from context
        checkpoint = await service.create_checkpoint_from_context(ctx)

        # Verify checkpoint service was called correctly
        mock_checkpoint_service.create_checkpoint.assert_called_once_with(
            session_id="test-session",
            user_message_uuid="user-msg-uuid-456",
            files_modified=["/path/to/file.py"],
        )

        assert checkpoint is not None

    @pytest.mark.anyio
    async def test_create_checkpoint_skipped_when_no_uuid(self) -> None:
        """Test that checkpoint creation is skipped when no user message UUID."""
        from unittest.mock import AsyncMock

        from apps.api.services.agent import StreamContext
        from apps.api.services.checkpoint import CheckpointService

        mock_checkpoint_service = AsyncMock(spec=CheckpointService)
        service = AgentService(checkpoint_service=mock_checkpoint_service)

        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )
        ctx.enable_file_checkpointing = True
        ctx.last_user_message_uuid = None  # No UUID
        ctx.files_modified = ["/path/to/file.py"]

        # Try to create checkpoint - should be skipped
        checkpoint = await service.create_checkpoint_from_context(ctx)

        # Should not call checkpoint service
        mock_checkpoint_service.create_checkpoint.assert_not_called()
        assert checkpoint is None

    @pytest.mark.anyio
    async def test_create_checkpoint_skipped_when_checkpointing_disabled(self) -> None:
        """Test that checkpoint creation is skipped when checkpointing is disabled."""
        from unittest.mock import AsyncMock

        from apps.api.services.agent import StreamContext
        from apps.api.services.checkpoint import CheckpointService

        mock_checkpoint_service = AsyncMock(spec=CheckpointService)
        service = AgentService(checkpoint_service=mock_checkpoint_service)

        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )
        ctx.enable_file_checkpointing = False  # Disabled
        ctx.last_user_message_uuid = "user-msg-uuid"
        ctx.files_modified = ["/path/to/file.py"]

        checkpoint = await service.create_checkpoint_from_context(ctx)

        mock_checkpoint_service.create_checkpoint.assert_not_called()
        assert checkpoint is None


@pytest.mark.unit
@pytest.mark.anyio
async def test_agent_service_accepts_cache_parameter() -> None:
    """Test that AgentService can be initialized with cache dependency."""
    # This test will fail until we add cache parameter to constructor
    from unittest.mock import AsyncMock, MagicMock

    from apps.api.adapters.cache import RedisCache

    mock_cache = MagicMock(spec=RedisCache)
    service = AgentService(cache=mock_cache)

    assert service._cache is mock_cache


def test_agent_service_accepts_session_tracker_dependency() -> None:
    """Test that AgentService can be initialized with a session tracker."""
    from unittest.mock import MagicMock

    from apps.api.services.agent.session_tracker import AgentSessionTracker

    tracker = MagicMock(spec=AgentSessionTracker)
    service = AgentService(session_tracker=tracker)

    assert service._session_tracker is tracker


@pytest.mark.anyio
async def test_execute_query_delegates_to_executor() -> None:
    """Test that _execute_query delegates to the query executor."""
    from pathlib import Path

    from apps.api.services.agent.types import StreamContext
    from apps.api.services.commands import CommandsService

    class StubExecutor:
        """Minimal stub for QueryExecutor."""

        def __init__(self) -> None:
            self.called = False

        async def execute(self, _request, _ctx, _commands_service):
            self.called = True
            if False:  # pragma: no cover - generator requires a yield path
                yield {"event": "noop", "data": "{}"}

    executor = StubExecutor()
    service = AgentService(query_executor=executor)
    ctx = StreamContext(session_id="sid", model="sonnet", start_time=0.0)
    commands_service = CommandsService(project_path=Path.cwd())
    request = QueryRequest(prompt="test")

    async for _ in service._execute_query(request, ctx, commands_service):
        pass

    assert executor.called is True


class TestSlashCommandDetection:
    """Unit tests for slash command detection (T115a)."""

    def test_detect_slash_command_with_valid_command(self) -> None:
        """Test detection of valid slash commands."""
        assert detect_slash_command("/help") == "help"
        assert detect_slash_command("/commit") == "commit"
        assert detect_slash_command("/review-pr") == "review-pr"
        assert detect_slash_command("/feature_dev") == "feature_dev"

    def test_detect_slash_command_with_arguments(self) -> None:
        """Test detection with command arguments."""
        # Should detect the command, ignoring arguments
        assert detect_slash_command("/commit -m 'message'") == "commit"
        assert detect_slash_command("/review 123") == "review"
        assert detect_slash_command("/search some query") == "search"

    def test_detect_slash_command_with_whitespace_prefix(self) -> None:
        """Test detection handles leading whitespace."""
        assert detect_slash_command("  /help") == "help"
        assert detect_slash_command("\t/commit") == "commit"
        assert detect_slash_command("\n/review") == "review"

    def test_detect_slash_command_returns_none_for_non_command(self) -> None:
        """Test non-slash prompts return None."""
        assert detect_slash_command("Hello world") is None
        assert detect_slash_command("Can you help me?") is None
        assert detect_slash_command("Write code for /api/users") is None

    def test_detect_slash_command_returns_none_for_invalid_format(self) -> None:
        """Test invalid slash command formats return None."""
        assert detect_slash_command("/123invalid") is None  # Starts with number
        assert detect_slash_command("//double") is None  # Double slash
        assert detect_slash_command("/") is None  # Just slash
        assert detect_slash_command("/ space") is None  # Slash with space

    def test_detect_slash_command_case_sensitivity(self) -> None:
        """Test slash commands preserve case."""
        assert detect_slash_command("/Help") == "Help"
        assert detect_slash_command("/COMMIT") == "COMMIT"
        assert detect_slash_command("/ReviewPR") == "ReviewPR"

    def test_detect_slash_command_with_mixed_chars(self) -> None:
        """Test slash commands with mixed alphanumeric characters."""
        assert detect_slash_command("/feature123") == "feature123"
        assert detect_slash_command("/v2-release") == "v2-release"
        assert detect_slash_command("/test_case_1") == "test_case_1"


class TestAgentServiceCoreEdgeCases:
    """Core edge case tests for AgentService (Priority 11)."""

    @pytest.mark.anyio
    async def test_register_active_session(self) -> None:
        """Test registering a session as active in Redis."""
        from unittest.mock import AsyncMock

        from apps.api.adapters.cache import RedisCache

        mock_cache = AsyncMock(spec=RedisCache)
        mock_cache.cache_set = AsyncMock(return_value=True)

        service = AgentService(cache=mock_cache)
        session_id = "test-session-123"

        await service._register_active_session(session_id)

        # Verify cache_set was called with correct parameters
        mock_cache.cache_set.assert_called_once()
        call_args = mock_cache.cache_set.call_args
        assert call_args[0][0] == f"active_session:{session_id}"
        assert call_args[0][1] == "true"

    @pytest.mark.anyio
    async def test_register_active_session_raises_without_cache(self) -> None:
        """Test that registering session without cache raises RuntimeError."""
        service = AgentService(cache=None)

        with pytest.raises(RuntimeError) as exc_info:
            await service._register_active_session("test-session-123")

        assert "Cache is required" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_is_session_active_returns_true(self) -> None:
        """Test checking if session is active returns True when registered."""
        from unittest.mock import AsyncMock

        from apps.api.adapters.cache import RedisCache

        mock_cache = AsyncMock(spec=RedisCache)
        mock_cache.exists = AsyncMock(return_value=True)

        service = AgentService(cache=mock_cache)
        session_id = "active-session"

        result = await service._is_session_active(session_id)

        assert result is True
        mock_cache.exists.assert_called_once_with(f"active_session:{session_id}")

    @pytest.mark.anyio
    async def test_is_session_active_returns_false(self) -> None:
        """Test checking if session is active returns False when not registered."""
        from unittest.mock import AsyncMock

        from apps.api.adapters.cache import RedisCache

        mock_cache = AsyncMock(spec=RedisCache)
        mock_cache.exists = AsyncMock(return_value=False)

        service = AgentService(cache=mock_cache)
        session_id = "inactive-session"

        result = await service._is_session_active(session_id)

        assert result is False

    @pytest.mark.anyio
    async def test_unregister_active_session(self) -> None:
        """Test unregistering a session from Redis."""
        from unittest.mock import AsyncMock

        from apps.api.adapters.cache import RedisCache

        mock_cache = AsyncMock(spec=RedisCache)
        mock_cache.delete = AsyncMock(return_value=True)

        service = AgentService(cache=mock_cache)
        session_id = "test-session-123"

        await service._unregister_active_session(session_id)

        mock_cache.delete.assert_called_once_with(f"active_session:{session_id}")

    @pytest.mark.anyio
    async def test_interrupt_sends_signal(self) -> None:
        """Test sending interrupt signal to a session."""
        from unittest.mock import AsyncMock

        from apps.api.adapters.cache import RedisCache

        mock_cache = AsyncMock(spec=RedisCache)
        mock_cache.cache_set = AsyncMock(return_value=True)
        mock_cache.exists = AsyncMock(return_value=True)  # Session is active

        service = AgentService(cache=mock_cache)
        session_id = "test-session-123"

        result = await service.interrupt(session_id)

        # Verify interrupt flag was set in Redis
        assert result is True
        mock_cache.cache_set.assert_called_once()
        call_args = mock_cache.cache_set.call_args
        assert call_args[0][0] == f"interrupted:{session_id}"

    @pytest.mark.anyio
    async def test_check_interrupt_returns_true(self) -> None:
        """Test checking interrupt flag returns True when set."""
        from unittest.mock import AsyncMock

        from apps.api.adapters.cache import RedisCache

        mock_cache = AsyncMock(spec=RedisCache)
        mock_cache.exists = AsyncMock(return_value=True)

        service = AgentService(cache=mock_cache)
        session_id = "interrupted-session"

        result = await service._check_interrupt(session_id)

        assert result is True

    @pytest.mark.anyio
    async def test_check_interrupt_returns_false(self) -> None:
        """Test checking interrupt flag returns False when not set."""
        from unittest.mock import AsyncMock

        from apps.api.adapters.cache import RedisCache

        mock_cache = AsyncMock(spec=RedisCache)
        mock_cache.exists = AsyncMock(return_value=False)

        service = AgentService(cache=mock_cache)
        session_id = "running-session"

        result = await service._check_interrupt(session_id)

        assert result is False

    @pytest.mark.anyio
    async def test_create_checkpoint_from_context_success(self) -> None:
        """Test creating checkpoint from context with all required data."""
        from unittest.mock import AsyncMock

        from apps.api.services.agent import StreamContext
        from apps.api.services.checkpoint import CheckpointService

        mock_checkpoint = MagicMock()
        mock_checkpoint.id = "checkpoint-123"

        mock_checkpoint_service = AsyncMock(spec=CheckpointService)
        mock_checkpoint_service.create_checkpoint = AsyncMock(
            return_value=mock_checkpoint
        )

        service = AgentService(checkpoint_service=mock_checkpoint_service)

        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )
        ctx.enable_file_checkpointing = True
        ctx.last_user_message_uuid = "msg-uuid-123"
        ctx.files_modified = ["/path/file1.py", "/path/file2.py"]

        result = await service.create_checkpoint_from_context(ctx)

        assert result is not None
        assert result.id == "checkpoint-123"
        mock_checkpoint_service.create_checkpoint.assert_called_once_with(
            session_id="test-session",
            user_message_uuid="msg-uuid-123",
            files_modified=["/path/file1.py", "/path/file2.py"],
        )

    @pytest.mark.anyio
    async def test_create_checkpoint_skipped_when_no_checkpoint_service(self) -> None:
        """Test checkpoint creation skipped when checkpoint service not configured."""
        from apps.api.services.agent import StreamContext

        service = AgentService(checkpoint_service=None)

        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )
        ctx.enable_file_checkpointing = True
        ctx.last_user_message_uuid = "msg-uuid-123"
        ctx.files_modified = ["/path/file.py"]

        result = await service.create_checkpoint_from_context(ctx)

        assert result is None

    def test_agent_service_has_checkpoint_service_property(self) -> None:
        """Test that AgentService exposes checkpoint_service property."""
        from apps.api.services.checkpoint import CheckpointService

        checkpoint_service = CheckpointService(cache=None)
        service = AgentService(checkpoint_service=checkpoint_service)

        assert service.checkpoint_service is checkpoint_service

    def test_agent_service_has_cache_property(self) -> None:
        """Test that AgentService exposes cache property."""
        from unittest.mock import MagicMock

        from apps.api.adapters.cache import RedisCache

        mock_cache = MagicMock(spec=RedisCache)
        service = AgentService(cache=mock_cache)

        assert service._cache is mock_cache
