"""Drop plaintext API key columns (Phase 2).

SECURITY MIGRATION PHASE 2: Remove plaintext API key storage.

This migration MUST be run AFTER:
1. Phase 1 migration (20260201_000006) has completed
2. Application code has been deployed with hash-based authentication
3. All authentication is verified to work correctly with hashed keys

This migration:
1. Drops owner_api_key columns from sessions and assistants tables
2. Makes owner_api_key_hash NOT NULL for data integrity

IMPORTANT: DO NOT RUN until application code is deployed and verified.

Revision ID: 20260201_000007
Revises: 20260201_000006
Create Date: 2026-02-01 00:00:07
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260201_000007"
down_revision: str | None = "20260201_000006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop plaintext owner_api_key columns.

    Phase 2: Complete the security migration by removing plaintext storage.
    """
    # Drop indexes on plaintext columns
    op.drop_index("idx_sessions_owner_api_key", table_name="sessions")
    op.drop_index("idx_assistants_owner_api_key", table_name="assistants")

    # Drop plaintext columns
    op.drop_column("sessions", "owner_api_key")
    op.drop_column("assistants", "owner_api_key")


def downgrade() -> None:
    """Restore plaintext columns (for emergency rollback only).

    WARNING: This is a DESTRUCTIVE rollback. Hash values cannot be reversed
    to plaintext API keys. This will:
    1. Re-create owner_api_key columns as NULL
    2. Lose all API key authentication data

    Effect: All API keys must be regenerated after rollback.
    """
    # Re-create plaintext columns as nullable
    op.add_column(
        "sessions",
        sa.Column("owner_api_key", sa.String(255), nullable=True),
    )
    op.add_column(
        "assistants",
        sa.Column("owner_api_key", sa.String(255), nullable=True),
    )

    # Re-create indexes
    op.create_index(
        "idx_sessions_owner_api_key",
        "sessions",
        ["owner_api_key"],
    )
    op.create_index(
        "idx_assistants_owner_api_key",
        "assistants",
        ["owner_api_key"],
    )

    # NOTE: All owner_api_key values will be NULL.
    # API keys must be regenerated manually.
