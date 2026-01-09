"""Unit tests for configuration module."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from apps.api.config import Settings, get_settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_values(self) -> None:
        """Test that defaults are applied when env vars not set."""
        with patch.dict(
            os.environ,
            {
                "API_KEY": "test-key",
                "ANTHROPIC_API_KEY": "test-anthropic-key",
                "CORS_ORIGINS": '["http://localhost:3000"]',
            },
            clear=True,
        ):
            # Disable .env file loading to test pure defaults
            settings = Settings(_env_file=None)

            assert settings.api_host == "0.0.0.0"
            assert settings.api_port == 54000
            assert settings.debug is False
            assert settings.log_level == "INFO"
            assert settings.log_json is True
            assert settings.db_pool_size == 10
            assert settings.db_max_overflow == 20
            assert settings.redis_session_ttl == 3600
            assert settings.rate_limit_requests == 100
            assert settings.rate_limit_burst == 20
            assert settings.request_timeout == 300
            assert settings.max_prompt_length == 100000
            assert settings.redis_max_connections == 50
            assert settings.redis_socket_connect_timeout == 5
            assert settings.redis_socket_timeout == 5

    def test_required_fields(self) -> None:
        """Test that required fields raise error when missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                # Disable .env file loading to test pure defaults
                Settings(_env_file=None)

            errors = exc_info.value.errors()
            error_fields = {e["loc"][0] for e in errors}
            assert "api_key" in error_fields
            # anthropic_api_key is optional (for Claude Max subscription users)
            assert "anthropic_api_key" not in error_fields

    def test_port_validation(self) -> None:
        """Test port number validation."""
        with patch.dict(
            os.environ,
            {
                "API_KEY": "test-key",
                "ANTHROPIC_API_KEY": "test-anthropic-key",
                "API_PORT": "0",
                "CORS_ORIGINS": '["http://localhost:3000"]',
            },
            clear=True,
        ):
            with pytest.raises(ValidationError) as exc_info:
                Settings()

            errors = exc_info.value.errors()
            assert any(e["loc"][0] == "api_port" for e in errors)

    def test_port_too_high(self) -> None:
        """Test port number upper bound validation."""
        with patch.dict(
            os.environ,
            {
                "API_KEY": "test-key",
                "ANTHROPIC_API_KEY": "test-anthropic-key",
                "API_PORT": "70000",
                "CORS_ORIGINS": '["http://localhost:3000"]',
            },
            clear=True,
        ):
            with pytest.raises(ValidationError) as exc_info:
                Settings()

            errors = exc_info.value.errors()
            assert any(e["loc"][0] == "api_port" for e in errors)

    def test_log_level_validation(self) -> None:
        """Test log level enum validation."""
        with patch.dict(
            os.environ,
            {
                "API_KEY": "test-key",
                "ANTHROPIC_API_KEY": "test-anthropic-key",
                "LOG_LEVEL": "INVALID",
                "CORS_ORIGINS": '["http://localhost:3000"]',
            },
            clear=True,
        ):
            with pytest.raises(ValidationError) as exc_info:
                Settings()

            errors = exc_info.value.errors()
            assert any(e["loc"][0] == "log_level" for e in errors)

    def test_valid_log_levels(self) -> None:
        """Test all valid log levels are accepted."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            with patch.dict(
                os.environ,
                {
                    "API_KEY": "test-key",
                    "ANTHROPIC_API_KEY": "test-anthropic-key",
                    "LOG_LEVEL": level,
                    "CORS_ORIGINS": '["http://localhost:3000"]',
                },
                clear=True,
            ):
                settings = Settings()
                assert settings.log_level == level

    def test_secret_str_values(self) -> None:
        """Test that secret values are properly wrapped."""
        with patch.dict(
            os.environ,
            {
                "API_KEY": "my-api-key",
                "ANTHROPIC_API_KEY": "my-anthropic-key",
                "CORS_ORIGINS": '["http://localhost:3000"]',
            },
            clear=True,
        ):
            settings = Settings()

            # Secrets should not expose value in string representation
            assert "my-api-key" not in str(settings.api_key)
            assert "my-anthropic-key" not in str(settings.anthropic_api_key)

            # But should be retrievable via get_secret_value()
            assert settings.api_key.get_secret_value() == "my-api-key"
            assert settings.anthropic_api_key.get_secret_value() == "my-anthropic-key"

    def test_database_url_default(self) -> None:
        """Test default database URL."""
        with patch.dict(
            os.environ,
            {
                "API_KEY": "test-key",
                "ANTHROPIC_API_KEY": "test-anthropic-key",
                "CORS_ORIGINS": '["http://localhost:3000"]',
            },
            clear=True,
        ):
            # Disable .env file loading to test pure defaults
            settings = Settings(_env_file=None)
            assert "postgresql+asyncpg://" in settings.database_url
            assert "53432" in settings.database_url

    def test_redis_url_default(self) -> None:
        """Test default Redis URL."""
        with patch.dict(
            os.environ,
            {
                "API_KEY": "test-key",
                "ANTHROPIC_API_KEY": "test-anthropic-key",
                "CORS_ORIGINS": '["http://localhost:3000"]',
            },
            clear=True,
        ):
            # Disable .env file loading to test pure defaults
            settings = Settings(_env_file=None)
            assert settings.redis_url.startswith("redis://")
            assert "53380" in settings.redis_url

    def test_redis_pubsub_channels_configured(self) -> None:
        """Test that Redis pub/sub channel names are configurable."""
        with patch.dict(
            os.environ,
            {
                "API_KEY": "test-key",
                "ANTHROPIC_API_KEY": "test-anthropic-key",
                "CORS_ORIGINS": '["http://localhost:3000"]',
                "REDIS_URL": "redis://localhost:53380/0",
                "REDIS_INTERRUPT_CHANNEL": "custom:interrupts",
            },
            clear=True,
        ):
            settings = Settings(_env_file=None)
            assert settings.redis_interrupt_channel == "custom:interrupts"

    def test_redis_pubsub_channel_defaults(self) -> None:
        """Test default Redis pub/sub channel names."""
        with patch.dict(
            os.environ,
            {
                "API_KEY": "test-key",
                "ANTHROPIC_API_KEY": "test-anthropic-key",
                "CORS_ORIGINS": '["http://localhost:3000"]',
                "REDIS_URL": "redis://localhost:53380/0",
            },
            clear=True,
        ):
            settings = Settings(_env_file=None)
            assert settings.redis_interrupt_channel == "agent:interrupts"


class TestGetSettings:
    """Tests for get_settings function."""

    def test_caching(self) -> None:
        """Test that settings are cached."""
        # Clear the cache first
        get_settings.cache_clear()

        with patch.dict(
            os.environ,
            {
                "API_KEY": "test-key",
                "ANTHROPIC_API_KEY": "test-anthropic-key",
                "CORS_ORIGINS": '["http://localhost:3000"]',
            },
            clear=True,
        ):
            settings1 = get_settings()
            settings2 = get_settings()

            # Should be the same instance
            assert settings1 is settings2
