/**
 * MessageItem component
 *
 * Displays a single chat message with role-specific styling, markdown support,
 * and rendering of thinking/tool blocks.
 *
 * @see tests/unit/components/MessageItem.test.tsx for test specifications
 * @see wireframes/01-chat-brainstorm-mode.html for design
 */

"use client";

import { useState, memo } from "react";
import { MessageContent } from "./MessageContent";
import type { Message, ContentBlock } from "@/types";

export interface MessageItemProps {
  /** Message to display */
  message: Message;
  /** Whether to show timestamp */
  showTimestamp?: boolean;
}

function MessageItemComponent({ message, showTimestamp = false }: MessageItemProps) {
  const [expandedThinking, setExpandedThinking] = useState<Set<number>>(
    new Set()
  );

  const isUser = message.role === "user";
  const label = isUser ? "You" : "Assistant";

  // Format timestamp (HH:MM)
  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  };

  // Toggle thinking block expansion
  const toggleThinking = (index: number) => {
    setExpandedThinking((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  return (
    <div
      className={`flex gap-12 ${isUser ? "justify-end" : ""}`}
      data-role={message.role}
      data-testid="message-item"
      role="article"
      aria-label={`${label} message`}
    >
      <div className={`flex max-w-[70%] flex-col gap-4`}>
        {/* Message label */}
        <div className="text-11 font-semibold uppercase text-gray-600">
          {label}
        </div>

        {/* Message bubble */}
        <div
          className={`rounded-8 border px-16 py-12 ${
            isUser
              ? "bg-blue-light border-blue-border"
              : "bg-gray-100 border-gray-300"
          }`}
          data-testid="message-bubble"
        >
          <div className="flex flex-col gap-12">
            {message.content.map((block, index) => (
              <div key={index}>
                {block.type === "text" && (
                  <MessageContent text={(block as { text: string }).text} />
                )}

                {block.type === "thinking" && (
                  <div className="rounded-6 border border-gray-300 bg-gray-50 p-12">
                    <button
                      onClick={() => toggleThinking(index)}
                      className="flex w-full items-center justify-between text-12 font-semibold text-gray-700 hover:text-gray-900"
                    >
                      <span>Thinking...</span>
                      <span>{expandedThinking.has(index) ? "−" : "+"}</span>
                    </button>
                    <div
                      className={`mt-8 text-13 text-gray-600 ${
                        expandedThinking.has(index) ? "block" : "hidden"
                      }`}
                    >
                      {(block as { thinking: string }).thinking}
                    </div>
                  </div>
                )}

                {block.type === "tool_use" && (
                  <ToolUseBlock
                    block={
                      block as {
                        id: string;
                        name: string;
                        input: Record<string, unknown>;
                      }
                    }
                  />
                )}

                {block.type === "tool_result" && (
                  <ToolResultBlock
                    block={
                      block as {
                        tool_use_id: string;
                        content: string | Record<string, unknown>;
                        is_error?: boolean;
                      }
                    }
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Timestamp */}
        {showTimestamp && (
          <div className="text-12 text-gray-500">
            {formatTime(message.created_at)}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Memoized MessageItem component
 *
 * Only re-renders when message or showTimestamp props change,
 * preventing unnecessary re-renders in message lists.
 */
export const MessageItem = memo(MessageItemComponent);

/** Tool use block component */
function ToolUseBlock({
  block,
}: {
  block: { id: string; name: string; input: Record<string, unknown> };
}) {
  return (
    <div className="rounded-6 border border-gray-400 bg-yellow-light p-12">
      <div className="mb-8 flex items-center justify-between">
        <div className="font-semibold text-13">{block.name}</div>
        <div className="rounded-3 bg-yellow-bg px-6 py-2 text-10 font-semibold uppercase text-yellow-text">
          Tool
        </div>
      </div>
      <div className="font-mono text-12 text-gray-600">
        {Object.entries(block.input).map(([key, value]) => (
          <div key={key}>
            <span className="text-gray-500">{key}:</span>{" "}
            {JSON.stringify(value)}
          </div>
        ))}
      </div>
    </div>
  );
}

/** Tool result block component */
function ToolResultBlock({
  block,
}: {
  block: {
    tool_use_id: string;
    content: string | Record<string, unknown>;
    is_error?: boolean;
  };
}) {
  const content =
    typeof block.content === "string"
      ? block.content
      : JSON.stringify(block.content, null, 2);

  return (
    <div
      className={`rounded-6 border p-12 ${
        block.is_error
          ? "border-red-DEFAULT bg-red-bg"
          : "border-gray-300 bg-gray-50"
      }`}
    >
      <div className="font-mono text-12 text-gray-700 whitespace-pre-wrap">
        {content}
      </div>
    </div>
  );
}
