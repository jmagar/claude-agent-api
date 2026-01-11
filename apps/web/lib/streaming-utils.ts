/**
 * Streaming utilities for SSE message handling
 *
 * Extracted from useStreamingQuery hook for better clarity and reusability.
 */

import type { Message, ContentBlock } from "@/types";

/**
 * Merge new content blocks into an accumulator message
 *
 * Text blocks are appended to the last text block if present,
 * other blocks are added as-is.
 */
export function mergeContentBlocks(
  accumulator: Message,
  newBlocks: ContentBlock[]
): Message {
  const updatedContent = [...accumulator.content];

  newBlocks.forEach((block) => {
    if (block.type === "text") {
      // Append to last text block or create new one
      const lastBlock = updatedContent[updatedContent.length - 1];

      if (lastBlock && lastBlock.type === "text") {
        // Create a new block instead of mutating the existing one
        updatedContent[updatedContent.length - 1] = {
          ...lastBlock,
          text: (lastBlock as { text: string }).text + (block as { text: string }).text,
        };
      } else {
        updatedContent.push(block);
      }
    } else {
      // Add non-text blocks as-is
      updatedContent.push(block);
    }
  });

  return {
    ...accumulator,
    content: updatedContent,
  };
}

/**
 * Update messages array with accumulated message
 *
 * Replaces existing message with same ID or appends if not found.
 */
export function updateMessagesWithAccumulator(
  messages: Message[],
  accumulator: Message
): Message[] {
  const newMessages = [...messages];
  const existingIndex = newMessages.findIndex((m) => m.id === accumulator.id);

  if (existingIndex >= 0) {
    newMessages[existingIndex] = { ...accumulator };
  } else {
    newMessages.push({ ...accumulator });
  }

  return newMessages;
}

/**
 * Create a user message from text input
 */
export function createUserMessage(text: string): Message {
  return {
    id: `user-${Date.now()}`,
    role: "user",
    content: [{ type: "text", text }],
    created_at: new Date(),
  };
}

/**
 * Create an empty assistant message accumulator
 */
export function createAssistantAccumulator(): Message {
  return {
    id: `assistant-${Date.now()}`,
    role: "assistant",
    content: [],
    created_at: new Date(),
  };
}
