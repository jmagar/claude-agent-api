/**
 * Composer component
 *
 * Message input with auto-resize, Shift+Enter multiline support,
 * draft persistence, and loading states.
 *
 * @see tests/unit/components/Composer.test.tsx for test specifications
 * @see wireframes/01-chat-brainstorm-mode.html for design
 */

"use client";

import { useState, useEffect, useRef, KeyboardEvent, ChangeEvent } from "react";

export interface ComposerProps {
  /** Callback when message is sent */
  onSend: (message: string) => void;
  /** Whether a response is currently loading/streaming */
  isLoading?: boolean;
  /** Session ID for draft persistence */
  sessionId?: string;
  /** Max height in pixels (default: 80px) */
  maxHeight?: number;
}

export function Composer({
  onSend,
  isLoading = false,
  sessionId,
  maxHeight = 80,
}: ComposerProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load draft from localStorage on mount
  useEffect(() => {
    if (sessionId && typeof window !== "undefined") {
      const draft = localStorage.getItem(`draft:${sessionId}`);
      if (draft) {
        setValue(draft);
      }
    }
  }, [sessionId]);

  // Save draft to localStorage (debounced)
  useEffect((): void | (() => void) => {
    if (sessionId && typeof window !== "undefined" && value) {
      const timeoutId = setTimeout(() => {
        localStorage.setItem(`draft:${sessionId}`, value);
      }, 300);
      return () => clearTimeout(timeoutId);
    }
  }, [value, sessionId]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`;
    }
  }, [value, maxHeight]);

  // Handle input change
  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
  };

  // Handle key down (Enter to send, Shift+Enter for newline)
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Handle send
  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;

    onSend(trimmed);
    setValue("");

    // Clear draft from localStorage
    if (sessionId && typeof window !== "undefined") {
      localStorage.removeItem(`draft:${sessionId}`);
    }
  };

  const isDisabled = isLoading;
  const isSendDisabled = isDisabled || !value.trim();

  return (
    <div
      className="border-t border-gray-300 bg-white px-20 py-16"
      data-testid="composer"
    >
      <div className="flex gap-12">
        {/* Textarea */}
        <div className="flex flex-1 flex-col">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            disabled={isDisabled}
            placeholder="Message Claude..."
            aria-label="Message input"
            aria-disabled={isDisabled}
            className="min-h-[40px] w-full resize-none rounded-6 border border-gray-300 px-12 py-10 text-14 focus:border-gray-700 focus:outline-none disabled:bg-gray-100 disabled:text-gray-500"
            style={{ maxHeight: `${maxHeight}px` }}
            rows={1}
          />

          {/* Keyboard hint */}
          <div className="mt-4 text-12 text-gray-500">
            <span className="font-semibold">Shift + Enter</span> for new line
          </div>
        </div>

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={isSendDisabled}
          aria-label="Send message"
          aria-disabled={isSendDisabled}
          className="h-40 rounded-6 bg-gray-700 px-20 text-14 font-medium text-white hover:bg-gray-600 disabled:bg-gray-300 disabled:text-gray-500"
        >
          {isLoading ? "Sending..." : "Send"}
        </button>
      </div>

      {/* Loading indicator */}
      {isLoading && (
        <div
          className="mt-8 text-12 text-gray-500"
          data-testid="composer-loading"
        >
          Claude is typing...
        </div>
      )}
    </div>
  );
}
