"""FastAPI dependencies for dependency injection."""

import secrets
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apps.api.config import Settings, get_settings
from apps.api.exceptions import AuthenticationError, ServiceUnavailableError

if TYPE_CHECKING:
    from apps.api.protocols import (
        AgentConfigProtocol,
        Cache,
        ProjectProtocol,
        SessionRepositoryProtocol,
    )
    from apps.api.protocols import AgentService as AgentServiceProtocol
    from apps.api.services.agent import AgentService
    from apps.api.services.assistants import (
        AssistantService,
        MessageService,
        RunService,
        ThreadService,
    )
    from apps.api.services.checkpoint import CheckpointService
    from apps.api.services.health import CacheHealthService
    from apps.api.services.mcp_config_injector import McpConfigInjector
    from apps.api.services.mcp_config_loader import McpConfigLoader
    from apps.api.services.mcp_discovery import McpDiscoveryService
    from apps.api.services.mcp_server_configs import McpServerConfigService
    from apps.api.services.mcp_share import McpShareService
    from apps.api.services.memory import MemoryService
    from apps.api.services.query_enrichment import QueryEnrichmentService
    from apps.api.services.session import SessionService
    from apps.api.services.shutdown import ShutdownManager
    from apps.api.services.skills import SkillsService
    from apps.api.services.skills_crud import SkillCrudService
    from apps.api.services.slash_commands import SlashCommandService
    from apps.api.services.tool_presets import ToolPresetService


@dataclass
class AppState:
    """Application state for dependency injection (ARC-04).

    Stores all application-wide singletons on app.state instead of module-level
    globals. This enables proper cleanup and test isolation (M-01, ARC-05).

    Attributes:
        engine: SQLAlchemy async engine for database connections.
        session_maker: Factory for creating database sessions.
        cache: Redis cache instance.
        agent_service: Optional singleton for tests (None = per-request).
        memory_service: Optional singleton for tests (None = cached).
    """

    engine: AsyncEngine | None = None
    session_maker: async_sessionmaker[AsyncSession] | None = None
    cache: "Cache | None" = None
    agent_service: "AgentService | None" = None
    memory_service: "MemoryService | None" = field(default=None)


def get_app_state(request: Request) -> "AppState":
    """Get application state from request context.

    Args:
        request: FastAPI request object.

    Returns:
        AppState instance from app.state.

    Raises:
        RuntimeError: If app state not initialized.
    """
    if not hasattr(request.app.state, "app_state"):
        raise RuntimeError("App state not initialized")
    return request.app.state.app_state


async def init_db(
    state: "AppState",
    settings: Settings,
) -> async_sessionmaker[AsyncSession]:
    """Initialize database engine and session maker (M-01, ARC-04).

    Args:
        state: Application state to store engine and session maker.
        settings: Application settings.

    Returns:
        Async session maker.
    """
    state.engine = create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        echo=settings.debug,
    )
    state.session_maker = async_sessionmaker(
        bind=state.engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return state.session_maker


async def close_db(state: "AppState") -> None:
    """Close database connections.

    Args:
        state: Application state containing engine to dispose.
    """
    if state.engine is not None:
        await state.engine.dispose()
        state.engine = None
        state.session_maker = None


async def init_cache(state: "AppState", settings: Settings) -> "Cache":
    """Initialize Redis cache with health check and retry (M-01, ARC-04).

    Args:
        state: Application state to store cache instance.
        settings: Application settings.

    Returns:
        Redis cache instance.

    Raises:
        ServiceUnavailableError: If Redis is not reachable after retries.
    """
    import asyncio

    import structlog

    # Import concrete class for runtime instantiation
    from apps.api.adapters.cache import RedisCache as RedisCacheImpl

    logger = structlog.get_logger(__name__)

    state.cache = await RedisCacheImpl.create(settings.redis_url)

    # Health check with retry logic
    max_attempts = 10
    backoff_base_ms = 100
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            await state.cache.ping()
            logger.info(
                "redis_health_check_passed",
                attempt=attempt,
                max_attempts=max_attempts,
            )
            return state.cache
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


async def close_cache(state: "AppState") -> None:
    """Close cache connections.

    Args:
        state: Application state containing cache to close.
    """
    if state.cache:
        await state.cache.close()
        state.cache = None


async def get_db(
    state: Annotated["AppState", Depends(get_app_state)],
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session from app state (ARC-04).

    Args:
        state: Application state containing session maker.

    Yields:
        Async database session.

    Raises:
        RuntimeError: If database not initialized.
    """
    if state.session_maker is None:
        raise RuntimeError("Database not initialized")

    async with state.session_maker() as session:
        yield session


async def get_cache(
    state: Annotated["AppState", Depends(get_app_state)],
) -> "Cache":
    """Get Redis cache instance from app state (ARC-04).

    Args:
        state: Application state containing cache.

    Returns:
        Redis cache instance.

    Raises:
        RuntimeError: If cache not initialized.
    """
    if state.cache is None:
        raise RuntimeError("Cache not initialized")
    return state.cache


async def get_session_repo(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> "SessionRepositoryProtocol":
    """Get session repository.

    Args:
        db: Database session.

    Returns:
        Session repository instance.
    """
    from apps.api.adapters.session_repo import SessionRepository

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
    cache: Annotated["Cache", Depends(get_cache)],
) -> "CheckpointService":
    """Get checkpoint service instance with injected cache.

    Args:
        cache: Redis cache from dependency injection.

    Returns:
        CheckpointService instance.
    """
    from apps.api.services.checkpoint import CheckpointService

    return CheckpointService(cache=cache)


async def get_agent_service(
    state: Annotated["AppState", Depends(get_app_state)],
    cache: Annotated["Cache", Depends(get_cache)],
    checkpoint_service: Annotated["CheckpointService", Depends(get_checkpoint_service)],
) -> "AgentService":
    """Get agent service instance from app state (ARC-04, ARC-05).

    Creates a new instance per request to avoid sharing mutable
    request-scoped state (_active_sessions) across concurrent requests.

    In tests, if a singleton is set on app.state, that instance is returned
    instead to allow test fixtures to share state (M-01).

    Args:
        state: Application state containing optional singleton.
        cache: Redis cache from dependency injection.
        checkpoint_service: Checkpoint service from dependency injection.

    Returns:
        AgentService instance with cache, config injector, and memory service configured.
    """
    from apps.api.services.agent import AgentService
    from apps.api.services.agent.config import AgentServiceConfig
    from apps.api.services.mcp_config_injector import McpConfigInjector
    from apps.api.services.mcp_config_validator import ConfigValidator
    from apps.api.services.webhook import WebhookService

    # Use singleton if set (for tests)
    if state.agent_service is not None:
        return state.agent_service

    # Create MCP config injector
    loader = get_mcp_config_loader()
    config_service = await get_mcp_server_config_service_provider(cache)
    validator = ConfigValidator()
    config_injector = McpConfigInjector(
        config_loader=loader,
        config_service=config_service,
        validator=validator,
    )

    # Get memory service
    memory_service = await get_memory_service(state=state)

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


async def get_session_service(
    cache: Annotated["Cache", Depends(get_cache)],
    db_repo: Annotated["SessionRepositoryProtocol", Depends(get_session_repo)],
) -> "SessionService":
    """Get session service instance with injected cache and DB repository.

    Args:
        cache: Redis cache from dependency injection.
        db_repo: Database repository for persistent storage.

    Returns:
        SessionService instance.
    """
    from apps.api.services.session import SessionService

    return SessionService(cache=cache, db_repo=db_repo)


def check_shutdown_state() -> "ShutdownManager":
    """Check if service is accepting new requests (T131).

    Returns:
        ShutdownManager instance.

    Raises:
        ServiceUnavailableError: If shutdown is in progress.
    """
    from apps.api.services.shutdown import get_shutdown_manager

    manager = get_shutdown_manager()
    if manager.is_shutting_down:
        raise ServiceUnavailableError(
            message="Service is shutting down, not accepting new requests",
            retry_after=30,
        )
    return manager


def get_skills_service() -> "SkillsService":
    """Get skills service instance.

    Returns:
        SkillsService instance configured with project path.
    """
    from pathlib import Path

    from apps.api.services.skills import SkillsService

    # Use current working directory as project root
    project_path = Path.cwd()
    return SkillsService(project_path=project_path)


def get_query_enrichment_service() -> "QueryEnrichmentService":
    """Get query enrichment service instance.

    Returns:
        QueryEnrichmentService instance configured with project path.
    """
    from pathlib import Path

    from apps.api.services.query_enrichment import QueryEnrichmentService

    # Use current working directory as project root
    project_path = Path.cwd()
    return QueryEnrichmentService(project_path=project_path)


def get_mcp_config_loader() -> "McpConfigLoader":
    """Get MCP config loader instance.

    Returns:
        McpConfigLoader instance configured with project path.
    """
    from pathlib import Path

    from apps.api.services.mcp_config_loader import McpConfigLoader

    # Use current working directory as project root
    project_path = Path.cwd()
    return McpConfigLoader(project_path=project_path)


async def get_mcp_server_config_service_provider(
    cache: Annotated["Cache", Depends(get_cache)],
) -> "McpServerConfigService":
    """Get MCP server config service.

    Note: This is a separate provider from the one used in get_mcp_config_injector.
    Routes that need direct access to MCP server configs should use this.

    Args:
        cache: Redis cache from dependency injection.

    Returns:
        McpServerConfigService instance.
    """
    from apps.api.services.mcp_server_configs import McpServerConfigService

    return McpServerConfigService(cache=cache)


async def get_mcp_config_injector(
    loader: Annotated["McpConfigLoader", Depends(get_mcp_config_loader)],
    config_service: Annotated[
        "McpServerConfigService", Depends(get_mcp_server_config_service_provider)
    ],
) -> "McpConfigInjector":
    """Get MCP config injector instance.

    Args:
        loader: MCP config loader from dependency injection.
        config_service: MCP server config service from dependency injection.

    Returns:
        McpConfigInjector instance with loader, config service, and validator.
    """
    from apps.api.services.mcp_config_injector import McpConfigInjector
    from apps.api.services.mcp_config_validator import ConfigValidator

    validator = ConfigValidator()
    return McpConfigInjector(
        config_loader=loader,
        config_service=config_service,
        validator=validator,
    )


async def get_memory_service(
    state: Annotated["AppState", Depends(get_app_state)],
) -> "MemoryService":
    """Get memory service instance from app state (M-02, ARC-05).

    In tests, if a singleton is set on app.state, that instance is returned
    instead to allow test fixtures to inject mocks.

    Note: The Memory client is initialized once and cached on app.state.
    This is intentional - Mem0 Memory instances are stateless and can be
    safely shared across requests. Caching on state avoids repeated initialization.

    Args:
        state: Application state containing optional singleton or cached instance.

    Returns:
        MemoryService instance with Mem0 adapter configured.
    """
    from apps.api.adapters.memory import Mem0MemoryAdapter
    from apps.api.services.memory import MemoryService

    # Use singleton if set (for tests)
    if state.memory_service is not None:
        return state.memory_service

    # Create and cache on first use
    settings = get_settings()
    adapter = Mem0MemoryAdapter(settings)
    memory_service = MemoryService(adapter)

    # Cache on state for subsequent requests
    state.memory_service = memory_service
    return memory_service


# --- CRUD Service Providers (Phase 2: DI Refactor) ---


async def get_agent_config_service(
    cache: Annotated["Cache", Depends(get_cache)],
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
    cache: Annotated["Cache", Depends(get_cache)],
) -> "ProjectProtocol":
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
    cache: Annotated["Cache", Depends(get_cache)],
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
    cache: Annotated["Cache", Depends(get_cache)],
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


async def get_mcp_share_service(
    cache: Annotated["Cache", Depends(get_cache)],
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
    cache: Annotated["Cache", Depends(get_cache)],
) -> "SkillCrudService":
    """Get skills CRUD service for database operations.

    Args:
        cache: Redis cache from dependency injection.

    Returns:
        SkillCrudService instance.
    """
    from apps.api.services.skills_crud import SkillCrudService

    return SkillCrudService(cache=cache)


async def get_openai_assistant_service(
    cache: Annotated["Cache", Depends(get_cache)],
) -> "AssistantService":
    """Get OpenAI assistant CRUD service."""
    from apps.api.services.assistants import AssistantService

    return AssistantService(cache=cache)


async def get_openai_thread_service(
    cache: Annotated["Cache", Depends(get_cache)],
    session_service: Annotated["SessionService", Depends(get_session_service)],
) -> "ThreadService":
    """Get OpenAI thread service."""
    from apps.api.services.assistants import ThreadService

    return ThreadService(session_service=session_service, cache=cache)


async def get_openai_message_service(
    cache: Annotated["Cache", Depends(get_cache)],
) -> "MessageService":
    """Get OpenAI message service."""
    from apps.api.services.assistants import MessageService

    return MessageService(cache=cache)


async def get_openai_run_service(
    cache: Annotated["Cache", Depends(get_cache)],
) -> "RunService":
    """Get OpenAI run service."""
    from apps.api.services.assistants import RunService

    return RunService(cache=cache)


async def get_cache_health_service(
    cache: Annotated["Cache", Depends(get_cache)],
) -> "CacheHealthService":
    """Get cache health service wrapper."""
    from apps.api.services.health import CacheHealthService

    return CacheHealthService(cache=cache)


# Type aliases for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
CacheDep = Annotated["Cache", Depends(get_cache)]
SessionRepo = Annotated["SessionRepositoryProtocol", Depends(get_session_repo)]
ApiKey = Annotated[str, Depends(verify_api_key)]
AgentSvc = Annotated["AgentServiceProtocol", Depends(get_agent_service)]
SessionSvc = Annotated["SessionService", Depends(get_session_service)]
CheckpointSvc = Annotated["CheckpointService", Depends(get_checkpoint_service)]
SkillsSvc = Annotated["SkillsService", Depends(get_skills_service)]
ShutdownState = Annotated["ShutdownManager", Depends(check_shutdown_state)]
QueryEnrichment = Annotated[
    "QueryEnrichmentService", Depends(get_query_enrichment_service)
]
McpConfigLdr = Annotated["McpConfigLoader", Depends(get_mcp_config_loader)]
McpConfigInj = Annotated["McpConfigInjector", Depends(get_mcp_config_injector)]
MemorySvc = Annotated["MemoryService", Depends(get_memory_service)]

# CRUD service type aliases (Phase 2: DI Refactor)
AgentConfigSvc = Annotated["AgentConfigProtocol", Depends(get_agent_config_service)]
ProjectSvc = Annotated["ProjectProtocol", Depends(get_project_service)]
ToolPresetSvc = Annotated["ToolPresetService", Depends(get_tool_preset_service)]
SlashCommandSvc = Annotated["SlashCommandService", Depends(get_slash_command_service)]
McpDiscoverySvc = Annotated["McpDiscoveryService", Depends(get_mcp_discovery_service)]
McpServerConfigSvc = Annotated[
    "McpServerConfigService", Depends(get_mcp_server_config_service_provider)
]
McpShareSvc = Annotated["McpShareService", Depends(get_mcp_share_service)]
SkillCrudSvc = Annotated["SkillCrudService", Depends(get_skills_crud_service)]
OpenAIAssistantSvc = Annotated[
    "AssistantService", Depends(get_openai_assistant_service)
]
OpenAIThreadSvc = Annotated["ThreadService", Depends(get_openai_thread_service)]
OpenAIMessageSvc = Annotated["MessageService", Depends(get_openai_message_service)]
OpenAIRunSvc = Annotated["RunService", Depends(get_openai_run_service)]
CacheHealthSvc = Annotated["CacheHealthService", Depends(get_cache_health_service)]


# --- Test Isolation (M-13) ---


def reset_dependencies(state: "AppState") -> None:
    """Reset dependency singletons for test isolation (M-13).

    Clears cached services on app.state to ensure fresh instances
    between test cases. Use this instead of direct state manipulation.

    Args:
        state: Application state to reset.
    """
    state.agent_service = None
    state.memory_service = None
