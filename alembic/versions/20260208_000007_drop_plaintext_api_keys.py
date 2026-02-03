"""Drop plaintext API key columns after Phase 2 verification.

IRREVERSIBLE MIGRATION: This migration permanently removes plaintext API keys.

Pre-Deployment Checklist:
1. Phase 2 code deployed and verified
2. Hash consistency verification passed (scripts/verify_hash_consistency.py)
3. Database backup created and verified
4. Zero authentication failures in production logs
5. Stakeholder approval obtained

Revision ID: 20260208_000007
Revises: 20260201_000006
Create Date: 2026-02-08 00:00:07
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260208_000007"
down_revision: str | None = "20260201_000006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop plaintext owner_api_key columns and indexes.

    WARNING: This is an IRREVERSIBLE operation. Plaintext API keys will be
    permanently lost. Only the SHA-256 hashes in owner_api_key_hash will remain.

    Phase 3: Final cleanup after Phase 2 verification period.
    """
    # Set transaction timeout to prevent long-running locks
    # This ensures the migration completes quickly or fails fast
    op.execute("SET LOCAL statement_timeout = '30s'")

    # Drop indexes on plaintext columns first (required before dropping columns)
    op.drop_index("idx_sessions_owner_api_key", table_name="sessions")
    op.drop_index("idx_assistants_owner_api_key", table_name="assistants")

    # Drop plaintext columns (IRREVERSIBLE - data loss!)
    op.drop_column("sessions", "owner_api_key")
    op.drop_column("assistants", "owner_api_key")


def downgrade() -> None:
    """Attempt to restore plaintext columns.

    WARNING: This downgrade is LOSSY. Original plaintext API keys cannot be
    recovered from SHA-256 hashes. This downgrade will:

    1. Recreate owner_api_key columns (but they will be NULL)
    2. Recreate indexes (on NULL columns - not useful)

    Effect: All API keys will be lost. Clients must regenerate API keys.
    Ownership associations will be preserved via owner_api_key_hash.

    This downgrade exists only for schema consistency, not data recovery.
    """
    # Recreate plaintext columns (nullable, will be NULL for all rows)
    op.add_column(
        "sessions",
        sa.Column("owner_api_key", sa.String(255), nullable=True),
    )
    op.add_column(
        "assistants",
        sa.Column("owner_api_key", sa.String(255), nullable=True),
    )

    # Recreate indexes on NULL columns (not particularly useful)
    op.create_index("idx_sessions_owner_api_key", "sessions", ["owner_api_key"])
    op.create_index("idx_assistants_owner_api_key", "assistants", ["owner_api_key"])

    # NOTE: Plaintext API keys are NOT restored. They are permanently lost.
    # Client applications must regenerate API keys after this downgrade.
