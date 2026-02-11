"""Session metadata merge helpers."""

from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from apps.api.types import JsonValue

if TYPE_CHECKING:
    from apps.api.adapters.session_repo import SessionRepository

logger = structlog.get_logger(__name__)


class SessionMetadataManager:
    """Handles metadata lookups used by promote/tag update flows."""

    def __init__(self, db_repo: "SessionRepository | None") -> None:
        self._db_repo = db_repo

    async def get_session_metadata_for_update(self, session_id: str) -> dict[str, JsonValue]:
        """Fetch existing metadata payload from DB source-of-truth."""
        if self._db_repo is None:
            return {}

        try:
            db_session = await self._db_repo.get(UUID(session_id))
        except ValueError as e:
            logger.debug(
                "invalid_uuid_format_in_metadata_fetch",
                session_id=session_id,
                error=str(e),
            )
            return {}
        except TypeError as e:
            logger.error(
                "uuid_type_error_in_metadata_fetch",
                session_id=session_id,
                session_id_type=type(session_id).__name__,
                error=str(e),
                error_id="ERR_UUID_TYPE_ERROR",
                exc_info=True,
            )
            raise

        if db_session and db_session.session_metadata is not None:
            return dict(db_session.session_metadata)
        return {}
