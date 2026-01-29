"""Unit tests for session SQLAlchemy model configuration."""

from typing import TYPE_CHECKING, cast

from sqlalchemy.orm import RelationshipProperty

from apps.api.models.session import Session

if TYPE_CHECKING:
    from sqlalchemy import Table


def test_session_relationships_use_lazy_raise() -> None:
    """Ensure relationships use lazy='raise' to prevent N+1 queries.

    With lazy='raise', accessing relationships without explicit loading
    will raise an error. This prevents accidental N+1 queries in list
    operations. Use selectinload() when relationships are needed.
    """
    assert isinstance(Session.messages.property, RelationshipProperty)
    assert isinstance(Session.checkpoints.property, RelationshipProperty)
    assert isinstance(Session.parent_session.property, RelationshipProperty)

    assert Session.messages.property.lazy == "raise"
    assert Session.checkpoints.property.lazy == "raise"
    assert Session.parent_session.property.lazy == "raise"


def test_session_owner_api_key_index_exists() -> None:
    """Ensure sessions.owner_api_key has an index for filtered lookups."""
    table = cast("Table", Session.__table__)
    index_names = {index.name for index in table.indexes}
    assert "idx_sessions_owner_api_key" in index_names
