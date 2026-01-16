"""Unit tests for session SQLAlchemy model configuration."""

from typing import TYPE_CHECKING, cast

from sqlalchemy.orm import RelationshipProperty

from apps.api.models.session import Session

if TYPE_CHECKING:
    from sqlalchemy import Table


def test_session_relationships_use_lazy_select() -> None:
    """Ensure relationships use selectin for optimal performance."""
    assert isinstance(Session.messages.property, RelationshipProperty)
    assert isinstance(Session.checkpoints.property, RelationshipProperty)
    assert isinstance(Session.parent_session.property, RelationshipProperty)

    assert Session.messages.property.lazy == "selectin"
    assert Session.checkpoints.property.lazy == "selectin"
    assert Session.parent_session.property.lazy == "selectin"


def test_session_owner_api_key_index_exists() -> None:
    """Ensure sessions.owner_api_key has an index for filtered lookups."""
    table = cast("Table", Session.__table__)
    index_names = {index.name for index in table.indexes}
    assert "idx_sessions_owner_api_key" in index_names
