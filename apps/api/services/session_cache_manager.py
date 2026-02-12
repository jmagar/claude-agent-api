"""Redis cache operations for sessions."""

from datetime import datetime
from typing import TYPE_CHECKING

import structlog

from apps.api.types import JsonValue
from apps.api.utils.session_utils import parse_session_status

from .session_models import Session

if TYPE_CHECKING:
    from apps.api.protocols import Cache

logger = structlog.get_logger(__name__)


class SessionCacheManager:
    """Encapsulates cache-aside access patterns for sessions."""

    def __init__(self, cache: "Cache | None", ttl: int) -> None:
        self._cache = cache
        self._ttl = ttl

    def cache_key(self, session_id: str) -> str:
        """Build canonical cache key for a session id."""
        return f"session:{session_id}"

    async def cache_session(self, session: Session) -> None:
        """Write session payload and owner index entries to cache."""
        if self._cache is None:
            return

        data: dict[str, JsonValue] = {
            "id": session.id,
            "model": session.model,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "total_turns": session.total_turns,
            "total_cost_usd": session.total_cost_usd,
            "parent_session_id": session.parent_session_id,
            "owner_api_key_hash": session.owner_api_key_hash,
            "session_metadata": session.session_metadata,
        }

        await self._cache.set_json(self.cache_key(session.id), data, self._ttl)

        if session.owner_api_key_hash:
            owner_index_key = f"session:owner:{session.owner_api_key_hash}"
            await self._cache.add_to_set(owner_index_key, session.id)

    async def get_cached_session(self, session_id: str) -> Session | None:
        """Read and parse a session from cache, deleting corrupt payloads."""
        if self._cache is None:
            return None

        key = self.cache_key(session_id)
        parsed = await self._cache.get_json(key)
        if not parsed:
            return None

        session = self.parse_cached_session(parsed)
        if session is not None:
            return session

        try:
            await self._cache.delete(key)
            logger.info("deleted_corrupted_cache_entry", session_id=session_id)
        except Exception as delete_err:
            logger.warning(
                "failed_to_delete_corrupted_cache",
                session_id=session_id,
                error=str(delete_err),
            )
        return None

    async def list_sessions_for_owner(self, owner_api_key_hash: str) -> list[Session]:
        """Bulk fetch owner-scoped sessions from cache index."""
        if self._cache is None:
            return []

        owner_index_key = f"session:owner:{owner_api_key_hash}"
        session_ids = await self._cache.set_members(owner_index_key)
        keys = [self.cache_key(session_id) for session_id in session_ids]
        cached_rows = await self._cache.get_many_json(keys)

        sessions: list[Session] = []
        for parsed in cached_rows:
            if not parsed:
                continue
            session = self.parse_cached_session(parsed)
            if session is not None:
                sessions.append(session)
        return sessions

    async def list_all_sessions(self, max_keys: int = 1000) -> list[Session]:
        """Scan and bulk fetch all cached sessions."""
        if self._cache is None:
            return []

        all_keys = await self._cache.scan_keys("session:*", max_keys=max_keys)
        # Filter out session:owner:* index keys (they are sets, not session data)
        session_keys = [k for k in all_keys if not k.startswith("session:owner:")]
        cached_rows = await self._cache.get_many_json(session_keys)

        sessions: list[Session] = []
        for parsed in cached_rows:
            if not parsed:
                continue
            session = self.parse_cached_session(parsed)
            if session is not None:
                sessions.append(session)
        return sessions

    async def delete_session(
        self, session_id: str, owner_api_key_hash: str | None
    ) -> bool:
        """Delete session cache entry and owner index membership."""
        if self._cache is None:
            return False

        if owner_api_key_hash:
            owner_index_key = f"session:owner:{owner_api_key_hash}"
            await self._cache.remove_from_set(owner_index_key, session_id)

        return await self._cache.delete(self.cache_key(session_id))

    async def session_exists(self, session_id: str) -> bool:
        """Check whether a session exists in cache."""
        if self._cache is None:
            return False
        return await self._cache.exists(self.cache_key(session_id))

    def parse_cached_session(self, parsed: dict[str, JsonValue]) -> Session | None:
        """Parse cached payload into a typed session model."""
        try:
            created_at_raw = parsed.get("created_at")
            updated_at_raw = parsed.get("updated_at")
            created_at_text = str(created_at_raw) if created_at_raw is not None else ""
            updated_at_text = str(updated_at_raw) if updated_at_raw is not None else ""

            created_dt = datetime.fromisoformat(created_at_text)
            updated_dt = datetime.fromisoformat(updated_at_text)

            total_turns_raw = parsed.get("total_turns", 0)
            if isinstance(total_turns_raw, int):
                total_turns = total_turns_raw
            elif isinstance(total_turns_raw, (str, float)):
                total_turns = int(total_turns_raw)
            else:
                total_turns = 0

            total_cost_raw = parsed.get("total_cost_usd")
            if total_cost_raw is None:
                total_cost = None
            elif isinstance(total_cost_raw, (int, float, str)):
                total_cost = float(total_cost_raw)
            else:
                total_cost = None

            metadata_raw = parsed.get("session_metadata")
            metadata = metadata_raw if isinstance(metadata_raw, dict) else None

            status_raw = str(parsed.get("status", "active"))
            return Session(
                id=str(parsed["id"]),
                model=str(parsed["model"]),
                status=parse_session_status(status_raw),
                created_at=created_dt,
                updated_at=updated_dt,
                total_turns=total_turns,
                total_cost_usd=total_cost,
                parent_session_id=(
                    str(parsed["parent_session_id"])
                    if parsed.get("parent_session_id") is not None
                    else None
                ),
                owner_api_key_hash=(
                    str(parsed["owner_api_key_hash"])
                    if parsed.get("owner_api_key_hash") is not None
                    else None
                ),
                session_metadata=metadata,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(
                "cache_parse_failed",
                error=str(e),
                safe_fields={
                    "session_id": parsed.get("id"),
                    "status": parsed.get("status"),
                },
                error_id="ERR_CACHE_PARSE_FAILED",
            )
            return None
