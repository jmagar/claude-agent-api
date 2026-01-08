"""Session-related exceptions."""

from apps.api.exceptions.base import APIError


class SessionNotFoundError(APIError):
    """Raised when a session is not found."""

    def __init__(self, session_id: str) -> None:
        """Initialize session not found error.

        Args:
            session_id: The session ID that was not found.
        """
        super().__init__(
            message=f"Session '{session_id}' not found",
            code="SESSION_NOT_FOUND",
            status_code=404,
            details={"session_id": session_id},
        )


class SessionLockedError(APIError):
    """Raised when a session is currently locked by another operation."""

    def __init__(self, session_id: str) -> None:
        """Initialize session locked error.

        Args:
            session_id: The locked session ID.
        """
        super().__init__(
            message=f"Session '{session_id}' is currently in use",
            code="SESSION_LOCKED",
            status_code=409,
            details={"session_id": session_id},
        )


class SessionCompletedError(APIError):
    """Raised when trying to resume a completed or errored session."""

    # Map status values to grammatically correct past-tense forms
    _STATUS_DISPLAY: dict[str, str] = {
        "completed": "completed",
        "error": "errored",
        "active": "active",
    }

    def __init__(self, session_id: str, status: str) -> None:
        """Initialize session completed error.

        Args:
            session_id: The session ID.
            status: Current session status.
        """
        display_status = self._STATUS_DISPLAY.get(status, status)
        super().__init__(
            message=f"Session '{session_id}' has already {display_status}",
            code="SESSION_COMPLETED",
            status_code=400,
            details={"session_id": session_id, "status": status},
        )
