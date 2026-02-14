"""Unit tests for session_utils module."""

import pytest

from apps.api.utils.session_utils import parse_session_status


class TestParseSessionStatus:
    """Tests for parse_session_status."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("active", "active"),
            ("completed", "completed"),
            ("error", "error"),
        ],
    )
    def test_lowercase_values(self, raw: str, expected: str) -> None:
        assert parse_session_status(raw) == expected

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("Active", "active"),
            ("ACTIVE", "active"),
            ("Completed", "completed"),
            ("COMPLETED", "completed"),
            ("Error", "error"),
            ("ERROR", "error"),
        ],
    )
    def test_case_insensitive(self, raw: str, expected: str) -> None:
        assert parse_session_status(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        ["unknown", "pending", "", "INVALID", "running"],
    )
    def test_unknown_defaults_to_active(self, raw: str) -> None:
        assert parse_session_status(raw) == "active"
