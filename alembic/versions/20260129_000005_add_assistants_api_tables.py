"""Add OpenAI Assistants API tables: assistants, runs, run_steps.

Revision ID: 20260129_000005
Revises: 20260110_000004_add_sessions_owner_api_key_index
Create Date: 2026-01-29 00:00:01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260129_000005"
down_revision: str | None = "20260110_000004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create assistants, runs, and run_steps tables."""
    # ==========================================================================
    # Create assistants table
    # ==========================================================================
    op.create_table(
        "assistants",
        # Primary key: OpenAI-format ID (asst_xxx)
        sa.Column("id", sa.String(64), nullable=False),
        # Required fields
        sa.Column("model", sa.String(100), nullable=False),
        # Optional fields
        sa.Column("name", sa.String(256), nullable=True),
        sa.Column("description", sa.String(512), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        # Tools: JSONB array of tool configurations
        sa.Column(
            "tools",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        # Metadata: JSONB key-value pairs
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        # Sampling parameters
        sa.Column("temperature", sa.Numeric(3, 2), nullable=True),
        sa.Column("top_p", sa.Numeric(3, 2), nullable=True),
        # Response format
        sa.Column("response_format", postgresql.JSONB(), nullable=True),
        # Ownership
        sa.Column("owner_api_key", sa.String(256), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for assistants
    op.create_index(
        "idx_assistants_owner_api_key",
        "assistants",
        ["owner_api_key"],
        postgresql_where=sa.text("owner_api_key IS NOT NULL"),
    )
    op.create_index(
        "idx_assistants_created_at",
        "assistants",
        [sa.text("created_at DESC")],
    )

    # ==========================================================================
    # Create runs table
    # ==========================================================================
    op.create_table(
        "runs",
        # Primary key: OpenAI-format ID (run_xxx)
        sa.Column("id", sa.String(64), nullable=False),
        # Foreign keys
        sa.Column("thread_id", sa.String(64), nullable=False),
        sa.Column("assistant_id", sa.String(64), nullable=False),
        # Status: queued, in_progress, requires_action, cancelling,
        #         cancelled, failed, completed, expired
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        # Model used
        sa.Column("model", sa.String(100), nullable=False),
        # Instructions override
        sa.Column("instructions", sa.Text(), nullable=True),
        # Tools: JSONB array of tool configurations
        sa.Column(
            "tools",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        # Metadata
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        # Required action: JSONB for tool_calls when status=requires_action
        sa.Column("required_action", postgresql.JSONB(), nullable=True),
        # Last error: JSONB with code and message
        sa.Column("last_error", postgresql.JSONB(), nullable=True),
        # Usage statistics: JSONB with prompt_tokens, completion_tokens, total_tokens
        sa.Column("usage", postgresql.JSONB(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["assistant_id"],
            ["assistants.id"],
            name="fk_runs_assistant_id",
            ondelete="CASCADE",
        ),
    )

    # Indexes for runs
    op.create_index("idx_runs_thread_id", "runs", ["thread_id"])
    op.create_index("idx_runs_assistant_id", "runs", ["assistant_id"])
    op.create_index("idx_runs_status", "runs", ["status"])
    op.create_index(
        "idx_runs_thread_status",
        "runs",
        ["thread_id", "status"],
    )
    op.create_index(
        "idx_runs_created_at",
        "runs",
        [sa.text("created_at DESC")],
    )

    # ==========================================================================
    # Create run_steps table
    # ==========================================================================
    op.create_table(
        "run_steps",
        # Primary key: OpenAI-format ID (step_xxx)
        sa.Column("id", sa.String(64), nullable=False),
        # Foreign keys
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("assistant_id", sa.String(64), nullable=False),
        sa.Column("thread_id", sa.String(64), nullable=False),
        # Type: message_creation or tool_calls
        sa.Column("type", sa.String(20), nullable=False),
        # Status: in_progress, cancelled, failed, completed, expired
        sa.Column("status", sa.String(20), nullable=False, server_default="in_progress"),
        # Step details: JSONB with type-specific content
        # For message_creation: { "message_creation": { "message_id": "msg_xxx" } }
        # For tool_calls: { "tool_calls": [{ "id": "call_xxx", ... }] }
        sa.Column("step_details", postgresql.JSONB(), nullable=False),
        # Last error
        sa.Column("last_error", postgresql.JSONB(), nullable=True),
        # Usage statistics
        sa.Column("usage", postgresql.JSONB(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name="fk_run_steps_run_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["assistant_id"],
            ["assistants.id"],
            name="fk_run_steps_assistant_id",
            ondelete="CASCADE",
        ),
    )

    # Indexes for run_steps
    op.create_index("idx_run_steps_run_id", "run_steps", ["run_id"])
    op.create_index("idx_run_steps_thread_id", "run_steps", ["thread_id"])
    op.create_index(
        "idx_run_steps_created_at",
        "run_steps",
        [sa.text("created_at DESC")],
    )


def downgrade() -> None:
    """Drop assistants API tables."""
    op.drop_table("run_steps")
    op.drop_table("runs")
    op.drop_table("assistants")
