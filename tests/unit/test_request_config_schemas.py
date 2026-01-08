"""Tests for config request schemas."""

import pytest
from pydantic import ValidationError

from apps.api.schemas.requests import (
    AgentDefinitionSchema,
    HooksConfigSchema,
    HookWebhookSchema,
    ImageContentSchema,
    McpServerConfigSchema,
    OutputFormatSchema,
    SandboxSettingsSchema,
    SdkPluginConfigSchema,
)


class TestImageContentSchema:
    """Tests for ImageContentSchema."""

    def test_valid_base64_image(self) -> None:
        """Test valid base64 image."""
        image = ImageContentSchema(
            type="base64",
            media_type="image/png",
            data="iVBORw0KGgoAAAANS..."
        )
        assert image.type == "base64"

    def test_valid_url_image(self) -> None:
        """Test valid URL image."""
        image = ImageContentSchema(
            type="url",
            media_type="image/jpeg",
            data="https://example.com/image.jpg"
        )
        assert image.type == "url"


class TestAgentDefinitionSchema:
    """Tests for AgentDefinitionSchema."""

    def test_valid_agent(self) -> None:
        """Test valid agent definition."""
        agent = AgentDefinitionSchema(
            description="Test agent",
            prompt="You are a test agent"
        )
        assert agent.description == "Test agent"

    def test_agent_cannot_have_task_tool(self) -> None:
        """Test agents cannot have Task tool."""
        with pytest.raises(ValidationError, match="cannot have Task tool"):
            AgentDefinitionSchema(
                description="Test agent",
                prompt="You are a test agent",
                tools=["Read", "Task"]
            )


class TestMcpServerConfigSchema:
    """Tests for McpServerConfigSchema."""

    def test_valid_stdio_transport(self) -> None:
        """Test valid stdio transport."""
        config = McpServerConfigSchema(
            type="stdio",
            command="python",
            args=["-m", "mcp_server"]
        )
        assert config.type == "stdio"

    def test_stdio_requires_command(self) -> None:
        """Test stdio transport requires command."""
        with pytest.raises(ValidationError, match="requires 'command'"):
            McpServerConfigSchema(type="stdio")

    def test_valid_sse_transport(self) -> None:
        """Test valid SSE transport."""
        config = McpServerConfigSchema(
            type="sse",
            url="https://example.com/sse"
        )
        assert config.type == "sse"

    def test_sse_requires_url(self) -> None:
        """Test SSE transport requires URL."""
        with pytest.raises(ValidationError, match="requires 'url'"):
            McpServerConfigSchema(type="sse")

    def test_command_with_shell_metachar_rejected(self) -> None:
        """Test shell metacharacters in command are rejected (T128)."""
        with pytest.raises(ValidationError, match="Shell metacharacters"):
            McpServerConfigSchema(
                type="stdio",
                command="python; rm -rf /"
            )

    def test_command_with_null_byte_rejected(self) -> None:
        """Test null bytes in command are rejected (T128)."""
        with pytest.raises(ValidationError, match="Null bytes"):
            McpServerConfigSchema(
                type="stdio",
                command="python\x00--version"
            )

    def test_args_with_null_byte_rejected(self) -> None:
        """Test null bytes in args are rejected (T128)."""
        with pytest.raises(ValidationError, match="Null bytes"):
            McpServerConfigSchema(
                type="stdio",
                command="python",
                args=["-m\x00inject"]
            )

    def test_url_to_internal_rejected(self) -> None:
        """Test SSRF protection on URL (T128)."""
        with pytest.raises(ValidationError, match="internal resources"):
            McpServerConfigSchema(
                type="sse",
                url="http://localhost:8080/sse"
            )


class TestHookWebhookSchema:
    """Tests for HookWebhookSchema."""

    def test_valid_external_url(self) -> None:
        """Test valid external webhook URL."""
        webhook = HookWebhookSchema(url="https://example.com/webhook")
        assert str(webhook.url) == "https://example.com/webhook"

    def test_internal_url_rejected(self) -> None:
        """Test SSRF protection on webhook URL (T128)."""
        with pytest.raises(ValidationError, match="internal resources"):
            HookWebhookSchema(url="http://127.0.0.1:8080/webhook")

    def test_metadata_url_rejected(self) -> None:
        """Test cloud metadata SSRF protection (T128)."""
        with pytest.raises(ValidationError, match="internal resources"):
            HookWebhookSchema(url="http://metadata.google.internal/")


class TestOutputFormatSchema:
    """Tests for OutputFormatSchema."""

    def test_json_schema_type_requires_schema(self) -> None:
        """Test json_schema type requires schema field."""
        with pytest.raises(ValidationError, match="requires 'schema' field"):
            OutputFormatSchema(type="json_schema")

    def test_valid_json_schema(self) -> None:
        """Test valid JSON schema."""
        fmt = OutputFormatSchema(
            type="json_schema",
            schema_={"type": "object", "properties": {}}
        )
        assert fmt.type == "json_schema"

    def test_json_schema_must_have_type(self) -> None:
        """Test JSON schema must have type property."""
        with pytest.raises(ValidationError, match="must have 'type' property"):
            OutputFormatSchema(
                type="json_schema",
                schema_={"properties": {}}
            )


class TestHooksConfigSchema:
    """Tests for HooksConfigSchema."""

    def test_valid_hooks(self) -> None:
        """Test valid hooks configuration."""
        hooks = HooksConfigSchema(
            pre_tool_use=HookWebhookSchema(url="https://example.com/hook")
        )
        assert hooks.pre_tool_use is not None

    def test_hooks_with_alias(self) -> None:
        """Test hooks with alias names."""
        hooks = HooksConfigSchema.model_validate({
            "PreToolUse": {"url": "https://example.com/hook"}
        })
        assert hooks.pre_tool_use is not None


class TestSdkPluginConfigSchema:
    """Tests for SdkPluginConfigSchema."""

    def test_valid_plugin(self) -> None:
        """Test valid plugin configuration."""
        plugin = SdkPluginConfigSchema(name="test-plugin")
        assert plugin.name == "test-plugin"
        assert plugin.enabled is True

    def test_plugin_name_required(self) -> None:
        """Test plugin name is required."""
        with pytest.raises(ValidationError):
            SdkPluginConfigSchema()  # type: ignore[call-arg]

    def test_plugin_with_path(self) -> None:
        """Test plugin with path."""
        plugin = SdkPluginConfigSchema(
            name="custom-plugin",
            path="/path/to/plugin",
            enabled=False
        )
        assert plugin.path == "/path/to/plugin"
        assert plugin.enabled is False


class TestSandboxSettingsSchema:
    """Tests for SandboxSettingsSchema."""

    def test_default_sandbox(self) -> None:
        """Test default sandbox settings."""
        sandbox = SandboxSettingsSchema()
        assert sandbox.enabled is True
        assert sandbox.allowed_paths == []
        assert sandbox.network_access is False

    def test_custom_sandbox(self) -> None:
        """Test custom sandbox settings."""
        sandbox = SandboxSettingsSchema(
            enabled=True,
            allowed_paths=["/tmp", "/data"],
            network_access=True
        )
        assert sandbox.allowed_paths == ["/tmp", "/data"]
        assert sandbox.network_access is True
