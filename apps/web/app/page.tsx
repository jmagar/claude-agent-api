/**
 * Home page - Basic chat interface
 *
 * Displays ChatInterface with a default session.
 * Full UI with sidebar will be added in later user stories.
 *
 * @see tests/e2e/chat-input.spec.ts for E2E tests
 */

"use client";

import { ChatInterface } from "@/components/chat/ChatInterface";
import { useState } from "react";

export default function Home() {
  // Generate or use session ID from URL
  const [sessionId] = useState(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      return params.get("session") || `session-${Date.now()}`;
    }
    return "session-default";
  });

  return (
    <main className="flex h-screen flex-col">
      {/* Simple header */}
      <div className="border-b border-gray-300 bg-white px-20 py-16">
        <h1 className="text-16 font-semibold">Claude Agent Web</h1>
      </div>

      {/* Chat interface */}
      <ChatInterface sessionId={sessionId} />
    </main>
  );
}
