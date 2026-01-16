"""Integration tests for skill invocation via agent."""

from pathlib import Path
from typing import cast

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
        return cast("dict[str, object]", result)
    except json.JSONDecodeError:
        return {"raw": data}


@pytest.mark.integration
@pytest.mark.anyio
async def test_agent_can_invoke_skill_when_in_allowed_tools(
    async_client: AsyncClient,
    tmp_path: Path,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test agent can invoke skills when Skill tool is in allowedTools."""
    # Create test skill
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "test-skill.md").write_text(
        """---
name: test-skill
description: Use this to test skill invocation
---

Test skill content.
"""
    )

    # Change working directory for test isolation
    monkeypatch.chdir(tmp_path)

    # Make query with Skill in allowedTools
    request_data = {
        "prompt": "Use the test-skill",
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

    # Verify Skill tool was available (check init event)
    assert len(events) >= 1
    init_event = events[0]
    assert init_event["event"] == "init"
    init_data = init_event["data"]
    assert isinstance(init_data, dict)
    init_data = cast("dict[str, object]", init_data)
    tools = init_data.get("tools")
    assert isinstance(tools, list)
    assert "Skill" in tools


@pytest.mark.integration
@pytest.mark.anyio
async def test_agent_cannot_invoke_skill_when_not_in_allowed_tools(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test agent cannot invoke skills when Skill tool not in allowedTools."""
    request_data = {
        "prompt": "Use a skill",
        "allowed_tools": ["Read", "Write"],  # No Skill tool
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

    # Verify Skill tool NOT in allowed tools
    assert len(events) >= 1
    init_event = events[0]
    assert init_event["event"] == "init"
    init_data = init_event["data"]
    assert isinstance(init_data, dict)
    init_data = cast("dict[str, object]", init_data)
    tools = init_data.get("tools")
    assert isinstance(tools, list)
    assert "Skill" not in tools
