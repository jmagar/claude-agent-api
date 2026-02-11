"""Health check endpoints."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from apps.api.dependencies import CacheHealthSvc, DbSession

router = APIRouter(tags=["Health"])


class DependencyStatus(BaseModel):
    """Status of a dependency."""

    status: Literal["ok", "error"]
    latency_ms: float | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["ok", "degraded", "unhealthy"]
    version: str
    dependencies: dict[str, DependencyStatus]


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: DbSession,
    cache_health: CacheHealthSvc,
) -> HealthResponse:
    """Check service health and dependencies.

    Returns:
        Health status of the service and its dependencies.
    """
    import time

    from apps.api import __version__

    dependencies: dict[str, DependencyStatus] = {}

    # Check PostgreSQL
    try:
        start = time.perf_counter()
        await db.execute(text("SELECT 1"))
        latency = (time.perf_counter() - start) * 1000
        dependencies["postgres"] = DependencyStatus(
            status="ok",
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        dependencies["postgres"] = DependencyStatus(
            status="error",
            error=str(e),
        )

    # Check Redis
    try:
        start = time.perf_counter()
        healthy = await cache_health.ping()
        latency = (time.perf_counter() - start) * 1000
        if healthy:
            dependencies["redis"] = DependencyStatus(
                status="ok",
                latency_ms=round(latency, 2),
            )
        else:
            dependencies["redis"] = DependencyStatus(
                status="error",
                error="Ping failed",
            )
    except Exception as e:
        dependencies["redis"] = DependencyStatus(
            status="error",
            error=str(e),
        )

    # Determine overall status
    all_ok = all(d.status == "ok" for d in dependencies.values())
    any_ok = any(d.status == "ok" for d in dependencies.values())

    if all_ok:
        status: Literal["ok", "degraded", "unhealthy"] = "ok"
    elif any_ok:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        version=__version__,
        dependencies=dependencies,
    )


@router.get("/")
async def root() -> dict[str, str]:
    """Root endpoint.

    Returns:
        Service name and version.
    """
    from apps.api import __version__

    return {
        "service": "claude-agent-api",
        "version": __version__,
    }
