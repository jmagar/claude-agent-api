"""SQLAlchemy model for OpenAI Assistants API assistants."""

import secrets
from datetime import datetime

from sqlalchemy import Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.session import Base


def generate_assistant_id() -> str:
    """Generate a unique assistant ID in OpenAI format.

    Returns:
        str: ID in format 'asst_' followed by 24 random alphanumeric characters.
    """
    random_suffix = secrets.token_hex(12)  # 24 hex characters
    return f"asst_{random_suffix}"


class Assistant(Base):
    """Persistent record of OpenAI-compatible assistants.

    Maps to the /v1/assistants API endpoints. Assistants can be configured
    with specific models, instructions, and tools, then used to create runs
    on threads.
    """

    __tablename__ = "assistants"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=generate_assistant_id,
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
    model: Mapped[str] = mapped_column(String(100))
    name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    instructions: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # Up to 256000 chars
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
    owner_api_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Additional optional fields per OpenAI spec
    temperature: Mapped[float | None] = mapped_column(nullable=True)
    top_p: Mapped[float | None] = mapped_column(nullable=True)
    response_format: Mapped[dict[str, str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    __table_args__ = (
        Index("idx_assistants_created_at", created_at.desc()),
        Index("idx_assistants_owner_api_key", owner_api_key),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Assistant(id={self.id}, model={self.model}, name={self.name})>"
