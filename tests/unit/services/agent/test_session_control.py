"""Unit tests for SessionControl."""

from unittest.mock import AsyncMock

import pytest

from apps.api.services.agent.session_control import SessionControl
from apps.api.services.agent.session_tracker import AgentSessionTracker


@pytest.mark.anyio
async def test_session_control_interrupt_requires_active_session() -> None:
    tracker = AsyncMock(spec=AgentSessionTracker)
    tracker.is_active.return_value = False
    control = SessionControl(session_tracker=tracker)

    result = await control.interrupt("sid")

    assert result is False
    tracker.is_active.assert_called_once_with("sid")


@pytest.mark.anyio
async def test_session_control_interrupt_marks_when_active() -> None:
    tracker = AsyncMock(spec=AgentSessionTracker)
    tracker.is_active.return_value = True
    control = SessionControl(session_tracker=tracker)

    result = await control.interrupt("sid")

    assert result is True
    tracker.is_active.assert_called_once_with("sid")
    tracker.mark_interrupted.assert_called_once_with("sid")


@pytest.mark.anyio
async def test_session_control_submit_answer_requires_active_session() -> None:
    tracker = AsyncMock(spec=AgentSessionTracker)
    tracker.is_active.return_value = False
    control = SessionControl(session_tracker=tracker)

    result = await control.submit_answer("sid", "answer")

    assert result is False
    tracker.is_active.assert_called_once_with("sid")


@pytest.mark.anyio
async def test_session_control_submit_answer_accepts_when_active() -> None:
    tracker = AsyncMock(spec=AgentSessionTracker)
    tracker.is_active.return_value = True
    control = SessionControl(session_tracker=tracker)

    result = await control.submit_answer("sid", "answer")

    assert result is True
    tracker.is_active.assert_called_once_with("sid")


@pytest.mark.anyio
async def test_session_control_update_permission_mode_requires_active_session() -> None:
    tracker = AsyncMock(spec=AgentSessionTracker)
    tracker.is_active.return_value = False
    control = SessionControl(session_tracker=tracker)

    result = await control.update_permission_mode("sid", "default")

    assert result is False
    tracker.is_active.assert_called_once_with("sid")


@pytest.mark.anyio
async def test_session_control_update_permission_mode_accepts_when_active() -> None:
    tracker = AsyncMock(spec=AgentSessionTracker)
    tracker.is_active.return_value = True
    control = SessionControl(session_tracker=tracker)

    result = await control.update_permission_mode("sid", "default")

    assert result is True
    tracker.is_active.assert_called_once_with("sid")
