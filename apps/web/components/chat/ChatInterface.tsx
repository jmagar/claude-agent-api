/**
 * ChatInterface component
 *
 * Main container for chat UI - combines MessageList, Composer, and streaming logic.
 * Manages message state, loading, and error handling.
 *
 * @see tests/integration/chat-flow.test.tsx for test specifications
 * @see wireframes/01-chat-brainstorm-mode.html for design
 */

"use client";

import { useEffect, useState } from "react";
import { MessageList } from "./MessageList";
import { Composer } from "./Composer";
import { useStreamingQuery } from "@/hooks/useStreamingQuery";
import { useQuery } from "@tanstack/react-query";
import type { Message } from "@/types";

export interface ChatInterfaceProps {
  /** Session ID for this chat */
  sessionId: string;
}

export function ChatInterface({ sessionId }: ChatInterfaceProps) {
  const [loadingMessages, setLoadingMessages] = useState(true);
  const {
    messages: streamMessages,
    isStreaming,
    error,
    sendMessage,
    retry,
    clearError,
  } = useStreamingQuery(sessionId);

  // Fetch existing messages on mount
  const { data: existingMessages } = useQuery<{ messages: Message[] }>({
    queryKey: ["messages", sessionId],
    queryFn: async () => {
      const response = await fetch(`/api/sessions/${sessionId}/messages`);
      if (!response.ok) {
        throw new Error("Failed to load messages");
      }
      return response.json();
    },
    enabled: !!sessionId,
  });

  // Merge existing messages with stream messages
  const [allMessages, setAllMessages] = useState<Message[]>([]);

  useEffect(() => {
    if (existingMessages?.messages) {
      setAllMessages(existingMessages.messages);
      setLoadingMessages(false);
    }
  }, [existingMessages]);

  useEffect(() => {
    if (streamMessages.length > 0) {
      // Merge with existing, avoid duplicates
      setAllMessages((prev) => {
        const existingIds = new Set(prev.map((m) => m.id));
        const newMessages = streamMessages.filter(
          (m) => !existingIds.has(m.id)
        );
        return [...prev, ...newMessages];
      });
    }
  }, [streamMessages]);

  // Handle send message
  const handleSend = async (text: string) => {
    clearError();
    await sendMessage(text);
  };

  return (
    <div className="flex h-full flex-col">
      {/* Message list */}
      <MessageList
        messages={allMessages}
        isLoading={loadingMessages}
        isStreaming={isStreaming}
      />

      {/* Error message */}
      {error && (
        <div className="border-t border-red-DEFAULT bg-red-bg px-20 py-12">
          <div className="flex items-center justify-between">
            <div className="text-14 text-red-dark">
              {error.includes("network") || error.includes("Network")
                ? "Network error - connection failed"
                : "Failed to send message"}
            </div>
            <div className="flex gap-8">
              <button
                onClick={retry}
                className="rounded-6 bg-red-DEFAULT px-16 py-8 text-13 font-medium text-white hover:opacity-90"
              >
                Retry
              </button>
              <button
                onClick={clearError}
                className="rounded-6 border border-red-DEFAULT px-16 py-8 text-13 font-medium text-red-dark hover:bg-red-light"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Composer */}
      <Composer
        onSend={handleSend}
        isLoading={isStreaming}
        sessionId={sessionId}
      />
    </div>
  );
}
