#!/usr/bin/env python3
"""Test TEI embeddings through Mem0's embedder directly."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.config import get_settings


async def test_embeddings():
    """Test embeddings generation."""
    print("Testing TEI Embeddings via Mem0")
    print("=" * 60)

    settings = get_settings()

    print("\nConfiguration:")
    print(f"  TEI URL: {settings.tei_url}")
    print(f"  Embedding dims: {settings.mem0_embedding_dims}")

    # Test with Memory.from_config() like the adapter does
    try:
        from mem0 import Memory

        # Use same config format as adapter
        config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "openai_base_url": settings.llm_base_url,
                    "model": settings.llm_model,
                    "api_key": settings.llm_api_key,
                },
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small",
                    "openai_base_url": f"{settings.tei_url}/v1",
                    "embedding_dims": settings.mem0_embedding_dims,
                    "api_key": settings.tei_api_key,
                },
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "url": settings.qdrant_url,
                    "collection_name": settings.mem0_collection_name,
                    "embedding_model_dims": settings.mem0_embedding_dims,
                    "on_disk": True,
                },
            },
            "version": "v1.1",
        }

        print("\nInitializing Memory with config...")
        print(f"Vector store config: {config['vector_store']}")

        memory = Memory.from_config(config)

        print("Memory initialized successfully!")
        print(f"Embedder type: {type(memory.embedding_model)}")
        print(f"Vector store client type: {type(memory.vector_store.client._client)}")
        print(f"Is local: {getattr(memory.vector_store, 'is_local', 'unknown')}")

        # Try to get embeddings directly (like memory.add() does)
        print("\nTesting embed_text method...")
        test_text = "This is a test message"

        # Test with single argument
        embedding1 = await asyncio.to_thread(memory.embedding_model.embed, test_text)
        print("\nEmbedding with 1 arg:")
        print(f"  Type: {type(embedding1)}")
        print(
            f"  Length: {len(embedding1) if embedding1 and hasattr(embedding1, '__len__') else 'None'}"
        )

        # Test with two arguments (like memory.add() does)
        embedding2 = await asyncio.to_thread(
            memory.embedding_model.embed, test_text, "add"
        )
        print("\nEmbedding with 2 args ('add'):")
        print(f"  Type: {type(embedding2)}")
        print(
            f"  Length: {len(embedding2) if embedding2 and hasattr(embedding2, '__len__') else 'None'}"
        )

        # Now test the full memory.add() flow
        print("\n" + "=" * 60)
        print("Testing full memory.add() operation...")
        print("=" * 60)

        try:
            from apps.api.utils.crypto import hash_api_key

            api_key = (
                settings.api_key.get_secret_value()
                if hasattr(settings.api_key, "get_secret_value")
                else settings.api_key
            )
            user_id = hash_api_key(api_key)

            result = await asyncio.to_thread(
                memory.add,
                messages="I prefer Python for backend development",
                user_id=user_id,
                agent_id="main",
            )

            print("\nAdd Result:")
            print(f"  Type: {type(result)}")
            if isinstance(result, dict):
                print(f"  Results: {result}")
            else:
                print(
                    f"  Count: {len(result) if hasattr(result, '__len__') else 'N/A'}"
                )
                if result:
                    print(f"  First memory: {result[0]}")

        except Exception as add_error:
            print(
                f"\nERROR during memory.add(): {type(add_error).__name__}: {add_error}"
            )
            import traceback

            traceback.print_exc()

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_embeddings())
