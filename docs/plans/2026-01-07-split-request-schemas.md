# Split Request Schemas Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **📁 Organization Note:** When this plan is fully implemented and verified, move this file to `docs/plans/complete/` to keep the plans folder organized.

**Goal:** Split the monolithic `apps/api/schemas/requests.py` (653 lines) into a modular structure with single-responsibility files.

**Architecture:** Create `schemas/requests/` package with dedicated modules for validators, config schemas, query, session operations, and control operations. Re-export all schemas from `__init__.py` to maintain backward compatibility.

**Tech Stack:** Python 3.11+, Pydantic v2, pytest

---

## Summary

Split `apps/api/schemas/requests.py` into:
```
schemas/
├── validators.py         # Security patterns, security validators, model validators
├── requests/
│   ├── __init__.py       # Re-export all request schemas
│   ├── config.py         # ImageContentSchema, AgentDefinitionSchema, McpServerConfigSchema, etc.
│   ├── query.py          # QueryRequest
│   ├── sessions.py       # ResumeRequest, ForkRequest, AnswerRequest
│   └── control.py        # ControlRequest, RewindRequest
```

## Files to Update After Split

- `apps/api/routes/query.py`
- `apps/api/routes/sessions.py`
- `apps/api/routes/websocket.py`
- `apps/api/services/agent.py`
- `apps/api/services/webhook.py`
- `tests/unit/test_schemas.py`
- `tests/unit/test_webhook_service.py`
- `tests/unit/test_agent_service.py`
- `tests/integration/test_permissions.py`
- `tests/integration/test_hooks.py`
- `tests/integration/test_structured_output.py`
- `tests/integration/test_tools.py`
- `tests/integration/test_subagents.py`

---

### Task 1: Create validators.py Module

**Files:**
- Create: `apps/api/schemas/validators.py`
- Test: `tests/unit/test_validators.py`

**Step 1: Write the failing test**

Create `tests/unit/test_validators.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_validators.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'apps.api.schemas.validators'"

**Step 3: Write minimal implementation**

Create `apps/api/schemas/validators.py`:

```python
"""Validation utilities for request schemas.

Contains security patterns (T128) and validation functions for:
- Null byte detection
- Path traversal prevention
- SSRF prevention (internal URL blocking)
- Tool name validation
- Model name validation
"""

import re

from apps.api.types import BUILT_IN_TOOLS, VALID_MODEL_PREFIXES, VALID_SHORT_MODEL_NAMES

# Security: Pattern for dangerous shell metacharacters
SHELL_METACHAR_PATTERN = re.compile(r"[;&|`$(){}[\]<>!\n\r\\]")

# Security: Pattern for path traversal attempts
PATH_TRAVERSAL_PATTERN = re.compile(r"(?:\.\./|\.\.\\|%2e%2e%2f|%2e%2e/|\.%2e/|%2e\./)")

# Security: Pattern for null bytes
NULL_BYTE_PATTERN = re.compile(r"\x00")

# Security: Blocked internal URL patterns for SSRF prevention
BLOCKED_URL_PATTERNS = (
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "169.254.",  # Link-local
    "10.",  # Private Class A
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.20.",
    "172.21.",
    "172.22.",
    "172.23.",
    "172.24.",
    "172.25.",
    "172.26.",
    "172.27.",
    "172.28.",
    "172.29.",
    "172.30.",
    "172.31.",  # Private Class B
    "192.168.",  # Private Class C
    "metadata.google.internal",  # Cloud metadata
    "metadata.aws.",
    "instance-data",
)


def validate_no_null_bytes(value: str, field_name: str) -> str:
    """Check for null bytes (T128 security).

    Args:
        value: String to validate.
        field_name: Name of field for error message.

    Returns:
        The validated string.

    Raises:
        ValueError: If null bytes found.
    """
    if NULL_BYTE_PATTERN.search(value):
        raise ValueError(f"Null bytes not allowed in {field_name}")
    return value


def validate_no_path_traversal(value: str, field_name: str) -> str:
    """Check for path traversal attempts (T128 security).

    Args:
        value: String to validate.
        field_name: Name of field for error message.

    Returns:
        The validated string.

    Raises:
        ValueError: If path traversal detected.
    """
    if PATH_TRAVERSAL_PATTERN.search(value.lower()):
        raise ValueError(f"Path traversal not allowed in {field_name}")
    return value


def validate_url_not_internal(url: str) -> str:
    """Check URL is not targeting internal resources (T128 SSRF prevention).

    Args:
        url: URL to validate.

    Returns:
        The validated URL.

    Raises:
        ValueError: If URL targets internal resources.
    """
    url_lower = url.lower()
    for pattern in BLOCKED_URL_PATTERNS:
        if pattern in url_lower:
            raise ValueError(f"URLs targeting internal resources are not allowed")
    return url


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


def validate_model_name(model: str | None) -> str | None:
    """Validate that a model name is valid.

    Accepts:
        - Short names: "sonnet", "opus", "haiku"
        - Full model IDs: "claude-sonnet-4-*", "claude-opus-4-*", etc.

    Args:
        model: Model name to validate.

    Returns:
        Validated model name.

    Raises:
        ValueError: If model name is invalid.
    """
    if model is None:
        return None

    # Reject empty strings
    if not model:
        raise ValueError(
            "Model cannot be empty. Valid options: sonnet, opus, haiku, "
            "or full model IDs like claude-sonnet-4-20250514"
        )

    # Accept short model names
    if model in VALID_SHORT_MODEL_NAMES:
        return model

    # Accept full model IDs with valid prefixes
    if any(model.startswith(prefix) for prefix in VALID_MODEL_PREFIXES):
        return model

    # Invalid model name
    raise ValueError(
        f"Invalid model: '{model}'. Valid options: sonnet, opus, haiku, "
        "or full model IDs like claude-sonnet-4-20250514, "
        "claude-3-5-sonnet-20241022"
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_validators.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/api/schemas/validators.py tests/unit/test_validators.py
git commit -m "refactor: extract validators to schemas/validators.py"
```

---

### Task 2: Create requests/config.py Module

**Files:**
- Create: `apps/api/schemas/requests/__init__.py` (empty initially)
- Create: `apps/api/schemas/requests/config.py`
- Test: `tests/unit/test_request_config_schemas.py`

**Step 1: Write the failing test**

Create `tests/unit/test_request_config_schemas.py`:

```python
"""Tests for config request schemas."""

import pytest
from pydantic import ValidationError

from apps.api.schemas.requests.config import (
    AgentDefinitionSchema,
    HookWebhookSchema,
    HooksConfigSchema,
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_request_config_schemas.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `apps/api/schemas/requests/__init__.py` (empty for now):

```python
"""Request schemas package."""
```

Create `apps/api/schemas/requests/config.py`:

```python
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
        """Validate command for injection attacks (T128 security).

        Args:
            v: Command string.

        Returns:
            Validated command.

        Raises:
            ValueError: If dangerous characters found.
        """
        if v is not None:
            validate_no_null_bytes(v, "command")
            # Allow basic commands but prevent shell metacharacters
            if SHELL_METACHAR_PATTERN.search(v):
                raise ValueError(
                    "Shell metacharacters not allowed in command. "
                    "Use 'args' for command arguments."
                )
        return v

    @field_validator("args")
    @classmethod
    def validate_args_security(cls, v: list[str]) -> list[str]:
        """Validate args for injection attacks (T128 security).

        Args:
            v: Command arguments.

        Returns:
            Validated arguments.

        Raises:
            ValueError: If dangerous characters found.
        """
        for arg in v:
            validate_no_null_bytes(arg, "args")
        return v

    @field_validator("url")
    @classmethod
    def validate_url_security(cls, v: str | None) -> str | None:
        """Validate URL for SSRF attacks (T128 security).

        Args:
            v: URL string.

        Returns:
            Validated URL.

        Raises:
            ValueError: If internal URL detected.
        """
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
        """Validate webhook URL for SSRF attacks (T128 security).

        Args:
            v: URL to validate.

        Returns:
            Validated URL.

        Raises:
            ValueError: If internal URL detected.
        """
        validate_url_not_internal(str(v))
        return v


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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_request_config_schemas.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/api/schemas/requests/ tests/unit/test_request_config_schemas.py
git commit -m "refactor: extract config schemas to requests/config.py"
```

---

### Task 3: Create requests/query.py Module

**Files:**
- Create: `apps/api/schemas/requests/query.py`
- Test: `tests/unit/test_request_query_schema.py`

**Step 1: Write the failing test**

Create `tests/unit/test_request_query_schema.py`:

```python
"""Tests for QueryRequest schema."""

import pytest
from pydantic import ValidationError

from apps.api.schemas.requests.query import QueryRequest


class TestQueryRequest:
    """Tests for QueryRequest schema."""

    def test_valid_minimal_query(self) -> None:
        """Test valid minimal query."""
        query = QueryRequest(prompt="Hello")
        assert query.prompt == "Hello"
        assert query.session_id is None

    def test_valid_query_with_model(self) -> None:
        """Test valid query with model."""
        query = QueryRequest(prompt="Hello", model="sonnet")
        assert query.model == "sonnet"

    def test_invalid_empty_prompt(self) -> None:
        """Test empty prompt is invalid."""
        with pytest.raises(ValidationError):
            QueryRequest(prompt="")

    def test_invalid_model(self) -> None:
        """Test invalid model raises error."""
        with pytest.raises(ValidationError, match="Invalid model"):
            QueryRequest(prompt="Hello", model="gpt-4")

    def test_valid_allowed_tools(self) -> None:
        """Test valid allowed tools."""
        query = QueryRequest(
            prompt="Hello",
            allowed_tools=["Read", "Write", "mcp__server__tool"]
        )
        assert len(query.allowed_tools) == 3

    def test_invalid_allowed_tools(self) -> None:
        """Test invalid tool names."""
        with pytest.raises(ValidationError, match="Invalid tool names"):
            QueryRequest(prompt="Hello", allowed_tools=["InvalidTool"])

    def test_tool_conflict(self) -> None:
        """Test conflict between allowed and disallowed tools."""
        with pytest.raises(ValidationError, match="Tool conflict"):
            QueryRequest(
                prompt="Hello",
                allowed_tools=["Read"],
                disallowed_tools=["Read"]
            )

    def test_query_with_hooks(self) -> None:
        """Test query with hooks configuration."""
        query = QueryRequest(
            prompt="Hello",
            hooks={"PreToolUse": {"url": "https://example.com/hook"}}
        )
        assert query.hooks is not None
        assert query.hooks.pre_tool_use is not None

    def test_cwd_path_traversal_rejected(self) -> None:
        """Test path traversal in cwd is rejected (T128)."""
        with pytest.raises(ValidationError, match="Path traversal"):
            QueryRequest(prompt="Hello", cwd="../etc/passwd")

    def test_cwd_null_byte_rejected(self) -> None:
        """Test null bytes in cwd are rejected (T128)."""
        with pytest.raises(ValidationError, match="Null bytes"):
            QueryRequest(prompt="Hello", cwd="/safe/path\x00/inject")

    def test_add_dirs_path_traversal_rejected(self) -> None:
        """Test path traversal in add_dirs is rejected (T128)."""
        with pytest.raises(ValidationError, match="Path traversal"):
            QueryRequest(prompt="Hello", add_dirs=["../sensitive"])

    def test_add_dirs_null_byte_rejected(self) -> None:
        """Test null bytes in add_dirs are rejected (T128)."""
        with pytest.raises(ValidationError, match="Null bytes"):
            QueryRequest(prompt="Hello", add_dirs=["/path\x00/inject"])

    def test_env_null_byte_rejected(self) -> None:
        """Test null bytes in env are rejected (T128)."""
        with pytest.raises(ValidationError, match="Null bytes"):
            QueryRequest(prompt="Hello", env={"KEY\x00": "value"})

    def test_env_dangerous_var_rejected(self) -> None:
        """Test dangerous env vars are rejected (T128)."""
        with pytest.raises(ValidationError, match="LD_PRELOAD"):
            QueryRequest(prompt="Hello", env={"LD_PRELOAD": "/lib/malicious.so"})

    def test_env_path_var_rejected(self) -> None:
        """Test PATH env var is rejected (T128)."""
        with pytest.raises(ValidationError, match="PATH"):
            QueryRequest(prompt="Hello", env={"PATH": "/malicious/bin"})
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_request_query_schema.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `apps/api/schemas/requests/query.py`:

```python
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
        """Validate cwd for path traversal attacks (T128 security).

        Args:
            v: Working directory path.

        Returns:
            Validated path.

        Raises:
            ValueError: If path traversal detected.
        """
        if v is not None:
            validate_no_null_bytes(v, "cwd")
            validate_no_path_traversal(v, "cwd")
        return v

    @field_validator("add_dirs")
    @classmethod
    def validate_add_dirs_security(cls, v: list[str]) -> list[str]:
        """Validate add_dirs for path traversal attacks (T128 security).

        Args:
            v: List of directory paths.

        Returns:
            Validated paths.

        Raises:
            ValueError: If path traversal detected.
        """
        for path in v:
            validate_no_null_bytes(path, "add_dirs")
            validate_no_path_traversal(path, "add_dirs")
        return v

    @field_validator("env")
    @classmethod
    def validate_env_security(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate environment variables for injection (T128 security).

        Args:
            v: Environment variable dict.

        Returns:
            Validated environment.

        Raises:
            ValueError: If dangerous characters found.
        """
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_request_query_schema.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/api/schemas/requests/query.py tests/unit/test_request_query_schema.py
git commit -m "refactor: extract QueryRequest to requests/query.py"
```

---

### Task 4: Create requests/sessions.py Module

**Files:**
- Create: `apps/api/schemas/requests/sessions.py`
- Test: `tests/unit/test_request_sessions_schema.py`

**Step 1: Write the failing test**

Create `tests/unit/test_request_sessions_schema.py`:

```python
"""Tests for session request schemas."""

import pytest
from pydantic import ValidationError

from apps.api.schemas.requests.sessions import (
    AnswerRequest,
    ForkRequest,
    ResumeRequest,
)


class TestResumeRequest:
    """Tests for ResumeRequest schema."""

    def test_valid_resume(self) -> None:
        """Test valid resume request."""
        req = ResumeRequest(prompt="Continue the task")
        assert req.prompt == "Continue the task"

    def test_resume_with_overrides(self) -> None:
        """Test resume with configuration overrides."""
        req = ResumeRequest(
            prompt="Continue",
            permission_mode="bypassPermissions",
            max_turns=10
        )
        assert req.permission_mode == "bypassPermissions"
        assert req.max_turns == 10


class TestForkRequest:
    """Tests for ForkRequest schema."""

    def test_valid_fork(self) -> None:
        """Test valid fork request."""
        req = ForkRequest(prompt="Fork and do something different")
        assert req.prompt == "Fork and do something different"

    def test_fork_with_model_override(self) -> None:
        """Test fork with model override."""
        req = ForkRequest(prompt="Fork", model="opus")
        assert req.model == "opus"

    def test_fork_invalid_model(self) -> None:
        """Test fork with invalid model."""
        with pytest.raises(ValidationError, match="Invalid model"):
            ForkRequest(prompt="Fork", model="gpt-4")


class TestAnswerRequest:
    """Tests for AnswerRequest schema."""

    def test_valid_answer(self) -> None:
        """Test valid answer request."""
        req = AnswerRequest(answer="Yes, proceed")
        assert req.answer == "Yes, proceed"

    def test_empty_answer_invalid(self) -> None:
        """Test empty answer is invalid."""
        with pytest.raises(ValidationError):
            AnswerRequest(answer="")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_request_sessions_schema.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `apps/api/schemas/requests/sessions.py`:

```python
"""Session-related request schemas."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from apps.api.schemas.requests.config import HooksConfigSchema, ImageContentSchema
from apps.api.schemas.validators import validate_model_name


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

    @field_validator("model")
    @classmethod
    def validate_model(cls, model: str | None) -> str | None:
        """Validate that the model name is valid."""
        return validate_model_name(model)


class AnswerRequest(BaseModel):
    """Request to answer an AskUserQuestion from the agent."""

    answer: str = Field(..., min_length=1, max_length=100000)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_request_sessions_schema.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/api/schemas/requests/sessions.py tests/unit/test_request_sessions_schema.py
git commit -m "refactor: extract session schemas to requests/sessions.py"
```

---

### Task 5: Create requests/control.py Module

**Files:**
- Create: `apps/api/schemas/requests/control.py`
- Test: `tests/unit/test_request_control_schema.py`

**Step 1: Write the failing test**

Create `tests/unit/test_request_control_schema.py`:

```python
"""Tests for control request schemas."""

import pytest
from pydantic import ValidationError

from apps.api.schemas.requests.control import ControlRequest, RewindRequest


class TestRewindRequest:
    """Tests for RewindRequest schema."""

    def test_valid_rewind(self) -> None:
        """Test valid rewind request."""
        req = RewindRequest(checkpoint_id="chk_123")
        assert req.checkpoint_id == "chk_123"

    def test_empty_checkpoint_id_invalid(self) -> None:
        """Test empty checkpoint_id is invalid."""
        with pytest.raises(ValidationError):
            RewindRequest(checkpoint_id="")


class TestControlRequest:
    """Tests for ControlRequest schema."""

    def test_valid_permission_mode_change(self) -> None:
        """Test valid permission mode change."""
        req = ControlRequest(
            type="permission_mode_change",
            permission_mode="bypassPermissions"
        )
        assert req.type == "permission_mode_change"
        assert req.permission_mode == "bypassPermissions"

    def test_permission_mode_change_requires_mode(self) -> None:
        """Test permission_mode_change requires permission_mode."""
        with pytest.raises(ValidationError, match="permission_mode is required"):
            ControlRequest(type="permission_mode_change")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_request_control_schema.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `apps/api/schemas/requests/control.py`:

```python
"""Control request schemas."""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class RewindRequest(BaseModel):
    """Request to rewind session to a checkpoint."""

    checkpoint_id: str = Field(..., min_length=1, description="ID of checkpoint to rewind to")


class ControlRequest(BaseModel):
    """Request to send a control event to an active session.

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
        """Validate that permission_mode is provided for permission_mode_change type."""
        if self.type == "permission_mode_change" and self.permission_mode is None:
            raise ValueError(
                "permission_mode is required for permission_mode_change control event"
            )
        return self
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_request_control_schema.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/api/schemas/requests/control.py tests/unit/test_request_control_schema.py
git commit -m "refactor: extract control schemas to requests/control.py"
```

---

### Task 6: Create requests/__init__.py with Re-exports

**Files:**
- Modify: `apps/api/schemas/requests/__init__.py`
- Test: existing tests should continue to pass

**Step 1: Run existing tests to establish baseline**

Run: `uv run pytest tests/unit/test_schemas.py -v`
Expected: Currently passing (or failing due to missing imports)

**Step 2: Write the re-export module**

Update `apps/api/schemas/requests/__init__.py`:

```python
"""Request schemas package.

Re-exports all request schemas for backward compatibility.
Import from this module or submodules as needed.
"""

from apps.api.schemas.requests.config import (
    AgentDefinitionSchema,
    HookWebhookSchema,
    HooksConfigSchema,
    ImageContentSchema,
    McpServerConfigSchema,
    OutputFormatSchema,
    SandboxSettingsSchema,
    SdkPluginConfigSchema,
)
from apps.api.schemas.requests.control import ControlRequest, RewindRequest
from apps.api.schemas.requests.query import QueryRequest
from apps.api.schemas.requests.sessions import AnswerRequest, ForkRequest, ResumeRequest

# Re-export validators for backward compatibility
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

__all__ = [
    # Config schemas
    "AgentDefinitionSchema",
    "HookWebhookSchema",
    "HooksConfigSchema",
    "ImageContentSchema",
    "McpServerConfigSchema",
    "OutputFormatSchema",
    "SandboxSettingsSchema",
    "SdkPluginConfigSchema",
    # Query
    "QueryRequest",
    # Sessions
    "AnswerRequest",
    "ForkRequest",
    "ResumeRequest",
    # Control
    "ControlRequest",
    "RewindRequest",
    # Validators (for backward compatibility)
    "validate_model_name",
    "validate_tool_name",
    "validate_no_null_bytes",
    "validate_no_path_traversal",
    "validate_url_not_internal",
    # Security patterns (for backward compatibility)
    "SHELL_METACHAR_PATTERN",
    "PATH_TRAVERSAL_PATTERN",
    "NULL_BYTE_PATTERN",
    "BLOCKED_URL_PATTERNS",
]
```

**Step 3: Run tests to verify re-exports work**

Run: `uv run pytest tests/unit/test_schemas.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add apps/api/schemas/requests/__init__.py
git commit -m "refactor: add re-exports to requests/__init__.py"
```

---

### Task 7: Update Import Paths in Application Code

**Files:**
- Modify: `apps/api/routes/query.py`
- Modify: `apps/api/routes/sessions.py`
- Modify: `apps/api/routes/websocket.py`
- Modify: `apps/api/services/agent.py`
- Modify: `apps/api/services/webhook.py`

**Step 1: Run full test suite to establish baseline**

Run: `uv run pytest -v`
Expected: Note any failures

**Step 2: Update imports**

All files should import from `apps.api.schemas.requests` (the package `__init__.py` re-exports everything):

**apps/api/routes/query.py** - Line 13:
```python
# No change needed - already imports from apps.api.schemas.requests
from apps.api.schemas.requests import QueryRequest
```

**apps/api/routes/sessions.py** - Lines 8-15:
```python
# No change needed - already imports from apps.api.schemas.requests
from apps.api.schemas.requests import (
    AnswerRequest,
    ControlRequest,
    ForkRequest,
    QueryRequest,
    ResumeRequest,
    RewindRequest,
)
```

**apps/api/routes/websocket.py** - Line 14:
```python
# No change needed
from apps.api.schemas.requests import QueryRequest
```

**apps/api/services/agent.py** - Line 21:
```python
# No change needed
from apps.api.schemas.requests import HooksConfigSchema, QueryRequest
```

**apps/api/services/webhook.py** - Line 14:
```python
# No change needed
from apps.api.schemas.requests import HooksConfigSchema, HookWebhookSchema
```

**Step 3: Run tests to verify all imports work**

Run: `uv run pytest -v`
Expected: PASS

**Step 4: Commit**

```bash
git add apps/api/routes/ apps/api/services/
git commit -m "refactor: verify import paths work with new package structure"
```

---

### Task 8: Update Test Imports

**Files:**
- Modify: `tests/unit/test_schemas.py`
- Modify: `tests/unit/test_webhook_service.py`
- Modify: `tests/unit/test_agent_service.py`
- Modify: `tests/integration/test_permissions.py`
- Modify: `tests/integration/test_hooks.py`
- Modify: `tests/integration/test_structured_output.py`
- Modify: `tests/integration/test_tools.py`
- Modify: `tests/integration/test_subagents.py`

**Step 1: Run tests**

Run: `uv run pytest -v`
Expected: Note any import failures

**Step 2: Verify existing imports work**

Most test files import from `apps.api.schemas.requests` which re-exports everything, so they should work without changes.

For tests that import inside functions (like `test_agent_service.py`), verify they still work:

```python
# Example - these should still work:
from apps.api.schemas.requests import McpServerConfigSchema
from apps.api.schemas.requests import AgentDefinitionSchema
from apps.api.schemas.requests import HooksConfigSchema, HookWebhookSchema
from apps.api.schemas.requests import OutputFormatSchema
```

**Step 3: Run full test suite**

Run: `uv run pytest -v`
Expected: PASS

**Step 4: Commit**

```bash
git add tests/
git commit -m "test: verify all test imports work with new package structure"
```

---

### Task 9: Delete Original Monolithic File

**Files:**
- Delete: `apps/api/schemas/requests.py`

**Step 1: Run full test suite before deletion**

Run: `uv run pytest -v`
Expected: PASS

**Step 2: Delete the original file**

```bash
rm apps/api/schemas/requests.py
```

**Step 3: Run full test suite after deletion**

Run: `uv run pytest -v`
Expected: PASS

**Step 4: Run type checking**

Run: `uv run mypy apps/api`
Expected: PASS (or only pre-existing issues)

**Step 5: Run linting**

Run: `uv run ruff check apps/api/schemas/`
Expected: PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "refactor: delete monolithic requests.py, split complete"
```

---

### Task 10: Final Verification

**Step 1: Run full test suite with coverage**

Run: `uv run pytest --cov=apps/api --cov-report=term-missing`
Expected: PASS with good coverage

**Step 2: Run type checking**

Run: `uv run mypy apps/api --strict`
Expected: PASS

**Step 3: Run linting**

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: PASS

**Step 4: Verify file structure**

```bash
tree apps/api/schemas/
```

Expected:
```
apps/api/schemas/
├── __init__.py
├── requests/
│   ├── __init__.py
│   ├── config.py
│   ├── control.py
│   ├── query.py
│   └── sessions.py
├── responses.py
└── validators.py
```

**Step 5: Final commit**

```bash
git add -A
git commit -m "refactor: complete request schemas split - modularity restored"
```

---

## Summary

| Original File | New Location | Contents |
|---------------|--------------|----------|
| `requests.py:10-161` | `validators.py` | Security patterns, `validate_no_null_bytes()`, `validate_no_path_traversal()`, `validate_url_not_internal()`, `validate_tool_name()`, `validate_model_name()` |
| `requests.py:163-354` | `requests/config.py` | 8 config schemas with security validators |
| `requests.py:356-554` | `requests/query.py` | `QueryRequest` with security validators |
| `requests.py:556-611` | `requests/sessions.py` | `ResumeRequest`, `ForkRequest`, `AnswerRequest` |
| `requests.py:613-654` | `requests/control.py` | `RewindRequest`, `ControlRequest` |

**Total tasks:** 10
**Estimated time:** ~45 minutes for careful TDD execution
