"""Unit tests for checkpoint routes module."""

from starlette.routing import Route


class TestCheckpointsRouterStructure:
    """Tests for checkpoints router structure."""

    def test_checkpoints_router_exists(self) -> None:
        """Test that checkpoints router can be imported."""
        from apps.api.routes.checkpoints import router

        assert router is not None
        assert router.prefix == "/sessions"

    def test_checkpoints_router_has_list_endpoint(self) -> None:
        """Test that router has list checkpoints endpoint."""
        from apps.api.routes.checkpoints import router

        routes = [r.path for r in router.routes if isinstance(r, Route)]
        assert "/sessions/{session_id}/checkpoints" in routes

    def test_checkpoints_router_has_rewind_endpoint(self) -> None:
        """Test that router has rewind endpoint."""
        from apps.api.routes.checkpoints import router

        routes = [r.path for r in router.routes if isinstance(r, Route)]
        assert "/sessions/{session_id}/rewind" in routes
