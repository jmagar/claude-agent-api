"""Tests for E2E client helper functions."""

from tests.helpers.e2e_client import (
    get_e2e_base_url,
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
