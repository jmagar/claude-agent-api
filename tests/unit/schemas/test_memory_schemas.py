"""Tests for memory schemas."""


from apps.api.schemas.memory import (
    MemoryAddRequest,
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


def test_memory_search_response_valid() -> None:
    """MemorySearchResponse should validate correct data."""
    response = MemorySearchResponse(
        results=[
            {
                "id": "mem_123",
                "memory": "User prefers technical explanations",
                "score": 0.95,
                "metadata": {"category": "preferences"},
            }
        ],
        count=1,
    )
    assert len(response.results) == 1
    assert response.count == 1
