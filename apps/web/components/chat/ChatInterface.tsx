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
import { ErrorBanner } from "@/components/ui/ErrorBanner";
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

      {/* Error banner */}
      {error && (
        <ErrorBanner error={error} onRetry={retry} onDismiss={clearError} />
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
