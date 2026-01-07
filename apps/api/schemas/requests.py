"""Pydantic request models for API endpoints."""

from typing import Literal, Self

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from apps.api.types import BUILT_IN_TOOLS


def validate_tool_name(tool: str) -> bool:
    """Check if a tool name is valid.

    Args:
        tool: Tool name to validate.

    Returns:
        True if valid (built-in or MCP tool).
    """
    # Built-in tools are valid
    if tool in BUILT_IN_TOOLS:
        return True
    # MCP tools have mcp__ prefix (e.g., mcp__server__tool)
    return bool(tool.startswith("mcp__"))


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


class HooksConfigSchema(BaseModel):
    """Webhook configuration for hooks."""

    pre_tool_use: HookWebhookSchema | None = Field(None, alias="PreToolUse")
    post_tool_use: HookWebhookSchema | None = Field(None, alias="PostToolUse")
    stop: HookWebhookSchema | None = Field(None, alias="Stop")
    subagent_stop: HookWebhookSchema | None = Field(None, alias="SubagentStop")
    user_prompt_submit: HookWebhookSchema | None = Field(None, alias="UserPromptSubmit")
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


class QueryRequest(BaseModel):
    """Request to send a query to the agent."""

    prompt: str = Field(..., min_length=1, max_length=100000)
    images: list[ImageContentSchema] | None = Field(
        None, description="Images to include with prompt"
    )
    session_id: str | None = Field(None, description="Resume existing session")
    fork_session: bool = Field(False, description="Fork instead of continue")
    continue_conversation: bool = Field(False, description="Continue without resume ID")

    # Tool configuration
    allowed_tools: list[str] = Field(default_factory=list)
    disallowed_tools: list[str] = Field(default_factory=list)

    # Permission settings
    permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"] = (
        "default"
    )
    permission_prompt_tool_name: str | None = Field(
        None, description="Custom tool for permission prompts"
    )

    # Model selection
    model: str | None = Field(None, description="Claude model to use")

    # Execution limits
    max_turns: int | None = Field(None, ge=1, le=1000)
    max_buffer_size: int | None = Field(None, description="Max message buffer size")
    cwd: str | None = Field(None, description="Working directory")
    add_dirs: list[str] = Field(
        default_factory=list, description="Additional directories to include"
    )
    env: dict[str, str] = Field(default_factory=dict)

    # System prompt customization
    system_prompt: str | None = None
    system_prompt_append: str | None = Field(
        None, description="Append to default system prompt (preset+append mode)"
    )
    output_style: str | None = Field(
        None, description="Output style from .claude/output-styles/"
    )
    settings: str | None = Field(None, description="Path to settings file")
    setting_sources: list[Literal["project", "user"]] | None = None

    # Subagents
    agents: dict[str, AgentDefinitionSchema] | None = None

    # MCP servers
    mcp_servers: dict[str, McpServerConfigSchema] | None = None

    # Plugins
    plugins: list[SdkPluginConfigSchema] | None = None

    # Hooks (webhook URLs)
    hooks: HooksConfigSchema | None = None

    # File checkpointing
    enable_file_checkpointing: bool = False

    # Structured output
    output_format: OutputFormatSchema | None = None

    # Streaming options
    include_partial_messages: bool = Field(
        False, description="Include partial messages in stream"
    )

    # Sandbox configuration
    sandbox: SandboxSettingsSchema | None = None

    # User identification
    user: str | None = Field(None, description="User identifier for tracking")

    # Extra CLI arguments
    extra_args: dict[str, str | None] = Field(
        default_factory=dict, description="Additional CLI arguments"
    )

    @field_validator("allowed_tools", "disallowed_tools")
    @classmethod
    def validate_tool_names(cls, tools: list[str]) -> list[str]:
        """Validate that all tool names are valid.

        Args:
            tools: List of tool names.

        Returns:
            Validated list of tools.

        Raises:
            ValueError: If any tool name is invalid.
        """
        invalid_tools = [t for t in tools if not validate_tool_name(t)]
        if invalid_tools:
            valid_tools_msg = ", ".join(BUILT_IN_TOOLS[:5]) + "..."
            raise ValueError(
                f"Invalid tool names: {invalid_tools}. "
                f"Valid tools include: {valid_tools_msg}, "
                "or MCP tools with mcp__* prefix."
            )
        return tools

    @model_validator(mode="after")
    def validate_no_tool_conflicts(self) -> Self:
        """Validate no conflicts between allowed and disallowed tools.

        Returns:
            Self after validation.

        Raises:
            ValueError: If same tool appears in both lists.
        """
        if self.allowed_tools and self.disallowed_tools:
            conflicts = set(self.allowed_tools) & set(self.disallowed_tools)
            if conflicts:
                raise ValueError(
                    f"Tool conflict: {conflicts} appear in both "
                    "allowed_tools and disallowed_tools"
                )
        return self


class ResumeRequest(BaseModel):
    """Request to resume an existing session."""

    prompt: str = Field(..., min_length=1, max_length=100000)
    images: list[ImageContentSchema] | None = Field(
        None, description="Images to include"
    )

    # Optional configuration overrides
    allowed_tools: list[str] | None = Field(None, description="Override allowed tools")
    disallowed_tools: list[str] | None = Field(
        None, description="Override disallowed tools"
    )
    permission_mode: (
        Literal["default", "acceptEdits", "plan", "bypassPermissions"] | None
    ) = None
    max_turns: int | None = Field(None, ge=1, le=1000)
    hooks: HooksConfigSchema | None = None


class ForkRequest(BaseModel):
    """Request to fork an existing session."""

    prompt: str = Field(..., min_length=1, max_length=100000)
    images: list[ImageContentSchema] | None = Field(
        None, description="Images to include"
    )

    # Optional configuration overrides (inherited from parent if not specified)
    allowed_tools: list[str] | None = Field(None, description="Override allowed tools")
    disallowed_tools: list[str] | None = Field(
        None, description="Override disallowed tools"
    )
    permission_mode: (
        Literal["default", "acceptEdits", "plan", "bypassPermissions"] | None
    ) = None
    max_turns: int | None = Field(None, ge=1, le=1000)
    model: str | None = Field(None, description="Override model for forked session")
    hooks: HooksConfigSchema | None = None


class AnswerRequest(BaseModel):
    """Request to answer an AskUserQuestion from the agent."""

    answer: str = Field(..., min_length=1, max_length=100000)


class RewindRequest(BaseModel):
    """Request to rewind session to a checkpoint."""

    checkpoint_uuid: str = Field(..., description="UUID of checkpoint to rewind to")


class ControlRequest(BaseModel):
    """Request to send a control event to an active session (FR-015).

    Control events allow dynamic changes during streaming, such as changing
    the permission mode mid-session.
    """

    type: Literal["permission_mode_change"] = Field(
        ..., description="Type of control event"
    )
    permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"] | None = (
        Field(None, description="New permission mode (required for permission_mode_change)")
    )

    @model_validator(mode="after")
    def validate_permission_mode_for_change(self) -> Self:
        """Validate that permission_mode is provided for permission_mode_change type.

        Returns:
            Self after validation.

        Raises:
            ValueError: If permission_mode is missing for permission_mode_change type.
        """
        if self.type == "permission_mode_change" and self.permission_mode is None:
            raise ValueError(
                "permission_mode is required for permission_mode_change control event"
            )
        return self
