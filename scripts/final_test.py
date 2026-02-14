#!/usr/bin/env python3
"""Final test of Mem0 with fixed Qdrant configuration."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.adapters.memory import Mem0MemoryAdapter
from apps.api.config import get_settings
from apps.api.utils.crypto import hash_api_key


async def main():
    """Test memory seeding with fixed configuration."""
    print("=" * 60)
    print("Final Mem0 Test - Fixed Configuration")
    print("=" * 60)

    settings = get_settings()
    adapter = Mem0MemoryAdapter(settings)

    api_key = (
        settings.api_key.get_secret_value()
        if hasattr(settings.api_key, "get_secret_value")
        else settings.api_key
    )
    user_id = hash_api_key(api_key)

    print("\n✓ Mem0 adapter initialized")
    print(f"✓ Qdrant URL: {settings.qdrant_url}")
    print(f"✓ User ID: {user_id[:16]}...")

    # Test 1: Simple message
    print("\n" + "=" * 60)
    print("Test 1: Add simple memory")
    print("=" * 60)

    try:
        result = await adapter.add(
            messages="I prefer Python for backend development",
            user_id=user_id,
            metadata={"test": "final"},
            enable_graph=False,
        )
        print(f"✓ Success! Memories: {result}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

    # Test 2: Search
    print("\n" + "=" * 60)
    print("Test 2: Search memories")
    print("=" * 60)

    try:
        results = await adapter.search(
            query="What does the user prefer?",
            user_id=user_id,
            limit=5,
            enable_graph=False,
        )
        print(f"✓ Found {len(results)} memories")
        for r in results:
            print(f"  - {r}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
