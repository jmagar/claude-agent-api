"""Initial sessions, messages, and checkpoints tables.

Revision ID: 20260107_000001
Revises:
Create Date: 2026-01-07 00:00:01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260107_000001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create sessions, session_messages, and checkpoints tables."""
    # Create sessions table
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("model", sa.String(50), nullable=False),
        sa.Column("working_directory", sa.String(500), nullable=True),
        sa.Column("total_turns", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("parent_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["parent_session_id"],
            ["sessions.id"],
            name="fk_sessions_parent_session_id",
        ),
    )

    # Create indexes for sessions
    op.create_index("idx_sessions_status", "sessions", ["status"])
    op.create_index(
        "idx_sessions_created_at", "sessions", [sa.text("created_at DESC")]
    )
    op.create_index(
        "idx_sessions_parent",
        "sessions",
        ["parent_session_id"],
        postgresql_where=sa.text("parent_session_id IS NOT NULL"),
    )

    # Create session_messages table
    op.create_table(
        "session_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_type", sa.String(20), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            name="fk_session_messages_session_id",
            ondelete="CASCADE",
        ),
    )

    # Create indexes for session_messages
    op.create_index("idx_messages_session_id", "session_messages", ["session_id"])
    op.create_index("idx_messages_created_at", "session_messages", ["created_at"])

    # Create checkpoints table
    op.create_table(
        "checkpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_message_uuid", sa.String(100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("files_modified", postgresql.ARRAY(sa.String()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            name="fk_checkpoints_session_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_message_uuid", name="uq_checkpoints_uuid"),
    )

    # Create indexes for checkpoints
    op.create_index("idx_checkpoints_session_id", "checkpoints", ["session_id"])
    op.create_index(
        "idx_checkpoints_uuid", "checkpoints", ["user_message_uuid"], unique=True
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("checkpoints")
    op.drop_table("session_messages")
    op.drop_table("sessions")
