/**
 * useStreamingQuery hook
 *
 * Manages SSE streaming for chat messages with state management.
 * Handles streaming events, errors, and message accumulation.
 *
 * @see tests/integration/chat-flow.test.tsx for test specifications
 */

"use client";

import { useState, useCallback, useRef } from "react";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import type { Message, ContentBlock } from "@/types";
import {
  mergeContentBlocks,
  updateMessagesWithAccumulator,
  createUserMessage,
  createAssistantAccumulator,
} from "@/lib/streaming-utils";

export interface StreamingQueryState {
  /** Whether a query is currently streaming */
  isStreaming: boolean;
  /** Error message if streaming failed */
  error: string | null;
  /** Accumulated messages from stream */
  messages: Message[];
  /** Current session ID */
  sessionId: string | null;
}

export interface UseStreamingQueryReturn extends StreamingQueryState {
  /** Send a new query message */
  sendMessage: (text: string) => Promise<void>;
  /** Retry last failed message */
  retry: () => void;
  /** Clear error state */
  clearError: () => void;
}

export function useStreamingQuery(
  initialSessionId?: string
): UseStreamingQueryReturn {
  const [state, setState] = useState<StreamingQueryState>({
    isStreaming: false,
    error: null,
    messages: [],
    sessionId: initialSessionId || null,
  });

  const lastMessageRef = useRef<string>("");
  const accumulatorRef = useRef<Message | null>(null);

  // Clear error
  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  // Send message with SSE streaming
  const sendMessage = useCallback(
    async (text: string) => {
      lastMessageRef.current = text;

      // Add user message immediately
      const userMessage = createUserMessage(text);

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isStreaming: true,
        error: null,
      }));

      // Initialize accumulator for assistant message
      accumulatorRef.current = createAssistantAccumulator();

      try {
        await fetchEventSource("/api/streaming/query", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: text,
            session_id: state.sessionId,
          }),
          onopen: async (response) => {
            if (!response.ok) {
              throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
          },
          onmessage: (event) => {
            if (!accumulatorRef.current) return;

            switch (event.event) {
              case "init":
                // Session initialized
                const initData = JSON.parse(event.data);
                setState((prev) => ({
                  ...prev,
                  sessionId: initData.session_id,
                }));
                break;

              case "message":
                // Append content to accumulator
                const messageData = JSON.parse(event.data);
                if (
                  messageData.content &&
                  Array.isArray(messageData.content) &&
                  accumulatorRef.current
                ) {
                  // Merge new content blocks into accumulator
                  accumulatorRef.current = mergeContentBlocks(
                    accumulatorRef.current,
                    messageData.content
                  );

                  // Update state with accumulated message
                  setState((prev) => ({
                    ...prev,
                    messages: updateMessagesWithAccumulator(
                      prev.messages,
                      accumulatorRef.current!
                    ),
                  }));
                }
                break;

              case "done":
                // Streaming complete
                setState((prev) => ({ ...prev, isStreaming: false }));
                accumulatorRef.current = null;
                break;

              case "error":
                // Server-side error
                const errorData = JSON.parse(event.data);
                throw new Error(errorData.error || "Streaming error");
            }
          },
          onerror: (error) => {
            console.error("SSE error:", error);
            throw error;
          },
        });
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to send message";

        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error: errorMessage,
        }));
        accumulatorRef.current = null;
      }
    },
    [state.sessionId]
  );

  // Retry last message
  const retry = useCallback(() => {
    if (lastMessageRef.current) {
      sendMessage(lastMessageRef.current);
    }
  }, [sendMessage]);

  return {
    ...state,
    sendMessage,
    retry,
    clearError,
  };
}
