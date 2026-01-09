# Refactor Agent Service Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **Organization Note:** When this plan is fully implemented and verified, move this file to `docs/plans/complete/` to keep the plans folder organized.

**Goal:** Refactor the monolithic `apps/api/services/agent.py` (1409 lines) into smaller, focused modules following single-responsibility principle.

**Architecture:** Extract logical groupings into separate modules within `apps/api/services/agent/` package. The main `AgentService` class will import and compose these modules. All existing public exports will be re-exported from the package `__init__.py` for backward compatibility.

**Tech Stack:** Python 3.11+, FastAPI, claude-agent-sdk, structlog

**TDD Pattern for Refactoring:** GREEN → REFACTOR → GREEN
- Existing tests are the safety net
- Every task MUST verify GREEN before making changes
- Every task MUST verify GREEN after making changes

---

## Current Structure Analysis

The existing `agent.py` contains:

| Lines | Component | Responsibility |
|-------|-----------|----------------|
| 67-121 | Utility functions | `detect_slash_command()`, `resolve_env_var()`, `resolve_env_dict()` |
| 123-136 | `QueryResponseDict` | TypedDict for non-streaming response |
| 138-158 | `StreamContext` | Dataclass for streaming query context |
| 409-520 | `_build_*` methods | SDK options construction (7 methods) |
| 615-711 | `_handle_*` methods | SDK message handling (6 methods) |
| 751-844 | Partial handlers | Streaming partial message handling (3 methods) |
| 846-883 | `_map_sdk_message` | Message type dispatch |
| 885-970 | Checkpoint methods | File modification tracking |
| 972-1041 | Extraction methods | Content block and usage extraction |
| 1249-1408 | Hook methods | Webhook hook execution (5 methods) |

## Target Structure

```
apps/api/services/agent/
├── __init__.py          # Re-exports public API
├── service.py           # Core AgentService class (query methods)
├── types.py             # QueryResponseDict, StreamContext
├── utils.py             # Environment resolution, slash command detection
├── options.py           # SDK options builder methods
├── handlers.py          # SDK message handlers
└── hooks.py             # Webhook hook execution
```

## Public API Contract (Must Preserve)

These exports must remain importable from `apps.api.services.agent`:

```python
from apps.api.services.agent import (
    AgentService,
    QueryResponseDict,
    StreamContext,
    detect_slash_command,
    resolve_env_var,
    resolve_env_dict,
)
```

---

## Task 0: Baseline Verification and Import Inventory

**Files:**
- Read: `apps/api/services/agent.py`
- Test: All test files

**Rollback:** N/A (baseline task)

**Step 1: Run full test suite to establish GREEN baseline**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS (this is our safety net)

**Step 2: Inventory all import sites**

```bash
grep -r "from apps.api.services.agent import" apps/ tests/
grep -r "from apps.api.services import agent" apps/ tests/
```

Document all files that import from agent.py - these will need verification after each extraction.

**Step 3: Establish coverage baseline**

```bash
uv run pytest --cov=apps/api/services/agent --cov-report=term
```

Record the coverage percentage - Task 10 must meet or exceed this.

**Step 4: Run type checker on agent module**

```bash
uv run mypy apps/api/services/agent.py --strict
```

Expected: PASS (or note existing issues)

**Step 5: Document baseline metrics**

Record:
- Total test count: ___
- Coverage percentage: ___%
- Import sites found: ___ files
- Type check status: PASS/FAIL with issues

---

## Task 1: Create Agent Package Structure

**Files:**
- Create: `apps/api/services/agent/__init__.py`

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 2: Create the agent package directory**

```bash
mkdir -p apps/api/services/agent
```

**Step 3: Create empty `__init__.py` with re-exports from original**

Create `apps/api/services/agent/__init__.py`:

```python
"""Agent service package.

This package contains the AgentService and supporting modules
for interacting with the Claude Agent SDK.

During refactoring, this re-exports from the original monolithic module.
"""

# Re-export public API from original module during transition
from apps.api.services.agent_original import (
    AgentService,
    QueryResponseDict,
    StreamContext,
    detect_slash_command,
    resolve_env_dict,
    resolve_env_var,
)

__all__ = [
    "AgentService",
    "QueryResponseDict",
    "StreamContext",
    "detect_slash_command",
    "resolve_env_dict",
    "resolve_env_var",
]
```

**Step 4: Rename original file temporarily**

```bash
mv apps/api/services/agent.py apps/api/services/agent_original.py
```

**Step 5: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS (imports now go through package `__init__.py`)

**Step 6: Verify both import paths work**

```bash
python -c "from apps.api.services.agent import AgentService; print('Package import OK')"
python -c "from apps.api.services.agent_original import AgentService; print('Direct import OK')"
```

**Step 7: Commit**

```bash
git add apps/api/services/agent/ apps/api/services/agent_original.py
git commit -m "refactor(agent): create agent package structure with re-exports"
```

---

## Task 2: Extract Types Module

**Files:**
- Create: `apps/api/services/agent/types.py`
- Modify: `apps/api/services/agent/__init__.py`

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 2: Create types.py with QueryResponseDict and StreamContext**

Create `apps/api/services/agent/types.py`:

```python
"""Type definitions for agent service."""

from dataclasses import dataclass, field
from typing import TypedDict


class QueryResponseDict(TypedDict):
    """TypedDict for non-streaming query response."""

    session_id: str
    model: str
    content: list[dict[str, object]]
    is_error: bool
    duration_ms: int
    num_turns: int
    total_cost_usd: float | None
    usage: dict[str, int] | None
    result: str | None
    structured_output: dict[str, object] | None


@dataclass
class StreamContext:
    """Context for a streaming query."""

    session_id: str
    model: str
    start_time: float
    num_turns: int = 0
    total_cost_usd: float | None = None
    is_error: bool = False
    result_text: str | None = None
    structured_output: dict[str, object] | None = None
    # Model usage tracking (T110)
    model_usage: dict[str, dict[str, int]] | None = None
    # Checkpoint tracking fields (T100, T104)
    enable_file_checkpointing: bool = False
    last_user_message_uuid: str | None = None
    files_modified: list[str] = field(default_factory=list)
    # Partial messages tracking (T118)
    include_partial_messages: bool = False
```

**Step 3: Update __init__.py to import from types.py first, fallback to original**

Update `apps/api/services/agent/__init__.py`:

```python
"""Agent service package.

This package contains the AgentService and supporting modules
for interacting with the Claude Agent SDK.
"""

# Import from extracted modules
from apps.api.services.agent.types import QueryResponseDict, StreamContext

# Re-export remaining from original module during transition
from apps.api.services.agent_original import (
    AgentService,
    detect_slash_command,
    resolve_env_dict,
    resolve_env_var,
)

__all__ = [
    "AgentService",
    "QueryResponseDict",
    "StreamContext",
    "detect_slash_command",
    "resolve_env_dict",
    "resolve_env_var",
]
```

**Step 4: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 5: Verify both import paths work**

```bash
python -c "from apps.api.services.agent import QueryResponseDict; print('Package import OK')"
python -c "from apps.api.services.agent.types import QueryResponseDict; print('Module import OK')"
```

**Step 6: Run type checker on new module**

```bash
uv run mypy apps/api/services/agent/types.py --strict
```

Expected: PASS

**Step 7: Commit**

```bash
git add apps/api/services/agent/types.py apps/api/services/agent/__init__.py
git commit -m "refactor(agent): extract types to dedicated module"
```

---

## Task 3: Extract Utils Module

**Files:**
- Create: `apps/api/services/agent/utils.py`
- Modify: `apps/api/services/agent/__init__.py`

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 2: Create utils.py with utility functions**

Create `apps/api/services/agent/utils.py`:

```python
"""Utility functions for agent service."""

import os
import re

# Pattern for ${VAR} or ${VAR:-default} environment variable syntax
_ENV_VAR_PATTERN = re.compile(r"\$\{([^}:]+)(?::-([^}]*))?\}")

# Pattern for slash command detection (T115a)
# Matches prompts starting with / followed by alphanumeric characters, dashes, or underscores
_SLASH_COMMAND_PATTERN = re.compile(r"^/([a-zA-Z][a-zA-Z0-9_-]*)")


def detect_slash_command(prompt: str) -> str | None:
    """Detect if a prompt starts with a slash command (T115a).

    Slash commands are prompts that start with / followed by a command name.
    Examples: /help, /clear, /commit, /review-pr

    Args:
        prompt: The user prompt to check.

    Returns:
        The command name (without /) if detected, None otherwise.
    """
    match = _SLASH_COMMAND_PATTERN.match(prompt.strip())
    return match.group(1) if match else None


def resolve_env_var(value: str) -> str:
    """Resolve environment variables in a string.

    Supports ${VAR} and ${VAR:-default} syntax.

    Args:
        value: String potentially containing env var references.

    Returns:
        String with environment variables resolved.
    """

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default = match.group(2)  # May be None if no default specified
        return os.environ.get(var_name, default if default is not None else "")

    return _ENV_VAR_PATTERN.sub(replacer, value)


def resolve_env_dict(env: dict[str, str]) -> dict[str, str]:
    """Resolve environment variables in a dict of strings.

    Args:
        env: Dictionary with string values that may contain env var references.

    Returns:
        Dictionary with all env vars resolved.
    """
    return {key: resolve_env_var(val) for key, val in env.items()}
```

**Step 3: Update __init__.py to import utils from new module**

Update `apps/api/services/agent/__init__.py`:

```python
"""Agent service package.

This package contains the AgentService and supporting modules
for interacting with the Claude Agent SDK.
"""

# Import from extracted modules
from apps.api.services.agent.types import QueryResponseDict, StreamContext
from apps.api.services.agent.utils import (
    detect_slash_command,
    resolve_env_dict,
    resolve_env_var,
)

# Re-export remaining from original module during transition
from apps.api.services.agent_original import AgentService

__all__ = [
    "AgentService",
    "QueryResponseDict",
    "StreamContext",
    "detect_slash_command",
    "resolve_env_dict",
    "resolve_env_var",
]
```

**Step 4: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 5: Verify both import paths work**

```bash
python -c "from apps.api.services.agent import detect_slash_command; print('Package import OK')"
python -c "from apps.api.services.agent.utils import detect_slash_command; print('Module import OK')"
```

**Step 6: Run type checker on new module**

```bash
uv run mypy apps/api/services/agent/utils.py --strict
```

Expected: PASS

**Step 7: Commit**

```bash
git add apps/api/services/agent/utils.py apps/api/services/agent/__init__.py
git commit -m "refactor(agent): extract utils to dedicated module"
```

---

## Task 4: Extract Options Builder Module

**Files:**
- Create: `apps/api/services/agent/options.py`
- Modify: `apps/api/services/agent/__init__.py`

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 2: Create options.py with OptionsBuilder class**

Create `apps/api/services/agent/options.py`:

```python
"""SDK options builder for agent service."""

from typing import TYPE_CHECKING, cast

from apps.api.services.agent.utils import resolve_env_dict

if TYPE_CHECKING:
    from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions
    from claude_agent_sdk.types import (
        McpHttpServerConfig,
        McpSdkServerConfig,
        McpSSEServerConfig,
        McpStdioServerConfig,
        SandboxSettings,
        SdkPluginConfig,
        SettingSource,
    )

    from apps.api.schemas.requests import QueryRequest

    # Union type for MCP server configs
    McpServerConfig = (
        McpStdioServerConfig
        | McpSSEServerConfig
        | McpHttpServerConfig
        | McpSdkServerConfig
    )


class OptionsBuilder:
    """Builds ClaudeAgentOptions from QueryRequest."""

    def __init__(self, request: "QueryRequest") -> None:
        """Initialize builder with request.

        Args:
            request: Query request to build options from.
        """
        self._request = request

    def build(self) -> "ClaudeAgentOptions":
        """Build SDK options from request.

        Returns:
            ClaudeAgentOptions instance.

        Note:
            The SDK has complex nested types that require dynamic construction.
            We use a typed approach with conditional building.
        """
        from claude_agent_sdk import ClaudeAgentOptions

        request = self._request

        # Extract basic options from request
        allowed_tools = request.allowed_tools if request.allowed_tools else None
        disallowed_tools = (
            request.disallowed_tools if request.disallowed_tools else None
        )
        permission_mode = request.permission_mode if request.permission_mode else None
        permission_prompt_tool_name = (
            request.permission_prompt_tool_name
            if request.permission_prompt_tool_name
            else None
        )

        # Session resume configuration
        resume: str | None = None
        fork_session: bool | None = None
        if request.session_id and not request.fork_session:
            resume = request.session_id
        elif request.session_id and request.fork_session:
            resume = request.session_id
            fork_session = True

        # Setting sources for CLAUDE.md loading (T114)
        setting_sources_typed: list[str] | None = None
        if request.setting_sources:
            setting_sources_typed = list(request.setting_sources)

        # Build complex configs using helper methods
        mcp_configs = self._build_mcp_configs()
        agent_defs = self._build_agent_defs()
        output_format = self._build_output_format()
        plugins_list = self._build_plugins()
        sandbox_config = self._build_sandbox_config()
        final_system_prompt = self._resolve_system_prompt()

        # Note: mcp_servers, agents, plugins, setting_sources, and sandbox are cast
        # because SDK expects specific config types but accepts dict-like structures
        return ClaudeAgentOptions(
            allowed_tools=allowed_tools or [],
            disallowed_tools=disallowed_tools or [],
            permission_mode=permission_mode,
            permission_prompt_tool_name=permission_prompt_tool_name,
            model=request.model if request.model else None,
            max_turns=request.max_turns if request.max_turns else None,
            cwd=request.cwd if request.cwd else None,
            env=request.env or {},
            system_prompt=final_system_prompt,
            enable_file_checkpointing=bool(request.enable_file_checkpointing),
            resume=resume,
            fork_session=fork_session or False,
            mcp_servers=cast("dict[str, McpServerConfig]", mcp_configs or {}),
            agents=cast("dict[str, AgentDefinition] | None", agent_defs),
            output_format=output_format,
            plugins=cast("list[SdkPluginConfig]", plugins_list),
            setting_sources=cast("list[SettingSource] | None", setting_sources_typed),
            sandbox=cast("SandboxSettings | None", sandbox_config),
            include_partial_messages=request.include_partial_messages,
        )

    def _build_mcp_configs(
        self,
    ) -> dict[str, dict[str, str | list[str] | dict[str, str] | None]] | None:
        """Build MCP server configurations from request.

        Returns:
            MCP server configs dict or None.
        """
        if not self._request.mcp_servers:
            return None

        mcp_configs: dict[str, dict[str, str | list[str] | dict[str, str] | None]] = {}
        for name, config in self._request.mcp_servers.items():
            # Resolve ${VAR:-default} syntax in env and headers
            resolved_env = resolve_env_dict(config.env) if config.env else {}
            resolved_headers = (
                resolve_env_dict(config.headers) if config.headers else {}
            )
            mcp_configs[name] = {
                "command": config.command,
                "args": config.args,
                "type": config.type,
                "url": config.url,
                "headers": resolved_headers,
                "env": resolved_env,
            }
        return mcp_configs

    def _build_agent_defs(
        self,
    ) -> dict[str, dict[str, str | list[str] | None]] | None:
        """Build agent definitions from request.

        Returns:
            Agent definitions dict or None.
        """
        if not self._request.agents:
            return None

        agent_defs: dict[str, dict[str, str | list[str] | None]] = {}
        for name, agent in self._request.agents.items():
            agent_defs[name] = {
                "description": agent.description,
                "prompt": agent.prompt,
                "tools": agent.tools,
                "model": agent.model,
            }
        return agent_defs

    def _build_output_format(
        self,
    ) -> dict[str, str | dict[str, object] | None] | None:
        """Build output format configuration from request.

        Returns:
            Output format dict or None.
        """
        if not self._request.output_format:
            return None

        return {
            "type": self._request.output_format.type,
            "schema": self._request.output_format.schema_,
        }

    def _build_plugins(self) -> list[dict[str, str | None]]:
        """Build plugins list from request.

        Returns:
            List of plugin config dicts.
        """
        plugins_list: list[dict[str, str | None]] = []
        if self._request.plugins:
            for plugin_config in self._request.plugins:
                if plugin_config.enabled:  # Only include enabled plugins
                    plugins_list.append({
                        "name": plugin_config.name,
                        "path": plugin_config.path,
                    })
        return plugins_list

    def _build_sandbox_config(
        self,
    ) -> dict[str, bool | list[str]] | None:
        """Build sandbox configuration from request.

        Returns:
            Sandbox config dict or None.
        """
        if not self._request.sandbox:
            return None

        return {
            "enabled": self._request.sandbox.enabled,
            "allowed_paths": self._request.sandbox.allowed_paths,
            "network_access": self._request.sandbox.network_access,
        }

    def _resolve_system_prompt(self) -> str | None:
        """Resolve system prompt with optional append.

        Combines base system_prompt with system_prompt_append if both provided.

        Returns:
            Resolved system prompt or None.
        """
        system_prompt = self._request.system_prompt if self._request.system_prompt else None

        if self._request.system_prompt_append:
            if system_prompt:
                return f"{system_prompt}\n\n{self._request.system_prompt_append}"
            return self._request.system_prompt_append

        return system_prompt
```

**Step 3: Update __init__.py to add OptionsBuilder**

Add to `apps/api/services/agent/__init__.py`:

```python
from apps.api.services.agent.options import OptionsBuilder
```

And add `"OptionsBuilder"` to `__all__`.

**Step 4: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 5: Verify both import paths work**

```bash
python -c "from apps.api.services.agent import OptionsBuilder; print('Package import OK')"
python -c "from apps.api.services.agent.options import OptionsBuilder; print('Module import OK')"
```

**Step 6: Run type checker on new module**

```bash
uv run mypy apps/api/services/agent/options.py --strict
```

Expected: PASS

**Step 7: Commit**

```bash
git add apps/api/services/agent/options.py apps/api/services/agent/__init__.py
git commit -m "refactor(agent): extract options builder to dedicated module"
```

---

## Task 5: Extract Message Handlers Module

**Files:**
- Create: `apps/api/services/agent/handlers.py`
- Modify: `apps/api/services/agent/__init__.py`

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 2: Create handlers.py with MessageHandler class**

Create `apps/api/services/agent/handlers.py`:

```python
"""SDK message handlers for agent service."""

import json
from typing import TYPE_CHECKING

import structlog

from apps.api.schemas.messages import map_sdk_content_block, map_sdk_usage
from apps.api.schemas.responses import (
    ContentBlockSchema,
    ContentDeltaSchema,
    MessageEvent,
    MessageEventData,
    PartialMessageEvent,
    PartialMessageEventData,
    QuestionEvent,
    QuestionEventData,
    UsageSchema,
)

if TYPE_CHECKING:
    from apps.api.services.agent.types import StreamContext

logger = structlog.get_logger(__name__)


class MessageHandler:
    """Handles SDK messages and converts to SSE events."""

    def map_sdk_message(
        self, message: object, ctx: "StreamContext"
    ) -> dict[str, str] | None:
        """Map SDK message to SSE event dict.

        Args:
            message: SDK message.
            ctx: Stream context.

        Returns:
            SSE event dict with 'event' and 'data' keys, or None.
        """
        msg_type = type(message).__name__

        if msg_type == "SystemMessage":
            return None

        if msg_type == "UserMessage":
            return self._handle_user_message(message, ctx)

        if msg_type == "AssistantMessage":
            return self._handle_assistant_message(message, ctx)

        if msg_type == "ResultMessage":
            self._handle_result_message(message, ctx)
            return None

        # T118: Handle partial/streaming messages when include_partial_messages is enabled
        if msg_type == "ContentBlockStart" and ctx.include_partial_messages:
            return self._handle_partial_start(message, ctx)

        if msg_type == "ContentBlockDelta" and ctx.include_partial_messages:
            return self._handle_partial_delta(message, ctx)

        if msg_type == "ContentBlockStop" and ctx.include_partial_messages:
            return self._handle_partial_stop(message, ctx)

        return None

    def _handle_user_message(
        self, message: object, ctx: "StreamContext"
    ) -> dict[str, str]:
        """Handle UserMessage from SDK.

        Args:
            message: SDK UserMessage.
            ctx: Stream context.

        Returns:
            SSE event dict with 'event' and 'data' keys.
        """
        content_blocks = self._extract_content_blocks(message)

        # Track user message UUID for checkpointing (T104)
        user_uuid = getattr(message, "uuid", None)
        if ctx.enable_file_checkpointing and user_uuid:
            ctx.last_user_message_uuid = user_uuid

        event = MessageEvent(
            data=MessageEventData(
                type="user",
                content=content_blocks,
                uuid=user_uuid,
            )
        )
        return self._format_sse(event.event, event.data.model_dump())

    def _handle_assistant_message(
        self, message: object, ctx: "StreamContext"
    ) -> dict[str, str]:
        """Handle AssistantMessage from SDK.

        Args:
            message: SDK AssistantMessage.
            ctx: Stream context.

        Returns:
            SSE event dict with 'event' and 'data' keys.
        """
        content_blocks = self._extract_content_blocks(message)
        usage = self._extract_usage(message)

        # Track file modifications from Write/Edit tools for checkpointing (T104)
        if ctx.enable_file_checkpointing:
            self._track_file_modifications(content_blocks, ctx)

        # Check for special tool uses (AskUserQuestion, TodoWrite)
        special_event = self._check_special_tool_uses(content_blocks, ctx)
        if special_event:
            return special_event

        event = MessageEvent(
            data=MessageEventData(
                type="assistant",
                content=content_blocks,
                model=getattr(message, "model", ctx.model),
                usage=usage,
            )
        )
        return self._format_sse(event.event, event.data.model_dump())

    def _check_special_tool_uses(
        self, content_blocks: list[ContentBlockSchema], ctx: "StreamContext"
    ) -> dict[str, str] | None:
        """Check for special tool uses and return event if found.

        Args:
            content_blocks: Content blocks from message.
            ctx: Stream context.

        Returns:
            SSE event dict for special tool, or None.
        """
        for block in content_blocks:
            if block.type == "tool_use" and block.name == "AskUserQuestion":
                question = block.input.get("question", "") if block.input else ""
                q_event = QuestionEvent(
                    data=QuestionEventData(
                        tool_use_id=block.id or "",
                        question=question,
                        session_id=ctx.session_id,
                    )
                )
                return self._format_sse(q_event.event, q_event.data.model_dump())

            # T116e: Log TodoWrite tool use for tracking
            if block.type == "tool_use" and block.name == "TodoWrite":
                todos_data = block.input.get("todos", []) if block.input else []
                if isinstance(todos_data, list):
                    logger.info(
                        "TodoWrite tool use detected",
                        session_id=ctx.session_id,
                        todos_count=len(todos_data),
                    )
        return None

    def _handle_result_message(self, message: object, ctx: "StreamContext") -> None:
        """Handle ResultMessage from SDK.

        Updates context with result data. Does not emit an event.

        Args:
            message: SDK ResultMessage.
            ctx: Stream context to update.
        """
        from typing import cast

        ctx.is_error = getattr(message, "is_error", False)
        ctx.num_turns = getattr(message, "num_turns", ctx.num_turns)
        ctx.total_cost_usd = getattr(message, "total_cost_usd", None)
        ctx.result_text = getattr(message, "result", None)

        # Extract model_usage if available (T110: Model Selection)
        raw_model_usage = getattr(message, "model_usage", None)
        if raw_model_usage is not None:
            if isinstance(raw_model_usage, dict):
                ctx.model_usage = cast("dict[str, dict[str, int]]", raw_model_usage)
            else:
                logger.warning(
                    "model_usage is not a dict",
                    session_id=ctx.session_id,
                    type=type(raw_model_usage).__name__,
                )

        # Extract structured output if available (US8: Structured Output)
        raw_structured = getattr(message, "structured_output", None)
        if raw_structured is not None:
            if isinstance(raw_structured, dict):
                ctx.structured_output = cast("dict[str, object]", raw_structured)
            else:
                logger.warning(
                    "structured_output is not a dict",
                    session_id=ctx.session_id,
                    type=type(raw_structured).__name__,
                )
                ctx.is_error = True

    def _handle_partial_start(
        self, message: object, _ctx: "StreamContext"
    ) -> dict[str, str]:
        """Handle ContentBlockStart for partial message streaming.

        Args:
            message: SDK ContentBlockStart message.
            _ctx: Stream context (unused, kept for API consistency).

        Returns:
            SSE event dict with 'event' and 'data' keys.
        """
        index = getattr(message, "index", 0)
        content_block = getattr(message, "content_block", None)

        block_schema: ContentBlockSchema | None = None
        if content_block:
            block_schema = ContentBlockSchema(
                type=getattr(content_block, "type", "text"),
                text=getattr(content_block, "text", None),
                id=getattr(content_block, "id", None),
                name=getattr(content_block, "name", None),
            )

        partial_start_event = PartialMessageEvent(
            data=PartialMessageEventData(
                type="content_block_start",
                index=index,
                content_block=block_schema,
            )
        )
        return self._format_sse(
            partial_start_event.event, partial_start_event.data.model_dump()
        )

    def _handle_partial_delta(
        self, message: object, _ctx: "StreamContext"
    ) -> dict[str, str]:
        """Handle ContentBlockDelta for partial message streaming.

        Args:
            message: SDK ContentBlockDelta message.
            _ctx: Stream context (unused, kept for API consistency).

        Returns:
            SSE event dict with 'event' and 'data' keys.
        """
        index = getattr(message, "index", 0)
        delta = getattr(message, "delta", None)

        delta_schema: ContentDeltaSchema | None = None
        if delta:
            delta_type = getattr(delta, "type", "text_delta")
            delta_schema = ContentDeltaSchema(
                type=delta_type,
                text=getattr(delta, "text", None) if delta_type == "text_delta" else None,
                thinking=getattr(delta, "thinking", None) if delta_type == "thinking_delta" else None,
                partial_json=getattr(delta, "partial_json", None) if delta_type == "input_json_delta" else None,
            )

        partial_delta_event = PartialMessageEvent(
            data=PartialMessageEventData(
                type="content_block_delta",
                index=index,
                delta=delta_schema,
            )
        )
        return self._format_sse(
            partial_delta_event.event, partial_delta_event.data.model_dump()
        )

    def _handle_partial_stop(
        self, message: object, _ctx: "StreamContext"
    ) -> dict[str, str]:
        """Handle ContentBlockStop for partial message streaming.

        Args:
            message: SDK ContentBlockStop message.
            _ctx: Stream context (unused, kept for API consistency).

        Returns:
            SSE event dict with 'event' and 'data' keys.
        """
        index = getattr(message, "index", 0)

        partial_stop_event = PartialMessageEvent(
            data=PartialMessageEventData(
                type="content_block_stop",
                index=index,
            )
        )
        return self._format_sse(
            partial_stop_event.event, partial_stop_event.data.model_dump()
        )

    def _track_file_modifications(
        self, content_blocks: list[ContentBlockSchema], ctx: "StreamContext"
    ) -> None:
        """Track file modifications from tool_use blocks (T104).

        Extracts file paths from Write and Edit tool invocations
        and adds them to the context's files_modified list.

        Args:
            content_blocks: List of content blocks from assistant message.
            ctx: Stream context to update.
        """
        for block in content_blocks:
            if block.type != "tool_use":
                continue

            if (
                block.name in ("Write", "Edit")
                and block.input
                and isinstance(block.input, dict)
            ):
                file_path = block.input.get("file_path")
                if (
                    file_path
                    and isinstance(file_path, str)
                    and file_path not in ctx.files_modified
                ):
                    ctx.files_modified.append(file_path)
                    logger.debug(
                        "Tracked file modification",
                        file_path=file_path,
                        tool=block.name,
                        session_id=ctx.session_id,
                    )

    def _extract_content_blocks(self, message: object) -> list[ContentBlockSchema]:
        """Extract content blocks from SDK message.

        Args:
            message: SDK message.

        Returns:
            List of content block schemas.
        """
        content = getattr(message, "content", [])
        if isinstance(content, str):
            return [ContentBlockSchema(type="text", text=content)]

        blocks = []
        for block in content:
            if isinstance(block, dict):
                mapped = map_sdk_content_block(block)
                blocks.append(ContentBlockSchema(**mapped))
            else:
                # Dataclass block
                block_dict: dict[str, object] = {
                    "type": getattr(block, "type", "text"),
                }
                if hasattr(block, "text"):
                    block_dict["text"] = block.text
                if hasattr(block, "thinking"):
                    block_dict["thinking"] = block.thinking
                if hasattr(block, "id"):
                    block_dict["id"] = block.id
                if hasattr(block, "name"):
                    block_dict["name"] = block.name
                if hasattr(block, "input"):
                    block_dict["input"] = block.input
                if hasattr(block, "tool_use_id"):
                    block_dict["tool_use_id"] = block.tool_use_id
                if hasattr(block, "content"):
                    block_dict["content"] = block.content
                if hasattr(block, "is_error"):
                    block_dict["is_error"] = block.is_error
                blocks.append(ContentBlockSchema(**block_dict))

        return blocks

    def _extract_usage(self, message: object) -> UsageSchema | None:
        """Extract usage data from SDK message.

        Args:
            message: SDK message.

        Returns:
            Usage schema or None.
        """
        usage = getattr(message, "usage", None)
        if usage is None:
            return None

        if isinstance(usage, dict):
            mapped = map_sdk_usage(usage)
            if mapped:
                return UsageSchema(**mapped)
        else:
            return UsageSchema(
                input_tokens=getattr(usage, "input_tokens", 0),
                output_tokens=getattr(usage, "output_tokens", 0),
                cache_read_input_tokens=getattr(usage, "cache_read_input_tokens", 0),
                cache_creation_input_tokens=getattr(
                    usage, "cache_creation_input_tokens", 0
                ),
            )
        return None

    @staticmethod
    def _format_sse(event_type: str, data: dict[str, object]) -> dict[str, str]:
        """Format data as SSE event dict for EventSourceResponse.

        Args:
            event_type: Event type name.
            data: Event data.

        Returns:
            Dict with event and data keys for SSE.
        """
        return {"event": event_type, "data": json.dumps(data)}
```

**Step 3: Update __init__.py to add MessageHandler**

Add to `apps/api/services/agent/__init__.py`:

```python
from apps.api.services.agent.handlers import MessageHandler
```

And add `"MessageHandler"` to `__all__`.

**Step 4: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 5: Verify both import paths work**

```bash
python -c "from apps.api.services.agent import MessageHandler; print('Package import OK')"
python -c "from apps.api.services.agent.handlers import MessageHandler; print('Module import OK')"
```

**Step 6: Run type checker on new module**

```bash
uv run mypy apps/api/services/agent/handlers.py --strict
```

Expected: PASS

**Step 7: Commit**

```bash
git add apps/api/services/agent/handlers.py apps/api/services/agent/__init__.py
git commit -m "refactor(agent): extract message handlers to dedicated module"
```

---

## Task 6: Extract Hooks Module

**Files:**
- Create: `apps/api/services/agent/hooks.py`
- Modify: `apps/api/services/agent/__init__.py`

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 2: Create hooks.py with HookExecutor class**

Create `apps/api/services/agent/hooks.py`:

```python
"""Webhook hook execution for agent service."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.api.schemas.requests import HooksConfigSchema
    from apps.api.services.webhook import WebhookService


class HookExecutor:
    """Executes webhook-based hooks for agent lifecycle events."""

    def __init__(self, webhook_service: "WebhookService") -> None:
        """Initialize hook executor.

        Args:
            webhook_service: WebhookService for making hook callbacks.
        """
        self._webhook_service = webhook_service

    async def execute_pre_tool_use(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        tool_name: str,
        tool_input: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Execute PreToolUse webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            tool_name: Name of tool being executed.
            tool_input: Tool input parameters.

        Returns:
            Webhook response with decision (allow/deny/ask).
        """
        if not hooks_config or not hooks_config.pre_tool_use:
            return {"decision": "allow"}

        return await self._webhook_service.execute_hook(
            hook_event="PreToolUse",
            hook_config=hooks_config.pre_tool_use,
            session_id=session_id,
            tool_name=tool_name,
            tool_input=tool_input,
        )

    async def execute_post_tool_use(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        tool_name: str,
        tool_input: dict[str, object] | None = None,
        tool_result: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Execute PostToolUse webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            tool_name: Name of tool that was executed.
            tool_input: Tool input parameters.
            tool_result: Result from tool execution.

        Returns:
            Webhook response.
        """
        if not hooks_config or not hooks_config.post_tool_use:
            return {"acknowledged": True}

        return await self._webhook_service.execute_hook(
            hook_event="PostToolUse",
            hook_config=hooks_config.post_tool_use,
            session_id=session_id,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_result=tool_result,
        )

    async def execute_stop(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        is_error: bool = False,
        duration_ms: int = 0,
        result: str | None = None,
    ) -> dict[str, object]:
        """Execute Stop webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            is_error: Whether session ended with error.
            duration_ms: Session duration in milliseconds.
            result: Final result text.

        Returns:
            Webhook response.
        """
        if not hooks_config or not hooks_config.stop:
            return {"acknowledged": True}

        result_data: dict[str, object] = {
            "is_error": is_error,
            "duration_ms": duration_ms,
        }
        if result:
            result_data["result"] = result

        return await self._webhook_service.execute_hook(
            hook_event="Stop",
            hook_config=hooks_config.stop,
            session_id=session_id,
            result_data=result_data,
        )

    async def execute_subagent_stop(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        subagent_name: str,
        is_error: bool = False,
        result: str | None = None,
    ) -> dict[str, object]:
        """Execute SubagentStop webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            subagent_name: Name of subagent that stopped.
            is_error: Whether subagent ended with error.
            result: Subagent result.

        Returns:
            Webhook response.
        """
        if not hooks_config or not hooks_config.subagent_stop:
            return {"acknowledged": True}

        result_data: dict[str, object] = {
            "subagent_name": subagent_name,
            "is_error": is_error,
        }
        if result:
            result_data["result"] = result

        return await self._webhook_service.execute_hook(
            hook_event="SubagentStop",
            hook_config=hooks_config.subagent_stop,
            session_id=session_id,
            result_data=result_data,
        )

    async def execute_user_prompt_submit(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        prompt: str,
    ) -> dict[str, object]:
        """Execute UserPromptSubmit webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            prompt: User prompt being submitted.

        Returns:
            Webhook response with potential modified prompt.
        """
        if not hooks_config or not hooks_config.user_prompt_submit:
            return {"decision": "allow"}

        return await self._webhook_service.execute_hook(
            hook_event="UserPromptSubmit",
            hook_config=hooks_config.user_prompt_submit,
            session_id=session_id,
            tool_input={"prompt": prompt},
        )
```

**Step 3: Update __init__.py to add HookExecutor**

Add to `apps/api/services/agent/__init__.py`:

```python
from apps.api.services.agent.hooks import HookExecutor
```

And add `"HookExecutor"` to `__all__`.

**Step 4: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 5: Verify both import paths work**

```bash
python -c "from apps.api.services.agent import HookExecutor; print('Package import OK')"
python -c "from apps.api.services.agent.hooks import HookExecutor; print('Module import OK')"
```

**Step 6: Run type checker on new module**

```bash
uv run mypy apps/api/services/agent/hooks.py --strict
```

Expected: PASS

**Step 7: Commit**

```bash
git add apps/api/services/agent/hooks.py apps/api/services/agent/__init__.py
git commit -m "refactor(agent): extract hook executor to dedicated module"
```

---

## Task 7: Create Slim AgentService (Multi-Step)

This task is broken into sub-tasks to minimize risk. Each sub-task has its own GREEN → REFACTOR → GREEN cycle.

### Task 7a: Create skeleton service.py

**Files:**
- Create: `apps/api/services/agent/service.py`

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 2: Create skeleton service.py with __init__ and imports**

Create `apps/api/services/agent/service.py`:

```python
"""Agent service wrapping Claude Agent SDK."""

import asyncio
import time
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

import structlog

from apps.api.config import get_settings
from apps.api.exceptions import AgentError
from apps.api.schemas.responses import (
    ContentBlockSchema,
    DoneEvent,
    DoneEventData,
    ErrorEvent,
    ErrorEventData,
    InitEvent,
    InitEventData,
    MessageEvent,
    MessageEventData,
    ResultEvent,
    ResultEventData,
    UsageSchema,
)
from apps.api.services.agent.handlers import MessageHandler
from apps.api.services.agent.hooks import HookExecutor
from apps.api.services.agent.options import OptionsBuilder
from apps.api.services.agent.types import QueryResponseDict, StreamContext
from apps.api.services.agent.utils import detect_slash_command
from apps.api.services.webhook import WebhookService

if TYPE_CHECKING:
    from apps.api.schemas.requests import HooksConfigSchema, QueryRequest
    from apps.api.services.checkpoint import Checkpoint, CheckpointService

logger = structlog.get_logger(__name__)


class AgentService:
    """Service for interacting with Claude Agent SDK."""

    def __init__(
        self,
        webhook_service: WebhookService | None = None,
        checkpoint_service: "CheckpointService | None" = None,
    ) -> None:
        """Initialize agent service.

        Args:
            webhook_service: Optional WebhookService for hook callbacks.
                           If not provided, a default instance is created.
            checkpoint_service: Optional CheckpointService for file checkpointing.
                              Required for enable_file_checkpointing functionality.
        """
        self._settings = get_settings()
        self._active_sessions: dict[str, asyncio.Event] = {}
        self._webhook_service = webhook_service or WebhookService()
        self._checkpoint_service = checkpoint_service
        self._message_handler = MessageHandler()
        self._hook_executor = HookExecutor(self._webhook_service)

    @property
    def checkpoint_service(self) -> "CheckpointService | None":
        """Get the checkpoint service instance.

        Returns:
            CheckpointService instance or None if not configured.
        """
        return self._checkpoint_service

    # Methods will be added in subsequent sub-tasks
    # For now, delegate to original module
    async def query_stream(
        self,
        request: "QueryRequest",
    ) -> AsyncGenerator[dict[str, str], None]:
        """Stream a query to the agent - delegated to original."""
        from apps.api.services.agent_original import AgentService as OriginalService
        original = OriginalService(self._webhook_service, self._checkpoint_service)
        async for event in original.query_stream(request):
            yield event
```

**Step 3: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 4: Commit**

```bash
git add apps/api/services/agent/service.py
git commit -m "refactor(agent): create AgentService skeleton with delegation"
```

---

### Task 7b: Move query_stream method

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

**Step 2: Copy query_stream implementation from original to service.py**

Replace the delegating `query_stream` method in `apps/api/services/agent/service.py` with the full implementation from `agent_original.py`.

**Step 3: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

**Step 4: Commit**

```bash
git add apps/api/services/agent/service.py
git commit -m "refactor(agent): move query_stream method to service.py"
```

---

### Task 7c: Move _execute_query method

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

**Step 2: Copy _execute_query implementation to service.py**

**Step 3: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

**Step 4: Commit**

```bash
git add apps/api/services/agent/service.py
git commit -m "refactor(agent): move _execute_query method to service.py"
```

---

### Task 7d: Move _mock_response method

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

**Step 2: Copy _mock_response implementation to service.py**

**Step 3: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

**Step 4: Commit**

```bash
git add apps/api/services/agent/service.py
git commit -m "refactor(agent): move _mock_response method to service.py"
```

---

### Task 7e: Move checkpoint methods

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

**Step 2: Copy create_checkpoint_from_context to service.py**

**Step 3: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

**Step 4: Commit**

```bash
git add apps/api/services/agent/service.py
git commit -m "refactor(agent): move checkpoint methods to service.py"
```

---

### Task 7f: Move session management methods

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

**Step 2: Copy interrupt, submit_answer, update_permission_mode to service.py**

**Step 3: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

**Step 4: Commit**

```bash
git add apps/api/services/agent/service.py
git commit -m "refactor(agent): move session management methods to service.py"
```

---

### Task 7g: Move query_single method

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

**Step 2: Copy query_single to service.py**

**Step 3: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

**Step 4: Commit**

```bash
git add apps/api/services/agent/service.py
git commit -m "refactor(agent): move query_single method to service.py"
```

---

### Task 7h: Add hook delegation methods

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

**Step 2: Add hook delegation methods to service.py**

Add the `execute_*_hook` methods that delegate to `HookExecutor`.

**Step 3: Update __init__.py to import AgentService from service.py**

Update `apps/api/services/agent/__init__.py` to import from the new module:

```python
from apps.api.services.agent.service import AgentService
```

Remove the import from `agent_original`.

**Step 4: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

**Step 5: Verify both import paths work**

```bash
python -c "from apps.api.services.agent import AgentService; print('Package import OK')"
python -c "from apps.api.services.agent.service import AgentService; print('Module import OK')"
```

**Step 6: Run type checker**

```bash
uv run mypy apps/api/services/agent/service.py --strict
```

**Step 7: Commit**

```bash
git add apps/api/services/agent/service.py apps/api/services/agent/__init__.py
git commit -m "refactor(agent): complete AgentService with hook delegation"
```

---

## Task 8: Incremental Import Migration and File Removal

**Files:**
- Delete: `apps/api/services/agent_original.py`
- Verify: All imports still work

**Rollback:** `git checkout HEAD -- apps/api/services/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 2: Find all files importing from agent_original**

```bash
grep -r "from apps.api.services.agent_original" apps/ tests/
```

**Step 3: Update each import site ONE AT A TIME**

For each file found:

1. Update import to use package: `from apps.api.services.agent import ...`
2. Run tests: `uv run pytest tests/ -v`
3. If tests pass, continue to next file
4. If tests fail, rollback and investigate

**Step 4: Verify no remaining imports from agent_original**

```bash
grep -r "agent_original" apps/ tests/
```

Expected: No matches

**Step 5: Run full test suite before deletion**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 6: Delete original agent_original.py**

```bash
rm apps/api/services/agent_original.py
```

**Step 7: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 8: Commit**

```bash
git add -A
git commit -m "refactor(agent): remove agent_original.py, migration complete"
```

---

## Task 9: Update Test Imports (If Needed)

**Files:**
- Modify: `tests/unit/test_agent_service.py` (if needed)

**Rollback:** `git checkout HEAD -- tests/`

**Step 1: Run full test suite (GREEN baseline)**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS (should already work via `__init__.py` re-exports)

**Step 2: Check for any deprecated import patterns**

```bash
grep -r "from apps.api.services.agent import" tests/
```

Verify all imports use the public API from `__init__.py`.

**Step 3: Verify both import styles work**

```bash
python -c "from apps.api.services.agent import StreamContext; print('Package import OK')"
python -c "from apps.api.services.agent.types import StreamContext; print('Direct module import OK')"
```

**Step 4: Run full test suite (verify still GREEN)**

```bash
uv run pytest tests/ -v
```

**Step 5: Commit if changes were needed**

```bash
git add tests/
git commit -m "test(agent): update imports for refactored agent package"
```

---

## Task 10: Final Verification

**Rollback:** N/A (verification task)

**Step 1: Run full test suite with coverage**

```bash
uv run pytest tests/ -v --cov=apps/api --cov-report=term-missing
```

Expected: All tests PASS

**Step 2: Compare coverage to Task 0 baseline**

Coverage must meet or exceed the baseline recorded in Task 0.
If coverage dropped, investigate and add tests if needed.

**Step 3: Run type checker**

```bash
uv run mypy apps/api --strict
```

Expected: PASS

**Step 4: Run linter**

```bash
uv run ruff check . && uv run ruff format --check .
```

Expected: No errors

**Step 5: Verify line counts**

```bash
wc -l apps/api/services/agent/*.py
```

Expected: Each file under 300 lines, total similar to original

**Step 6: Verify backward compatibility**

```bash
python -c "
from apps.api.services.agent import (
    AgentService,
    QueryResponseDict,
    StreamContext,
    detect_slash_command,
    resolve_env_var,
    resolve_env_dict,
)
print('All public exports accessible')
"
```

**Step 7: Create summary commit**

```bash
git log --oneline -15
```

Document the refactoring is complete.

---

## Summary

| Task | Module | Lines (approx) | Responsibility |
|------|--------|----------------|----------------|
| 0 | - | - | Baseline verification |
| 1 | `__init__.py` | ~30 | Package structure |
| 2 | `types.py` | ~50 | Type definitions |
| 3 | `utils.py` | ~60 | Environment resolution, slash command detection |
| 4 | `options.py` | ~180 | SDK options building |
| 5 | `handlers.py` | ~300 | SDK message handling |
| 6 | `hooks.py` | ~120 | Webhook hook execution |
| 7a-h | `service.py` | ~350 | Core AgentService (incremental) |
| 8 | - | - | Migration and cleanup |
| 9 | - | - | Test import updates |
| 10 | - | - | Final verification |
| **Total** | | ~1090 | (vs 1409 original - removed duplication) |

Each module is now focused on a single responsibility, making the codebase easier to understand, test, and maintain. The refactoring follows GREEN → REFACTOR → GREEN pattern with explicit rollback instructions for each task.
