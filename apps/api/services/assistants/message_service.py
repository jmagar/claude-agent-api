"""Service for managing OpenAI-compatible thread messages.

Messages are stored in Redis cache with thread association.
"""

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal, TypedDict

import structlog

from apps.api.config import get_settings
from apps.api.types import JsonValue

if TYPE_CHECKING:
    from apps.api.protocols import Cache

logger = structlog.get_logger(__name__)


def generate_message_id() -> str:
    """Generate a unique message ID in OpenAI format.

    Returns:
        str: ID in format 'msg_' followed by 24 random alphanumeric characters.
    """
    random_suffix = secrets.token_hex(12)
    return f"msg_{random_suffix}"


# =============================================================================
# Content Types
# =============================================================================


class TextContent(TypedDict):
    """Text content value."""

    value: str
    annotations: list[dict[str, str | int]]


class MessageTextContent(TypedDict):
    """Text content block."""

    type: Literal["text"]
    text: TextContent


class ImageFileDetail(TypedDict):
    """Image file details."""

    file_id: str


class MessageImageFileContent(TypedDict):
    """Image file content block."""

    type: Literal["image_file"]
    image_file: ImageFileDetail


MessageContent = MessageTextContent | MessageImageFileContent


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class Message:
    """Message data model.

    Maps to OpenAI's thread message object.
    """

    id: str  # msg_xxx format
    thread_id: str
    created_at: int  # Unix timestamp
    role: Literal["user", "assistant"]
    content: list[MessageContent]
    metadata: dict[str, str] = field(default_factory=dict)
    # Optional fields for assistant messages
    assistant_id: str | None = None
    run_id: str | None = None


@dataclass
class MessageListResult:
    """Result of listing messages with pagination."""

    data: list[Message]
    first_id: str | None
    last_id: str | None
    has_more: bool


# =============================================================================
# Service
# =============================================================================


class MessageService:
    """Service for managing thread messages."""

    def __init__(
        self,
        cache: "Cache | None" = None,
    ) -> None:
        """Initialize message service.

        Args:
            cache: Cache instance for storage.
        """
        self._cache = cache
        settings = get_settings()
        self._ttl = settings.redis_session_ttl

    def _cache_key(self, thread_id: str, message_id: str) -> str:
        """Generate cache key for a message."""
        return f"message:{thread_id}:{message_id}"

    async def create_message(
        self,
        thread_id: str,
        role: Literal["user", "assistant"],
        content: str,
        metadata: dict[str, str] | None = None,
        assistant_id: str | None = None,
        run_id: str | None = None,
    ) -> Message:
        """Create a new message in a thread.

        Args:
            thread_id: Thread ID to add message to.
            role: Message role ("user" or "assistant").
            content: Text content of the message.
            metadata: Key-value metadata.
            assistant_id: Assistant ID (for assistant messages).
            run_id: Run ID (for assistant messages).

        Returns:
            Created message.
        """
        message_id = generate_message_id()
        now = datetime.now(UTC)
        created_at = int(now.timestamp())

        # Create text content block
        text_content: MessageTextContent = {
            "type": "text",
            "text": {"value": content, "annotations": []},
        }

        message = Message(
            id=message_id,
            thread_id=thread_id,
            created_at=created_at,
            role=role,
            content=[text_content],
            metadata=metadata if metadata is not None else {},
            assistant_id=assistant_id,
            run_id=run_id,
        )

        # Cache the message
        await self._cache_message(message)

        logger.info(
            "Message created",
            message_id=message_id,
            thread_id=thread_id,
            role=role,
        )

        return message

    async def get_message(
        self,
        thread_id: str,
        message_id: str,
    ) -> Message | None:
        """Get a message by ID.

        Args:
            thread_id: Thread ID containing the message.
            message_id: Message ID to retrieve.

        Returns:
            Message if found, None otherwise.
        """
        return await self._get_cached_message(thread_id, message_id)

    async def list_messages(
        self,
        thread_id: str,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
        before: str | None = None,
    ) -> MessageListResult:
        """List messages in a thread.

        Args:
            thread_id: Thread ID to list messages from.
            limit: Maximum number of results.
            order: Sort order ("asc" or "desc").
            after: Cursor for pagination.
            before: Cursor for pagination.

        Returns:
            Paginated message list.
        """
        _ = (after, before)
        if not self._cache:
            return MessageListResult(
                data=[],
                first_id=None,
                last_id=None,
                has_more=False,
            )

        # Scan for messages in this thread
        pattern = f"message:{thread_id}:*"
        keys = await self._cache.scan_keys(pattern)

        if not keys:
            return MessageListResult(
                data=[],
                first_id=None,
                last_id=None,
                has_more=False,
            )

        # Fetch all messages
        cached_rows = await self._cache.get_many_json(keys)

        messages: list[Message] = []
        for parsed in cached_rows:
            if parsed:
                message = self._parse_cached_message(parsed)
                if message:
                    messages.append(message)

        # Sort by created_at
        reverse = order == "desc"
        messages.sort(key=lambda m: m.created_at, reverse=reverse)

        # Apply cursor pagination
        # TODO: Implement proper cursor-based pagination
        has_more = len(messages) > limit
        messages = messages[:limit]

        return MessageListResult(
            data=messages,
            first_id=messages[0].id if messages else None,
            last_id=messages[-1].id if messages else None,
            has_more=has_more,
        )

    async def modify_message(
        self,
        thread_id: str,
        message_id: str,
        metadata: dict[str, str] | None = None,
    ) -> Message | None:
        """Modify a message's metadata.

        Args:
            thread_id: Thread ID containing the message.
            message_id: Message ID to modify.
            metadata: New metadata (replaces existing).

        Returns:
            Modified message or None if not found.
        """
        message = await self.get_message(thread_id, message_id)
        if not message:
            return None

        if metadata is not None:
            message.metadata = metadata

        # Update cache
        await self._cache_message(message)

        logger.info(
            "Message modified",
            message_id=message_id,
            thread_id=thread_id,
        )

        return message

    async def _cache_message(self, message: Message) -> None:
        """Cache a message in Redis."""
        if not self._cache:
            return

        key = self._cache_key(message.thread_id, message.id)

        # Serialize content blocks
        content_json: list[JsonValue] = []
        for block in message.content:
            content_json.append(dict(block))

        data: dict[str, JsonValue] = {
            "id": message.id,
            "thread_id": message.thread_id,
            "created_at": message.created_at,
            "role": message.role,
            "content": content_json,
            "metadata": message.metadata,
            "assistant_id": message.assistant_id,
            "run_id": message.run_id,
        }

        await self._cache.set_json(key, data, self._ttl)

    async def _get_cached_message(
        self,
        thread_id: str,
        message_id: str,
    ) -> Message | None:
        """Get a message from cache."""
        if not self._cache:
            return None

        key = self._cache_key(thread_id, message_id)
        parsed = await self._cache.get_json(key)

        if not parsed:
            return None

        return self._parse_cached_message(parsed)

    def _parse_cached_message(
        self,
        parsed: dict[str, JsonValue],
    ) -> Message | None:
        """Parse cached message data into Message object."""
        try:
            message_id = str(parsed["id"])
            thread_id = str(parsed["thread_id"])

            created_at_val = parsed.get("created_at", 0)
            if isinstance(created_at_val, (int, float)):
                created_at = int(created_at_val)
            else:
                created_at = 0

            role_val = str(parsed["role"])
            role: Literal["user", "assistant"] = (
                "user" if role_val == "user" else "assistant"
            )

            # Parse content blocks
            content_raw = parsed.get("content", [])
            content: list[MessageContent] = []
            if isinstance(content_raw, list):
                for block in content_raw:
                    if isinstance(block, dict):
                        block_type = block.get("type")
                        if block_type == "text":
                            text_data = block.get("text", {})
                            if isinstance(text_data, dict):
                                text_block: MessageTextContent = {
                                    "type": "text",
                                    "text": {
                                        "value": str(text_data.get("value", "")),
                                        "annotations": [],
                                    },
                                }
                                content.append(text_block)

            # Parse metadata
            metadata_raw = parsed.get("metadata", {})
            metadata: dict[str, str] = {}
            if isinstance(metadata_raw, dict):
                for k, v in metadata_raw.items():
                    if isinstance(k, str) and isinstance(v, str):
                        metadata[k] = v

            assistant_id_raw = parsed.get("assistant_id")
            assistant_id = str(assistant_id_raw) if assistant_id_raw else None

            run_id_raw = parsed.get("run_id")
            run_id = str(run_id_raw) if run_id_raw else None

            return Message(
                id=message_id,
                thread_id=thread_id,
                created_at=created_at,
                role=role,
                content=content,
                metadata=metadata,
                assistant_id=assistant_id,
                run_id=run_id,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(
                "Failed to parse cached message",
                error=str(e),
            )
            return None
