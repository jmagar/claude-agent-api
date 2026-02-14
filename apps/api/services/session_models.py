"""Shared session service models and parsing helpers."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, TypedDict

from apps.api.types import JsonValue

SessionStatus = Literal["active", "completed", "error"]


class CachedSessionData(TypedDict):
    """TypedDict for session data stored in Redis cache."""

    id: str
    model: str
    status: SessionStatus
    created_at: str
    updated_at: str
    total_turns: int
    total_cost_usd: float | None
    parent_session_id: str | None
    owner_api_key_hash: str | None
    session_metadata: dict[str, JsonValue] | None


@dataclass
class Session:
    """Session data model for service operations."""

    id: str
    model: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    total_turns: int = 0
    total_cost_usd: float | None = None
    parent_session_id: str | None = None
    owner_api_key_hash: str | None = None
    session_metadata: dict[str, JsonValue] | None = None


@dataclass
class SessionListResult:
    """Result of listing sessions."""

    sessions: list[Session]
    total: int
    page: int
    page_size: int
