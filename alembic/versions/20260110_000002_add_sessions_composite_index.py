"""Add composite index for sessions status and created_at.

Revision ID: 20260110_000002
Revises: 20260107_000001
Create Date: 2026-01-10 00:00:02

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260110_000002"
down_revision: str | None = "20260107_000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add composite index for sessions status and created_at."""
    op.create_index(
        "idx_sessions_status_created",
        "sessions",
        ["status", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    """Drop composite index for sessions status and created_at."""
    op.drop_index("idx_sessions_status_created", table_name="sessions")
