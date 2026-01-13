"""Tests for OptionsBuilder setting_sources validation."""

from unittest.mock import MagicMock, patch

from apps.api.services.agent.options import OptionsBuilder


class TestValidateSettingSources:
    """Tests for _validate_setting_sources method."""

    def test_no_warning_when_project_included(self) -> None:
        """Should not log warning when 'project' is in setting_sources."""
        builder = OptionsBuilder.__new__(OptionsBuilder)
        builder.request = MagicMock()

        with patch("apps.api.services.agent.options.logger") as mock_logger:
            builder._validate_setting_sources(["project", "user"])
            mock_logger.warning.assert_not_called()

    def test_no_warning_when_only_project(self) -> None:
        """Should not log warning when only 'project' is specified."""
        builder = OptionsBuilder.__new__(OptionsBuilder)
        builder.request = MagicMock()

        with patch("apps.api.services.agent.options.logger") as mock_logger:
            builder._validate_setting_sources(["project"])
            mock_logger.warning.assert_not_called()

    def test_warning_when_project_missing(self) -> None:
        """Should log warning when 'project' is not in setting_sources."""
        builder = OptionsBuilder.__new__(OptionsBuilder)
        builder.request = MagicMock()

        with patch("apps.api.services.agent.options.logger") as mock_logger:
            builder._validate_setting_sources(["user"])
            mock_logger.warning.assert_called_once_with(
                "setting_sources_missing_project",
                setting_sources=["user"],
                hint="Include 'project' in setting_sources to load CLAUDE.md files",
            )

    def test_warning_when_empty_list(self) -> None:
        """Should log warning when setting_sources is empty list."""
        builder = OptionsBuilder.__new__(OptionsBuilder)
        builder.request = MagicMock()

        with patch("apps.api.services.agent.options.logger") as mock_logger:
            builder._validate_setting_sources([])
            mock_logger.warning.assert_called_once()
            call_kwargs = mock_logger.warning.call_args[1]
            assert call_kwargs["setting_sources"] == []
