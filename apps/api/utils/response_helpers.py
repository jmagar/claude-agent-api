"""Response mapping helpers to eliminate code duplication.

This module provides helper functions to map protocol objects to Pydantic
response models in a type-safe manner, replacing the **obj.__dict__ pattern.
"""

from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Literal, Protocol, cast

from apps.api.utils.session_utils import parse_session_status

if TYPE_CHECKING:
    from apps.api.schemas.responses import SessionWithMetaResponse


class _SessionLike(Protocol):
    id: object
    status: object
    created_at: datetime
    updated_at: datetime
    total_turns: object
    total_cost_usd: object
    parent_session_id: object
    session_metadata: Mapping[str, object] | None


def map_session_with_metadata(
    session: object,
    metadata: Mapping[str, object] | None = None,
) -> "SessionWithMetaResponse":
    """Map session object with metadata to SessionWithMetaResponse.

    Args:
        session: Session object with attributes (id, status, created_at, etc.)
        metadata: Session metadata dictionary containing mode, project_id, etc.
                  If None, extracted from session.session_metadata attribute.

    Returns:
        SessionWithMetaResponse with properly typed fields.
    """
    # Import locally to avoid circular import
    from apps.api.schemas.responses import SessionWithMetaResponse

    # Extract metadata from session if not provided
    session_obj = cast("_SessionLike", session)
    if metadata is None:
        metadata = session_obj.session_metadata
        if metadata is None:
            metadata = {}

    # Extract session attributes
    # Note: Protocol declares fields as object, but we know runtime types
    # Use getattr with defaults for type checker compatibility
    session_id = str(session_obj.id)
    status_raw = str(session_obj.status)
    created_at = session_obj.created_at
    updated_at = session_obj.updated_at
    total_turns = int(getattr(session_obj, "total_turns", 0))
    total_cost_raw = getattr(session_obj, "total_cost_usd", None)
    parent_id_raw = getattr(session_obj, "parent_session_id", None)

    # Validate status
    status_val = parse_session_status(status_raw)

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
        metadata=dict(metadata),
    )
