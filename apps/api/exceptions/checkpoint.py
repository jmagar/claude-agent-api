"""Checkpoint-related exceptions."""

from apps.api.exceptions.base import APIError


class CheckpointNotFoundError(APIError):
    """Raised when a checkpoint is not found."""

    def __init__(self, checkpoint_id: str) -> None:
        """Initialize checkpoint not found error.

        Args:
            checkpoint_id: The checkpoint ID that was not found.
        """
        super().__init__(
            message=f"Checkpoint '{checkpoint_id}' not found",
            code="CHECKPOINT_NOT_FOUND",
            status_code=404,
            details={"checkpoint_id": checkpoint_id},
        )


class InvalidCheckpointError(APIError):
    """Raised when a checkpoint is invalid for the requested operation."""

    def __init__(
        self, checkpoint_id: str, session_id: str, reason: str | None = None
    ) -> None:
        """Initialize invalid checkpoint error.

        Args:
            checkpoint_id: The checkpoint ID.
            session_id: The session ID.
            reason: Optional reason for invalidity.
        """
        msg = reason or f"Checkpoint '{checkpoint_id}' is not valid for session"
        super().__init__(
            message=msg,
            code="INVALID_CHECKPOINT",
            status_code=400,
            details={"checkpoint_id": checkpoint_id, "session_id": session_id},
        )
