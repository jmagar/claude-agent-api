"""FastAPI dependencies for dependency injection."""

import secrets
from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apps.api.adapters.cache import RedisCache
from apps.api.adapters.memory import Mem0MemoryAdapter
from apps.api.adapters.session_repo import SessionRepository
from apps.api.config import Settings, get_settings
from apps.api.exceptions import AuthenticationError, ServiceUnavailableError
from apps.api.protocols import AgentConfigProtocol, ProjectProtocol
from apps.api.services.agent import AgentService
from apps.api.services.checkpoint import CheckpointService
from apps.api.services.mcp_config_injector import McpConfigInjector
from apps.api.services.mcp_config_loader import McpConfigLoader
from apps.api.services.mcp_config_validator import ConfigValidator
from apps.api.services.mcp_server_configs import McpServerConfigService
from apps.api.services.memory import MemoryService
from apps.api.services.query_enrichment import QueryEnrichmentService
from apps.api.services.session import SessionService
from apps.api.services.shutdown import ShutdownManager, get_shutdown_manager
from apps.api.services.skills import SkillsService

# Global instances (initialized in lifespan)
_async_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None
_redis_cache: RedisCache | None = None
_agent_service: AgentService | None = None  # Singleton for tests, None for per-request
_memory_service: MemoryService | None = None  # Singleton for tests, None for cached


async def init_db(settings: Settings) -> async_sessionmaker[AsyncSession]:
    """Initialize database engine and session maker.

    Args:
        settings: Application settings.

    Returns:
        Async session maker.
    """
    global _async_engine, _async_session_maker

    _async_engine = create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        echo=settings.debug,
    )
    _async_session_maker = async_sessionmaker(
        bind=_async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return _async_session_maker


async def close_db() -> None:
    """Close database connections."""
    global _async_engine, _async_session_maker
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
        _async_session_maker = None


async def init_cache(settings: Settings) -> RedisCache:
    """Initialize Redis cache with health check and retry.

    Args:
        settings: Application settings.

    Returns:
        Redis cache instance.

    Raises:
        ServiceUnavailableError: If Redis is not reachable after retries.
    """
    import asyncio

    import structlog

    from apps.api.adapters.cache import RedisCache

    logger = structlog.get_logger(__name__)
    global _redis_cache

    _redis_cache = await RedisCache.create(settings.redis_url)

    # Health check with retry logic
    max_attempts = 10
    backoff_base_ms = 100
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            await _redis_cache.ping()
            logger.info(
                "redis_health_check_passed",
                attempt=attempt,
                max_attempts=max_attempts,
            )
            return _redis_cache
        except Exception as exc:
            last_error = exc
            if attempt < max_attempts:
                backoff_ms = backoff_base_ms * (2 ** (attempt - 1))
                backoff_s = backoff_ms / 1000
                logger.warning(
                    "redis_health_check_failed_retrying",
                    attempt=attempt,
                    max_attempts=max_attempts,
                    backoff_seconds=backoff_s,
                    error=str(exc),
                )
                await asyncio.sleep(backoff_s)
            else:
                logger.error(
                    "redis_health_check_failed_permanently",
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=str(exc),
                )

    # All retries exhausted
    raise ServiceUnavailableError(
        message=f"Redis health check failed after {max_attempts} attempts: {last_error}",
        retry_after=10,
    )


async def close_cache() -> None:
    """Close cache connections."""
    global _redis_cache
    if _redis_cache:
        await _redis_cache.close()
        _redis_cache = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.

    Yields:
        Async database session.

    Raises:
        RuntimeError: If database not initialized.
    """
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized")

    async with _async_session_maker() as session:
        yield session


async def get_cache() -> RedisCache:
    """Get Redis cache instance.

    Returns:
        Redis cache instance.

    Raises:
        RuntimeError: If cache not initialized.
    """
    if _redis_cache is None:
        raise RuntimeError("Cache not initialized")
    return _redis_cache


async def get_session_repo(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionRepository:
    """Get session repository.

    Args:
        db: Database session.

    Returns:
        Session repository instance.
    """
    return SessionRepository(db)


def verify_api_key(
    _request: Request,
    x_api_key: Annotated[str | None, Header()] = None,
) -> str:
    """Verify API key from header or request state.

    Args:
        request: FastAPI request.
        x_api_key: API key from header.

    Returns:
        Verified API key.

    Raises:
        AuthenticationError: If API key is invalid.
    """
    settings = get_settings()

    # Check request.state first (set by middleware)
    if hasattr(_request, "state") and hasattr(_request.state, "api_key"):
        api_key_from_state: str = _request.state.api_key
        return api_key_from_state

    # Then check header
    if not x_api_key:
        raise AuthenticationError("Missing API key")

    if not secrets.compare_digest(x_api_key, settings.api_key.get_secret_value()):
        raise AuthenticationError("Invalid API key")

    return x_api_key


async def get_checkpoint_service(
    cache: Annotated[RedisCache, Depends(get_cache)],
) -> CheckpointService:
    """Get checkpoint service instance with injected cache.

    Args:
        cache: Redis cache from dependency injection.

    Returns:
        CheckpointService instance.
    """
    return CheckpointService(cache=cache)


async def get_agent_service(
    cache: Annotated[RedisCache, Depends(get_cache)],
    checkpoint_service: Annotated[CheckpointService, Depends(get_checkpoint_service)],
) -> AgentService:
    """Get agent service instance.

    Creates a new instance per request to avoid sharing mutable
    request-scoped state (_active_sessions) across concurrent requests.

    In tests, if a global singleton is set via set_agent_service_singleton(),
    that instance is returned instead to allow test fixtures to share state.

    Args:
        cache: Redis cache from dependency injection.
        checkpoint_service: Checkpoint service from dependency injection.

    Returns:
        AgentService instance with cache, config injector, and memory service configured.
    """
    from apps.api.services.agent.config import AgentServiceConfig
    from apps.api.services.webhook import WebhookService

    # Use singleton if set (for tests)
    if _agent_service is not None:
        return _agent_service

    # Create MCP config injector
    loader = get_mcp_config_loader()
    config_service = McpServerConfigService(cache=cache)
    validator = ConfigValidator()
    config_injector = McpConfigInjector(
        config_loader=loader,
        config_service=config_service,
        validator=validator,
    )

    # Get memory service
    memory_service = get_memory_service()

    # Build config object
    config = AgentServiceConfig(
        webhook_service=WebhookService(),
        checkpoint_service=checkpoint_service,
        cache=cache,
        mcp_config_injector=config_injector,
        memory_service=memory_service,
    )

    # Otherwise create new instance per request with config
    return AgentService(config=config)


def set_agent_service_singleton(service: AgentService | None) -> None:
    """Set a global agent service singleton for tests.

    Args:
        service: AgentService instance to use as singleton, or None to disable.
    """
    global _agent_service
    _agent_service = service


async def get_session_service(
    cache: Annotated[RedisCache, Depends(get_cache)],
    db_repo: Annotated[SessionRepository, Depends(get_session_repo)],
) -> SessionService:
    """Get session service instance with injected cache and DB repository.

    Args:
        cache: Redis cache from dependency injection.
        db_repo: Database repository for persistent storage.

    Returns:
        SessionService instance.
    """
    return SessionService(cache=cache, db_repo=db_repo)


def check_shutdown_state() -> ShutdownManager:
    """Check if service is accepting new requests (T131).

    Returns:
        ShutdownManager instance.

    Raises:
        ServiceUnavailableError: If shutdown is in progress.
    """
    manager = get_shutdown_manager()
    if manager.is_shutting_down:
        raise ServiceUnavailableError(
            message="Service is shutting down, not accepting new requests",
            retry_after=30,
        )
    return manager


def get_skills_service() -> SkillsService:
    """Get skills service instance.

    Returns:
        SkillsService instance configured with project path.
    """
    from pathlib import Path

    # Use current working directory as project root
    project_path = Path.cwd()
    return SkillsService(project_path=project_path)


def get_query_enrichment_service() -> "QueryEnrichmentService":
    """Get query enrichment service instance.

    Returns:
        QueryEnrichmentService instance configured with project path.
    """
    from pathlib import Path

    # Use current working directory as project root
    project_path = Path.cwd()
    return QueryEnrichmentService(project_path=project_path)


def get_mcp_config_loader() -> McpConfigLoader:
    """Get MCP config loader instance.

    Returns:
        McpConfigLoader instance configured with project path.
    """
    from pathlib import Path

    # Use current working directory as project root
    project_path = Path.cwd()
    return McpConfigLoader(project_path=project_path)


async def get_mcp_config_injector(
    loader: Annotated[McpConfigLoader, Depends(get_mcp_config_loader)],
    cache: Annotated[RedisCache, Depends(get_cache)],
) -> McpConfigInjector:
    """Get MCP config injector instance.

    Args:
        loader: MCP config loader from dependency injection.
        cache: Redis cache from dependency injection.

    Returns:
        McpConfigInjector instance with loader, config service, and validator.
    """
    config_service = McpServerConfigService(cache=cache)
    validator = ConfigValidator()
    return McpConfigInjector(
        config_loader=loader,
        config_service=config_service,
        validator=validator,
    )


@lru_cache
def get_memory_service() -> MemoryService:
    """Get cached memory service instance.

    In tests, if a global singleton is set, that instance is returned instead
    to allow test fixtures to inject mocks.

    Note: The Memory client is initialized once and reused (singleton).
    This is intentional - Mem0 Memory instances are stateless and can be
    safely shared across requests. The lru_cache ensures only one instance
    is created per process.

    Returns:
        MemoryService instance with Mem0 adapter configured.
    """
    # Use singleton if set (for tests)
    if _memory_service is not None:
        return _memory_service

    settings = get_settings()
    adapter = Mem0MemoryAdapter(settings)
    return MemoryService(adapter)


# --- CRUD Service Providers (Phase 2: DI Refactor) ---


async def get_agent_config_service(
    cache: Annotated[RedisCache, Depends(get_cache)],
) -> "AgentConfigProtocol":
    """Get agent CRUD service (for agents.py route).

    Note: Different from AgentService in services/agent/service.py (orchestration).
    This is the CRUD service from services/agents.py.

    Args:
        cache: Redis cache from dependency injection.

    Returns:
        AgentService instance for agent CRUD operations.
    """
    from typing import cast

    from apps.api.services.agents import AgentService as AgentCrudService

    return cast("AgentConfigProtocol", AgentCrudService(cache=cache))


async def get_project_service(
    cache: Annotated[RedisCache, Depends(get_cache)],
) -> ProjectProtocol:
    """Get project CRUD service.

    Args:
        cache: Redis cache from dependency injection.

    Returns:
        ProjectService instance.
    """
    from typing import cast

    from apps.api.services.projects import ProjectService

    return cast("ProjectProtocol", ProjectService(cache=cache))


async def get_tool_preset_service(
    cache: Annotated[RedisCache, Depends(get_cache)],
) -> "ToolPresetService":
    """Get tool preset CRUD service.

    Args:
        cache: Redis cache from dependency injection.

    Returns:
        ToolPresetService instance.
    """
    from apps.api.services.tool_presets import ToolPresetService

    return ToolPresetService(cache=cache)


async def get_slash_command_service(
    cache: Annotated[RedisCache, Depends(get_cache)],
) -> "SlashCommandService":
    """Get slash command CRUD service.

    Args:
        cache: Redis cache from dependency injection.

    Returns:
        SlashCommandService instance.
    """
    from apps.api.services.slash_commands import SlashCommandService

    return SlashCommandService(cache=cache)


def get_mcp_discovery_service() -> "McpDiscoveryService":
    """Get MCP discovery service for filesystem operations.

    Returns:
        McpDiscoveryService instance configured with current working directory.
    """
    from pathlib import Path

    from apps.api.services.mcp_discovery import McpDiscoveryService

    return McpDiscoveryService(project_path=Path.cwd())


async def get_mcp_server_config_service_provider(
    cache: Annotated[RedisCache, Depends(get_cache)],
) -> McpServerConfigService:
    """Get MCP server config service.

    Note: This is a separate provider from the one used in get_mcp_config_injector.
    Routes that need direct access to MCP server configs should use this.

    Args:
        cache: Redis cache from dependency injection.

    Returns:
        McpServerConfigService instance.
    """
    return McpServerConfigService(cache=cache)


async def get_mcp_share_service(
    cache: Annotated[RedisCache, Depends(get_cache)],
) -> "McpShareService":
    """Get MCP share service for share token management.

    Args:
        cache: Redis cache from dependency injection.

    Returns:
        McpShareService instance.
    """
    from apps.api.services.mcp_share import McpShareService

    return McpShareService(cache=cache)


async def get_skills_crud_service(
    cache: Annotated[RedisCache, Depends(get_cache)],
) -> "SkillCrudService":
    """Get skills CRUD service for database operations.

    Args:
        cache: Redis cache from dependency injection.

    Returns:
        SkillCrudService instance.
    """
    from apps.api.services.skills_crud import SkillCrudService

    return SkillCrudService(cache=cache)


# Type aliases for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
Cache = Annotated[RedisCache, Depends(get_cache)]
SessionRepo = Annotated[SessionRepository, Depends(get_session_repo)]
ApiKey = Annotated[str, Depends(verify_api_key)]
AgentSvc = Annotated[AgentService, Depends(get_agent_service)]
SessionSvc = Annotated[SessionService, Depends(get_session_service)]
CheckpointSvc = Annotated[CheckpointService, Depends(get_checkpoint_service)]
SkillsSvc = Annotated[SkillsService, Depends(get_skills_service)]
ShutdownState = Annotated[ShutdownManager, Depends(check_shutdown_state)]
QueryEnrichment = Annotated[
    QueryEnrichmentService, Depends(get_query_enrichment_service)
]
McpConfigLdr = Annotated[McpConfigLoader, Depends(get_mcp_config_loader)]
McpConfigInj = Annotated[McpConfigInjector, Depends(get_mcp_config_injector)]
MemorySvc = Annotated[MemoryService, Depends(get_memory_service)]

# CRUD service type aliases (Phase 2: DI Refactor)
AgentConfigSvc = Annotated["AgentConfigProtocol", Depends(get_agent_config_service)]
ProjectSvc = Annotated[ProjectProtocol, Depends(get_project_service)]
ToolPresetSvc = Annotated["ToolPresetService", Depends(get_tool_preset_service)]
SlashCommandSvc = Annotated["SlashCommandService", Depends(get_slash_command_service)]
McpDiscoverySvc = Annotated["McpDiscoveryService", Depends(get_mcp_discovery_service)]
McpServerConfigSvc = Annotated[
    McpServerConfigService, Depends(get_mcp_server_config_service_provider)
]
McpShareSvc = Annotated["McpShareService", Depends(get_mcp_share_service)]
SkillCrudSvc = Annotated["SkillCrudService", Depends(get_skills_crud_service)]
