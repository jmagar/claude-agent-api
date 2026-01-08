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
