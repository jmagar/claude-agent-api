#!/bin/bash
# Quick memory demonstration

echo "🧠 Memory System Quick Demo"
echo "============================"
echo ""

# Test 1: Add a memory
echo "📝 Test 1: Adding memory..."
echo "   Input: 'I love Python and FastAPI'"
uv run python -c "
import asyncio
from apps.api.adapters.memory import Mem0MemoryAdapter
from apps.api.config import get_settings
from apps.api.utils.crypto import hash_api_key

async def test():
    settings = get_settings()
    adapter = Mem0MemoryAdapter(settings)
    api_key = settings.api_key.get_secret_value() if hasattr(settings.api_key, 'get_secret_value') else settings.api_key
    user_id = hash_api_key(api_key)

    result = await adapter.add(
        messages='I love Python and FastAPI for building APIs',
        user_id=user_id,
        metadata={'test': 'demo'},
        enable_graph=False
    )
    print(f'   ✓ Stored (extracted {len(result)} memories)')

asyncio.run(test())
" 2>&1 | grep -v "Error processing\|info\|vector.list"

echo ""
echo "🔍 Test 2: Searching memory..."
echo "   Query: 'What programming languages does the user like?'"
uv run python -c "
import asyncio
from apps.api.adapters.memory import Mem0MemoryAdapter
from apps.api.config import get_settings
from apps.api.utils.crypto import hash_api_key

async def test():
    settings = get_settings()
    adapter = Mem0MemoryAdapter(settings)
    api_key = settings.api_key.get_secret_value() if hasattr(settings.api_key, 'get_secret_value') else settings.api_key
    user_id = hash_api_key(api_key)

    results = await adapter.search(
        query='What programming languages does the user like?',
        user_id=user_id,
        limit=3,
        enable_graph=False
    )

    print(f'   ✓ Found {len(results)} memories:')
    for i, mem in enumerate(results[:3], 1):
        print(f'      {i}. {mem.get(\"memory\", \"\")[:70]}... (score: {mem.get(\"score\", 0):.3f})')

asyncio.run(test())
" 2>&1 | grep -v "Error processing\|info\|vector.list"

echo ""
echo "✅ Demo complete!"
echo ""
echo "Try the full interactive chat:"
echo "  uv run python scripts/chat_with_memory.py"
