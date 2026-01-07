"""Configuration schemas for requests."""

from typing import Literal, Self

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from apps.api.schemas.validators import (
    SHELL_METACHAR_PATTERN,
    validate_no_null_bytes,
    validate_url_not_internal,
)


class ImageContentSchema(BaseModel):
    """Image content for multimodal prompts."""

    type: Literal["base64", "url"] = "base64"
    media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"]
    data: str = Field(..., description="Base64-encoded image data or URL")


class AgentDefinitionSchema(BaseModel):
    """Definition for a custom subagent."""

    description: str = Field(..., min_length=1, max_length=1000)
    prompt: str = Field(..., min_length=1, max_length=50000)
    tools: list[str] | None = None
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None

    @model_validator(mode="after")
    def validate_no_task_tool(self) -> Self:
        """Validate that subagents cannot have Task tool."""
        if self.tools and "Task" in self.tools:
            raise ValueError("Subagents cannot have Task tool (no nested subagents)")
        return self


class McpServerConfigSchema(BaseModel):
    """Configuration for an MCP server."""

    # Stdio transport
    command: str | None = None
    args: list[str] = Field(default_factory=list)

    # Remote transports
    type: Literal["stdio", "sse", "http"] = "stdio"
    url: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)

    # Environment
    env: dict[str, str] = Field(default_factory=dict)

    @field_validator("command")
    @classmethod
    def validate_command_security(cls, v: str | None) -> str | None:
        """Validate command for injection attacks (T128 security)."""
        if v is not None:
            validate_no_null_bytes(v, "command")
            if SHELL_METACHAR_PATTERN.search(v):
                raise ValueError(
                    "Shell metacharacters not allowed in command. "
                    "Use 'args' for command arguments."
                )
        return v

    @field_validator("args")
    @classmethod
    def validate_args_security(cls, v: list[str]) -> list[str]:
        """Validate args for injection attacks (T128 security)."""
        for arg in v:
            validate_no_null_bytes(arg, "args")
        return v

    @field_validator("url")
    @classmethod
    def validate_url_security(cls, v: str | None) -> str | None:
        """Validate URL for SSRF attacks (T128 security)."""
        if v is not None:
            validate_url_not_internal(v)
        return v

    @model_validator(mode="after")
    def validate_transport(self) -> Self:
        """Validate transport configuration."""
        if self.type == "stdio" and not self.command:
            raise ValueError("stdio transport requires 'command'")
        if self.type in ("sse", "http") and not self.url:
            raise ValueError(f"{self.type} transport requires 'url'")
        return self


class HookWebhookSchema(BaseModel):
    """Webhook configuration for a hook event."""

    url: HttpUrl
    headers: dict[str, str] = Field(default_factory=dict)
    timeout: int = Field(default=30, ge=1, le=300)
    matcher: str | None = Field(None, description="Regex pattern for tool names")

    @field_validator("url")
    @classmethod
    def validate_webhook_url_security(cls, v: HttpUrl) -> HttpUrl:
        """Validate webhook URL for SSRF attacks (T128 security)."""
        validate_url_not_internal(str(v))
        return v


class HooksConfigSchema(BaseModel):
    """Webhook configuration for hooks."""

    pre_tool_use: HookWebhookSchema | None = Field(None, alias="PreToolUse")
    post_tool_use: HookWebhookSchema | None = Field(None, alias="PostToolUse")
    stop: HookWebhookSchema | None = Field(None, alias="Stop")
    subagent_stop: HookWebhookSchema | None = Field(None, alias="SubagentStop")
    user_prompt_submit: HookWebhookSchema | None = Field(
        None, alias="UserPromptSubmit"
    )
    pre_compact: HookWebhookSchema | None = Field(None, alias="PreCompact")
    notification: HookWebhookSchema | None = Field(None, alias="Notification")

    model_config = {"populate_by_name": True}


class OutputFormatSchema(BaseModel):
    """Structured output format specification."""

    type: Literal["json", "json_schema"] = "json_schema"
    schema_: dict[str, object] | None = Field(None, alias="schema")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_schema_requirement(self) -> Self:
        """Validate schema is provided for json_schema type."""
        if self.type == "json_schema" and not self.schema_:
            raise ValueError("json_schema type requires 'schema' field")
        return self

    @field_validator("schema_")
    @classmethod
    def validate_json_schema(
        cls, v: dict[str, object] | None
    ) -> dict[str, object] | None:
        """Validate JSON schema has type property."""
        if v is not None and "type" not in v:
            raise ValueError("JSON schema must have 'type' property")
        return v


class SdkPluginConfigSchema(BaseModel):
    """Configuration for an SDK plugin."""

    name: str = Field(..., min_length=1, description="Plugin name")
    path: str | None = Field(None, description="Path to plugin directory")
    enabled: bool = Field(True, description="Whether plugin is enabled")


class SandboxSettingsSchema(BaseModel):
    """Sandbox configuration for agent execution."""

    enabled: bool = Field(True, description="Enable sandbox mode")
    allowed_paths: list[str] = Field(
        default_factory=list, description="Paths accessible in sandbox"
    )
    network_access: bool = Field(False, description="Allow network access in sandbox")
