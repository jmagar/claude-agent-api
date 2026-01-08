"""Session repository implementation using SQLAlchemy."""

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.session import Checkpoint, Session, SessionMessage


class SessionRepository:
    """SQLAlchemy implementation of session repository."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository.

        Args:
            db: Async SQLAlchemy session.
        """
        self._db = db

    async def create(
        self,
        session_id: UUID,
        model: str,
        working_directory: str | None = None,
        parent_session_id: UUID | None = None,
        metadata: dict[str, object] | None = None,
    ) -> Session:
        """Create a new session record.

        Args:
            session_id: Unique session identifier.
            model: Claude model used for the session.
            working_directory: Working directory path.
            parent_session_id: Parent session ID for forks.
            metadata: Additional session metadata.

        Returns:
            Created session.
        """
        session = Session(
            id=session_id,
            model=model,
            working_directory=working_directory,
            parent_session_id=parent_session_id,
            metadata_=metadata,
        )
        self._db.add(session)
        await self._db.commit()
        await self._db.refresh(session)
        return session

    async def get(self, session_id: UUID) -> Session | None:
        """Get a session by ID.

        Args:
            session_id: Session identifier.

        Returns:
            Session or None if not found.
        """
        stmt = select(Session).where(Session.id == session_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        session_id: UUID,
        status: str | None = None,
        total_turns: int | None = None,
        total_cost_usd: float | None = None,
    ) -> Session | None:
        """Update a session record.

        Args:
            session_id: Session identifier.
            status: New status value.
            total_turns: Updated turn count.
            total_cost_usd: Updated cost.

        Returns:
            Updated session or None if not found.
        """
        session = await self.get(session_id)
        if session is None:
            return None

        if status is not None:
            session.status = status
        if total_turns is not None:
            session.total_turns = total_turns
        if total_cost_usd is not None:
            session.total_cost_usd = Decimal(str(total_cost_usd))
        session.updated_at = datetime.now(UTC)

        await self._db.commit()
        await self._db.refresh(session)
        return session

    async def list_sessions(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Session], int]:
        """List sessions with optional filtering.

        Args:
            status: Filter by status.
            limit: Maximum results.
            offset: Pagination offset.

        Returns:
            Tuple of session list and total count.
        """
        # Build query
        stmt = select(Session).order_by(Session.created_at.desc())
        count_stmt = select(func.count()).select_from(Session)

        if status:
            stmt = stmt.where(Session.status == status)
            count_stmt = count_stmt.where(Session.status == status)

        # Get total count
        count_result = await self._db.execute(count_stmt)
        total = count_result.scalar_one()

        # Get paginated results
        stmt = stmt.limit(limit).offset(offset)
        result = await self._db.execute(stmt)
        sessions = result.scalars().all()

        return sessions, total

    async def add_message(
        self,
        session_id: UUID,
        message_type: str,
        content: dict[str, object],
    ) -> SessionMessage:
        """Add a message to a session.

        Args:
            session_id: Session identifier.
            message_type: Type of message (user, assistant, system, result).
            content: Message content.

        Returns:
            Created message.
        """
        message = SessionMessage(
            session_id=session_id,
            message_type=message_type,
            content=content,
        )
        self._db.add(message)
        await self._db.commit()
        await self._db.refresh(message)
        return message

    async def get_messages(
        self,
        session_id: UUID,
        limit: int | None = None,
    ) -> Sequence[SessionMessage]:
        """Get messages for a session.

        Args:
            session_id: Session identifier.
            limit: Maximum messages to return.

        Returns:
            List of messages.
        """
        stmt = (
            select(SessionMessage)
            .where(SessionMessage.session_id == session_id)
            .order_by(SessionMessage.created_at)
        )
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def add_checkpoint(
        self,
        session_id: UUID,
        user_message_uuid: str,
        files_modified: list[str],
    ) -> Checkpoint:
        """Add a checkpoint to a session.

        Args:
            session_id: Session identifier.
            user_message_uuid: UUID from user message.
            files_modified: List of modified file paths.

        Returns:
            Created checkpoint.
        """
        checkpoint = Checkpoint(
            session_id=session_id,
            user_message_uuid=user_message_uuid,
            files_modified=files_modified,
        )
        self._db.add(checkpoint)
        await self._db.commit()
        await self._db.refresh(checkpoint)
        return checkpoint

    async def get_checkpoints(self, session_id: UUID) -> Sequence[Checkpoint]:
        """Get checkpoints for a session.

        Args:
            session_id: Session identifier.

        Returns:
            List of checkpoints.
        """
        stmt = (
            select(Checkpoint)
            .where(Checkpoint.session_id == session_id)
            .order_by(Checkpoint.created_at)
        )
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def get_checkpoint_by_uuid(
        self,
        user_message_uuid: str,
    ) -> Checkpoint | None:
        """Get a checkpoint by its user message UUID.

        Args:
            user_message_uuid: Checkpoint UUID.

        Returns:
            Checkpoint or None if not found.
        """
        stmt = select(Checkpoint).where(
            Checkpoint.user_message_uuid == user_message_uuid
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_session(self, session_id: UUID) -> bool:
        """Delete a session and all related data.

        Args:
            session_id: Session identifier.

        Returns:
            True if deleted.
        """
        session = await self.get(session_id)
        if session is None:
            return False

        await self._db.delete(session)
        await self._db.commit()
        return True
