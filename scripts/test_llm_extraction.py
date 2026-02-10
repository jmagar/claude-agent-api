#!/usr/bin/env python3
"""Test LLM memory extraction directly."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.adapters.memory import Mem0MemoryAdapter
from apps.api.config import get_settings
from apps.api.utils.crypto import hash_api_key


async def test_llm():
    """Test LLM memory extraction."""
    print("Testing LLM Memory Extraction")
    print("=" * 60)

    settings = get_settings()
    adapter = Mem0MemoryAdapter(settings)

    api_key = (
        settings.api_key.get_secret_value()
        if hasattr(settings.api_key, "get_secret_value")
        else settings.api_key
    )
    user_id = hash_api_key(api_key)

    print(f"\nUser ID: {user_id[:16]}...")
    print("\nAdding simple test message...")
    print("Message: 'I like Python programming'")

    try:
        import time

        start = time.time()
        result = await adapter.add(
            messages="I like Python programming",
            user_id=user_id,
            metadata={"test": "llm_extraction"},
            enable_graph=False,  # Disable graph to simplify
        )
        elapsed = time.time() - start

        print(f"\n✓ Success in {elapsed:.2f}s")
        print(f"Memories extracted: {len(result)}")
        for i, mem in enumerate(result, 1):
            print(f"  {i}. {mem.get('memory', mem)}")

    except Exception as e:
        print(f"\n✗ Failed: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_llm())
