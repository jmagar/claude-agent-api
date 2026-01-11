"""Helpers for configuring E2E HTTP clients."""

from collections.abc import Mapping

E2E_BASE_URL_ENV = "E2E_BASE_URL"
E2E_API_KEY_ENV = "E2E_API_KEY"
E2E_TIMEOUT_ENV = "E2E_TIMEOUT_SECONDS"


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


def get_e2e_api_key(env: Mapping[str, str] | None = None) -> str | None:
    """Return the configured E2E API key, if any."""
    environment = env or {}
    raw_value = environment.get(E2E_API_KEY_ENV, "")
    api_key = raw_value.strip()
    return api_key or None


def get_e2e_timeout_seconds(env: Mapping[str, str] | None = None) -> float:
    """Return the configured E2E timeout in seconds."""
    environment = env or {}
    raw_value = environment.get(E2E_TIMEOUT_ENV, "")
    if not raw_value:
        return 30.0
    try:
        parsed = float(raw_value.strip())
    except ValueError:
        return 30.0
    return parsed if parsed > 0 else 30.0
