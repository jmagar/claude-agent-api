"""Add owner_api_key column to sessions.

Revision ID: 20260110_000003
Revises: 20260110_000002
Create Date: 2026-01-10 00:00:03

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260110_000003"
down_revision: str | None = "20260110_000002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add owner_api_key column to sessions."""
    op.add_column(
        "sessions",
        sa.Column("owner_api_key", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    """Drop owner_api_key column from sessions."""
    op.drop_column("sessions", "owner_api_key")
