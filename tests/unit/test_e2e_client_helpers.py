"""Tests for E2E client helper functions."""

from tests.helpers.e2e_client import (
    get_e2e_api_key,
    get_e2e_base_url,
    get_e2e_timeout_seconds,
    should_use_live_e2e_client,
)


def test_get_e2e_base_url_returns_none_when_unset() -> None:
    """Return None when E2E base URL is missing."""
    assert get_e2e_base_url({}) is None


def test_get_e2e_base_url_returns_value_when_set() -> None:
    """Return base URL when E2E base URL is set."""
    assert get_e2e_base_url({"E2E_BASE_URL": "http://localhost:54000"}) == (
        "http://localhost:54000"
    )


def test_get_e2e_base_url_strips_whitespace() -> None:
    """Strip whitespace from base URL value."""
    assert get_e2e_base_url({"E2E_BASE_URL": "  http://x  "}) == "http://x"


def test_get_e2e_api_key_returns_none_when_unset() -> None:
    """Return None when E2E API key is missing."""
    assert get_e2e_api_key({}) is None


def test_get_e2e_api_key_returns_value_when_set() -> None:
    """Return API key when E2E API key is set."""
    assert get_e2e_api_key({"E2E_API_KEY": "real-key"}) == "real-key"


def test_get_e2e_api_key_strips_whitespace() -> None:
    """Strip whitespace from API key value."""
    assert get_e2e_api_key({"E2E_API_KEY": "  real-key  "}) == "real-key"


def test_get_e2e_timeout_defaults_when_unset() -> None:
    """Return default timeout when unset."""
    assert get_e2e_timeout_seconds({}) == 30.0


def test_get_e2e_timeout_parses_int() -> None:
    """Parse integer timeout values."""
    assert get_e2e_timeout_seconds({"E2E_TIMEOUT_SECONDS": "45"}) == 45.0


def test_get_e2e_timeout_parses_float() -> None:
    """Parse float timeout values."""
    assert get_e2e_timeout_seconds({"E2E_TIMEOUT_SECONDS": "12.5"}) == 12.5


def test_get_e2e_timeout_strips_whitespace() -> None:
    """Strip whitespace from timeout values."""
    assert get_e2e_timeout_seconds({"E2E_TIMEOUT_SECONDS": "  15  "}) == 15.0


def test_get_e2e_timeout_falls_back_on_invalid() -> None:
    """Fallback to default timeout on invalid values."""
    assert get_e2e_timeout_seconds({"E2E_TIMEOUT_SECONDS": "nope"}) == 30.0


def test_get_e2e_timeout_falls_back_on_non_positive() -> None:
    """Fallback to default timeout on non-positive values."""
    assert get_e2e_timeout_seconds({"E2E_TIMEOUT_SECONDS": "0"}) == 30.0


def test_should_use_live_e2e_client_requires_e2e_marker() -> None:
    """Return False when not an E2E test."""
    assert (
        should_use_live_e2e_client(
            is_e2e=False,
            env={"E2E_BASE_URL": "http://localhost:54000"},
        )
        is False
    )


def test_should_use_live_e2e_client_requires_base_url() -> None:
    """Return False when E2E base URL is missing."""
    assert (
        should_use_live_e2e_client(
            is_e2e=True,
            env={},
        )
        is False
    )


def test_should_use_live_e2e_client_returns_true_when_configured() -> None:
    """Return True when E2E base URL is configured."""
    assert (
        should_use_live_e2e_client(
            is_e2e=True,
            env={"E2E_BASE_URL": "http://localhost:54000"},
        )
        is True
    )
