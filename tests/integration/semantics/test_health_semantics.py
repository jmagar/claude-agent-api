"""Semantic tests for Health Check endpoints.

Tests health check response structure, dependency status reporting,
latency measurements, and root endpoint version info.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# =============================================================================
# Health Check Endpoint: GET /health
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_health_check_returns_200(
    async_client: AsyncClient,
) -> None:
    """Health check endpoint returns 200 when service is running.

    Validates that the health endpoint is reachable and responds
    successfully without requiring authentication.
    """
    # ACT
    response = await async_client.get("/health")

    # ASSERT
    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.anyio
async def test_health_check_response_structure(
    async_client: AsyncClient,
) -> None:
    """Health check response contains status, version, and dependencies fields.

    Validates the top-level HealthResponse schema with all required
    fields present and correctly typed.
    """
    # ACT
    response = await async_client.get("/health")

    # ASSERT
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "version" in data
    assert "dependencies" in data

    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)
    assert isinstance(data["dependencies"], dict)


@pytest.mark.integration
@pytest.mark.anyio
async def test_health_check_status_is_valid_value(
    async_client: AsyncClient,
) -> None:
    """Health check status is one of the allowed literal values.

    The status field must be 'ok', 'degraded', or 'unhealthy' per
    the HealthResponse model definition.
    """
    # ACT
    response = await async_client.get("/health")

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"ok", "degraded", "unhealthy"}


@pytest.mark.integration
@pytest.mark.anyio
async def test_health_check_version_is_semver(
    async_client: AsyncClient,
) -> None:
    """Health check version string follows semantic versioning format.

    Validates that the version field looks like a semver string
    (e.g. '1.0.0', '0.2.1') rather than an empty or malformed value.
    """
    # ACT
    response = await async_client.get("/health")

    # ASSERT
    assert response.status_code == 200
    version = response.json()["version"]
    assert isinstance(version, str)
    assert len(version) > 0
    # Loose semver check: at least major.minor.patch digits
    assert re.match(r"^\d+\.\d+\.\d+", version)


@pytest.mark.integration
@pytest.mark.anyio
async def test_health_check_postgres_dependency(
    async_client: AsyncClient,
) -> None:
    """Health check reports PostgreSQL dependency status.

    Validates that the dependencies dict includes a 'postgres' entry
    with the required DependencyStatus fields.
    """
    # ACT
    response = await async_client.get("/health")

    # ASSERT
    assert response.status_code == 200
    deps = response.json()["dependencies"]
    assert "postgres" in deps

    pg = deps["postgres"]
    assert "status" in pg
    assert pg["status"] in {"ok", "error"}


@pytest.mark.integration
@pytest.mark.anyio
async def test_health_check_redis_dependency(
    async_client: AsyncClient,
) -> None:
    """Health check reports Redis dependency status.

    Validates that the dependencies dict includes a 'redis' entry
    with the required DependencyStatus fields.
    """
    # ACT
    response = await async_client.get("/health")

    # ASSERT
    assert response.status_code == 200
    deps = response.json()["dependencies"]
    assert "redis" in deps

    redis = deps["redis"]
    assert "status" in redis
    assert redis["status"] in {"ok", "error"}


@pytest.mark.integration
@pytest.mark.anyio
async def test_health_check_latency_present_when_ok(
    async_client: AsyncClient,
) -> None:
    """Healthy dependencies include non-negative latency measurements.

    When a dependency reports status 'ok', the latency_ms field must
    be present and contain a non-negative numeric value.
    """
    # ACT
    response = await async_client.get("/health")

    # ASSERT
    assert response.status_code == 200
    deps = response.json()["dependencies"]

    for name, dep in deps.items():
        if dep["status"] == "ok":
            assert dep["latency_ms"] is not None, (
                f"Dependency '{name}' is ok but latency_ms is None"
            )
            assert isinstance(dep["latency_ms"], (int, float))
            assert dep["latency_ms"] >= 0, (
                f"Dependency '{name}' has negative latency: {dep['latency_ms']}"
            )


@pytest.mark.integration
@pytest.mark.anyio
async def test_health_check_all_ok_means_status_ok(
    async_client: AsyncClient,
) -> None:
    """Overall status is 'ok' when all dependencies report 'ok'.

    Validates the status derivation logic: if every dependency
    has status 'ok', the top-level status must also be 'ok'.
    """
    # ACT
    response = await async_client.get("/health")

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    deps = data["dependencies"]

    all_ok = all(d["status"] == "ok" for d in deps.values())
    if all_ok:
        assert data["status"] == "ok"


@pytest.mark.integration
@pytest.mark.anyio
async def test_health_check_no_auth_required(
    async_client: AsyncClient,
) -> None:
    """Health check endpoint does not require API key authentication.

    The health endpoint must be publicly accessible for load balancers
    and monitoring systems that cannot provide credentials.
    """
    # ACT - No auth headers
    response = await async_client.get("/health")

    # ASSERT - Should succeed without auth
    assert response.status_code == 200
    assert "status" in response.json()


# =============================================================================
# Root Endpoint: GET /
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_root_returns_200(
    async_client: AsyncClient,
) -> None:
    """Root endpoint returns 200 OK.

    Validates that the root path is reachable and responds
    successfully without requiring authentication.
    """
    # ACT
    response = await async_client.get("/")

    # ASSERT
    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.anyio
async def test_root_response_structure(
    async_client: AsyncClient,
) -> None:
    """Root endpoint returns service name and version.

    Validates that the response contains exactly the 'service' and
    'version' keys with string values.
    """
    # ACT
    response = await async_client.get("/")

    # ASSERT
    assert response.status_code == 200
    data = response.json()

    assert "service" in data
    assert "version" in data
    assert isinstance(data["service"], str)
    assert isinstance(data["version"], str)


@pytest.mark.integration
@pytest.mark.anyio
async def test_root_service_name(
    async_client: AsyncClient,
) -> None:
    """Root endpoint returns correct service name.

    The service field must be 'claude-agent-api' to identify
    this specific API service.
    """
    # ACT
    response = await async_client.get("/")

    # ASSERT
    assert response.status_code == 200
    assert response.json()["service"] == "claude-agent-api"


@pytest.mark.integration
@pytest.mark.anyio
async def test_root_version_matches_health(
    async_client: AsyncClient,
) -> None:
    """Root endpoint version matches health check version.

    Both endpoints derive version from the same source (__version__),
    so they must report identical values.
    """
    # ACT
    root_response = await async_client.get("/")
    health_response = await async_client.get("/health")

    # ASSERT
    assert root_response.status_code == 200
    assert health_response.status_code == 200

    root_version = root_response.json()["version"]
    health_version = health_response.json()["version"]
    assert root_version == health_version


@pytest.mark.integration
@pytest.mark.anyio
async def test_root_no_auth_required(
    async_client: AsyncClient,
) -> None:
    """Root endpoint does not require API key authentication.

    The root endpoint must be publicly accessible for basic
    service discovery and version checks.
    """
    # ACT - No auth headers
    response = await async_client.get("/")

    # ASSERT - Should succeed without auth
    assert response.status_code == 200
    assert "service" in response.json()
