/**
 * MessageList component
 *
 * Displays chat messages in chronological order with virtualized scrolling.
 * Auto-scrolls to bottom on new messages, shows loading/empty states.
 *
 * @see tests/unit/components/MessageList.test.tsx for test specifications
 * @see wireframes/01-chat-brainstorm-mode.html for design
 */

"use client";

import { useEffect, useRef } from "react";
import { MessageItem } from "./MessageItem";
import { MessageSkeleton } from "@/components/ui/LoadingState";
import { EmptyState } from "@/components/ui/EmptyState";
import { StreamingIndicator } from "@/components/ui/LoadingState";
import type { Message } from "@/types";

export interface MessageListProps {
  /** Array of messages to display */
  messages: Message[];
  /** Whether messages are currently loading */
  isLoading?: boolean;
  /** Whether a response is currently streaming */
  isStreaming?: boolean;
  /** Whether to show timestamps on messages */
  showTimestamps?: boolean;
}

export function MessageList({
  messages,
  isLoading = false,
  isStreaming = false,
  showTimestamps = false,
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const previousMessageCountRef = useRef(messages.length);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (messages.length > previousMessageCountRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
    previousMessageCountRef.current = messages.length;
  }, [messages.length]);

  // Auto-scroll on initial load
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "auto" });
  }, []);

  // Show loading skeleton while fetching messages
  if (isLoading && messages.length === 0) {
    return (
      <div
        className="flex flex-1 flex-col overflow-auto px-20 py-20"
        data-testid="message-list-container"
        role="log"
        aria-label="Chat messages"
      >
        <div data-testid="message-skeleton">
          <MessageSkeleton />
          <MessageSkeleton />
          <MessageSkeleton />
        </div>
      </div>
    );
  }

  // Show empty state when no messages
  if (messages.length === 0 && !isLoading) {
    return (
      <div
        className="flex flex-1 flex-col overflow-auto"
        data-testid="message-list-container"
        role="log"
        aria-label="Chat messages"
      >
        <EmptyState
          icon="💬"
          title="No messages yet"
          description="Start a conversation with Claude by typing a message below."
        />
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="flex flex-1 flex-col overflow-auto px-20 py-20"
      data-testid="message-list-container"
      role="log"
      aria-label="Chat messages"
    >
      {/* Message list */}
      <div className="flex flex-col gap-24">
        {messages.map((message) => (
          <MessageItem
            key={message.id}
            message={message}
            showTimestamp={showTimestamps}
          />
        ))}
      </div>

      {/* Streaming indicator on last message */}
      {isStreaming && messages.length > 0 && (
        <div className="mt-8" data-testid="streaming-indicator">
          <StreamingIndicator showCursor={true} />
        </div>
      )}

      {/* Auto-scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  );
}
