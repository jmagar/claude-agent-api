"""FastAPI dependencies for dependency injection."""

import secrets
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apps.api.adapters.cache import RedisCache
from apps.api.adapters.session_repo import SessionRepository
from apps.api.config import Settings, get_settings
from apps.api.exceptions import AuthenticationError, ServiceUnavailableError
from apps.api.services.agent import AgentService
from apps.api.services.checkpoint import CheckpointService
from apps.api.services.query_enrichment import QueryEnrichmentService
from apps.api.services.session import SessionService
from apps.api.services.shutdown import ShutdownManager, get_shutdown_manager
from apps.api.services.skills import SkillsService

# Global instances (initialized in lifespan)
_async_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None
_redis_cache: RedisCache | None = None
_agent_service: AgentService | None = None  # Singleton for tests, None for per-request


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
    """Initialize Redis cache.

    Args:
        settings: Application settings.

    Returns:
        Redis cache instance.
    """
    global _redis_cache
    _redis_cache = await RedisCache.create(settings.redis_url)
    return _redis_cache


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
        return _request.state.api_key

    # Then check header
    if not x_api_key:
        raise AuthenticationError("Missing API key")

    if not secrets.compare_digest(x_api_key, settings.api_key.get_secret_value()):
        raise AuthenticationError("Invalid API key")

    return x_api_key


def get_agent_service() -> AgentService:
    """Get agent service instance.

    Creates a new instance per request to avoid sharing mutable
    request-scoped state (_active_sessions) across concurrent requests.

    In tests, if a global singleton is set via set_agent_service_singleton(),
    that instance is returned instead to allow test fixtures to share state.

    Returns:
        AgentService instance with cache configured.
    """
    # Use singleton if set (for tests)
    if _agent_service is not None:
        return _agent_service
    # Otherwise create new instance per request with cache
    return AgentService(cache=_redis_cache)


def set_agent_service_singleton(service: AgentService | None) -> None:
    """Set a global agent service singleton for tests.

    Args:
        service: AgentService instance to use as singleton, or None to disable.
    """
    global _agent_service
    _agent_service = service


async def get_session_service(
    cache: Annotated[RedisCache, Depends(get_cache)],
    db_repo: Annotated[SessionRepository | None, Depends(lambda: None)] = None,
) -> SessionService:
    """Get session service instance with injected cache and optional DB repository.

    Args:
        cache: Redis cache from dependency injection.
        db_repo: Optional database repository for persistent storage.

    Returns:
        SessionService instance.
    """
    return SessionService(cache=cache, db_repo=db_repo)


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
