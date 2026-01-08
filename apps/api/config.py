"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=54000, ge=1, le=65535, description="API port")
    api_key: SecretStr = Field(..., description="API key for client authentication")
    debug: bool = Field(default=False, description="Enable debug mode")
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins (use ['*'] for development only)",
    )

    # Anthropic API (optional when using Claude Max subscription)
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        description="Anthropic API key for Claude (optional with Claude Max)",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:53432/claude_agent",
        description="PostgreSQL connection string",
    )
    db_pool_size: int = Field(default=5, ge=1, le=20, description="Database pool size")
    db_max_overflow: int = Field(
        default=10, ge=0, le=50, description="Database max overflow"
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:53380/0",
        description="Redis connection string",
    )
    redis_session_ttl: int = Field(
        default=3600, ge=60, le=86400, description="Session cache TTL in seconds"
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Log level"
    )
    log_json: bool = Field(default=True, description="Use JSON log format")

    # File Checkpointing
    enable_file_checkpointing: bool = Field(
        default=False, description="Enable SDK file checkpointing"
    )

    # Proxy Settings
    trust_proxy_headers: bool = Field(
        default=False,
        description="Trust X-Forwarded-For header (only enable behind trusted proxy)",
    )

    # Rate Limiting (T124)
    rate_limit_requests: int = Field(
        default=100, ge=1, description="Max requests per minute"
    )
    rate_limit_burst: int = Field(default=20, ge=1, description="Burst limit")
    rate_limit_query_per_minute: int = Field(
        default=10, ge=1, description="Query endpoint rate limit per minute"
    )
    rate_limit_session_per_minute: int = Field(
        default=30, ge=1, description="Session endpoint rate limit per minute"
    )
    rate_limit_general_per_minute: int = Field(
        default=100, ge=1, description="General endpoint rate limit per minute"
    )

    # Request Settings
    request_timeout: int = Field(
        default=300, ge=10, le=600, description="Request timeout in seconds"
    )
    max_prompt_length: int = Field(
        default=100000, ge=1, le=500000, description="Max prompt length"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Cached Settings instance.
    """
    return Settings()
