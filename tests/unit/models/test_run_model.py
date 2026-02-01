"""Unit tests for Run and RunStep database models (TDD - RED phase)."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Table


class TestRunModel:
    """Tests for the Run SQLAlchemy model."""

    def test_can_import_model(self) -> None:
        """Model can be imported from the module."""
        from apps.api.models.run import Run

        assert Run is not None

    def test_has_required_columns(self) -> None:
        """Model has all required columns."""
        from apps.api.models.run import Run

        columns = {c.name for c in Run.__table__.columns}

        assert "id" in columns
        assert "created_at" in columns
        assert "thread_id" in columns
        assert "assistant_id" in columns
        assert "status" in columns
        assert "model" in columns
        assert "instructions" in columns
        assert "tools" in columns
        assert "metadata" in columns
        assert "required_action" in columns
        assert "last_error" in columns
        assert "usage" in columns

    def test_id_is_string_primary_key(self) -> None:
        """ID column is a string (run_xxx format) primary key."""
        from apps.api.models.run import Run

        id_col = Run.__table__.c.id
        assert id_col.primary_key

    def test_required_action_is_jsonb(self) -> None:
        """required_action column is JSONB type."""
        from sqlalchemy.dialects.postgresql import JSONB

        from apps.api.models.run import Run

        col = Run.__table__.c.required_action
        assert isinstance(col.type, JSONB)

    def test_last_error_is_jsonb(self) -> None:
        """last_error column is JSONB type."""
        from sqlalchemy.dialects.postgresql import JSONB

        from apps.api.models.run import Run

        col = Run.__table__.c.last_error
        assert isinstance(col.type, JSONB)

    def test_usage_is_jsonb(self) -> None:
        """usage column is JSONB type."""
        from sqlalchemy.dialects.postgresql import JSONB

        from apps.api.models.run import Run

        col = Run.__table__.c.usage
        assert isinstance(col.type, JSONB)

    def test_has_thread_id_index(self) -> None:
        """Has index on thread_id column."""
        from typing import cast

        from apps.api.models.run import Run

        table = cast("Table", Run.__table__)
        index_names = {idx.name for idx in table.indexes}
        assert "idx_runs_thread_id" in index_names

    def test_has_status_index(self) -> None:
        """Has index on status column."""
        from typing import cast

        from apps.api.models.run import Run

        table = cast("Table", Run.__table__)
        index_names = {idx.name for idx in table.indexes}
        assert "idx_runs_status" in index_names

    def test_tablename_is_runs(self) -> None:
        """Table name is 'runs'."""
        from apps.api.models.run import Run

        assert Run.__tablename__ == "runs"

    def test_can_create_instance(self) -> None:
        """Can create a Run instance."""
        from apps.api.models.run import Run

        run = Run(
            id="run_abc123",
            thread_id="thread_abc123",
            assistant_id="asst_abc123",
            status="queued",
            model="gpt-4",
        )
        assert run.id == "run_abc123"
        assert run.status == "queued"

    def test_repr(self) -> None:
        """__repr__ returns meaningful string."""
        from apps.api.models.run import Run

        run = Run(
            id="run_abc123",
            thread_id="thread_abc123",
            assistant_id="asst_abc123",
            status="queued",
            model="gpt-4",
        )
        repr_str = repr(run)
        assert "run_abc123" in repr_str
        assert "queued" in repr_str


class TestRunStepModel:
    """Tests for the RunStep SQLAlchemy model."""

    def test_can_import_model(self) -> None:
        """Model can be imported from the module."""
        from apps.api.models.run import RunStep

        assert RunStep is not None

    def test_has_required_columns(self) -> None:
        """Model has all required columns."""
        from apps.api.models.run import RunStep

        columns = {c.name for c in RunStep.__table__.columns}

        assert "id" in columns
        assert "created_at" in columns
        assert "run_id" in columns
        assert "assistant_id" in columns
        assert "thread_id" in columns
        assert "type" in columns
        assert "status" in columns
        assert "step_details" in columns
        assert "last_error" in columns
        assert "usage" in columns

    def test_step_details_is_jsonb(self) -> None:
        """step_details column is JSONB type."""
        from sqlalchemy.dialects.postgresql import JSONB

        from apps.api.models.run import RunStep

        col = RunStep.__table__.c.step_details
        assert isinstance(col.type, JSONB)

    def test_has_run_id_index(self) -> None:
        """Has index on run_id column."""
        from typing import cast

        from apps.api.models.run import RunStep

        table = cast("Table", RunStep.__table__)
        index_names = {idx.name for idx in table.indexes}
        assert "idx_run_steps_run_id" in index_names

    def test_tablename_is_run_steps(self) -> None:
        """Table name is 'run_steps'."""
        from apps.api.models.run import RunStep

        assert RunStep.__tablename__ == "run_steps"

    def test_can_create_message_creation_step(self) -> None:
        """Can create a message_creation RunStep instance."""
        from apps.api.models.run import RunStep

        step = RunStep(
            id="step_abc123",
            run_id="run_abc123",
            assistant_id="asst_abc123",
            thread_id="thread_abc123",
            type="message_creation",
            status="completed",
            step_details={
                "type": "message_creation",
                "message_creation": {"message_id": "msg_abc123"},
            },
        )
        assert step.type == "message_creation"
        assert step.status == "completed"

    def test_can_create_tool_calls_step(self) -> None:
        """Can create a tool_calls RunStep instance."""
        from apps.api.models.run import RunStep

        step = RunStep(
            id="step_def456",
            run_id="run_abc123",
            assistant_id="asst_abc123",
            thread_id="thread_abc123",
            type="tool_calls",
            status="in_progress",
            step_details={
                "type": "tool_calls",
                "tool_calls": [
                    {
                        "id": "call_abc123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": "{}",
                            "output": None,
                        },
                    }
                ],
            },
        )
        assert step.type == "tool_calls"

    def test_repr(self) -> None:
        """__repr__ returns meaningful string."""
        from apps.api.models.run import RunStep

        step = RunStep(
            id="step_abc123",
            run_id="run_abc123",
            assistant_id="asst_abc123",
            thread_id="thread_abc123",
            type="message_creation",
            status="completed",
            step_details={},
        )
        repr_str = repr(step)
        assert "step_abc123" in repr_str


class TestIdGeneration:
    """Tests for ID generation functions."""

    def test_generate_run_id(self) -> None:
        """generate_run_id creates valid run IDs."""
        from apps.api.models.run import generate_run_id

        id1 = generate_run_id()
        id2 = generate_run_id()

        assert id1.startswith("run_")
        assert id2.startswith("run_")
        assert id1 != id2
        assert len(id1) > 10

    def test_generate_run_step_id(self) -> None:
        """generate_run_step_id creates valid step IDs."""
        from apps.api.models.run import generate_run_step_id

        id1 = generate_run_step_id()
        id2 = generate_run_step_id()

        assert id1.startswith("step_")
        assert id2.startswith("step_")
        assert id1 != id2
        assert len(id1) > 10
