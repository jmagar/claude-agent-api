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
import type { Message, ToolCall, ToolStatus } from "@/types";
import {
  mergeContentBlocks,
  updateMessagesWithAccumulator,
  createUserMessage,
  createAssistantAccumulator,
} from "@/lib/streaming-utils";
import { logger } from "@/lib/logger";

export interface StreamingQueryState {
  /** Whether a query is currently streaming */
  isStreaming: boolean;
  /** Error message if streaming failed */
  error: string | null;
  /** Accumulated messages from stream */
  messages: Message[];
  /** Active tool calls from the stream */
  toolCalls: ToolCall[];
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
    toolCalls: [],
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
        await fetchEventSource("/api/streaming", {
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
            switch (event.event) {
              case "tool_start": {
                const toolStartData = JSON.parse(event.data);
                setState((prev) => {
                  const existingIndex = prev.toolCalls.findIndex(
                    (toolCall) => toolCall.id === toolStartData.id
                  );
                  const nextToolCalls = [...prev.toolCalls];
                  const nextToolCall: ToolCall = {
                    id: toolStartData.id,
                    name: toolStartData.name || "Tool",
                    status: "running",
                    input: toolStartData.input ?? {},
                    requires_approval: toolStartData.requires_approval ?? false,
                    parent_tool_use_id: toolStartData.parent_tool_use_id,
                    started_at: new Date(),
                  };

                  if (existingIndex >= 0) {
                    nextToolCalls[existingIndex] = {
                      ...nextToolCalls[existingIndex],
                      ...nextToolCall,
                    };
                  } else {
                    nextToolCalls.push(nextToolCall);
                  }

                  return {
                    ...prev,
                    toolCalls: nextToolCalls,
                  };
                });
                break;
              }

              case "tool_end": {
                const toolEndData = JSON.parse(event.data);
                setState((prev) => {
                  const existingIndex = prev.toolCalls.findIndex(
                    (toolCall) => toolCall.id === toolEndData.id
                  );
                  const nextToolCalls = [...prev.toolCalls];
                  const outputValue =
                    typeof toolEndData.output === "undefined"
                      ? toolEndData.content
                      : toolEndData.output;

                  if (existingIndex >= 0) {
                    const existing = nextToolCalls[existingIndex];
                    nextToolCalls[existingIndex] = {
                      ...existing,
                      status: "success",
                      output: outputValue,
                    };
                  } else {
                    nextToolCalls.push({
                      id: toolEndData.id,
                      name: toolEndData.name || "Tool",
                      status: "success",
                      input: toolEndData.input ?? {},
                      output: outputValue,
                      started_at: new Date(),
                    });
                  }

                  return {
                    ...prev,
                    toolCalls: nextToolCalls,
                  };
                });
                break;
              }

              case "init": {
                // Session initialized
                const initData = JSON.parse(event.data);
                setState((prev) => ({
                  ...prev,
                  sessionId: initData.session_id,
                }));
                break;
              }

              case "message": {
                if (!accumulatorRef.current) {
                  return;
                }
                // Append content to accumulator
                const messageData = JSON.parse(event.data);
                if (
                  messageData.content &&
                  Array.isArray(messageData.content) &&
                  accumulatorRef.current
                ) {
                  const toolCallsFromMessage: ToolCall[] = messageData.content
                    .filter((block: { type?: string }) => block.type === "tool_use")
                    .map(
                      (block: {
                        id: string;
                        name: string;
                        input: Record<string, unknown>;
                        parent_tool_use_id?: string;
                      }) => ({
                        id: block.id,
                        name: block.name,
                        status: "running" as ToolStatus,
                        input: block.input,
                        parent_tool_use_id: block.parent_tool_use_id,
                        started_at: new Date(),
                      })
                    );

                  // Merge new content blocks into accumulator
                  const nextAccumulator = mergeContentBlocks(
                    accumulatorRef.current,
                    messageData.content
                  );
                  accumulatorRef.current = nextAccumulator;

                  // Update state with accumulated message
                  setState((prev) => ({
                    ...prev,
                    messages: updateMessagesWithAccumulator(
                      prev.messages,
                      nextAccumulator
                    ),
                    toolCalls:
                      toolCallsFromMessage.length > 0
                        ? [
                            ...prev.toolCalls.filter(
                              (toolCall) =>
                                !toolCallsFromMessage.some(
                                  (incoming) => incoming.id === toolCall.id
                                )
                            ),
                            ...toolCallsFromMessage,
                          ]
                        : prev.toolCalls,
                  }));
                }
                break;
              }

              case "tool_result": {
                const toolResultData = JSON.parse(event.data);
                setState((prev) => {
                  const existingIndex = prev.toolCalls.findIndex(
                    (toolCall) => toolCall.id === toolResultData.tool_use_id
                  );
                  const nextToolCalls = [...prev.toolCalls];
                  const nextStatus = toolResultData.status as ToolStatus;
                  const outputValue =
                    typeof toolResultData.content === "undefined"
                      ? undefined
                      : toolResultData.content;
                  const errorValue =
                    toolResultData.is_error || nextStatus === "error"
                      ? typeof toolResultData.content === "string"
                        ? toolResultData.content
                        : JSON.stringify(toolResultData.content)
                      : undefined;

                  if (existingIndex >= 0) {
                    const existing = nextToolCalls[existingIndex];
                    nextToolCalls[existingIndex] = {
                      ...existing,
                      status: nextStatus,
                      output: outputValue,
                      error: errorValue,
                      duration_ms: toolResultData.duration_ms ?? existing.duration_ms,
                    };
                  } else {
                    nextToolCalls.push({
                      id: toolResultData.tool_use_id,
                      name: toolResultData.name || "Tool",
                      status: nextStatus,
                      input: toolResultData.input ?? {},
                      output: outputValue,
                      error: errorValue,
                      duration_ms: toolResultData.duration_ms,
                      started_at: new Date(),
                    });
                  }

                  return {
                    ...prev,
                    toolCalls: nextToolCalls,
                  };
                });
                break;
              }

              case "done": {
                // Streaming complete
                setState((prev) => ({ ...prev, isStreaming: false }));
                accumulatorRef.current = null;
                break;
              }

              case "error": {
                // Server-side error
                const errorData = JSON.parse(event.data);
                throw new Error(errorData.error || "Streaming error");
              }
            }
          },
          onerror: (error) => {
            logger.error(
              "SSE streaming error",
              error instanceof Error ? error : new Error(String(error)),
              { sessionId: state.sessionId }
            );
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
