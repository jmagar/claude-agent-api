"""Unit tests for sessions routes module (CRUD only)."""

from starlette.routing import Route


def _get_route_paths(router: object) -> list[str]:
    """Extract route paths from a FastAPI router.

    Args:
        router: FastAPI APIRouter instance.

    Returns:
        List of route path strings.
    """
    # router.routes contains Route objects which have path attribute
    routes = getattr(router, "routes", [])
    return [r.path for r in routes if isinstance(r, Route)]


class TestSessionsRouterStructure:
    """Tests for sessions router structure after refactor."""

    def test_sessions_router_exists(self) -> None:
        """Test that sessions router can be imported."""
        from apps.api.routes.sessions import router

        assert router is not None
        assert router.prefix == "/sessions"

    def test_sessions_router_has_list_endpoint(self) -> None:
        """Test that router has list endpoint."""
        from apps.api.routes.sessions import router

        routes = _get_route_paths(router)
        # Router includes prefix in path
        assert "/sessions" in routes

    def test_sessions_router_has_get_endpoint(self) -> None:
        """Test that router has get endpoint."""
        from apps.api.routes.sessions import router

        routes = _get_route_paths(router)
        # Router includes prefix in path
        assert "/sessions/{session_id}" in routes

    def test_sessions_router_does_not_have_checkpoint_endpoints(self) -> None:
        """Test that checkpoint endpoints were extracted."""
        from apps.api.routes.sessions import router

        routes = _get_route_paths(router)
        # Router includes prefix in paths
        assert "/sessions/{session_id}/checkpoints" not in routes
        assert "/sessions/{session_id}/rewind" not in routes

    def test_sessions_router_does_not_have_control_endpoints(self) -> None:
        """Test that control endpoints were extracted."""
        from apps.api.routes.sessions import router

        routes = _get_route_paths(router)
        # Router includes prefix in paths
        assert "/sessions/{session_id}/resume" not in routes
        assert "/sessions/{session_id}/fork" not in routes
        assert "/sessions/{session_id}/interrupt" not in routes
        assert "/sessions/{session_id}/control" not in routes

    def test_sessions_router_does_not_have_answer_endpoint(self) -> None:
        """Test that answer endpoint was extracted."""
        from apps.api.routes.sessions import router

        routes = _get_route_paths(router)
        # Router includes prefix in path
        assert "/sessions/{session_id}/answer" not in routes
