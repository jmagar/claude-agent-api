/**
 * Active session context
 */

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import type { Message, PermissionMode, Session } from "@/types";

interface ActiveSessionContextValue {
  session: Session | null;
  messages: Message[];
  isStreaming: boolean;
  setSession: (session: Session | null) => void;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[] | ((prev: Message[]) => Message[])) => void;
  clearMessages: () => void;
  setIsStreaming: (isStreaming: boolean) => void;
  permissionMode: PermissionMode;
  setPermissionMode: (mode: PermissionMode) => void;
}

const ActiveSessionContext = createContext<ActiveSessionContextValue | null>(
  null
);

export function ActiveSessionProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [permissionMode, setPermissionMode] = useState<PermissionMode>("auto");

  const addMessage = useCallback((message: Message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const setAllMessages = useCallback(
    (nextMessages: Message[] | ((prev: Message[]) => Message[])) => {
      setMessages((prev) =>
        typeof nextMessages === "function"
          ? (nextMessages as (current: Message[]) => Message[])(prev)
          : nextMessages
      );
    },
    []
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const value = useMemo(
    () => ({
      session,
      messages,
      isStreaming,
      setSession,
      addMessage,
      setMessages: setAllMessages,
      clearMessages,
      setIsStreaming,
      permissionMode,
      setPermissionMode,
    }),
    [
      session,
      messages,
      isStreaming,
      setSession,
      addMessage,
      setAllMessages,
      clearMessages,
      setIsStreaming,
      permissionMode,
      setPermissionMode,
    ]
  );

  return (
    <ActiveSessionContext.Provider value={value}>
      {children}
    </ActiveSessionContext.Provider>
  );
}

export function useActiveSession() {
  const context = useContext(ActiveSessionContext);
  if (!context) {
    throw new Error("useActiveSession must be used within ActiveSessionProvider");
  }
  return context;
}
