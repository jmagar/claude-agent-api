"""Unit tests for OpenAI StreamingAdapter (TDD RED phase)."""

from typing import AsyncGenerator

import pytest

from apps.api.schemas.openai.responses import OpenAIStreamChunk
from apps.api.services.openai.streaming import StreamingAdapter
from apps.api.types import (
    ContentBlockDict,
    MessageEventDataDict,
    ResultEventDataDict,
)


async def mock_partial_events() -> AsyncGenerator[tuple[str, MessageEventDataDict], None]:
    """Generate mock partial events for streaming."""
    # First partial with content
    yield (
        "partial",
        {
            "type": "assistant",
            "content": [{"type": "text", "text": "Hello"}],
        },
    )
    # Second partial with more content
    yield (
        "partial",
        {
            "type": "assistant",
            "content": [{"type": "text", "text": " World"}],
        },
    )


async def mock_result_event() -> AsyncGenerator[tuple[str, ResultEventDataDict], None]:
    """Generate mock result event."""
    yield (
        "result",
        {
            "session_id": "test-session",
            "is_error": False,
            "result": "Hello World",
        },
    )


async def mock_full_stream() -> AsyncGenerator[
    tuple[str, MessageEventDataDict | ResultEventDataDict], None
]:
    """Generate full mock stream: partials → result."""
    # Partial events
    yield (
        "partial",
        {
            "type": "assistant",
            "content": [{"type": "text", "text": "Hello"}],
        },
    )
    yield (
        "partial",
        {
            "type": "assistant",
            "content": [{"type": "text", "text": " World"}],
        },
    )
    # Result event
    yield (
        "result",
        {
            "session_id": "test-session",
            "is_error": False,
            "result": "Hello World",
        },
    )


@pytest.mark.anyio
async def test_yields_role_delta_first() -> None:
    """First chunk should have delta.role='assistant'."""
    adapter = StreamingAdapter(original_model="gpt-4")
    chunks: list[OpenAIStreamChunk | str] = []

    async for chunk in adapter.adapt_stream(mock_partial_events()):
        chunks.append(chunk)

    # First chunk should have role delta
    assert len(chunks) >= 1
    assert isinstance(chunks[0], dict)
    first_chunk = chunks[0]
    assert first_chunk["choices"][0]["delta"].get("role") == "assistant"


@pytest.mark.anyio
async def test_yields_content_deltas_for_partials() -> None:
    """Partial events should be transformed to delta.content chunks."""
    adapter = StreamingAdapter(original_model="gpt-4")
    chunks: list[OpenAIStreamChunk | str] = []

    async for chunk in adapter.adapt_stream(mock_partial_events()):
        chunks.append(chunk)

    # Should have at least 2 content chunks (role + content chunks)
    assert len(chunks) >= 2

    # Check content deltas
    content_chunks = [c for c in chunks if isinstance(c, dict) and "content" in c["choices"][0]["delta"]]
    assert len(content_chunks) >= 2
    assert content_chunks[0]["choices"][0]["delta"]["content"] == "Hello"
    assert content_chunks[1]["choices"][0]["delta"]["content"] == " World"


@pytest.mark.anyio
async def test_yields_finish_chunk_on_result() -> None:
    """Result event should produce chunk with finish_reason='stop'."""
    adapter = StreamingAdapter(original_model="gpt-4")
    chunks: list[OpenAIStreamChunk | str] = []

    async for chunk in adapter.adapt_stream(mock_full_stream()):
        chunks.append(chunk)

    # Find chunk with finish_reason
    finish_chunks = [
        c
        for c in chunks
        if isinstance(c, dict) and c["choices"][0]["finish_reason"] is not None
    ]
    assert len(finish_chunks) >= 1
    assert finish_chunks[0]["choices"][0]["finish_reason"] == "stop"


@pytest.mark.anyio
async def test_yields_done_marker_at_end() -> None:
    """Stream should end with [DONE] marker."""
    adapter = StreamingAdapter(original_model="gpt-4")
    chunks: list[OpenAIStreamChunk | str] = []

    async for chunk in adapter.adapt_stream(mock_full_stream()):
        chunks.append(chunk)

    # Last chunk should be [DONE]
    assert len(chunks) >= 1
    assert chunks[-1] == "[DONE]"


@pytest.mark.anyio
async def test_consistent_completion_id() -> None:
    """All chunks should have the same completion ID."""
    adapter = StreamingAdapter(original_model="gpt-4")
    chunk_ids: list[str] = []

    async for chunk in adapter.adapt_stream(mock_full_stream()):
        if isinstance(chunk, dict):
            chunk_ids.append(chunk["id"])

    # All IDs should be identical
    assert len(chunk_ids) >= 2
    assert all(chunk_id == chunk_ids[0] for chunk_id in chunk_ids)
    # ID should start with "chatcmpl-"
    assert chunk_ids[0].startswith("chatcmpl-")


@pytest.mark.anyio
async def test_custom_completion_id() -> None:
    """Adapter should accept custom completion ID."""
    custom_id = "chatcmpl-test-123"
    adapter = StreamingAdapter(original_model="gpt-4", completion_id=custom_id)
    chunk_ids: list[str] = []

    async for chunk in adapter.adapt_stream(mock_partial_events()):
        if isinstance(chunk, dict):
            chunk_ids.append(chunk["id"])

    # All IDs should match custom ID
    assert len(chunk_ids) >= 1
    assert all(chunk_id == custom_id for chunk_id in chunk_ids)
