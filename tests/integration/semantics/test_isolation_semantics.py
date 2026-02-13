"""Cross-tenant isolation tests for Phase 2 semantic validation.

Validates that API key A cannot access API key B's resources.
All cross-tenant access returns 404 (not 403) to prevent enumeration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient
