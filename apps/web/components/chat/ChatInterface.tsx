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

import { useEffect, useMemo, useState } from "react";
import { MessageList } from "./MessageList";
import { Composer } from "./Composer";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { useStreamingQuery } from "@/hooks/useStreamingQuery";
import { useQuery } from "@tanstack/react-query";
import type { Message } from "@/types";

export interface ChatInterfaceProps {
  /** Session ID for this chat (optional - will be generated if not provided) */
  sessionId?: string;
}

export function ChatInterface({ sessionId: initialSessionId }: ChatInterfaceProps) {
  // Only show loading state if we're resuming an existing session
  const [loadingMessages, setLoadingMessages] = useState(!!initialSessionId);
  const {
    messages: streamMessages,
    toolCalls,
    sessionId, // Get the actual session ID from the hook (updated from init event)
    isStreaming,
    error,
    sendMessage,
    retry,
    clearError,
  } = useStreamingQuery(initialSessionId);

  // Fetch existing messages on mount (only if we have an initial session ID to resume)
  const { data: existingMessages } = useQuery<{ messages: Message[] }>({
    queryKey: ["messages", initialSessionId],
    queryFn: async () => {
      const response = await fetch(`/api/sessions/${initialSessionId}/messages`);
      if (!response.ok) {
        throw new Error("Failed to load messages");
      }
      return response.json();
    },
    enabled: !!initialSessionId, // Only fetch if we're resuming an existing session
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

  const toolCallsById = useMemo(
    () =>
      toolCalls.reduce<Record<string, (typeof toolCalls)[number]>>((acc, toolCall) => {
        acc[toolCall.id] = toolCall;
        return acc;
      }, {}),
    [toolCalls]
  );

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
        toolCallsById={toolCallsById}
        onRetryTool={retry}
      />

      {/* Error banner */}
      {error && (
        <ErrorBanner error={error} onRetry={retry} onDismiss={clearError} />
      )}

      {/* Composer */}
      <Composer
        onSend={handleSend}
        isLoading={isStreaming}
        sessionId={sessionId ?? undefined}
      />
    </div>
  );
}
