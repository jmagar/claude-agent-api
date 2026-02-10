"""Integration tests for projects route DI refactor (Phase 3)."""

import inspect

import pytest


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_projects_uses_di_signature() -> None:
    """List projects endpoint should use DI-injected ProjectService."""
    from apps.api.routes.projects import list_projects

    # Verify function signature uses DI (not Cache + direct instantiation)
    sig = inspect.signature(list_projects)
    params = sig.parameters

    # Should have project_service: ProjectSvc parameter
    assert "project_service" in params, "Missing project_service DI parameter"

    # Should NOT have cache: Cache parameter (old anti-pattern)
    assert (
        "cache" not in params
    ), "Route still has cache parameter (should use project_service)"

    # Verify type annotation is ProjectSvc
    project_service_param = params["project_service"]
    # Note: ProjectSvc is Annotated[object, Depends(get_project_service)]
    # We can't easily check the Annotated type at runtime, but we can verify it exists
    assert project_service_param.annotation is not inspect.Parameter.empty


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_project_uses_di_signature() -> None:
    """Create project endpoint should use DI-injected ProjectService."""
    from apps.api.routes.projects import create_project

    sig = inspect.signature(create_project)
    params = sig.parameters

    assert "project_service" in params, "Missing project_service DI parameter"
    assert (
        "cache" not in params
    ), "Route still has cache parameter (should use project_service)"


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_project_uses_di_signature() -> None:
    """Get project endpoint should use DI-injected ProjectService."""
    from apps.api.routes.projects import get_project

    sig = inspect.signature(get_project)
    params = sig.parameters

    assert "project_service" in params, "Missing project_service DI parameter"
    assert (
        "cache" not in params
    ), "Route still has cache parameter (should use project_service)"


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_project_uses_di_signature() -> None:
    """Update project endpoint should use DI-injected ProjectService."""
    from apps.api.routes.projects import update_project

    sig = inspect.signature(update_project)
    params = sig.parameters

    assert "project_service" in params, "Missing project_service DI parameter"
    assert (
        "cache" not in params
    ), "Route still has cache parameter (should use project_service)"


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_project_uses_di_signature() -> None:
    """Delete project endpoint should use DI-injected ProjectService."""
    from apps.api.routes.projects import delete_project

    sig = inspect.signature(delete_project)
    params = sig.parameters

    assert "project_service" in params, "Missing project_service DI parameter"
    assert (
        "cache" not in params
    ), "Route still has cache parameter (should use project_service)"
