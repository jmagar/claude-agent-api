#!/usr/bin/env python3
"""Simple interactive chat to demonstrate memory system."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.adapters.memory import Mem0MemoryAdapter
from apps.api.config import get_settings
from apps.api.services.agent.service import AgentService
from apps.api.utils.crypto import hash_api_key


class MemoryChat:
    """Interactive chat with memory demonstration."""

    def __init__(self):
        self.settings = get_settings()
        self.memory_adapter = Mem0MemoryAdapter(self.settings)
        self.agent_service = AgentService()

        api_key = (
            self.settings.api_key.get_secret_value()
            if hasattr(self.settings.api_key, "get_secret_value")
            else self.settings.api_key
        )
        self.user_id = hash_api_key(api_key)

    async def get_relevant_memories(self, query: str, limit: int = 5):
        """Get relevant memories for the query."""
        results = await self.memory_adapter.search(
            query=query,
            user_id=self.user_id,
            limit=limit,
            enable_graph=False,
        )
        return results

    async def add_memory(self, text: str):
        """Add conversation to memory."""
        await self.memory_adapter.add(
            messages=text,
            user_id=self.user_id,
            metadata={"source": "chat", "type": "conversation"},
            enable_graph=False,
        )

    def print_banner(self):
        """Print welcome banner."""
        print("\n" + "=" * 70)
        print("  🧠 Memory-Enabled Chat Demo")
        print("=" * 70)
        print("\nThis chat demonstrates the Mem0 memory system:")
        print("  • Your messages are analyzed and stored as memories")
        print("  • Relevant memories are retrieved for each query")
        print("  • The system learns about you over time")
        print("\nCommands:")
        print("  /memories - Show all your memories")
        print("  /search <query> - Search memories")
        print("  /clear - Clear all memories")
        print("  /quit - Exit chat")
        print("\n" + "=" * 70 + "\n")

    async def show_memories(self):
        """Display all stored memories."""
        # Get a large number to fetch all
        results = await self.memory_adapter.search(
            query="",  # Empty query to get recent memories
            user_id=self.user_id,
            limit=50,
            enable_graph=False,
        )

        if not results:
            print("\n📭 No memories stored yet. Start chatting to build your memory!\n")
            return

        print(f"\n📚 Your Memories ({len(results)} total):")
        print("-" * 70)
        for i, mem in enumerate(results, 1):
            print(f"{i}. {mem.get('memory', '')}")
            print(f"   Score: {mem.get('score', 0):.3f}")
            print()

    async def search_memories(self, query: str):
        """Search memories with a specific query."""
        results = await self.get_relevant_memories(query, limit=10)

        if not results:
            print(f"\n🔍 No memories found for: {query}\n")
            return

        print(f"\n🔍 Search Results for '{query}':")
        print("-" * 70)
        for i, mem in enumerate(results, 1):
            print(f"{i}. {mem.get('memory', '')}")
            print(f"   Relevance: {mem.get('score', 0):.3f}")
            print()

    async def clear_memories(self):
        """Clear all memories for this user."""
        # Delete all memories
        await self.memory_adapter.delete_all(user_id=self.user_id)
        print("\n🗑️  All memories cleared!\n")

    async def chat(self, user_input: str):
        """Process a chat message with memory context."""
        # Get relevant memories
        print("\n🧠 Retrieving relevant memories...")
        memories = await self.get_relevant_memories(user_input, limit=5)

        if memories:
            print(f"   Found {len(memories)} relevant memories:")
            for i, mem in enumerate(memories[:3], 1):  # Show top 3
                preview = mem.get('memory', '')[:60]
                print(f"   {i}. {preview}... (score: {mem.get('score', 0):.3f})")
        else:
            print("   No relevant memories found.")

        # Build prompt with memory context
        if memories:
            memory_context = "\n".join([
                f"- {mem.get('memory', '')}"
                for mem in memories[:5]
            ])
            system_prompt = f"You are a helpful assistant. Here's what you know about the user:\n\n{memory_context}\n\nUse this context naturally in your responses."
        else:
            system_prompt = "You are a helpful assistant."

        print("\n💭 Thinking...\n")

        # Call the actual agent
        try:
            from apps.api.schemas.requests.query import QueryRequest

            request = QueryRequest(
                prompt=user_input,
                system_prompt=system_prompt,
                model="sonnet",
                max_turns=3,
            )

            result = await self.agent_service.query_single(request, api_key="demo")

            # Extract text from content blocks
            content_blocks = result.get("content", [])
            response_parts = []
            for block in content_blocks:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if isinstance(text, str):
                        response_parts.append(text)

            response_text = "".join(response_parts) if response_parts else "No response"

            print("🤖 Assistant:")
            print(f"   {response_text}\n")

            response_text_for_memory = response_text

        except Exception as e:
            print(f"❌ Error calling agent: {e}")
            print("   Using fallback response...\n")
            response_text_for_memory = f"I understand you said: {user_input}"
            print(f"🤖 Assistant:\n   {response_text_for_memory}\n")

        # Store this conversation as memory
        print("💾 Saving to memory...")
        conversation = f"User said: {user_input}\nAssistant responded: {response_text_for_memory}"
        await self.add_memory(conversation)
        print("   ✓ Saved!\n")

    async def run(self):
        """Run the interactive chat loop."""
        self.print_banner()

        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input == "/quit":
                    print("\n👋 Goodbye!\n")
                    break

                elif user_input == "/memories":
                    await self.show_memories()

                elif user_input.startswith("/search "):
                    query = user_input[8:].strip()
                    if query:
                        await self.search_memories(query)
                    else:
                        print("\n⚠️  Usage: /search <query>\n")

                elif user_input == "/clear":
                    confirm = input("⚠️  Clear all memories? (yes/no): ").strip().lower()
                    if confirm == "yes":
                        await self.clear_memories()

                else:
                    # Regular chat message
                    await self.chat(user_input)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


async def main():
    """Main entry point."""
    chat = MemoryChat()
    await chat.run()


if __name__ == "__main__":
    asyncio.run(main())
