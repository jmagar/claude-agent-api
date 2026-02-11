"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
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
    api_host: str = Field(
        default="0.0.0.0",
        description="API host (0.0.0.0 binds to all interfaces - ensure firewall/proxy protection)",
    )
    api_port: int = Field(default=54000, ge=1, le=65535, description="API port")
    api_key: SecretStr = Field(..., description="API key for client authentication")
    debug: bool = Field(default=False, description="Enable debug mode")
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins (use ['*'] for development only)",
    )

    # Anthropic API (optional when using Claude Max subscription)
    # NOTE: If you are logged in with Claude Max subscription, this is NOT needed.
    # Only set this if you want to use an API key instead of your subscription.
    # Setting this environment variable will override your Claude Max subscription.
    # See CLAUDE.md for details.
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        description="Anthropic API key for Claude (optional with Claude Max)",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:54432/claude_agent",
        description="PostgreSQL connection string",
    )
    db_pool_size: int = Field(default=10, ge=5, le=50, description="Database pool size")
    db_max_overflow: int = Field(
        default=20, ge=10, le=100, description="Database max overflow"
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:54379/0",
        description="Redis connection string",
    )
    redis_session_ttl: int = Field(
        default=3600, ge=60, le=86400, description="Session cache TTL in seconds"
    )
    redis_interrupt_ttl: int = Field(
        default=300, ge=60, le=3600, description="Interrupt marker TTL in seconds"
    )
    mcp_share_ttl_seconds: int = Field(
        default=86400,
        ge=300,
        le=604800,
        description="MCP share token TTL in seconds",
    )
    redis_max_connections: int | None = Field(
        default=None,
        description="Redis max connections (defaults to max(db_pool_size + db_max_overflow, 50) if not set, must be 5-200 if explicitly set)",
    )
    redis_socket_connect_timeout: int = Field(
        default=5, ge=1, le=30, description="Redis socket connect timeout (seconds)"
    )
    redis_socket_timeout: int = Field(
        default=5, ge=1, le=30, description="Redis socket timeout (seconds)"
    )
    redis_retry_max_attempts: int = Field(
        default=3, ge=1, le=10, description="Redis max retry attempts"
    )
    redis_retry_backoff_base_ms: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Redis retry backoff base (milliseconds)",
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

    # Mem0 LLM Configuration
    llm_api_key: str = Field(default="", description="LLM API key for Mem0")
    llm_base_url: str = Field(
        default="https://cli-api.tootie.tv/v1", description="LLM base URL for Mem0"
    )
    llm_model: str = Field(
        default="gemini-3-flash-preview", description="LLM model for Mem0"
    )
    llm_user_agent: str = Field(
        default="claude-agent-api/mem0",
        description="User-Agent header for Mem0 LLM requests",
    )

    # Neo4j Configuration
    neo4j_url: str = Field(
        default="bolt://localhost:54687", description="Neo4j connection URL"
    )
    neo4j_username: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="neo4jpassword", description="Neo4j password")
    neo4j_database: str = Field(default="neo4j", description="Neo4j database name")

    # Qdrant Configuration
    qdrant_url: str = Field(
        default="http://localhost:53333", description="Qdrant connection URL"
    )

    # TEI Configuration
    tei_url: str = Field(
        default="http://localhost:52000",
        description="Text Embeddings Inference URL",
    )
    # SECURITY NOTE: This is a placeholder value, NOT a real credential.
    # Mem0's OpenAI embedder requires OPENAI_API_KEY to be set even when using
    # HuggingFace embedder with TEI (which doesn't require authentication).
    # The value "not-needed" satisfies Mem0's validation without exposing credentials.
    # See apps/api/main.py lifespan() for usage details.
    tei_api_key: str = Field(
        default="not-needed",
        description="TEI API key (placeholder - TEI doesn't require auth but Mem0's OpenAI client needs a value)",
    )

    # Mem0 Configuration
    mem0_collection_name: str = Field(
        default="mem0_memories", description="Mem0 vector collection name"
    )
    mem0_embedding_dims: int = Field(
        default=1024, ge=1, le=4096, description="Mem0 embedding dimensions"
    )
    mem0_agent_id: str = Field(default="main", description="Mem0 agent identifier")

    @model_validator(mode="after")
    def compute_redis_max_connections(self) -> "Settings":
        """Compute redis_max_connections if not explicitly set.

        Uses formula: max(db_pool_size + db_max_overflow, 50)
        This ensures Redis pool scales with database pool size.

        Returns:
            Self with computed redis_max_connections

        Raises:
            ValueError: If explicitly set value is outside valid range [5, 200]
        """
        if self.redis_max_connections is None:
            # Compute based on DB pool settings
            computed = max(self.db_pool_size + self.db_max_overflow, 50)
            # Clamp to valid range [5, 200]
            self.redis_max_connections = max(5, min(computed, 200))
        else:
            # Validate explicitly set value
            if not (5 <= self.redis_max_connections <= 200):
                raise ValueError(
                    f"redis_max_connections must be between 5 and 200, got {self.redis_max_connections}"
                )
        return self

    @model_validator(mode="after")
    def validate_cors_in_production(self) -> "Settings":
        """Validate CORS configuration in production.

        Prevents using wildcard (*) CORS origins when debug mode is disabled.

        Raises:
            ValueError: If wildcard CORS is used in production
        """
        if not self.debug and "*" in self.cors_origins:
            raise ValueError(
                "CORS wildcard (*) is not allowed in production. "
                "Set DEBUG=true for development or configure specific origins in CORS_ORIGINS."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Cached Settings instance.
    """
    return Settings()
