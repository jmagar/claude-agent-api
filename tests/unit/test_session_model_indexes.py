"""Unit tests for session model indexes."""

from typing import TYPE_CHECKING, cast

from apps.api.models.session import Session

if TYPE_CHECKING:
    from sqlalchemy import Index, Table


def test_session_has_composite_status_created_index() -> None:
    """Test session model defines composite index on status and created_at."""
    table = cast("Table", Session.__table__)
    # Cast to dict with str keys since quoted_name is a str subclass
    indexes = cast(
        "dict[str | None, Index]",
        {index.name: index for index in table.indexes},
    )

    composite_index = indexes.get("idx_sessions_status_created")
    assert composite_index is not None
    assert len(composite_index.expressions) == 2
    first_expr = composite_index.expressions[0]
    first_name = getattr(first_expr, "name", None)
    assert first_name == "status"

    created_expr = composite_index.expressions[1]
    created_repr = str(created_expr).lower()
    assert "created_at" in created_repr
    assert "desc" in created_repr
