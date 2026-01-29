"""Unit tests for structured logging in distributed session operations."""

from pathlib import Path

import pytest


@pytest.mark.unit
def test_session_service_logs_include_storage_context() -> None:
    """Test that SessionService logs include storage backend context."""
    session_py = Path("apps/api/services/session.py")
    content = session_py.read_text()

    # Verify logs include storage context for observability
    assert 'source="redis"' in content or "source='redis'" in content, (
        "SessionService should log source=redis for cache hits"
    )
    assert 'source="postgres"' in content or "source='postgres'" in content, (
        "SessionService should log source=postgres for DB fallback"
    )


@pytest.mark.unit
def test_agent_service_logs_include_distributed_context() -> None:
    """Test that AgentService logs include distributed context."""
    agent_py = Path("apps/api/services/agent/service.py")
    content = agent_py.read_text()

    # Verify logs include distributed flag for observability
    assert 'storage="redis"' in content or "storage='redis'" in content, (
        "AgentService should log storage=redis for distributed ops"
    )
