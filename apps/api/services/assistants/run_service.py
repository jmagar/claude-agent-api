"""Service for managing OpenAI-compatible runs.

Runs represent executions of an assistant on a thread.
"""

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal, Protocol, TypedDict, cast, runtime_checkable

import structlog

from apps.api.config import get_settings
from apps.api.types import JsonValue

if TYPE_CHECKING:
    from apps.api.protocols import Cache

logger = structlog.get_logger(__name__)


# Type alias for run status
RunStatus = Literal[
    "queued",
    "in_progress",
    "requires_action",
    "cancelling",
    "cancelled",
    "failed",
    "completed",
    "expired",
]


def generate_run_id() -> str:
    """Generate a unique run ID in OpenAI format.

    Returns:
        str: ID in format 'run_' followed by 24 random alphanumeric characters.
    """
    random_suffix = secrets.token_hex(12)
    return f"run_{random_suffix}"


# =============================================================================
# Tool Call Types
# =============================================================================


class FunctionCall(TypedDict):
    """Function call details."""

    name: str
    arguments: str


class ToolCall(TypedDict):
    """Tool call in a run."""

    id: str
    type: Literal["function"]
    function: FunctionCall


class SubmitToolOutputs(TypedDict):
    """Submit tool outputs structure."""

    tool_calls: list[ToolCall]


class RequiredAction(TypedDict):
    """Required action for tool calls."""

    type: Literal["submit_tool_outputs"]
    submit_tool_outputs: SubmitToolOutputs


class RunError(TypedDict):
    """Run error details."""

    code: str
    message: str


class RunUsage(TypedDict):
    """Token usage for run."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


# =============================================================================
# Repository Protocol
# =============================================================================


@runtime_checkable
class RunRepository(Protocol):
    """Protocol for run database repository."""

    async def create(
        self,
        run_id: str,
        thread_id: str,
        assistant_id: str,
        status: str,
        model: str,
        instructions: str | None,
        tools: list[dict[str, object]],
        metadata: dict[str, str],
    ) -> None:
        """Create run in database."""
        ...

    async def get(self, run_id: str) -> object | None:
        """Get run by ID."""
        ...

    async def list_runs(
        self,
        thread_id: str,
        limit: int = 20,
        offset: int = 0,
        order: str = "desc",
    ) -> tuple[list[object], int]:
        """List runs for a thread."""
        ...

    async def update(
        self,
        run_id: str,
        status: str | None = None,
        required_action: dict[str, object] | None = None,
        last_error: dict[str, str] | None = None,
        usage: dict[str, int] | None = None,
    ) -> bool:
        """Update run. Returns True if updated."""
        ...


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class Run:
    """Run data model.

    Represents an execution of an assistant on a thread.
    """

    id: str  # run_xxx format
    thread_id: str
    assistant_id: str
    created_at: int  # Unix timestamp
    status: RunStatus
    model: str
    instructions: str | None = None
    tools: list[dict[str, object]] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    required_action: RequiredAction | None = None
    last_error: RunError | None = None
    usage: RunUsage | None = None
    started_at: int | None = None
    expires_at: int | None = None
    cancelled_at: int | None = None
    failed_at: int | None = None
    completed_at: int | None = None


@dataclass
class RunListResult:
    """Result of listing runs with pagination."""

    data: list[Run]
    first_id: str | None
    last_id: str | None
    has_more: bool


# =============================================================================
# Service
# =============================================================================


class RunService:
    """Service for managing runs.

    Handles the run lifecycle and state machine:
    - queued → in_progress → completed
    - in_progress → requires_action → (submit) → in_progress
    - in_progress → failed
    - in_progress → cancelled
    - in_progress → expired
    """

    def __init__(
        self,
        cache: "Cache | None" = None,
        db_repo: RunRepository | None = None,
    ) -> None:
        """Initialize run service.

        Args:
            cache: Cache instance for fast lookups.
            db_repo: Database repository for persistence.
        """
        self._cache = cache
        self._db_repo = db_repo
        settings = get_settings()
        self._ttl = settings.redis_session_ttl

    def _cache_key(self, thread_id: str, run_id: str) -> str:
        """Generate cache key for a run."""
        return f"run:{thread_id}:{run_id}"

    async def create_run(
        self,
        thread_id: str,
        assistant_id: str,
        model: str,
        instructions: str | None = None,
        tools: list[dict[str, object]] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Run:
        """Create a new run.

        Args:
            thread_id: Thread ID to run on.
            assistant_id: Assistant ID to use.
            model: Model to use.
            instructions: Instructions override.
            tools: Tools override.
            metadata: Run metadata.

        Returns:
            Created run in queued state.
        """
        run_id = generate_run_id()
        now = datetime.now(UTC)
        created_at = int(now.timestamp())

        run = Run(
            id=run_id,
            thread_id=thread_id,
            assistant_id=assistant_id,
            created_at=created_at,
            status="queued",
            model=model,
            instructions=instructions,
            tools=tools if tools is not None else [],
            metadata=metadata if metadata is not None else {},
        )

        # Persist to database
        if self._db_repo:
            await self._db_repo.create(
                run_id=run_id,
                thread_id=thread_id,
                assistant_id=assistant_id,
                status="queued",
                model=model,
                instructions=instructions,
                tools=run.tools,
                metadata=run.metadata,
            )

        # Cache
        await self._cache_run(run)

        logger.info(
            "Run created",
            run_id=run_id,
            thread_id=thread_id,
            assistant_id=assistant_id,
        )

        return run

    async def get_run(
        self,
        thread_id: str,
        run_id: str,
    ) -> Run | None:
        """Get a run by ID.

        Args:
            thread_id: Thread ID containing the run.
            run_id: Run ID to retrieve.

        Returns:
            Run if found, None otherwise.
        """
        return await self._get_cached_run(thread_id, run_id)

    async def list_runs(
        self,
        thread_id: str,
        limit: int = 20,
        order: str = "desc",
    ) -> RunListResult:
        """List runs for a thread.

        Args:
            thread_id: Thread ID to list runs from.
            limit: Maximum number of results.
            order: Sort order.

        Returns:
            Paginated run list.
        """
        if not self._cache:
            return RunListResult(
                data=[],
                first_id=None,
                last_id=None,
                has_more=False,
            )

        # Scan for runs in this thread
        pattern = f"run:{thread_id}:*"
        keys = await self._cache.scan_keys(pattern)

        if not keys:
            return RunListResult(
                data=[],
                first_id=None,
                last_id=None,
                has_more=False,
            )

        # Fetch all runs
        cached_rows = await self._cache.get_many_json(keys)

        runs: list[Run] = []
        for parsed in cached_rows:
            if parsed:
                run = self._parse_cached_run(parsed)
                if run:
                    runs.append(run)

        # Sort
        reverse = order == "desc"
        runs.sort(key=lambda r: r.created_at, reverse=reverse)

        # Paginate
        has_more = len(runs) > limit
        runs = runs[:limit]

        return RunListResult(
            data=runs,
            first_id=runs[0].id if runs else None,
            last_id=runs[-1].id if runs else None,
            has_more=has_more,
        )

    async def start_run(
        self,
        thread_id: str,
        run_id: str,
    ) -> Run | None:
        """Start a run (transition from queued to in_progress).

        Args:
            thread_id: Thread ID.
            run_id: Run ID.

        Returns:
            Updated run or None if not found.
        """
        run = await self.get_run(thread_id, run_id)
        if not run:
            return None

        if run.status != "queued":
            logger.warning(
                "Cannot start run: not in queued state",
                run_id=run_id,
                current_status=run.status,
            )
            return run

        run.status = "in_progress"
        run.started_at = int(datetime.now(UTC).timestamp())

        await self._update_run(run)

        logger.info("Run started", run_id=run_id)
        return run

    async def complete_run(
        self,
        thread_id: str,
        run_id: str,
        usage: RunUsage | None = None,
    ) -> Run | None:
        """Complete a run.

        Args:
            thread_id: Thread ID.
            run_id: Run ID.
            usage: Token usage statistics.

        Returns:
            Updated run or None if not found.
        """
        run = await self.get_run(thread_id, run_id)
        if not run:
            return None

        run.status = "completed"
        run.completed_at = int(datetime.now(UTC).timestamp())
        if usage:
            run.usage = usage

        await self._update_run(run)

        logger.info("Run completed", run_id=run_id)
        return run

    async def fail_run(
        self,
        thread_id: str,
        run_id: str,
        error: RunError,
    ) -> Run | None:
        """Fail a run.

        Args:
            thread_id: Thread ID.
            run_id: Run ID.
            error: Error details.

        Returns:
            Updated run or None if not found.
        """
        run = await self.get_run(thread_id, run_id)
        if not run:
            return None

        run.status = "failed"
        run.failed_at = int(datetime.now(UTC).timestamp())
        run.last_error = error

        await self._update_run(run)

        logger.info("Run failed", run_id=run_id, error=error)
        return run

    async def cancel_run(
        self,
        thread_id: str,
        run_id: str,
    ) -> Run | None:
        """Cancel a run.

        Args:
            thread_id: Thread ID.
            run_id: Run ID.

        Returns:
            Updated run or None if not found.
        """
        run = await self.get_run(thread_id, run_id)
        if not run:
            return None

        # Can only cancel queued or in_progress runs
        if run.status not in ("queued", "in_progress", "requires_action"):
            logger.warning(
                "Cannot cancel run: invalid state",
                run_id=run_id,
                current_status=run.status,
            )
            return run

        run.status = "cancelled"
        run.cancelled_at = int(datetime.now(UTC).timestamp())

        await self._update_run(run)

        logger.info("Run cancelled", run_id=run_id)
        return run

    async def require_action(
        self,
        thread_id: str,
        run_id: str,
        tool_calls: list[ToolCall],
    ) -> Run | None:
        """Set run to requires_action state.

        Args:
            thread_id: Thread ID.
            run_id: Run ID.
            tool_calls: Tool calls requiring responses.

        Returns:
            Updated run or None if not found.
        """
        run = await self.get_run(thread_id, run_id)
        if not run:
            return None

        run.status = "requires_action"
        run.required_action = {
            "type": "submit_tool_outputs",
            "submit_tool_outputs": {"tool_calls": tool_calls},
        }

        await self._update_run(run)

        logger.info(
            "Run requires action",
            run_id=run_id,
            tool_call_count=len(tool_calls),
        )
        return run

    async def submit_tool_outputs(
        self,
        thread_id: str,
        run_id: str,
    ) -> Run | None:
        """Resume run after tool outputs submitted.

        Args:
            thread_id: Thread ID.
            run_id: Run ID.

        Returns:
            Updated run or None if not found.
        """
        run = await self.get_run(thread_id, run_id)
        if not run:
            return None

        if run.status != "requires_action":
            logger.warning(
                "Cannot submit tool outputs: not in requires_action state",
                run_id=run_id,
                current_status=run.status,
            )
            return run

        run.status = "in_progress"
        run.required_action = None

        await self._update_run(run)

        logger.info("Run resumed after tool outputs", run_id=run_id)
        return run

    async def _update_run(self, run: Run) -> None:
        """Update run in cache and database."""
        # Update cache
        await self._cache_run(run)

        # Update database
        if self._db_repo:
            await self._db_repo.update(
                run_id=run.id,
                status=run.status,
                required_action=dict(run.required_action)
                if run.required_action
                else None,
                last_error=dict(run.last_error) if run.last_error else None,
                usage=dict(run.usage) if run.usage else None,
            )

    async def _cache_run(self, run: Run) -> None:
        """Cache a run in Redis."""
        if not self._cache:
            return

        key = self._cache_key(run.thread_id, run.id)

        # Serialize tools
        tools_json: list[JsonValue] = [dict(t) for t in run.tools]

        data: dict[str, JsonValue] = {
            "id": run.id,
            "thread_id": run.thread_id,
            "assistant_id": run.assistant_id,
            "created_at": run.created_at,
            "status": run.status,
            "model": run.model,
            "instructions": run.instructions,
            "tools": tools_json,
            "metadata": run.metadata,
            "required_action": dict(run.required_action)
            if run.required_action
            else None,
            "last_error": dict(run.last_error) if run.last_error else None,
            "usage": dict(run.usage) if run.usage else None,
            "started_at": run.started_at,
            "expires_at": run.expires_at,
            "cancelled_at": run.cancelled_at,
            "failed_at": run.failed_at,
            "completed_at": run.completed_at,
        }

        await self._cache.set_json(key, data, self._ttl)

    async def _get_cached_run(
        self,
        thread_id: str,
        run_id: str,
    ) -> Run | None:
        """Get a run from cache."""
        if not self._cache:
            return None

        key = self._cache_key(thread_id, run_id)
        parsed = await self._cache.get_json(key)

        if not parsed:
            return None

        return self._parse_cached_run(parsed)

    def _parse_cached_run(
        self,
        parsed: dict[str, JsonValue],
    ) -> Run | None:
        """Parse cached run data into Run object."""
        try:
            run_id = str(parsed["id"])
            thread_id = str(parsed["thread_id"])
            assistant_id = str(parsed["assistant_id"])

            created_at_val = parsed.get("created_at", 0)
            if isinstance(created_at_val, (int, float)):
                created_at = int(created_at_val)
            else:
                created_at = 0

            status_val = str(parsed.get("status", "queued"))
            status: RunStatus = "queued"
            if status_val in (
                "queued",
                "in_progress",
                "requires_action",
                "cancelling",
                "cancelled",
                "failed",
                "completed",
                "expired",
            ):
                status = cast("RunStatus", status_val)

            model = str(parsed.get("model", ""))
            instructions_raw = parsed.get("instructions")
            instructions = str(instructions_raw) if instructions_raw else None

            # Parse tools
            tools_raw = parsed.get("tools", [])
            tools: list[dict[str, object]] = []
            if isinstance(tools_raw, list):
                for tool in tools_raw:
                    if isinstance(tool, dict):
                        tools.append(dict(tool))

            # Parse metadata
            metadata_raw = parsed.get("metadata", {})
            metadata: dict[str, str] = {}
            if isinstance(metadata_raw, dict):
                for k, v in metadata_raw.items():
                    if isinstance(k, str) and isinstance(v, str):
                        metadata[k] = v

            # Parse optional fields
            required_action_raw = parsed.get("required_action")
            required_action: RequiredAction | None = None
            if isinstance(required_action_raw, dict):
                required_action = cast("RequiredAction", required_action_raw)

            last_error_raw = parsed.get("last_error")
            last_error: RunError | None = None
            if isinstance(last_error_raw, dict):
                last_error = cast("RunError", last_error_raw)

            usage_raw = parsed.get("usage")
            usage: RunUsage | None = None
            if isinstance(usage_raw, dict):
                usage = cast("RunUsage", usage_raw)

            # Parse timestamps
            def parse_timestamp(val: JsonValue) -> int | None:
                if isinstance(val, (int, float)):
                    return int(val)
                return None

            return Run(
                id=run_id,
                thread_id=thread_id,
                assistant_id=assistant_id,
                created_at=created_at,
                status=status,
                model=model,
                instructions=instructions,
                tools=tools,
                metadata=metadata,
                required_action=required_action,
                last_error=last_error,
                usage=usage,
                started_at=parse_timestamp(parsed.get("started_at")),
                expires_at=parse_timestamp(parsed.get("expires_at")),
                cancelled_at=parse_timestamp(parsed.get("cancelled_at")),
                failed_at=parse_timestamp(parsed.get("failed_at")),
                completed_at=parse_timestamp(parsed.get("completed_at")),
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(
                "Failed to parse cached run",
                error=str(e),
            )
            return None
