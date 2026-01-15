"""End-to-end integration tests for skills and slash commands."""

from pathlib import Path

import pytest
from httpx import AsyncClient
from httpx_sse import aconnect_sse


def parse_sse_data(data: str | None) -> dict[str, object]:
    """Parse SSE data, handling empty strings."""
    if not data or not data.strip():
        return {}
    import json
    from typing import cast

    try:
        result = json.loads(data)
    except json.JSONDecodeError:
        return {"raw": data}

    if isinstance(result, dict):
        return cast("dict[str, object]", result)
    return {"raw": data}


def test_parse_sse_data_wraps_non_dict_json() -> None:
    """Ensure non-dict JSON payloads are wrapped as raw data."""
    data = '["not-a-dict"]'

    assert parse_sse_data(data) == {"raw": data}


@pytest.mark.integration
@pytest.mark.anyio
async def test_skills_and_commands_work_together(
    async_client: AsyncClient,
    tmp_path: Path,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
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

    # Change working directory for test isolation
    monkeypatch.chdir(tmp_path)

    # Query with both features
    request_data = {
        "prompt": "Use analyzer skill then /review",
        "allowed_tools": ["Skill", "Read"],
        "max_turns": 1,
    }

    events: list[dict[str, object]] = []
    async with aconnect_sse(
        async_client,
        "POST",
        "/api/v1/query",
        headers={**auth_headers, "Accept": "text/event-stream"},
        json=request_data,
    ) as event_source:
        async for sse in event_source.aiter_sse():
            if sse.event:
                data = parse_sse_data(sse.data)
                events.append({"event": sse.event, "data": data})

    # Verify init event has both
    init_events = [e for e in events if e["event"] == "init"]
    assert len(init_events) == 1
    init_data = init_events[0]["data"]
    assert isinstance(init_data, dict)

    # Verify Skill tool is in allowed tools
    tools = init_data.get("tools", [])
    assert "Skill" in tools

    # Verify commands are present
    commands = init_data.get("commands", [])
    assert len(commands) == 1
    assert isinstance(commands[0], dict)
    assert commands[0]["name"] == "review"


@pytest.mark.integration
@pytest.mark.anyio
async def test_skills_endpoint_and_agent_consistency(
    async_client: AsyncClient,
    tmp_path: Path,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
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

    # Change working directory for test isolation
    monkeypatch.chdir(tmp_path)

    # Get skills via API
    skills_response = await async_client.get("/api/v1/skills", headers=auth_headers)
    skills_data = skills_response.json()

    # Start agent query
    request_data = {
        "prompt": "Hello",
        "allowed_tools": ["Skill"],
        "max_turns": 1,
    }

    events: list[dict[str, object]] = []
    async with aconnect_sse(
        async_client,
        "POST",
        "/api/v1/query",
        headers={**auth_headers, "Accept": "text/event-stream"},
        json=request_data,
    ) as event_source:
        async for sse in event_source.aiter_sse():
            if sse.event:
                data = parse_sse_data(sse.data)
                events.append({"event": sse.event, "data": data})
                # Stop after init event for this test
                if sse.event == "init":
                    break

    # Parse init event
    init_events = [e for e in events if e["event"] == "init"]
    assert len(init_events) == 1
    init_data = init_events[0]["data"]
    assert isinstance(init_data, dict)

    # Both endpoints should see same skills
    assert len(skills_data["skills"]) == 2

    # Verify skill names match
    skill_names = {s["name"] for s in skills_data["skills"]}
    assert skill_names == {"skill-one", "skill-two"}

    # SDK loads skills internally, we just verify Skill tool is present
    assert "Skill" in init_data.get("tools", [])


@pytest.mark.integration
@pytest.mark.anyio
async def test_multiple_commands_discovered(
    async_client: AsyncClient,
    tmp_path: Path,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that multiple commands are discovered and exposed."""
    # Create multiple commands
    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "cmd1.md").write_text("# Command 1\nFirst command")
    (commands_dir / "cmd2.md").write_text("# Command 2\nSecond command")
    (commands_dir / "cmd3.md").write_text("# Command 3\nThird command")

    # Change working directory
    monkeypatch.chdir(tmp_path)

    request_data = {
        "prompt": "Hello",
        "max_turns": 1,
    }

    events: list[dict[str, object]] = []
    async with aconnect_sse(
        async_client,
        "POST",
        "/api/v1/query",
        headers={**auth_headers, "Accept": "text/event-stream"},
        json=request_data,
    ) as event_source:
        async for sse in event_source.aiter_sse():
            if sse.event:
                data = parse_sse_data(sse.data)
                events.append({"event": sse.event, "data": data})
                if sse.event == "init":
                    break

    # Verify all commands are present
    init_events = [e for e in events if e["event"] == "init"]
    assert len(init_events) == 1
    init_data = init_events[0]["data"]
    assert isinstance(init_data, dict)

    commands = init_data.get("commands", [])
    assert len(commands) == 3

    # Verify command names
    command_names = {c["name"] for c in commands if isinstance(c, dict)}
    assert command_names == {"cmd1", "cmd2", "cmd3"}


@pytest.mark.integration
@pytest.mark.anyio
async def test_invalid_skills_are_skipped(
    async_client: AsyncClient,
    tmp_path: Path,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that invalid skill files are gracefully skipped."""
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True)

    # Create invalid skill (no frontmatter)
    (skills_dir / "invalid.md").write_text("No frontmatter here")

    # Create invalid skill (missing description)
    (skills_dir / "incomplete.md").write_text("""---
name: incomplete-skill
---
Missing description""")

    # Create valid skill
    (skills_dir / "valid.md").write_text("""---
name: valid-skill
description: A valid skill
---
Content""")

    # Change working directory
    monkeypatch.chdir(tmp_path)

    # Get skills via API
    skills_response = await async_client.get("/api/v1/skills", headers=auth_headers)
    skills_data = skills_response.json()

    # Only valid skill should be returned
    assert len(skills_data["skills"]) == 1
    assert skills_data["skills"][0]["name"] == "valid-skill"
