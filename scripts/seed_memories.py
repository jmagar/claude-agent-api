#!/usr/bin/env python3
"""Seed project documentation into Mem0 memory system.

Usage:
    uv run python scripts/seed_memories.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.adapters.memory import Mem0MemoryAdapter
from apps.api.config import get_settings
from apps.api.utils.crypto import hash_api_key


async def seed_documentation():
    """Seed project documentation into memory system."""
    print("=" * 60)
    print("Mem0 Memory Seeding Script")
    print("=" * 60)

    # Initialize adapter
    print("\nInitializing Mem0 adapter...")
    settings = get_settings()
    adapter = Mem0MemoryAdapter(settings)

    # Use default API key from .env
    api_key = (
        settings.api_key.get_secret_value()
        if hasattr(settings.api_key, "get_secret_value")
        else settings.api_key
    )
    user_id = hash_api_key(api_key)
    print(f"User ID (hashed): {user_id[:16]}...")

    # Documentation to seed
    docs = [
        {
            "name": "Tech Stack",
            "content": """The Claude Agent API is built with FastAPI and Python 3.11+.
            Key dependencies include PostgreSQL for persistence, Redis for caching and session tracking,
            SQLAlchemy with async support for ORM, Pydantic for validation and settings,
            Ruff for linting and formatting, ty for type checking, pytest with pytest-asyncio for testing,
            Uvicorn as ASGI server, Alembic for database migrations, and uv for dependency management.""",
        },
        {
            "name": "Architecture",
            "content": """The API runs on port 54000 and provides an HTTP wrapper around the Claude Agent Python SDK.
            It uses distributed session management with PostgreSQL on port 54432 as source of truth and
            Redis on port 54379 for caching. The architecture supports horizontal scaling across multiple instances.""",
        },
        {
            "name": "API Endpoints",
            "content": """Key endpoints include POST /api/v1/query for SSE streaming responses,
            POST /api/v1/query/single for non-streaming queries, session management at /api/v1/sessions,
            OpenAI-compatible endpoints at /v1/chat/completions and /v1/models,
            skills listing at /api/v1/skills, memory management at /api/v1/memories, and health checks.""",
        },
        {
            "name": "Memory System",
            "content": """Uses Mem0 OSS v1.0.3 for persistent memory. Components include an LLM at cli-api.tootie.tv
            with gemini-3-flash-preview for memory extraction, TEI embeddings with Qwen/Qwen3-Embedding-0.6B
            (1024 dimensions) at 100.74.16.82:52000, Qdrant vector store on port 53333 for semantic search,
            and Neo4j graph store on ports 54687/54474 for entity relationships.""",
        },
        {
            "name": "Memory Features",
            "content": """Memory injection is automatic on every request with top 5 relevant memories by default.
            Uses semantic search with vector embeddings. Memories stored in both Qdrant and Neo4j.
            Multi-tenant isolation via SHA-256 hashed API keys. LLM extracts memories asynchronously after responses.
            Graph store optional for entity/relationship extraction.""",
        },
        {
            "name": "Session Management",
            "content": """Distributed session management uses PostgreSQL for durability and Redis for caching.
            Supports session resume, fork, and delete operations. Active sessions tracked in Redis with TTL.
            Horizontal scaling supported with shared session state across API instances.""",
        },
        {
            "name": "OpenAI Compatibility",
            "content": """OpenAI-compatible endpoints at /v1/* provide drop-in compatibility.
            Includes chat completions endpoint with streaming and non-streaming support, models listing endpoint,
            and model info endpoint. Supports Bearer token authentication. Request/response translation layer
            converts between OpenAI and Claude formats.""",
        },
        {
            "name": "Development Tools",
            "content": """Uses uv for fast package management, Ruff for linting and formatting with 88 character line limit,
            ty for extremely fast type checking, pytest for testing with asyncio support, Docker Compose for infrastructure,
            Alembic for database migrations, and structlog for structured logging.""",
        },
        {
            "name": "Code Standards",
            "content": """Follows PEP 8 style with 4-space indentation. Type hints required on all functions.
            Uses async/await for all I/O operations. Protocol-based dependency injection via FastAPI.
            Zero tolerance for Any types - use specific types or Protocols. TDD approach with RED-GREEN-REFACTOR cycle.""",
        },
        {
            "name": "Port Assignments",
            "content": """API server runs on port 54000, PostgreSQL on 54432, Redis on 54379,
            Neo4j Bolt on 54687, Neo4j HTTP on 54474, Qdrant on 53333 (external),
            and TEI embeddings on 52000 at 100.74.16.82. All ports above 53000 to avoid conflicts.""",
        },
    ]

    # Seed each document
    print(f"\nSeeding {len(docs)} documents...\n")
    success_count = 0
    total_memories = 0

    for i, doc in enumerate(docs, 1):
        print(f"[{i}/{len(docs)}] {doc['name']}...")
        try:
            result = await adapter.add(
                messages=doc["content"],
                user_id=user_id,
                metadata={
                    "source": doc["name"].lower().replace(" ", "_"),
                    "type": "documentation",
                },
                enable_graph=True,  # Adapter handles version compatibility
            )
            count = len(result)
            total_memories += count
            success_count += 1
            print(f"  ✓ Extracted {count} memories")

        except Exception as e:
            print(f"  ✗ Failed: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"Seeding Complete!")
    print(f"  Success: {success_count}/{len(docs)} documents")
    print(f"  Total memories extracted: {total_memories}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_documentation())
