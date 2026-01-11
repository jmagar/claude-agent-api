/**
 * Server-Sent Events (SSE) streaming utilities
 */
import { fetchEventSource } from "@microsoft/fetch-event-source";

export interface StreamOptions {
  apiKey: string;
  sessionId?: string;
  onInit?: (data: { session_id: string }) => void;
  onMessage?: (data: unknown) => void;
  onMessageDelta?: (data: { delta: string }) => void;
  onToolStart?: (data: { tool_name: string; tool_use_id: string }) => void;
  onToolEnd?: (data: { tool_use_id: string }) => void;
  onThinkingStart?: (data: { thinking_id: string }) => void;
  onThinkingDelta?: (data: { delta: string }) => void;
  onThinkingEnd?: (data: { thinking_id: string }) => void;
  onError?: (error: Error) => void;
  onResult?: (data: { status: string; session_id: string }) => void;
  onAbort?: () => void;
}

export class StreamController {
  private abortController: AbortController | null = null;

  async startStream(
    url: string,
    body: Record<string, unknown>,
    options: StreamOptions
  ): Promise<void> {
    this.abortController = new AbortController();

    try {
      await fetchEventSource(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": options.apiKey,
        },
        body: JSON.stringify({
          ...body,
          session_id: options.sessionId,
        }),
        signal: this.abortController.signal,
        openWhenHidden: true,

        onopen: async (response) => {
          if (!response.ok) {
            const error = await response.json().catch(() => ({
              error: "Stream connection failed",
            }));
            throw new Error(error.error || error.detail || "Stream failed");
          }
        },

        onmessage: (event) => {
          try {
            const data = JSON.parse(event.data);

            switch (event.event) {
              case "init":
                options.onInit?.(data);
                break;
              case "message":
                options.onMessage?.(data);
                break;
              case "message_delta":
                options.onMessageDelta?.(data);
                break;
              case "tool_start":
                options.onToolStart?.(data);
                break;
              case "tool_end":
                options.onToolEnd?.(data);
                break;
              case "thinking_start":
                options.onThinkingStart?.(data);
                break;
              case "thinking_delta":
                options.onThinkingDelta?.(data);
                break;
              case "thinking_end":
                options.onThinkingEnd?.(data);
                break;
              case "error":
                options.onError?.(new Error(data.error || "Stream error"));
                break;
              case "result":
                options.onResult?.(data);
                break;
            }
          } catch (error) {
            console.error("Failed to parse stream event:", error);
          }
        },

        onerror: (error) => {
          console.error("Stream error:", error);
          options.onError?.(
            error instanceof Error ? error : new Error("Stream error")
          );
          throw error; // Rethrow to stop retry
        },

        onclose: () => {
          this.abortController = null;
        },
      });
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        options.onAbort?.();
        return;
      }
      throw error;
    }
  }

  abort(): void {
    this.abortController?.abort();
    this.abortController = null;
  }

  isStreaming(): boolean {
    return this.abortController !== null;
  }
}

export function createStreamController(): StreamController {
  return new StreamController();
}
