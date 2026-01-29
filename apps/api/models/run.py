"""SQLAlchemy models for OpenAI Assistants API runs and run steps."""

import secrets
from datetime import datetime

from sqlalchemy import Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.session import Base


def generate_run_id() -> str:
    """Generate a unique run ID in OpenAI format.

    Returns:
        str: ID in format 'run_' followed by 24 random alphanumeric characters.
    """
    random_suffix = secrets.token_hex(12)
    return f"run_{random_suffix}"


def generate_run_step_id() -> str:
    """Generate a unique run step ID in OpenAI format.

    Returns:
        str: ID in format 'step_' followed by 24 random alphanumeric characters.
    """
    random_suffix = secrets.token_hex(12)
    return f"step_{random_suffix}"


class Run(Base):
    """Persistent record of OpenAI-compatible runs.

    A run represents an execution of an assistant on a thread.
    Maps to the /v1/threads/{thread_id}/runs API endpoints.

    Status lifecycle:
        queued → in_progress → completed
                            ↘ requires_action → (submit) → in_progress
                            ↘ failed
                            ↘ cancelled (via cancel)
                            ↘ expired (timeout)
    """

    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=generate_run_id,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    thread_id: Mapped[str] = mapped_column(String(50), index=True)
    assistant_id: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(
        String(20),
        default="queued",
    )
    model: Mapped[str] = mapped_column(String(100))
    instructions: Mapped[str | None] = mapped_column(String, nullable=True)
    tools: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
    )
    metadata_: Mapped[dict[str, str] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        server_default="{}",
    )
    # Status-dependent fields
    required_action: Mapped[dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    last_error: Mapped[dict[str, str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    usage: Mapped[dict[str, int] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    # Timestamps for state transitions
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    # Additional configuration
    max_prompt_tokens: Mapped[int | None] = mapped_column(nullable=True)
    max_completion_tokens: Mapped[int | None] = mapped_column(nullable=True)
    truncation_strategy: Mapped[dict[str, str | int] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    response_format: Mapped[dict[str, str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    tool_choice: Mapped[dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    parallel_tool_calls: Mapped[bool | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index("idx_runs_thread_id", thread_id),
        Index("idx_runs_status", status),
        Index("idx_runs_created_at", created_at.desc()),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Run(id={self.id}, thread_id={self.thread_id}, "
            f"status={self.status})>"
        )


class RunStep(Base):
    """Persistent record of individual steps within a run.

    A run step represents either:
    - A message_creation step (when assistant responds)
    - A tool_calls step (when assistant invokes tools)

    Maps to the /v1/threads/{thread_id}/runs/{run_id}/steps API endpoints.
    """

    __tablename__ = "run_steps"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=generate_run_step_id,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    run_id: Mapped[str] = mapped_column(String(50), index=True)
    assistant_id: Mapped[str] = mapped_column(String(50))
    thread_id: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(20))  # message_creation or tool_calls
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    step_details: Mapped[dict[str, object]] = mapped_column(JSONB)
    # Status-dependent fields
    last_error: Mapped[dict[str, str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    usage: Mapped[dict[str, int] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    # Timestamps for state transitions
    expired_at: Mapped[datetime | None] = mapped_column(nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index("idx_run_steps_run_id", run_id),
        Index("idx_run_steps_created_at", created_at.desc()),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<RunStep(id={self.id}, run_id={self.run_id}, "
            f"type={self.type}, status={self.status})>"
        )
