"""Unit tests for session model indexes."""

from apps.api.models.session import Session


def test_session_has_composite_status_created_index() -> None:
    """Test session model defines composite index on status and created_at."""
    indexes = {index.name: index for index in Session.__table__.indexes}

    composite_index = indexes.get("idx_sessions_status_created")
    assert composite_index is not None
    assert len(composite_index.expressions) == 2
    assert composite_index.expressions[0].name == "status"

    created_expr = composite_index.expressions[1]
    created_repr = str(created_expr).lower()
    assert "created_at" in created_repr
    assert "desc" in created_repr
