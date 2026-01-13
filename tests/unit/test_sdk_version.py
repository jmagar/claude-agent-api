"""Tests for SDK version compatibility check."""

from unittest.mock import patch

from packaging.version import parse as parse_version


class TestVerifySdkVersion:
    """Tests for verify_sdk_version function."""

    def test_passes_when_version_meets_minimum(self) -> None:
        """Should log debug when installed version >= minimum."""
        from apps.api.main import verify_sdk_version

        with patch("apps.api.main.logger") as mock_logger:
            verify_sdk_version()
            # Should log debug, not warning
            mock_logger.debug.assert_called()
            mock_logger.warning.assert_not_called()

    def test_version_comparison_logic(self) -> None:
        """Test that version comparison works correctly."""
        from apps.api.main import MIN_SDK_VERSION

        minimum = parse_version(MIN_SDK_VERSION)

        # These should be below minimum
        assert parse_version("0.1.0") < minimum
        assert parse_version("0.0.1") < minimum

        # These should meet minimum
        assert parse_version(MIN_SDK_VERSION) >= minimum
        assert parse_version("0.2.0") >= minimum
        assert parse_version("1.0.0") >= minimum


class TestMinSdkVersion:
    """Tests for MIN_SDK_VERSION constant."""

    def test_min_version_is_defined(self) -> None:
        """Should have MIN_SDK_VERSION defined."""
        from apps.api.main import MIN_SDK_VERSION

        assert MIN_SDK_VERSION is not None
        assert isinstance(MIN_SDK_VERSION, str)

    def test_min_version_is_valid_semver(self) -> None:
        """Should be a valid semantic version."""
        from apps.api.main import MIN_SDK_VERSION

        # Should not raise
        version = parse_version(MIN_SDK_VERSION)
        assert version is not None

    def test_min_version_matches_pyproject(self) -> None:
        """MIN_SDK_VERSION should match pyproject.toml requirement."""
        from apps.api.main import MIN_SDK_VERSION

        # MIN_SDK_VERSION should be 0.1.19 per pyproject.toml
        assert MIN_SDK_VERSION == "0.1.19"
