"""OpenAI streaming adapter for Claude Agent SDK events."""

import time
import uuid
from collections.abc import AsyncGenerator

import structlog

from apps.api.schemas.openai.responses import (
    OpenAIDelta,
    OpenAIStreamChunk,
)
from apps.api.types import (
    MessageEventDataDict,
    ResultEventDataDict,
)

logger = structlog.get_logger(__name__)


class StreamingAdapter:
    """Adapts Claude Agent SDK streaming events to OpenAI streaming format.

    Transforms native SDK events (init, partial, result, etc.) into OpenAI
    chat completion chunks with delta objects. Maintains consistent completion
    ID across all chunks and yields [DONE] marker at end.

    Args:
        original_model: Original OpenAI model name from request (e.g., "gpt-4").
        completion_id: Optional custom completion ID. If not provided, generates
            a new ID with format "chatcmpl-{uuid}".

    Example:
        adapter = StreamingAdapter(original_model="gpt-4")
        async for chunk in adapter.adapt_stream(native_events):
            yield chunk  # OpenAIStreamChunk or "[DONE]"
    """

    def __init__(self, original_model: str, completion_id: str | None = None) -> None:
        """Initialize streaming adapter.

        Args:
            original_model: Original OpenAI model name (e.g., "gpt-4").
            completion_id: Optional custom completion ID. If None, generates new ID.
        """
        self.original_model = original_model
        self.completion_id = completion_id or f"chatcmpl-{uuid.uuid4()}"
        self.first_chunk = True

    async def adapt_stream(
        self,
        native_events: AsyncGenerator[
            tuple[str, MessageEventDataDict | ResultEventDataDict], None
        ],
    ) -> AsyncGenerator[OpenAIStreamChunk | str, None]:
        """Transform native SDK events to OpenAI streaming chunks.

        Args:
            native_events: Async generator of (event_type, event_data) tuples.

        Yields:
            OpenAIStreamChunk: Streaming chunk with delta object.
            str: "[DONE]" marker at end of stream.

        Example:
            async for event_type, event_data in native_events:
                if event_type == "partial":
                    yield chunk with delta.content
                elif event_type == "result":
                    yield chunk with finish_reason
        """
        logger.info(
            "Starting stream adaptation",
            completion_id=self.completion_id,
            original_model=self.original_model,
        )

        created_timestamp = int(time.time())
        chunk_count = 0

        async for event_type, event_data in native_events:
            # First chunk: yield role delta
            if self.first_chunk:
                self.first_chunk = False
                role_delta: OpenAIDelta = {"role": "assistant"}
                role_chunk: OpenAIStreamChunk = {
                    "id": self.completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_timestamp,
                    "model": self.original_model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": role_delta,
                            "finish_reason": None,
                        }
                    ],
                }
                yield role_chunk

            # Handle partial events (content deltas)
            if event_type == "partial":
                partial_data = event_data
                if isinstance(partial_data, dict) and "content" in partial_data:
                    content_blocks = partial_data.get("content", [])
                    if isinstance(content_blocks, list):
                        # Extract text from text blocks
                        for block in content_blocks:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text = block.get("text", "")
                                if text:
                                    content_delta: OpenAIDelta = {"content": text}
                                    content_chunk: OpenAIStreamChunk = {
                                        "id": self.completion_id,
                                        "object": "chat.completion.chunk",
                                        "created": created_timestamp,
                                        "model": self.original_model,
                                        "choices": [
                                            {
                                                "index": 0,
                                                "delta": content_delta,
                                                "finish_reason": None,
                                            }
                                        ],
                                    }
                                    yield content_chunk
                                    chunk_count += 1
                                    logger.debug(
                                        "Yielded content chunk",
                                        completion_id=self.completion_id,
                                        text_length=len(text),
                                    )

            # Handle result events (finish reason)
            elif event_type == "result":
                result_data = event_data
                if isinstance(result_data, dict):
                    is_error = result_data.get("is_error", False)
                    finish_reason = "error" if is_error else "stop"

                    # Empty delta with finish_reason
                    finish_delta: OpenAIDelta = {}
                    finish_chunk: OpenAIStreamChunk = {
                        "id": self.completion_id,
                        "object": "chat.completion.chunk",
                        "created": created_timestamp,
                        "model": self.original_model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": finish_delta,
                                "finish_reason": finish_reason,
                            }
                        ],
                    }
                    yield finish_chunk
                    logger.debug(
                        "Yielded finish chunk",
                        completion_id=self.completion_id,
                        finish_reason=finish_reason,
                    )

        # Yield [DONE] marker at end
        yield "[DONE]"
        logger.info(
            "Stream adaptation complete",
            completion_id=self.completion_id,
            chunk_count=chunk_count,
        )
