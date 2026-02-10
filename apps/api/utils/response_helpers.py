"""Response mapping helpers to eliminate code duplication.

This module provides helper functions to map protocol objects to Pydantic
response models in a type-safe manner, replacing the **obj.__dict__ pattern.
"""

from typing import TypeVar, cast
from datetime import datetime
from typing import Literal

from apps.api.schemas.responses import SessionWithMetaResponse

T = TypeVar("T")


def map_session_with_metadata(
    session: object,
    metadata: dict[str, object] | None = None,
) -> SessionWithMetaResponse:
    """Map session object with metadata to SessionWithMetaResponse.

    Args:
        session: Session object with attributes (id, status, created_at, etc.)
        metadata: Session metadata dictionary containing mode, project_id, etc.
                  If None, extracted from session.session_metadata attribute.

    Returns:
        SessionWithMetaResponse with properly typed fields.
    """
    # Extract metadata from session if not provided
    if metadata is None:
        metadata = cast("dict[str, object]", getattr(session, "session_metadata", {}))
        if metadata is None:
            metadata = {}

    # Extract session attributes
    session_id = str(getattr(session, "id"))
    status_raw = str(getattr(session, "status"))
    created_at = cast("datetime", getattr(session, "created_at"))
    updated_at = cast("datetime", getattr(session, "updated_at"))
    total_turns = int(getattr(session, "total_turns", 0))
    total_cost_raw = getattr(session, "total_cost_usd", None)
    parent_id_raw = getattr(session, "parent_session_id", None)

    # Validate status
    status_val: Literal["active", "completed", "error"]
    if status_raw == "active":
        status_val = "active"
    elif status_raw == "completed":
        status_val = "completed"
    elif status_raw == "error":
        status_val = "error"
    else:
        status_val = "active"

    # Extract metadata fields
    session_mode = metadata.get("mode", "code")
    mode: Literal["brainstorm", "code"] = (
        "brainstorm" if session_mode == "brainstorm" else "code"
    )
    project_id_raw = metadata.get("project_id")
    title_raw = metadata.get("title")
    tags_raw = metadata.get("tags")

    return SessionWithMetaResponse(
        id=session_id,
        mode=mode,
        status=status_val,
        project_id=str(project_id_raw) if project_id_raw else None,
        title=str(title_raw) if title_raw else None,
        created_at=created_at,
        updated_at=updated_at,
        total_turns=total_turns,
        total_cost_usd=float(total_cost_raw) if total_cost_raw is not None else None,
        parent_session_id=str(parent_id_raw) if parent_id_raw else None,
        tags=cast("list[str] | None", tags_raw) if isinstance(tags_raw, list) else None,
        metadata=metadata,
    )


def validate_status_literal(
    status_raw: str,
) -> Literal["active", "completed", "error"]:
    """Validate and convert status string to literal type.

    Args:
        status_raw: Raw status string from database or cache.

    Returns:
        Validated status literal (defaults to "active" for invalid values).
    """
    if status_raw == "active":
        return "active"
    elif status_raw == "completed":
        return "completed"
    elif status_raw == "error":
        return "error"
    else:
        return "active"  # Default to active for invalid values
