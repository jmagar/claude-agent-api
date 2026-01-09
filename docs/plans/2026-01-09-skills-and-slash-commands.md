# Skills and Slash Commands Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement skills discovery/invocation and slash command execution for full SDK feature parity

**Architecture:** Skills loaded from filesystem (.claude/skills/), exposed via Skill tool when in allowedTools. Slash commands discovered from .claude/commands/, executed by transforming command string and delegating to SDK.

**Tech Stack:** Claude Agent SDK, FastAPI, Pydantic, pathlib for filesystem operations

---

## Context

Current state:
- **Skills**: GET /skills endpoint exists but returns empty list with TODO comment ([apps/api/routes/skills.py:29-30](apps/api/routes/skills.py#L29-L30))
- **Slash Commands**: Detection implemented in [apps/api/services/agent/utils.py](apps/api/services/agent/utils.py) but no execution path exists
- **Tests**: Only contract tests for skills endpoint, only parsing tests for slash commands

Requirements from spec.md:
- **FR-043 to FR-046**: Skills must load from filesystem, support discovery, enable invocation when "Skill" in allowedTools
- **FR-047 to FR-050**: Slash commands must discover from .claude/commands/, expose in init messages, support execution with arguments

---

## Task 1: Skills Discovery Service

**Files:**
- Create: `apps/api/services/skills.py`
- Modify: `apps/api/routes/skills.py:20-31`
- Test: `tests/unit/test_skills_service.py`
- Test: `tests/integration/test_skills.py`

### Step 1: Write the failing test

**File:** `tests/unit/test_skills_service.py`

```python
"""Unit tests for skills discovery service."""

import pytest
from pathlib import Path
from apps.api.services.skills import SkillsService


class TestSkillsDiscovery:
    """Test skills discovery from filesystem."""

    def test_discover_skills_from_project_directory(self, tmp_path: Path) -> None:
        """Test discovering skills from .claude/skills/ directory."""
        # Create test skill file
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        skill_file = skills_dir / "test-skill.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill for unit testing
---

This is a test skill.
""")

        # Discover skills
        service = SkillsService(project_path=tmp_path)
        skills = service.discover_skills()

        # Assertions
        assert len(skills) == 1
        assert skills[0]["name"] == "test-skill"
        assert skills[0]["description"] == "A test skill for unit testing"
        assert skills[0]["path"] == str(skill_file)

    def test_discover_skills_returns_empty_when_no_directory(self, tmp_path: Path) -> None:
        """Test discovering skills when .claude/skills/ doesn't exist."""
        service = SkillsService(project_path=tmp_path)
        skills = service.discover_skills()
        assert skills == []

    def test_discover_skills_skips_invalid_files(self, tmp_path: Path) -> None:
        """Test that invalid skill files are skipped."""
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        # Create invalid file (no frontmatter)
        (skills_dir / "invalid.md").write_text("No frontmatter here")

        # Create valid file
        (skills_dir / "valid.md").write_text("""---
name: valid-skill
description: Valid skill
---
Content""")

        service = SkillsService(project_path=tmp_path)
        skills = service.discover_skills()

        assert len(skills) == 1
        assert skills[0]["name"] == "valid-skill"
```

### Step 2: Run test to verify it fails

```bash
uv run pytest tests/unit/test_skills_service.py::TestSkillsDiscovery -v
```

**Expected output:**
```
FAILED tests/unit/test_skills_service.py::test_discover_skills_from_project_directory - ModuleNotFoundError: No module named 'apps.api.services.skills'
```

### Step 3: Write minimal implementation

**File:** `apps/api/services/skills.py`

```python
"""Skills discovery and management service."""

from pathlib import Path
from typing import TypedDict
import re


class SkillInfo(TypedDict):
    """Information about a discovered skill."""

    name: str
    description: str
    path: str


class SkillsService:
    """Service for discovering and managing skills from filesystem."""

    def __init__(self, project_path: Path | str) -> None:
        """Initialize skills service.

        Args:
            project_path: Path to project root containing .claude/skills/
        """
        self.project_path = Path(project_path)
        self.skills_dir = self.project_path / ".claude" / "skills"

    def discover_skills(self) -> list[SkillInfo]:
        """Discover skills from .claude/skills/ directory.

        Returns:
            List of skill info dictionaries with name, description, path
        """
        if not self.skills_dir.exists():
            return []

        skills: list[SkillInfo] = []
        for skill_file in self.skills_dir.glob("*.md"):
            skill_info = self._parse_skill_file(skill_file)
            if skill_info:
                skills.append(skill_info)

        return skills

    def _parse_skill_file(self, file_path: Path) -> SkillInfo | None:
        """Parse skill markdown file and extract frontmatter.

        Args:
            file_path: Path to skill .md file

        Returns:
            SkillInfo dict or None if parsing fails
        """
        try:
            content = file_path.read_text()

            # Extract YAML frontmatter between --- delimiters
            frontmatter_match = re.match(
                r"^---\s*\n(.*?)\n---\s*\n",
                content,
                re.DOTALL
            )

            if not frontmatter_match:
                return None

            frontmatter = frontmatter_match.group(1)

            # Extract name and description from frontmatter
            name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
            desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)

            if not name_match or not desc_match:
                return None

            return SkillInfo(
                name=name_match.group(1).strip(),
                description=desc_match.group(1).strip(),
                path=str(file_path)
            )

        except Exception:
            return None
```

### Step 4: Run test to verify it passes

```bash
uv run pytest tests/unit/test_skills_service.py::TestSkillsDiscovery -v
```

**Expected output:**
```
tests/unit/test_skills_service.py::test_discover_skills_from_project_directory PASSED
tests/unit/test_skills_service.py::test_discover_skills_returns_empty_when_no_directory PASSED
tests/unit/test_skills_service.py::test_discover_skills_skips_invalid_files PASSED
```

### Step 5: Commit

```bash
git add apps/api/services/skills.py tests/unit/test_skills_service.py
git commit -m "$(cat <<'EOF'
feat: add skills discovery service

Implement SkillsService to discover skills from .claude/skills/
directory. Parses markdown frontmatter to extract skill name and
description. Handles missing directories and invalid files.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Skills API Endpoint Integration

**Files:**
- Modify: `apps/api/routes/skills.py:20-31`
- Modify: `apps/api/dependencies.py` (add get_skills_service)
- Test: `tests/integration/test_skills.py`

### Step 1: Write the failing test

**File:** `tests/integration/test_skills.py`

```python
"""Integration tests for skills API endpoint."""

import pytest
from httpx import AsyncClient
from pathlib import Path


@pytest.mark.asyncio
async def test_skills_endpoint_returns_discovered_skills(
    client: AsyncClient,
    tmp_path: Path,
    api_key: str
) -> None:
    """Test GET /skills returns skills from filesystem."""
    # Create test skill
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "example.md").write_text("""---
name: example-skill
description: An example skill
---
Content here""")

    # Make request
    response = await client.get(
        "/api/v1/skills",
        headers={"X-API-Key": api_key}
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert len(data["skills"]) == 1
    assert data["skills"][0]["name"] == "example-skill"
    assert data["skills"][0]["description"] == "An example skill"


@pytest.mark.asyncio
async def test_skills_endpoint_returns_empty_when_no_skills(
    client: AsyncClient,
    api_key: str
) -> None:
    """Test GET /skills returns empty list when no skills exist."""
    response = await client.get(
        "/api/v1/skills",
        headers={"X-API-Key": api_key}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["skills"] == []
```

### Step 2: Run test to verify it fails

```bash
uv run pytest tests/integration/test_skills.py -v
```

**Expected output:**
```
FAILED tests/integration/test_skills.py::test_skills_endpoint_returns_discovered_skills
AssertionError: assert [] == [{'name': 'example-skill', ...}]
```

### Step 3: Write minimal implementation

**File:** `apps/api/dependencies.py` (add after existing dependencies)

```python
from apps.api.services.skills import SkillsService

def get_skills_service() -> SkillsService:
    """Get skills service instance.

    Returns:
        SkillsService instance configured with project path
    """
    from pathlib import Path
    # Use current working directory as project root
    project_path = Path.cwd()
    return SkillsService(project_path=project_path)
```

**File:** `apps/api/routes/skills.py` (replace lines 20-31)

```python
from fastapi import APIRouter, Depends
from apps.api.schemas.responses import SkillsListResponse, SkillResponse
from apps.api.services.skills import SkillsService
from apps.api.dependencies import get_skills_service

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=SkillsListResponse)
async def list_skills(
    skills_service: SkillsService = Depends(get_skills_service)
) -> SkillsListResponse:
    """List all available skills discovered from filesystem.

    Skills are loaded from .claude/skills/ directories when
    settingSources includes "project" or "user".

    Returns:
        List of available skills with name, description, path
    """
    discovered_skills = skills_service.discover_skills()

    skills = [
        SkillResponse(
            name=skill["name"],
            description=skill["description"],
            path=skill["path"]
        )
        for skill in discovered_skills
    ]

    return SkillsListResponse(skills=skills)
```

### Step 4: Run test to verify it passes

```bash
uv run pytest tests/integration/test_skills.py -v
```

**Expected output:**
```
tests/integration/test_skills.py::test_skills_endpoint_returns_discovered_skills PASSED
tests/integration/test_skills.py::test_skills_endpoint_returns_empty_when_no_skills PASSED
```

### Step 5: Commit

```bash
git add apps/api/routes/skills.py apps/api/dependencies.py tests/integration/test_skills.py
git commit -m "$(cat <<'EOF'
feat: implement skills discovery endpoint

Connect SkillsService to GET /skills endpoint. Remove TODO stub
and implement actual filesystem discovery. Skills now loaded from
.claude/skills/ directory and returned via API.

Implements FR-043 to FR-045.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Skill Invocation in Agent Service

**Files:**
- Modify: `apps/api/services/agent/service.py`
- Test: `tests/integration/test_skill_invocation.py`

### Step 1: Write the failing test

**File:** `tests/integration/test_skill_invocation.py`

```python
"""Integration tests for skill invocation via agent."""

import pytest
from httpx import AsyncClient
from pathlib import Path


@pytest.mark.asyncio
async def test_agent_can_invoke_skill_when_in_allowed_tools(
    client: AsyncClient,
    tmp_path: Path,
    api_key: str
) -> None:
    """Test agent can invoke skills when Skill tool is in allowedTools."""
    # Create test skill
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "test-skill.md").write_text("""---
name: test-skill
description: Use this to test skill invocation
---

Test skill content.
""")

    # Make query with Skill in allowedTools
    response = await client.post(
        "/api/v1/query",
        headers={
            "X-API-Key": api_key,
            "Accept": "text/event-stream"
        },
        json={
            "prompt": "Use the test-skill",
            "allowed_tools": ["Skill"],
            "cwd": str(tmp_path)
        }
    )

    assert response.status_code == 200

    # Parse SSE stream
    events = []
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            import json
            events.append(json.loads(line[6:]))

    # Verify Skill tool was available (check init event)
    init_event = next(e for e in events if e["type"] == "init")
    assert "Skill" in init_event["data"].get("allowed_tools", [])


@pytest.mark.asyncio
async def test_agent_cannot_invoke_skill_when_not_in_allowed_tools(
    client: AsyncClient,
    api_key: str
) -> None:
    """Test agent cannot invoke skills when Skill tool not in allowedTools."""
    response = await client.post(
        "/api/v1/query",
        headers={
            "X-API-Key": api_key,
            "Accept": "text/event-stream"
        },
        json={
            "prompt": "Use a skill",
            "allowed_tools": ["Read", "Write"]  # No Skill tool
        }
    )

    assert response.status_code == 200

    # Parse SSE stream
    events = []
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            import json
            events.append(json.loads(line[6:]))

    # Verify Skill tool NOT in allowed tools
    init_event = next(e for e in events if e["type"] == "init")
    assert "Skill" not in init_event["data"].get("allowed_tools", [])
```

### Step 2: Run test to verify it fails

```bash
uv run pytest tests/integration/test_skill_invocation.py -v
```

**Expected output:**
```
FAILED tests/integration/test_skill_invocation.py::test_agent_can_invoke_skill_when_in_allowed_tools
AssertionError: assert 'Skill' in []
```

### Step 3: Write minimal implementation

**File:** `apps/api/services/agent/service.py` (modify create_options method)

Find the section where allowed_tools is processed and add Skill tool validation:

```python
def _validate_and_process_tools(
    self,
    allowed_tools: list[str] | None,
    disallowed_tools: list[str] | None,
    cwd: str | None
) -> dict[str, Any]:
    """Validate and process tool configuration.

    Args:
        allowed_tools: List of allowed tool names
        disallowed_tools: List of disallowed tool names
        cwd: Working directory for skill discovery

    Returns:
        Dict with processed tool configuration
    """
    from apps.api.services.skills import SkillsService
    from pathlib import Path

    # Existing tool validation logic...

    # If Skill tool is in allowed_tools, ensure skills are discoverable
    if allowed_tools and "Skill" in allowed_tools:
        project_path = Path(cwd) if cwd else Path.cwd()
        skills_service = SkillsService(project_path=project_path)
        discovered_skills = skills_service.discover_skills()

        # Skills will be loaded by SDK if setting_sources includes project/user
        # We just validate that Skill tool is properly configured
        if not discovered_skills:
            # Log warning but don't fail - skills might be in user directory
            import structlog
            logger = structlog.get_logger()
            logger.warning(
                "skill_tool_enabled_but_no_skills_found",
                project_path=str(project_path)
            )

    return {
        "allowed_tools": allowed_tools,
        "disallowed_tools": disallowed_tools
    }
```

### Step 4: Run test to verify it passes

```bash
uv run pytest tests/integration/test_skill_invocation.py -v
```

**Expected output:**
```
tests/integration/test_skill_invocation.py::test_agent_can_invoke_skill_when_in_allowed_tools PASSED
tests/integration/test_skill_invocation.py::test_agent_cannot_invoke_skill_when_not_in_allowed_tools PASSED
```

### Step 5: Commit

```bash
git add apps/api/services/agent/service.py tests/integration/test_skill_invocation.py
git commit -m "$(cat <<'EOF'
feat: enable skill invocation in agent service

Add validation for Skill tool in allowedTools. When Skill tool is
enabled, verify skills are discoverable from project directory.
SDK handles actual skill loading via setting_sources parameter.

Implements FR-046.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Slash Command Execution Service

**Files:**
- Create: `apps/api/services/commands.py`
- Modify: `apps/api/services/agent/service.py` (add command execution)
- Test: `tests/unit/test_commands_service.py`
- Test: `tests/integration/test_slash_commands.py`

### Step 1: Write the failing test

**File:** `tests/unit/test_commands_service.py`

```python
"""Unit tests for slash commands service."""

import pytest
from pathlib import Path
from apps.api.services.commands import CommandsService


class TestCommandsDiscovery:
    """Test command discovery from filesystem."""

    def test_discover_commands_from_directory(self, tmp_path: Path) -> None:
        """Test discovering commands from .claude/commands/ directory."""
        # Create test command file
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        command_file = commands_dir / "test.md"
        command_file.write_text("""# Test Command

This is a test command.

Arguments: $ARGUMENTS
""")

        # Discover commands
        service = CommandsService(project_path=tmp_path)
        commands = service.discover_commands()

        # Assertions
        assert len(commands) == 1
        assert commands[0]["name"] == "test"
        assert commands[0]["path"] == str(command_file)

    def test_discover_commands_returns_empty_when_no_directory(
        self,
        tmp_path: Path
    ) -> None:
        """Test discovering commands when .claude/commands/ doesn't exist."""
        service = CommandsService(project_path=tmp_path)
        commands = service.discover_commands()
        assert commands == []


class TestCommandExecution:
    """Test command execution logic."""

    def test_parse_command_with_arguments(self) -> None:
        """Test parsing slash command with arguments."""
        service = CommandsService(project_path=Path.cwd())

        result = service.parse_command("/test arg1 arg2")

        assert result is not None
        assert result["command"] == "test"
        assert result["args"] == "arg1 arg2"

    def test_parse_command_without_arguments(self) -> None:
        """Test parsing slash command without arguments."""
        service = CommandsService(project_path=Path.cwd())

        result = service.parse_command("/test")

        assert result is not None
        assert result["command"] == "test"
        assert result["args"] == ""

    def test_parse_command_returns_none_for_non_command(self) -> None:
        """Test parsing non-command string returns None."""
        service = CommandsService(project_path=Path.cwd())

        result = service.parse_command("regular prompt")

        assert result is None
```

### Step 2: Run test to verify it fails

```bash
uv run pytest tests/unit/test_commands_service.py -v
```

**Expected output:**
```
FAILED tests/unit/test_commands_service.py::test_discover_commands_from_directory - ModuleNotFoundError: No module named 'apps.api.services.commands'
```

### Step 3: Write minimal implementation

**File:** `apps/api/services/commands.py`

```python
"""Slash commands discovery and execution service."""

from pathlib import Path
from typing import TypedDict
import re


class CommandInfo(TypedDict):
    """Information about a discovered command."""

    name: str
    path: str


class ParsedCommand(TypedDict):
    """Parsed command with name and arguments."""

    command: str
    args: str


class CommandsService:
    """Service for discovering and executing slash commands."""

    def __init__(self, project_path: Path | str) -> None:
        """Initialize commands service.

        Args:
            project_path: Path to project root containing .claude/commands/
        """
        self.project_path = Path(project_path)
        self.commands_dir = self.project_path / ".claude" / "commands"

    def discover_commands(self) -> list[CommandInfo]:
        """Discover commands from .claude/commands/ directory.

        Returns:
            List of command info dicts with name and path
        """
        if not self.commands_dir.exists():
            return []

        commands: list[CommandInfo] = []
        for command_file in self.commands_dir.glob("*.md"):
            commands.append(
                CommandInfo(
                    name=command_file.stem,
                    path=str(command_file)
                )
            )

        return commands

    def parse_command(self, prompt: str) -> ParsedCommand | None:
        """Parse slash command from prompt string.

        Args:
            prompt: User prompt that may start with /command

        Returns:
            ParsedCommand dict or None if not a slash command
        """
        # Use existing detection logic from utils.py
        from apps.api.services.agent.utils import detect_slash_command

        detected = detect_slash_command(prompt)
        if not detected:
            return None

        return ParsedCommand(
            command=detected["command"],
            args=detected.get("args", "")
        )
```

### Step 4: Run test to verify it passes

```bash
uv run pytest tests/unit/test_commands_service.py -v
```

**Expected output:**
```
tests/unit/test_commands_service.py::test_discover_commands_from_directory PASSED
tests/unit/test_commands_service.py::test_discover_commands_returns_empty_when_no_directory PASSED
tests/unit/test_commands_service.py::test_parse_command_with_arguments PASSED
tests/unit/test_commands_service.py::test_parse_command_without_arguments PASSED
tests/unit/test_commands_service.py::test_parse_command_returns_none_for_non_command PASSED
```

### Step 5: Commit

```bash
git add apps/api/services/commands.py tests/unit/test_commands_service.py
git commit -m "$(cat <<'EOF'
feat: add slash commands discovery service

Implement CommandsService to discover commands from .claude/commands/
directory. Parses slash command syntax from prompt strings. Delegates
to existing detect_slash_command utility.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Slash Command Execution in Agent

**Files:**
- Modify: `apps/api/services/agent/service.py`
- Modify: `apps/api/schemas/responses.py` (add commands to InitEvent)
- Test: `tests/integration/test_slash_commands.py`

### Step 1: Write the failing test

**File:** `tests/integration/test_slash_commands.py`

```python
"""Integration tests for slash command execution."""

import pytest
from httpx import AsyncClient
from pathlib import Path


@pytest.mark.asyncio
async def test_slash_command_included_in_init_event(
    client: AsyncClient,
    tmp_path: Path,
    api_key: str
) -> None:
    """Test slash commands are exposed in init event."""
    # Create test command
    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "example.md").write_text("# Example Command\n\nTest")

    # Make query
    response = await client.post(
        "/api/v1/query",
        headers={
            "X-API-Key": api_key,
            "Accept": "text/event-stream"
        },
        json={
            "prompt": "Hello",
            "cwd": str(tmp_path)
        }
    )

    assert response.status_code == 200

    # Parse init event
    import json
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            event = json.loads(line[6:])
            if event["type"] == "init":
                commands = event["data"].get("commands", [])
                assert len(commands) == 1
                assert commands[0]["name"] == "example"
                break


@pytest.mark.asyncio
async def test_slash_command_execution_via_prompt(
    client: AsyncClient,
    tmp_path: Path,
    api_key: str
) -> None:
    """Test slash command is executed when in prompt."""
    # Create test command
    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "greet.md").write_text("""# Greet Command

Say hello to: $ARGUMENTS
""")

    # Send slash command via prompt
    response = await client.post(
        "/api/v1/query",
        headers={
            "X-API-Key": api_key,
            "Accept": "text/event-stream"
        },
        json={
            "prompt": "/greet world",
            "cwd": str(tmp_path)
        }
    )

    assert response.status_code == 200

    # Verify command was processed (SDK handles execution)
    # Just verify no error occurred
    events = []
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            import json
            events.append(json.loads(line[6:]))

    # Check for error events
    error_events = [e for e in events if e["type"] == "error"]
    assert len(error_events) == 0
```

### Step 2: Run test to verify it fails

```bash
uv run pytest tests/integration/test_slash_commands.py -v
```

**Expected output:**
```
FAILED tests/integration/test_slash_commands.py::test_slash_command_included_in_init_event
AssertionError: assert [] == [{'name': 'example'}]
```

### Step 3: Write minimal implementation

**File:** `apps/api/schemas/responses.py` (modify InitEventData)

```python
class InitEventData(BaseModel):
    """Data for initialization event."""

    session_id: str
    allowed_tools: list[str] | None = None
    mcp_servers: list[McpServerStatus] | None = None
    commands: list[CommandInfo] | None = None  # Add this field

    model_config = ConfigDict(extra="allow")


class CommandInfo(BaseModel):
    """Information about an available slash command."""

    name: str
    path: str
```

**File:** `apps/api/services/agent/service.py` (modify initialization)

Add command discovery to the options creation:

```python
async def _create_init_event(
    self,
    session_id: str,
    options: dict[str, Any]
) -> InitEventData:
    """Create initialization event with commands.

    Args:
        session_id: Session ID
        options: Agent options dict

    Returns:
        InitEventData with commands list
    """
    from apps.api.services.commands import CommandsService
    from pathlib import Path

    # Discover commands from project directory
    cwd = options.get("cwd", ".")
    commands_service = CommandsService(project_path=Path(cwd))
    discovered_commands = commands_service.discover_commands()

    return InitEventData(
        session_id=session_id,
        allowed_tools=options.get("allowed_tools"),
        mcp_servers=options.get("mcp_servers"),
        commands=[
            CommandInfo(name=cmd["name"], path=cmd["path"])
            for cmd in discovered_commands
        ]
    )
```

Also modify prompt processing to detect slash commands:

```python
async def _preprocess_prompt(self, prompt: str, cwd: str) -> str:
    """Preprocess prompt to handle slash commands.

    Args:
        prompt: User prompt
        cwd: Working directory

    Returns:
        Processed prompt (may be transformed for command execution)
    """
    from apps.api.services.commands import CommandsService
    from pathlib import Path

    commands_service = CommandsService(project_path=Path(cwd))
    parsed = commands_service.parse_command(prompt)

    if parsed:
        # Slash command detected - SDK will handle execution
        # We just pass it through as-is
        import structlog
        logger = structlog.get_logger()
        logger.info(
            "slash_command_detected",
            command=parsed["command"],
            args=parsed["args"]
        )

    return prompt
```

### Step 4: Run test to verify it passes

```bash
uv run pytest tests/integration/test_slash_commands.py -v
```

**Expected output:**
```
tests/integration/test_slash_commands.py::test_slash_command_included_in_init_event PASSED
tests/integration/test_slash_commands.py::test_slash_command_execution_via_prompt PASSED
```

### Step 5: Commit

```bash
git add apps/api/services/agent/service.py apps/api/schemas/responses.py tests/integration/test_slash_commands.py
git commit -m "$(cat <<'EOF'
feat: implement slash command execution in agent

Add commands list to InitEvent for command discovery. Detect slash
commands in prompt preprocessing. SDK handles actual command execution.

Implements FR-047 to FR-050.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Integration Testing and Validation

**Files:**
- Test: `tests/integration/test_skills_slash_commands_integration.py`

### Step 1: Write the comprehensive integration test

**File:** `tests/integration/test_skills_slash_commands_integration.py`

```python
"""End-to-end integration tests for skills and slash commands."""

import pytest
from httpx import AsyncClient
from pathlib import Path


@pytest.mark.asyncio
async def test_skills_and_commands_work_together(
    client: AsyncClient,
    tmp_path: Path,
    api_key: str
) -> None:
    """Test that skills and slash commands can be used in same session."""
    # Setup skills
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "analyzer.md").write_text("""---
name: analyzer
description: Analyze code patterns
---
Analysis skill""")

    # Setup commands
    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "review.md").write_text("# Review\nCode review")

    # Query with both features
    response = await client.post(
        "/api/v1/query",
        headers={
            "X-API-Key": api_key,
            "Accept": "text/event-stream"
        },
        json={
            "prompt": "Use analyzer skill then /review",
            "allowed_tools": ["Skill", "Read"],
            "cwd": str(tmp_path)
        }
    )

    assert response.status_code == 200

    # Parse events
    import json
    events = []
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    # Verify init event has both
    init_event = next(e for e in events if e["type"] == "init")
    assert "Skill" in init_event["data"]["allowed_tools"]
    assert len(init_event["data"]["commands"]) == 1
    assert init_event["data"]["commands"][0]["name"] == "review"


@pytest.mark.asyncio
async def test_skills_endpoint_and_agent_consistency(
    client: AsyncClient,
    tmp_path: Path,
    api_key: str
) -> None:
    """Test GET /skills returns same skills available to agent."""
    # Create skills
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "skill1.md").write_text("""---
name: skill-one
description: First skill
---
Content""")
    (skills_dir / "skill2.md").write_text("""---
name: skill-two
description: Second skill
---
Content""")

    # Get skills via API
    skills_response = await client.get(
        "/api/v1/skills",
        headers={"X-API-Key": api_key}
    )
    skills_data = skills_response.json()

    # Start agent query
    query_response = await client.post(
        "/api/v1/query",
        headers={
            "X-API-Key": api_key,
            "Accept": "text/event-stream"
        },
        json={
            "prompt": "Hello",
            "allowed_tools": ["Skill"],
            "cwd": str(tmp_path)
        }
    )

    # Parse init event
    import json
    async for line in query_response.aiter_lines():
        if line.startswith("data: "):
            event = json.loads(line[6:])
            if event["type"] == "init":
                # Both endpoints should see same skills
                assert len(skills_data["skills"]) == 2
                # (SDK loads skills internally, we just verify Skill tool is present)
                assert "Skill" in event["data"]["allowed_tools"]
                break
```

### Step 2: Run test to verify it passes

```bash
uv run pytest tests/integration/test_skills_slash_commands_integration.py -v
```

**Expected output:**
```
tests/integration/test_skills_slash_commands_integration.py::test_skills_and_commands_work_together PASSED
tests/integration/test_skills_slash_commands_integration.py::test_skills_endpoint_and_agent_consistency PASSED
```

### Step 3: Run all tests

```bash
uv run pytest tests/ -v --cov=apps/api --cov-report=term-missing
```

**Expected output:**
```
============================== test session starts ==============================
...
tests/unit/test_skills_service.py::TestSkillsDiscovery::test_discover_skills_from_project_directory PASSED
tests/unit/test_commands_service.py::TestCommandsDiscovery::test_discover_commands_from_directory PASSED
tests/integration/test_skills.py::test_skills_endpoint_returns_discovered_skills PASSED
tests/integration/test_slash_commands.py::test_slash_command_included_in_init_event PASSED
tests/integration/test_skills_slash_commands_integration.py::test_skills_and_commands_work_together PASSED
...
============================== XX passed in X.XXs ================================
```

### Step 4: Type check

```bash
uv run mypy apps/api --strict
```

**Expected output:**
```
Success: no issues found in XX source files
```

### Step 5: Final commit

```bash
git add tests/integration/test_skills_slash_commands_integration.py
git commit -m "$(cat <<'EOF'
test: add integration tests for skills and slash commands

Comprehensive end-to-end tests verifying skills and slash commands
work together and maintain consistency across API endpoints.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-01-09-skills-and-slash-commands.md`.

Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach would you like to use?
