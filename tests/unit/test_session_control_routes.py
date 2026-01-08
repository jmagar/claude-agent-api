"""Unit tests for session control routes module."""

from starlette.routing import Route


class TestSessionControlRouterStructure:
    """Tests for session control router structure."""

    def test_session_control_router_exists(self) -> None:
        """Test that session control router can be imported."""
        from apps.api.routes.session_control import router

        assert router is not None
        assert router.prefix == "/sessions"

    def test_session_control_router_has_resume_endpoint(self) -> None:
        """Test that router has resume endpoint."""
        from apps.api.routes.session_control import router

        routes = [r.path for r in router.routes if isinstance(r, Route)]
        assert "/sessions/{session_id}/resume" in routes

    def test_session_control_router_has_fork_endpoint(self) -> None:
        """Test that router has fork endpoint."""
        from apps.api.routes.session_control import router

        routes = [r.path for r in router.routes if isinstance(r, Route)]
        assert "/sessions/{session_id}/fork" in routes

    def test_session_control_router_has_interrupt_endpoint(self) -> None:
        """Test that router has interrupt endpoint."""
        from apps.api.routes.session_control import router

        routes = [r.path for r in router.routes if isinstance(r, Route)]
        assert "/sessions/{session_id}/interrupt" in routes

    def test_session_control_router_has_control_endpoint(self) -> None:
        """Test that router has control endpoint."""
        from apps.api.routes.session_control import router

        routes = [r.path for r in router.routes if isinstance(r, Route)]
        assert "/sessions/{session_id}/control" in routes
