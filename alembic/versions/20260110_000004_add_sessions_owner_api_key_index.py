"""Add index on sessions.owner_api_key.

Revision ID: 20260110_000004
Revises: 20260110_000003
Create Date: 2026-01-10 00:00:04
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260110_000004"
down_revision: str | None = "20260110_000003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create index on sessions.owner_api_key."""
    op.create_index(
        "idx_sessions_owner_api_key",
        "sessions",
        ["owner_api_key"],
        unique=False,
    )


def downgrade() -> None:
    """Drop index on sessions.owner_api_key."""
    op.drop_index("idx_sessions_owner_api_key", table_name="sessions")
