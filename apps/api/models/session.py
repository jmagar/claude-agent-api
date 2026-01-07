"""SQLAlchemy models for session management."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class Session(Base):
    """Persistent record of agent conversation sessions."""

    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        index=True,
    )
    model: Mapped[str] = mapped_column(String(50))
    working_directory: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_turns: Mapped[int] = mapped_column(default=0)
    total_cost_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 6),
        nullable=True,
    )
    parent_session_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sessions.id"),
        nullable=True,
        index=True,
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )

    # Relationships
    messages: Mapped[list["SessionMessage"]] = relationship(
        "SessionMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    checkpoints: Mapped[list["Checkpoint"]] = relationship(
        "Checkpoint",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    parent_session: Mapped["Session | None"] = relationship(
        "Session",
        remote_side=[id],
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_sessions_created_at", created_at.desc()),
        Index(
            "idx_sessions_parent",
            parent_session_id,
            postgresql_where=parent_session_id.isnot(None),
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Session(id={self.id}, status={self.status}, model={self.model})>"


class SessionMessage(Base):
    """Individual messages within a session (for audit/replay)."""

    __tablename__ = "session_messages"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True,
    )
    message_type: Mapped[str] = mapped_column(String(20))
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )

    # Relationships
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="messages",
    )

    __table_args__ = (Index("idx_messages_created_at", created_at),)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<SessionMessage(id={self.id}, "
            f"session_id={self.session_id}, type={self.message_type})>"
        )


class Checkpoint(Base):
    """File state snapshots for rewind capability."""

    __tablename__ = "checkpoints"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True,
    )
    user_message_uuid: Mapped[str] = mapped_column(
        String(100),
        unique=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    files_modified: Mapped[list[str]] = mapped_column(ARRAY(String))

    # Relationships
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="checkpoints",
    )

    __table_args__ = (Index("idx_checkpoints_uuid", user_message_uuid, unique=True),)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Checkpoint(id={self.id}, "
            f"session_id={self.session_id}, uuid={self.user_message_uuid})>"
        )
