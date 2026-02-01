"""Hash API keys for security.

SECURITY MIGRATION: Converts plaintext API keys to SHA-256 hashes.

This migration implements a multi-phase approach to safely migrate
existing data while preventing downtime:

Phase 1 (FORWARD):
1. Add owner_api_key_hash column (nullable)
2. Hash all existing owner_api_key values into owner_api_key_hash
3. Keep both columns temporarily for rollback safety

Phase 2 (Manual - after deployment verification):
1. Deploy application code that uses hashed keys
2. Verify all authentication works correctly
3. Run Phase 2 migration to drop owner_api_key column

Phase 3 (ROLLBACK if needed):
- Downgrade restores owner_api_key from hash (lossy - generates new keys)
- WARNING: Existing API keys will be invalidated on rollback

Revision ID: 20260201_000006
Revises: 20260129_000005
Create Date: 2026-02-01 00:00:06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260201_000006"
down_revision: str | None = "20260129_000005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add owner_api_key_hash column and hash existing keys.

    Phase 1: Safe migration with dual-column approach.
    """
    # Enable pgcrypto extension for digest() and encode() functions
    op.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    # Add new hash column (nullable for migration)
    op.add_column(
        "sessions",
        sa.Column("owner_api_key_hash", sa.String(64), nullable=True),
    )

    # Hash all existing API keys using PostgreSQL's encode(digest(...), 'hex')
    # This matches Python's hashlib.sha256().hexdigest() output
    op.execute(
        text(
            """
            UPDATE sessions
            SET owner_api_key_hash = encode(digest(owner_api_key, 'sha256'), 'hex')
            WHERE owner_api_key IS NOT NULL
            """
        )
    )

    # Create index on hash column for efficient lookups
    op.create_index(
        "idx_sessions_owner_api_key_hash",
        "sessions",
        ["owner_api_key_hash"],
    )

    # Add same column to assistants table
    op.add_column(
        "assistants",
        sa.Column("owner_api_key_hash", sa.String(64), nullable=True),
    )

    # Hash existing assistant API keys
    op.execute(
        text(
            """
            UPDATE assistants
            SET owner_api_key_hash = encode(digest(owner_api_key, 'sha256'), 'hex')
            WHERE owner_api_key IS NOT NULL
            """
        )
    )

    # Create index on assistants hash column
    op.create_index(
        "idx_assistants_owner_api_key_hash",
        "assistants",
        ["owner_api_key_hash"],
    )


def downgrade() -> None:
    """Remove hash columns and restore plaintext keys.

    WARNING: This is a LOSSY downgrade. Original API keys cannot be recovered
    from hashes. This downgrade will:
    1. Drop hash columns
    2. Keep existing owner_api_key values (which are NULL if they were hashed)

    Effect: API keys that were hashed will be lost and need regeneration.
    """
    # Drop indexes first
    op.drop_index("idx_sessions_owner_api_key_hash", table_name="sessions")
    op.drop_index("idx_assistants_owner_api_key_hash", table_name="assistants")

    # Drop hash columns
    op.drop_column("sessions", "owner_api_key_hash")
    op.drop_column("assistants", "owner_api_key_hash")

    # NOTE: owner_api_key columns remain but may be NULL if keys were hashed.
    # Admins must regenerate API keys after rollback.
