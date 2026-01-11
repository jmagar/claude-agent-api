/**
 * MessageList component
 *
 * Displays chat messages in chronological order.
 * Auto-scrolls to bottom on new messages, shows loading/empty states.
 *
 * Performance optimizations:
 * - Memoized to prevent unnecessary re-renders
 * - Auto-scroll only triggers on new messages
 * - Note: For >100 messages, consider react-window or react-virtuoso
 *
 * @see tests/unit/components/MessageList.test.tsx for test specifications
 * @see wireframes/01-chat-brainstorm-mode.html for design
 */

"use client";

import { useEffect, useRef, useState, memo, forwardRef } from "react";
import type { HTMLAttributes } from "react";
import { Virtuoso } from "react-virtuoso";
import { MessageItem } from "./MessageItem";
import { MessageSkeleton } from "@/components/ui/LoadingState";
import { EmptyState } from "@/components/ui/EmptyState";
import { StreamingIndicator } from "@/components/ui/LoadingState";
import type { Message, ToolCall } from "@/types";

export interface MessageListProps {
  /** Array of messages to display */
  messages: Message[];
  /** Whether messages are currently loading */
  isLoading?: boolean;
  /** Whether a response is currently streaming */
  isStreaming?: boolean;
  /** Whether to show timestamps on messages */
  showTimestamps?: boolean;
  /** Tool calls keyed by tool_use id */
  toolCallsById?: Record<string, ToolCall>;
  /** Retry handler for failed tools */
  onRetryTool?: () => void;
}

function MessageListComponent({
  messages,
  isLoading = false,
  isStreaming = false,
  showTimestamps = false,
  toolCallsById,
  onRetryTool,
}: MessageListProps) {
  const previousMessageCountRef = useRef(messages.length);
  const isInitialMount = useRef(true);
  const [followOutput, setFollowOutput] = useState<"auto" | "smooth" | false>("auto");

  // Update followOutput when messages change
  useEffect(() => {
    if (isInitialMount.current) {
      setFollowOutput("auto");
      isInitialMount.current = false;
    } else if (messages.length > previousMessageCountRef.current) {
      setFollowOutput("smooth");
    } else {
      setFollowOutput(false);
    }
    previousMessageCountRef.current = messages.length;
  }, [messages.length]);

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
      className="flex flex-1 flex-col"
      role="log"
      aria-label="Chat messages"
    >
      <Virtuoso
        data={messages}
        followOutput={followOutput}
        className="flex-1"
        components={{
          Scroller: forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
            function MessageScroller({ className = "", ...props }, ref) {
              return (
                <div
                  ref={ref}
                  {...props}
                  className={`overflow-auto px-20 py-20 ${className}`}
                  data-testid="message-list-container"
                />
              );
            }
          ),
          List: forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
            function MessageListContainer({ className = "", ...props }, ref) {
              return (
                <div
                  ref={ref}
                  {...props}
                  className={`flex flex-col gap-24 ${className}`}
                />
              );
            }
          ),
          Footer: () =>
            isStreaming && messages.length > 0 ? (
              <div className="mt-8" data-testid="streaming-indicator">
                <StreamingIndicator showCursor={true} />
              </div>
            ) : null,
        }}
        itemContent={(_, message) => (
          <MessageItem
            message={message}
            showTimestamp={showTimestamps}
            toolCallsById={toolCallsById}
            onRetryTool={onRetryTool}
          />
        )}
      />
    </div>
  );
}

/**
 * Memoized MessageList component
 *
 * Only re-renders when props actually change, preventing
 * unnecessary re-renders from parent component updates.
 */
export const MessageList = memo(MessageListComponent);
