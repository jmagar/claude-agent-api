"""Helpers for configuring E2E HTTP clients."""

from collections.abc import Mapping

E2E_BASE_URL_ENV = "E2E_BASE_URL"


def get_e2e_base_url(env: Mapping[str, str] | None = None) -> str | None:
    """Return the configured E2E base URL, if any."""
    environment = env or {}
    raw_value = environment.get(E2E_BASE_URL_ENV, "")
    base_url = raw_value.strip()
    return base_url or None


def should_use_live_e2e_client(
    is_e2e: bool,
    env: Mapping[str, str] | None = None,
) -> bool:
    """Return True when E2E tests should use a live server."""
    return is_e2e and get_e2e_base_url(env) is not None
