"""Session utility functions for status parsing and validation.

This module provides helper functions for normalizing and validating session
status values. It's separate from response_helpers to avoid circular imports.
"""

from typing import Literal


def parse_session_status(status_raw: str) -> Literal["active", "completed", "error"]:
    """Normalize potentially-invalid status values into a valid session status.

    Args:
        status_raw: Raw status string from database or cache.

    Returns:
        Validated session status (active, completed, or error).
    """
    if status_raw == "completed":
        return "completed"
    if status_raw == "error":
        return "error"
    return "active"
