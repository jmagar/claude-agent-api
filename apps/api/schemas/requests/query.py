"""Query request schema."""

from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from apps.api.schemas.requests.config import (
    AgentDefinitionSchema,
    HooksConfigSchema,
    ImageContentSchema,
    McpServerConfigSchema,
    OutputFormatSchema,
    SandboxSettingsSchema,
    SdkPluginConfigSchema,
)
from apps.api.schemas.validators import (
    validate_model_name,
    validate_no_null_bytes,
    validate_no_path_traversal,
    validate_tool_name,
)
from apps.api.types import BUILT_IN_TOOLS


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

    @field_validator("model")
    @classmethod
    def validate_model(cls, model: str | None) -> str | None:
        """Validate that the model name is valid."""
        return validate_model_name(model)

    @field_validator("cwd")
    @classmethod
    def validate_cwd_security(cls, v: str | None) -> str | None:
        """Validate cwd for path traversal attacks (T128 security)."""
        if v is not None:
            validate_no_null_bytes(v, "cwd")
            validate_no_path_traversal(v, "cwd")
        return v

    @field_validator("add_dirs")
    @classmethod
    def validate_add_dirs_security(cls, v: list[str]) -> list[str]:
        """Validate add_dirs for path traversal attacks (T128 security)."""
        for path in v:
            validate_no_null_bytes(path, "add_dirs")
            validate_no_path_traversal(path, "add_dirs")
        return v

    @field_validator("env")
    @classmethod
    def validate_env_security(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate environment variables for injection (T128 security)."""
        for key, value in v.items():
            validate_no_null_bytes(key, "env key")
            validate_no_null_bytes(value, "env value")
            # Check for dangerous env var names
            if key.upper() in ("LD_PRELOAD", "LD_LIBRARY_PATH", "PATH"):
                raise ValueError(f"Setting {key} environment variable is not allowed")
        return v

    @field_validator("allowed_tools", "disallowed_tools")
    @classmethod
    def validate_tool_names(cls, tools: list[str]) -> list[str]:
        """Validate that all tool names are valid."""
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
        """Validate no conflicts between allowed and disallowed tools."""
        if self.allowed_tools and self.disallowed_tools:
            conflicts = set(self.allowed_tools) & set(self.disallowed_tools)
            if conflicts:
                raise ValueError(
                    f"Tool conflict: {conflicts} appear in both "
                    "allowed_tools and disallowed_tools"
                )
        return self
