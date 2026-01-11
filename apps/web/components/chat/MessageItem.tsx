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
import { ToolCallCard } from "./ToolCallCard";
import { ThinkingBlock } from "./ThinkingBlock";
import { ThreadingVisualization } from "./ThreadingVisualization";
import type {
  Message,
  ToolResultBlock as ToolResultBlockType,
  ToolCall,
} from "@/types";
import { isTextBlock, isThinkingBlock, isToolUseBlock, isToolResultBlock } from "@/types";

export interface MessageItemProps {
  /** Message to display */
  message: Message;
  /** Whether to show timestamp */
  showTimestamp?: boolean;
  /** Tool calls keyed by tool_use id */
  toolCallsById?: Record<string, ToolCall>;
  /** Retry handler for failed tools */
  onRetryTool?: () => void;
}

function MessageItemComponent({
  message,
  showTimestamp = false,
  toolCallsById,
  onRetryTool,
}: MessageItemProps) {
  const [expandedThinking, setExpandedThinking] = useState<Set<number>>(
    new Set()
  );

  const isUser = message.role === "user";
  const label = isUser ? "You" : "Assistant";
  const toolUseBlocks = message.content.filter(isToolUseBlock);
  const toolUseBlockIds = new Set(toolUseBlocks.map((block) => block.id));
  const toolUseBlockOrder = new Map(
    toolUseBlocks.map((block, index) => [block.id, index])
  );
  const childToolCallsByParent = new Map<string, ToolCall[]>();
  const childToolCallIds = new Set<string>();

  if (toolCallsById) {
    Object.values(toolCallsById).forEach((toolCall) => {
      if (!toolCall.parent_tool_use_id) {
        return;
      }
      if (!toolUseBlockIds.has(toolCall.parent_tool_use_id)) {
        return;
      }
      if (!toolUseBlockIds.has(toolCall.id)) {
        return;
      }

      const existing = childToolCallsByParent.get(toolCall.parent_tool_use_id) ?? [];
      existing.push(toolCall);
      childToolCallsByParent.set(toolCall.parent_tool_use_id, existing);
      childToolCallIds.add(toolCall.id);
    });

    childToolCallsByParent.forEach((children, parentId) => {
      const sorted = [...children].sort((a, b) => {
        const aIndex = toolUseBlockOrder.get(a.id) ?? 0;
        const bIndex = toolUseBlockOrder.get(b.id) ?? 0;
        return aIndex - bIndex;
      });
      childToolCallsByParent.set(parentId, sorted);
    });
  }

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
                {isTextBlock(block) && <MessageContent text={block.text} />}

                {isThinkingBlock(block) && (
                  <ThinkingBlock
                    thinking={block.thinking}
                    collapsed={!expandedThinking.has(index)}
                    onToggle={() => toggleThinking(index)}
                  />
                )}

                {isToolUseBlock(block) && (() => {
                  if (childToolCallIds.has(block.id)) {
                    return null;
                  }

                  const resolvedToolCall =
                    toolCallsById?.[block.id] ?? {
                      id: block.id,
                      name: block.name,
                      status: "running",
                      input: block.input,
                      started_at: new Date(),
                    };
                  const childToolCalls = childToolCallsByParent.get(block.id);

                  if (childToolCalls && childToolCalls.length > 0) {
                    return (
                      <div className="flex flex-col gap-8">
                        <ToolCallCard
                          toolCall={resolvedToolCall}
                          onRetry={onRetryTool}
                        />
                        <ThreadingVisualization
                          toolCalls={childToolCalls}
                          mode="always"
                          onRetryTool={onRetryTool}
                        />
                      </div>
                    );
                  }

                  return (
                    <ToolCallCard
                      toolCall={resolvedToolCall}
                      onRetry={onRetryTool}
                    />
                  );
                })()}

                {isToolResultBlock(block) && <ToolResultBlock block={block} />}
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

/** Tool result block component */
function ToolResultBlock({ block }: { block: ToolResultBlockType }) {
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
