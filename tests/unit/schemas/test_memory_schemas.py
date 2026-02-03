"""Tests for memory schemas."""

import pytest
from pydantic import ValidationError

from apps.api.schemas.memory import (
    MemoryAddRequest,
    MemoryDeleteResponse,
    MemoryListResponse,
    MemoryResult,
    MemorySearchRequest,
    MemorySearchResponse,
)


def test_memory_add_request_valid() -> None:
    """MemoryAddRequest should validate correct data."""
    request = MemoryAddRequest(
        messages="User prefers technical explanations",
        metadata={"category": "preferences"},
        enable_graph=True,
    )
    assert request.messages == "User prefers technical explanations"
    assert request.metadata == {"category": "preferences"}
    assert request.enable_graph is True


def test_memory_add_request_defaults() -> None:
    """MemoryAddRequest should have sensible defaults."""
    request = MemoryAddRequest(messages="Test memory")
    assert request.metadata is None
    assert request.enable_graph is True


def test_memory_add_request_missing_messages() -> None:
    """MemoryAddRequest should require messages field."""
    with pytest.raises(ValidationError) as exc_info:
        MemoryAddRequest()  # type: ignore
    assert "messages" in str(exc_info.value)


def test_memory_search_request_valid() -> None:
    """MemorySearchRequest should validate correct data."""
    request = MemorySearchRequest(
        query="What are user preferences?",
        limit=10,
        enable_graph=True,
    )
    assert request.query == "What are user preferences?"
    assert request.limit == 10
    assert request.enable_graph is True


def test_memory_search_request_defaults() -> None:
    """MemorySearchRequest should have sensible defaults."""
    request = MemorySearchRequest(query="Test query")
    assert request.limit == 10
    assert request.enable_graph is True


def test_memory_search_request_limit_validation() -> None:
    """MemorySearchRequest should enforce limit range 1-100."""
    # Test below minimum
    with pytest.raises(ValidationError) as exc_info:
        MemorySearchRequest(query="test", limit=0)
    assert "greater than or equal to 1" in str(exc_info.value).lower()

    # Test above maximum
    with pytest.raises(ValidationError) as exc_info:
        MemorySearchRequest(query="test", limit=101)
    assert "less than or equal to 100" in str(exc_info.value).lower()

    # Test boundaries (should pass)
    MemorySearchRequest(query="test", limit=1)
    MemorySearchRequest(query="test", limit=100)


def test_memory_result_defaults() -> None:
    """MemoryResult should have sensible defaults."""
    result = MemoryResult(id="mem_123", memory="Test memory")
    assert result.id == "mem_123"
    assert result.memory == "Test memory"
    assert result.score == 0.0
    assert result.metadata == {}


def test_memory_search_response_valid() -> None:
    """MemorySearchResponse should validate correct data."""
    response = MemorySearchResponse(
        results=[
            MemoryResult(
                id="mem_123",
                memory="User prefers technical explanations",
                score=0.95,
                metadata={"category": "preferences"},
            )
        ],
        count=1,
    )
    assert len(response.results) == 1
    assert response.count == 1
    assert response.results[0].id == "mem_123"
    assert response.results[0].score == 0.95


def test_memory_list_response_valid() -> None:
    """MemoryListResponse should validate correct data."""
    response = MemoryListResponse(
        memories=[
            {"id": "mem_123", "memory": "Test memory 1"},
            {"id": "mem_456", "memory": "Test memory 2"},
        ],
        count=2,
    )
    assert len(response.memories) == 2
    assert response.count == 2
    assert response.memories[0]["id"] == "mem_123"


def test_memory_delete_response_valid() -> None:
    """MemoryDeleteResponse should validate correct data."""
    response = MemoryDeleteResponse(deleted=True, message="Memory deleted successfully")
    assert response.deleted is True
    assert response.message == "Memory deleted successfully"
