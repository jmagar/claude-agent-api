"""Unit tests for main app router registration."""

from starlette.routing import Route


class TestMainRouterRegistration:
    """Tests for router registration in main.py."""

    def test_all_session_routers_registered(self) -> None:
        """Test that all session-related routers are registered."""
        from apps.api.main import app

        routes: list[str] = [r.path for r in app.routes if isinstance(r, Route)]

        # Sessions CRUD
        assert "/api/v1/sessions" in routes
        assert "/api/v1/sessions/{session_id}" in routes

        # Session control
        assert "/api/v1/sessions/{session_id}/resume" in routes
        assert "/api/v1/sessions/{session_id}/fork" in routes
        assert "/api/v1/sessions/{session_id}/interrupt" in routes
        assert "/api/v1/sessions/{session_id}/control" in routes

        # Checkpoints
        assert "/api/v1/sessions/{session_id}/checkpoints" in routes
        assert "/api/v1/sessions/{session_id}/rewind" in routes

        # Interactions
        assert "/api/v1/sessions/{session_id}/answer" in routes
