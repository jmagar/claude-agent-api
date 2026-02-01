"""Session repository implementation using SQLAlchemy."""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.exceptions.session import SessionNotFoundError
from apps.api.models.session import Checkpoint, Session, SessionMessage
from apps.api.utils.crypto import hash_api_key


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
        owner_api_key: str | None = None,
    ) -> Session:
        """Create a new session record.

        Args:
            session_id: Unique session identifier.
            model: Claude model used for the session.
            working_directory: Working directory path.
            parent_session_id: Parent session ID for forks.
            metadata: Additional session metadata.
            owner_api_key: Owning API key for authorization checks.

        Returns:
            Created session.
        """
        # Hash API key for secure storage (Phase 2: API key hashing)
        owner_api_key_hash = hash_api_key(owner_api_key) if owner_api_key else None

        session = Session(
            id=session_id,
            model=model,
            working_directory=working_directory,
            parent_session_id=parent_session_id,
            metadata_=metadata,
            owner_api_key=owner_api_key,  # Keep for backward compatibility during rollout
            owner_api_key_hash=owner_api_key_hash,
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
        """Update a session record atomically.

        Args:
            session_id: Session identifier.
            status: New status value.
            total_turns: Updated turn count.
            total_cost_usd: Updated cost.

        Returns:
            Updated session or None if not found.
        """
        from sqlalchemy import update as sql_update

        # Build update values
        update_values: dict[str, object] = {"updated_at": datetime.now()}

        if status is not None:
            update_values["status"] = status
        if total_turns is not None:
            update_values["total_turns"] = total_turns
        if total_cost_usd is not None:
            update_values["total_cost_usd"] = Decimal(str(total_cost_usd))

        # Atomic update with RETURNING
        stmt = (
            sql_update(Session)
            .where(Session.id == session_id)
            .values(**update_values)
            .returning(Session)
        )

        result = await self._db.execute(stmt)
        await self._db.commit()

        return result.scalar_one_or_none()

    async def update_metadata(
        self,
        session_id: UUID,
        metadata: dict[str, object],
    ) -> Session | None:
        """Update session metadata.

        Args:
            session_id: Session identifier.
            metadata: Metadata payload to store.

        Returns:
            Updated session or None if not found.
        """
        from sqlalchemy import update as sql_update

        stmt = (
            sql_update(Session)
            .where(Session.id == session_id)
            .values(metadata_=metadata, updated_at=datetime.now())
            .returning(Session)
        )

        result = await self._db.execute(stmt)
        await self._db.commit()
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        status: str | None = None,
        owner_api_key: str | None = None,
        limit: int = 50,
        offset: int = 0,
        *,
        filter_by_owner_or_public: bool = False,
    ) -> tuple[Sequence[Session], int]:
        """List sessions with optional filtering.

        Args:
            status: Filter by status.
            owner_api_key: Filter by owner API key (exact match).
            limit: Maximum results.
            offset: Pagination offset.
            filter_by_owner_or_public: If True, returns sessions where
                owner_api_key is NULL (public) OR matches the provided key.
                This is the secure multi-tenant filter.

        Returns:
            Tuple of session list and total count.
        """
        from sqlalchemy import or_

        # Build query
        stmt = select(Session).order_by(Session.created_at.desc())
        count_stmt = select(func.count()).select_from(Session)

        if status:
            stmt = stmt.where(Session.status == status)
            count_stmt = count_stmt.where(Session.status == status)

        # Phase 2: Filter by hashed API key instead of plaintext
        if owner_api_key:
            owner_api_key_hash = hash_api_key(owner_api_key)

            if filter_by_owner_or_public:
                # Secure multi-tenant filter: public sessions OR owned by this key
                owner_filter = or_(
                    Session.owner_api_key_hash.is_(None),
                    Session.owner_api_key_hash == owner_api_key_hash,
                )
                stmt = stmt.where(owner_filter)
                count_stmt = count_stmt.where(owner_filter)
            else:
                # Exact match only
                stmt = stmt.where(Session.owner_api_key_hash == owner_api_key_hash)
                count_stmt = count_stmt.where(
                    Session.owner_api_key_hash == owner_api_key_hash
                )

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

        Raises:
            SessionNotFoundError: If session does not exist.
        """
        try:
            session = await self.get(session_id)
            if session is None:
                raise SessionNotFoundError(str(session_id))

            message = SessionMessage(
                session_id=session_id,
                message_type=message_type,
                content=content,
            )
            self._db.add(message)
            await self._db.commit()
            await self._db.refresh(message)
            return message
        except Exception:
            await self._db.rollback()
            raise

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

        Raises:
            SessionNotFoundError: If session does not exist.
        """
        try:
            session = await self.get(session_id)
            if session is None:
                raise SessionNotFoundError(str(session_id))

            checkpoint = Checkpoint(
                session_id=session_id,
                user_message_uuid=user_message_uuid,
                files_modified=files_modified,
            )
            self._db.add(checkpoint)
            await self._db.commit()
            await self._db.refresh(checkpoint)
            return checkpoint
        except Exception:
            await self._db.rollback()
            raise

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
