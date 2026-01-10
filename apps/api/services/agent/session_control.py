"""<summary>Session control actions for AgentService.</summary>"""

from typing import Literal

import structlog

from apps.api.services.agent.session_tracker import AgentSessionTracker

logger = structlog.get_logger(__name__)


class SessionControl:
    """<summary>Controls session-level operations.</summary>"""

    def __init__(self, session_tracker: AgentSessionTracker) -> None:
        """<summary>Initialize with a session tracker.</summary>"""
        self._session_tracker = session_tracker

    async def _require_active(self, session_id: str) -> bool:
        """<summary>Return True if session is active, log otherwise.</summary>"""
        is_active = await self._session_tracker.is_active(session_id)
        if not is_active:
            logger.info("Session is not active", session_id=session_id)
            return False
        return True

    async def interrupt(self, session_id: str) -> bool:
        """<summary>Interrupt a running session.</summary>"""
        if not await self._require_active(session_id):
            return False

        await self._session_tracker.mark_interrupted(session_id)
        logger.info("Interrupt signal sent", session_id=session_id)
        return True

    async def submit_answer(self, session_id: str, answer: str) -> bool:
        """<summary>Submit an answer to a pending question.</summary>"""
        if not await self._require_active(session_id):
            return False

        logger.info(
            "Answer submitted for session",
            session_id=session_id,
            answer_length=len(answer),
        )
        return True

    async def update_permission_mode(
        self,
        session_id: str,
        permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"],
    ) -> bool:
        """<summary>Update permission mode for an active session.</summary>"""
        if not await self._require_active(session_id):
            return False

        logger.info(
            "Permission mode updated for session",
            session_id=session_id,
            new_permission_mode=permission_mode,
        )
        return True
