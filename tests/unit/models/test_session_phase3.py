"""Unit tests for Session model after Phase 3 migration."""

from sqlalchemy import inspect

from apps.api.models.session import Session


def test_session_model_has_only_hash_column() -> None:
    """Session model should only have owner_api_key_hash, not owner_api_key."""
    # Get model columns
    mapper = inspect(Session)
    column_names = {col.key for col in mapper.columns}

    # Should have hash column
    assert "owner_api_key_hash" in column_names

    # Should NOT have plaintext column (Phase 3 removes it)
    assert "owner_api_key" not in column_names


def test_session_model_indexes_only_hash() -> None:
    """Session model should only index owner_api_key_hash."""
    # Get table indexes from SQLAlchemy Table object
    table = Session.__table__
    index_names = {idx.name for idx in table.indexes}  # type: ignore[attr-defined]

    # Should have hash index
    assert "idx_sessions_owner_api_key_hash" in index_names

    # Should NOT have plaintext index (Phase 3 removes it)
    assert "idx_sessions_owner_api_key" not in index_names
