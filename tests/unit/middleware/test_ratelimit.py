"""Unit tests for Rate Limiting Middleware (Priority 5).

Tests client IP extraction, API key handling, and rate limit responses.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import Request
from slowapi.errors import RateLimitExceeded

from apps.api.middleware.ratelimit import (
    get_api_key,
    get_client_ip,
    get_query_rate_limit,
    rate_limit_handler,
)


@pytest.fixture
def mock_request() -> MagicMock:
    """Create mock FastAPI request.

    Returns:
        Mock Request object.
    """
    request = MagicMock(spec=Request)
    request.headers = {}
    request.client = MagicMock()
    request.client.host = "192.168.1.100"
    return request


@pytest.fixture
def mock_settings_trusted_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock settings with trusted proxy headers enabled.

    Args:
        monkeypatch: pytest monkeypatch fixture.
    """
    from apps.api.config import Settings

    def mock_get_settings() -> Settings:
        return Settings.model_construct(
            trust_proxy_headers=True,
            rate_limit_query_per_minute=10,
            rate_limit_session_per_minute=30,
            rate_limit_general_per_minute=100,
        )

    monkeypatch.setattr(
        "apps.api.middleware.ratelimit.get_settings", mock_get_settings
    )


@pytest.fixture
def mock_settings_no_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock settings with proxy headers disabled.

    Args:
        monkeypatch: pytest monkeypatch fixture.
    """
    from apps.api.config import Settings

    def mock_get_settings() -> Settings:
        return Settings.model_construct(
            trust_proxy_headers=False,
            rate_limit_query_per_minute=10,
            rate_limit_session_per_minute=30,
            rate_limit_general_per_minute=100,
        )

    monkeypatch.setattr(
        "apps.api.middleware.ratelimit.get_settings", mock_get_settings
    )


class TestClientIPExtraction:
    """Tests for client IP extraction."""

    def test_get_client_ip_from_direct_connection(
        self,
        mock_request: MagicMock,
        mock_settings_no_proxy: None,
    ) -> None:
        """Test IP extraction from direct connection.

        GREEN: This test verifies direct IP is used when proxy not trusted.
        """
        mock_request.headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}

        # Should ignore X-Forwarded-For and use client.host
        ip = get_client_ip(mock_request)

        assert ip == "192.168.1.100"

    def test_get_client_ip_with_trusted_proxy(
        self,
        mock_request: MagicMock,
        mock_settings_trusted_proxy: None,
    ) -> None:
        """Test X-Forwarded-For handling with trusted proxy.

        GREEN: This test verifies rightmost IP is used when proxy trusted.
        """
        mock_request.headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8, 9.10.11.12"}

        # Should use rightmost IP (from trusted proxy)
        ip = get_client_ip(mock_request)

        assert ip == "9.10.11.12"

    def test_get_client_ip_ignores_proxy_when_not_trusted(
        self,
        mock_request: MagicMock,
        mock_settings_no_proxy: None,
    ) -> None:
        """Test security check when proxy not trusted.

        GREEN: This test verifies X-Forwarded-For is ignored for security.
        """
        # Client could spoof this header
        mock_request.headers = {"X-Forwarded-For": "192.168.0.1"}

        # Should ignore header and use actual client IP
        ip = get_client_ip(mock_request)

        assert ip == "192.168.1.100"


class TestAPIKeyExtraction:
    """Tests for API key extraction."""

    def test_get_api_key_returns_key_when_present(
        self,
        mock_request: MagicMock,
        mock_settings_no_proxy: None,
    ) -> None:
        """Test API key extraction from header.

        GREEN: This test verifies API key is extracted correctly.
        """
        mock_request.headers = {"X-API-Key": "test-key-12345"}

        key = get_api_key(mock_request)

        assert key == "key:test-key-12345"

    def test_get_api_key_falls_back_to_ip(
        self,
        mock_request: MagicMock,
        mock_settings_no_proxy: None,
    ) -> None:
        """Test IP fallback when no API key present.

        GREEN: This test verifies fallback to IP-based rate limiting.
        """
        # No API key header
        key = get_api_key(mock_request)

        # Should fall back to IP
        assert key == "192.168.1.100"


class TestRateLimitHandler:
    """Tests for rate limit error handling."""

    @pytest.mark.anyio
    async def test_rate_limit_handler_returns_429(
        self,
        mock_request: MagicMock,
    ) -> None:
        """Test 429 response for rate limit exceeded.

        GREEN: This test verifies 429 status code is returned.
        """
        # Mock a RateLimitExceeded exception
        exc = MagicMock(spec=RateLimitExceeded)
        exc.detail = "10 per 1 minute"
        exc.retry_after = 30

        response = await rate_limit_handler(mock_request, exc)

        assert response.status_code == 429

    @pytest.mark.anyio
    async def test_rate_limit_handler_includes_retry_after(
        self,
        mock_request: MagicMock,
    ) -> None:
        """Test Retry-After header in response.

        GREEN: This test verifies Retry-After header is set correctly.
        """
        # Mock a RateLimitExceeded exception
        exc = MagicMock(spec=RateLimitExceeded)
        exc.detail = "10 per 1 minute"
        exc.retry_after = 45

        response = await rate_limit_handler(mock_request, exc)

        # Check headers
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "45"

        # Check JSON body
        import json

        body = json.loads(response.body)
        assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"


class TestRateLimitCalculation:
    """Tests for rate limit value calculation."""

    def test_get_query_rate_limit_uses_settings(
        self,
        mock_settings_no_proxy: None,
    ) -> None:
        """Test query rate limit from settings.

        GREEN: This test verifies settings integration for query limits.
        """
        limit = get_query_rate_limit()

        assert limit == "10/minute"
