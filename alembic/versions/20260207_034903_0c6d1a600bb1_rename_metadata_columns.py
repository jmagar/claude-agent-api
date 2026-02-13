"""rename_metadata_columns

Revision ID: 0c6d1a600bb1
Revises: 20260208_000007
Create Date: 2026-02-07 03:49:03.347444+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0c6d1a600bb1"
down_revision: str | None = "20260208_000007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema.

    Renames metadata columns to avoid SQLAlchemy reserved keyword conflicts:
    - sessions.metadata → session_metadata
    - assistants.metadata → assistant_metadata
    - runs.metadata → run_metadata
    """
    # Rename sessions.metadata to session_metadata
    op.alter_column(
        "sessions",
        "metadata",
        new_column_name="session_metadata",
    )

    # Rename assistants.metadata to assistant_metadata
    op.alter_column(
        "assistants",
        "metadata",
        new_column_name="assistant_metadata",
    )

    # Rename runs.metadata to run_metadata
    op.alter_column(
        "runs",
        "metadata",
        new_column_name="run_metadata",
    )


def downgrade() -> None:
    """Downgrade database schema.

    Reverts metadata column renames back to original names.
    """
    # Revert runs.run_metadata to metadata
    op.alter_column(
        "runs",
        "run_metadata",
        new_column_name="metadata",
    )

    # Revert assistants.assistant_metadata to metadata
    op.alter_column(
        "assistants",
        "assistant_metadata",
        new_column_name="metadata",
    )

    # Revert sessions.session_metadata to metadata
    op.alter_column(
        "sessions",
        "session_metadata",
        new_column_name="metadata",
    )
