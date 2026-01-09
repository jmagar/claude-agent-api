"""Unit tests for distributed session configuration."""

import pytest
from pathlib import Path


@pytest.mark.unit
def test_env_example_has_distributed_session_settings():
    """Test that .env.example documents all distributed session settings."""
    env_example = Path(".env.example")

    assert env_example.exists(), ".env.example should exist"

    content = env_example.read_text()

    # Verify required settings are documented
    assert "REDIS_URL" in content, ".env.example should have REDIS_URL"
    assert "REDIS_SESSION_TTL" in content, ".env.example should have REDIS_SESSION_TTL"
    assert "REDIS_INTERRUPT_CHANNEL" in content, ".env.example should have REDIS_INTERRUPT_CHANNEL"


@pytest.mark.unit
def test_settings_loads_distributed_session_config():
    """Test that Settings can load distributed session configuration."""
    from apps.api.config import Settings

    # Create settings with distributed session config
    settings = Settings(
        redis_url="redis://localhost:53380/0",
        redis_interrupt_channel="test:interrupts",
        database_url="postgresql+asyncpg://localhost:53432/test",
        api_key="test-key",
    )

    assert settings.redis_interrupt_channel == "test:interrupts"
    assert settings.redis_session_ttl > 0  # Has default
