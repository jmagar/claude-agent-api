"""Integration tests for slash command execution."""

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
        return cast("dict[str, object]", result)
    except json.JSONDecodeError:
        return {"raw": data}


@pytest.mark.integration
@pytest.mark.anyio
async def test_slash_command_included_in_init_event(
    async_client: AsyncClient,
    tmp_path: Path,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test slash commands are exposed in init event."""
    # Create test command
    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "example.md").write_text("# Example Command\n\nTest")

    # Change working directory for test isolation
    monkeypatch.chdir(tmp_path)

    # Make query
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
                # Stop after init event for this test
                if sse.event == "init":
                    break

    # Parse init event
    assert len(events) >= 1
    init_event = events[0]
    assert init_event["event"] == "init"
    init_data = init_event["data"]
    assert isinstance(init_data, dict)

    # Verify commands are present
    commands = init_data.get("commands", [])
    assert len(commands) == 1
    assert isinstance(commands[0], dict)
    assert commands[0]["name"] == "example"
    # Path should be absolute path to command file
    assert commands[0]["path"].endswith(".claude/commands/example.md")


@pytest.mark.integration
@pytest.mark.anyio
async def test_slash_command_execution_via_prompt(
    async_client: AsyncClient,
    tmp_path: Path,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test slash command is executed when in prompt."""
    # Create test command
    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "greet.md").write_text("""# Greet Command

Say hello to: $ARGUMENTS
""")

    # Change working directory
    monkeypatch.chdir(tmp_path)

    # Send slash command via prompt
    request_data = {
        "prompt": "/greet world",
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

    # Check for error events
    error_events = [e for e in events if e["event"] == "error"]
    assert len(error_events) == 0

    # Verify we got a done event (stream completed successfully)
    done_events = [e for e in events if e["event"] == "done"]
    assert len(done_events) == 1


@pytest.mark.integration
@pytest.mark.anyio
async def test_no_commands_when_directory_missing(
    async_client: AsyncClient,
    tmp_path: Path,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test empty commands list when .claude/commands/ directory doesn't exist."""
    # Change to directory without commands
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

    # Verify empty commands list
    assert len(events) >= 1
    init_event = events[0]
    init_data = init_event["data"]
    assert isinstance(init_data, dict)
    commands = init_data.get("commands", [])
    assert len(commands) == 0
