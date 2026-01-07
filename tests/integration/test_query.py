"""Integration tests for query endpoints."""

import pytest
from httpx import AsyncClient


class TestQueryStreaming:
    """Integration tests for streaming query functionality."""

    @pytest.mark.anyio
    async def test_query_stream_init_event(
        self,
        _async_client: AsyncClient,
        _auth_headers: dict[str, str],
    ) -> None:
        """Test that query stream starts with init event."""
        # This test requires the actual SDK integration
        pytest.skip("Requires SDK integration")

    @pytest.mark.anyio
    async def test_query_stream_result_event(
        self,
        _async_client: AsyncClient,
        _auth_headers: dict[str, str],
    ) -> None:
        """Test that query stream ends with result event."""
        pytest.skip("Requires SDK integration")

    @pytest.mark.anyio
    async def test_query_stream_done_event(
        self,
        _async_client: AsyncClient,
        _auth_headers: dict[str, str],
    ) -> None:
        """Test that query stream ends with done event."""
        pytest.skip("Requires SDK integration")

    @pytest.mark.anyio
    async def test_query_stream_error_handling(
        self,
        _async_client: AsyncClient,
        _auth_headers: dict[str, str],
    ) -> None:
        """Test error handling in streaming mode."""
        pytest.skip("Requires SDK integration")

    @pytest.mark.anyio
    async def test_query_stream_with_allowed_tools(
        self,
        _async_client: AsyncClient,
        _auth_headers: dict[str, str],
    ) -> None:
        """Test query with allowed_tools restriction."""
        pytest.skip("Requires SDK integration")

    @pytest.mark.anyio
    async def test_query_stream_session_id_returned(
        self,
        _async_client: AsyncClient,
        _auth_headers: dict[str, str],
    ) -> None:
        """Test that session_id is returned in init event."""
        pytest.skip("Requires SDK integration")


class TestQuerySingle:
    """Integration tests for single (non-streaming) query."""

    @pytest.mark.anyio
    async def test_query_single_returns_complete_response(
        self,
        _async_client: AsyncClient,
        _auth_headers: dict[str, str],
    ) -> None:
        """Test that single query returns complete response."""
        pytest.skip("Requires SDK integration")

    @pytest.mark.anyio
    async def test_query_single_includes_usage(
        self,
        _async_client: AsyncClient,
        _auth_headers: dict[str, str],
    ) -> None:
        """Test that single query response includes usage data."""
        pytest.skip("Requires SDK integration")
