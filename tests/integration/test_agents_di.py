"""Integration tests for agents route DI refactor (Phase 4)."""

import inspect

import pytest


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_agents_uses_di_signature() -> None:
    """List agents endpoint should use DI-injected AgentService."""
    from apps.api.routes.agents import list_agents

    # Verify function signature uses DI (not Cache + direct instantiation)
    sig = inspect.signature(list_agents)
    params = sig.parameters

    # Should have agent_service: AgentConfigSvc parameter
    assert "agent_service" in params, "Missing agent_service DI parameter"

    # Should NOT have cache: Cache parameter (old anti-pattern)
    assert (
        "cache" not in params
    ), "Route still has cache parameter (should use agent_service)"

    # Verify type annotation is not empty
    agent_service_param = params["agent_service"]
    # Note: AgentConfigSvc is Annotated[object, Depends(get_agent_config_service)]
    # We can't easily check the Annotated type at runtime, but we can verify it exists
    assert agent_service_param.annotation is not inspect.Parameter.empty


@pytest.mark.integration
@pytest.mark.anyio
async def test_create_agent_uses_di_signature() -> None:
    """Create agent endpoint should use DI-injected AgentService."""
    from apps.api.routes.agents import create_agent

    sig = inspect.signature(create_agent)
    params = sig.parameters

    assert "agent_service" in params, "Missing agent_service DI parameter"
    assert (
        "cache" not in params
    ), "Route still has cache parameter (should use agent_service)"


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_agent_uses_di_signature() -> None:
    """Get agent endpoint should use DI-injected AgentService."""
    from apps.api.routes.agents import get_agent

    sig = inspect.signature(get_agent)
    params = sig.parameters

    assert "agent_service" in params, "Missing agent_service DI parameter"
    assert (
        "cache" not in params
    ), "Route still has cache parameter (should use agent_service)"


@pytest.mark.integration
@pytest.mark.anyio
async def test_update_agent_uses_di_signature() -> None:
    """Update agent endpoint should use DI-injected AgentService."""
    from apps.api.routes.agents import update_agent

    sig = inspect.signature(update_agent)
    params = sig.parameters

    assert "agent_service" in params, "Missing agent_service DI parameter"
    assert (
        "cache" not in params
    ), "Route still has cache parameter (should use agent_service)"


@pytest.mark.integration
@pytest.mark.anyio
async def test_delete_agent_uses_di_signature() -> None:
    """Delete agent endpoint should use DI-injected AgentService."""
    from apps.api.routes.agents import delete_agent

    sig = inspect.signature(delete_agent)
    params = sig.parameters

    assert "agent_service" in params, "Missing agent_service DI parameter"
    assert (
        "cache" not in params
    ), "Route still has cache parameter (should use agent_service)"


@pytest.mark.integration
@pytest.mark.anyio
async def test_share_agent_uses_di_signature() -> None:
    """Share agent endpoint should use DI-injected AgentService."""
    from apps.api.routes.agents import share_agent

    sig = inspect.signature(share_agent)
    params = sig.parameters

    assert "agent_service" in params, "Missing agent_service DI parameter"
    assert (
        "cache" not in params
    ), "Route still has cache parameter (should use agent_service)"
