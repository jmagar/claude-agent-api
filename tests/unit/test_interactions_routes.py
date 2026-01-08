"""Unit tests for interactions routes module."""

from starlette.routing import Route


class TestInteractionsRouterStructure:
    """Tests for interactions router structure."""

    def test_interactions_router_exists(self) -> None:
        """Test that interactions router can be imported."""
        from apps.api.routes.interactions import router

        assert router is not None
        assert router.prefix == "/sessions"

    def test_interactions_router_has_answer_endpoint(self) -> None:
        """Test that router has answer endpoint."""
        from apps.api.routes.interactions import router

        routes = [r.path for r in router.routes if isinstance(r, Route)]
        assert "/sessions/{session_id}/answer" in routes
