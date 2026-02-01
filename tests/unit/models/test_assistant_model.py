"""Unit tests for Assistant database model (TDD - RED phase)."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Table


class TestAssistantModel:
    """Tests for the Assistant SQLAlchemy model."""

    def test_can_import_model(self) -> None:
        """Model can be imported from the module."""
        from apps.api.models.assistant import Assistant

        assert Assistant is not None

    def test_has_required_columns(self) -> None:
        """Model has all required columns."""
        from apps.api.models.assistant import Assistant

        # Check column names via __table__
        columns = {c.name for c in Assistant.__table__.columns}

        assert "id" in columns
        assert "created_at" in columns
        assert "updated_at" in columns
        assert "model" in columns
        assert "name" in columns
        assert "description" in columns
        assert "instructions" in columns
        assert "tools" in columns
        assert "metadata" in columns
        assert "owner_api_key" in columns

    def test_id_is_string_primary_key(self) -> None:
        """ID column is a string (asst_xxx format) primary key."""
        from apps.api.models.assistant import Assistant

        id_col = Assistant.__table__.c.id
        assert id_col.primary_key

    def test_tools_is_jsonb(self) -> None:
        """Tools column is JSONB type."""
        from sqlalchemy.dialects.postgresql import JSONB

        from apps.api.models.assistant import Assistant

        tools_col = Assistant.__table__.c.tools
        assert isinstance(tools_col.type, JSONB)

    def test_metadata_is_jsonb(self) -> None:
        """Metadata column is JSONB type."""
        from sqlalchemy.dialects.postgresql import JSONB

        from apps.api.models.assistant import Assistant

        metadata_col = Assistant.__table__.c.metadata
        assert isinstance(metadata_col.type, JSONB)

    def test_has_owner_api_key_index(self) -> None:
        """Has index on owner_api_key column."""
        from typing import cast

        from apps.api.models.assistant import Assistant

        table = cast("Table", Assistant.__table__)
        index_names = {idx.name for idx in table.indexes}
        assert "idx_assistants_owner_api_key" in index_names

    def test_tablename_is_assistants(self) -> None:
        """Table name is 'assistants'."""
        from apps.api.models.assistant import Assistant

        assert Assistant.__tablename__ == "assistants"

    def test_can_create_instance(self) -> None:
        """Can create an Assistant instance."""
        from apps.api.models.assistant import Assistant

        assistant = Assistant(
            id="asst_abc123",
            model="gpt-4",
            name="Test Assistant",
            instructions="You are helpful.",
            tools=[{"type": "code_interpreter"}],
            metadata_={"key": "value"},
        )
        assert assistant.id == "asst_abc123"
        assert assistant.model == "gpt-4"
        assert assistant.name == "Test Assistant"

    def test_repr(self) -> None:
        """__repr__ returns meaningful string."""
        from apps.api.models.assistant import Assistant

        assistant = Assistant(
            id="asst_abc123",
            model="gpt-4",
            name="Test",
        )
        repr_str = repr(assistant)
        assert "asst_abc123" in repr_str
        assert "gpt-4" in repr_str


class TestAssistantIdGeneration:
    """Tests for assistant ID generation."""

    def test_generate_assistant_id_function(self) -> None:
        """Helper function generates valid assistant ID."""
        from apps.api.models.assistant import generate_assistant_id

        id1 = generate_assistant_id()
        id2 = generate_assistant_id()

        # Should start with asst_
        assert id1.startswith("asst_")
        assert id2.startswith("asst_")

        # Should be unique
        assert id1 != id2

        # Should have reasonable length
        assert len(id1) > 10
