"""convert_datetime_columns_to_timestamptz

Revision ID: 9ddfdd63af30
Revises: 0c6d1a600bb1
Create Date: 2026-02-10 17:04:25.289186+00:00

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9ddfdd63af30"
down_revision: Union[str, None] = "0c6d1a600bb1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert datetime columns to timezone-aware timestamptz.

    This migration updates all timestamp columns to timestamptz to ensure
    timezone-aware datetime handling across the application. Prevents
    'offset-naive and offset-aware datetime' errors when mixing Python
    timezone-aware datetimes with database timestamps.
    """
    # Sessions table
    op.execute("""
        ALTER TABLE sessions
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
    """)
    op.execute("""
        ALTER TABLE sessions
        ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE
        USING updated_at AT TIME ZONE 'UTC'
    """)

    # SessionMessages table
    op.execute("""
        ALTER TABLE session_messages
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
    """)

    # Checkpoints table
    op.execute("""
        ALTER TABLE checkpoints
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
    """)


def downgrade() -> None:
    """Revert datetime columns to timezone-naive timestamp.

    WARNING: This will drop timezone information from all datetime columns.
    Only use for rollback in development environments.

    IMPORTANT: Using 'AT TIME ZONE' clause to preserve UTC values during
    conversion. Without this, PostgreSQL converts to session timezone before
    dropping tzinfo, which can corrupt data if session timezone ≠ UTC.
    """
    # Sessions table
    op.execute("""
        ALTER TABLE sessions
        ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
    """)
    op.execute("""
        ALTER TABLE sessions
        ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING updated_at AT TIME ZONE 'UTC'
    """)

    # SessionMessages table
    op.execute("""
        ALTER TABLE session_messages
        ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
    """)

    # Checkpoints table
    op.execute("""
        ALTER TABLE checkpoints
        ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
    """)
