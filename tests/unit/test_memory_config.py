"""Tests for memory configuration."""

import os

import pytest

from apps.api.config import Settings


def test_memory_config_loaded_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Memory config should load from environment variables."""
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("NEO4J_URL", "bolt://localhost:54687")
    monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "testpass")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:53333")
    monkeypatch.setenv("TEI_URL", "http://100.74.16.82:52000")

    settings = Settings()

    assert settings.llm_api_key == "test-key"
    assert settings.neo4j_url == "bolt://localhost:54687"
    assert settings.neo4j_username == "neo4j"
    assert settings.neo4j_password == "testpass"
    assert settings.qdrant_url == "http://localhost:53333"
    assert settings.tei_url == "http://100.74.16.82:52000"


def test_memory_config_defaults() -> None:
    """Memory config should have sensible defaults."""
    settings = Settings()

    assert settings.mem0_collection_name == "mem0_memories"
    assert settings.mem0_embedding_dims == 1024
    assert settings.mem0_agent_id == "main"
