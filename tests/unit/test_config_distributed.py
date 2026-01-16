"""Unit tests for distributed session configuration."""

from pathlib import Path

import pytest
from pydantic import SecretStr


@pytest.mark.unit
def test_env_example_has_distributed_session_settings():
    """Test that .env.example documents all distributed session settings."""
    env_example = Path(".env.example")

    assert env_example.exists(), ".env.example should exist"

    content = env_example.read_text()

    # Verify required settings are documented
    assert "REDIS_URL" in content, ".env.example should have REDIS_URL"
    assert "REDIS_SESSION_TTL" in content, ".env.example should have REDIS_SESSION_TTL"


@pytest.mark.unit
def test_settings_loads_distributed_session_config():
    """Test that Settings can load distributed session configuration."""
    from apps.api.config import Settings

    # Create settings with distributed session config
    settings = Settings(
        redis_url="redis://localhost:53380/0",
        database_url="postgresql+asyncpg://localhost:53432/test",
        api_key=SecretStr("test-key"),
    )

    assert settings.redis_session_ttl > 0  # Has default
