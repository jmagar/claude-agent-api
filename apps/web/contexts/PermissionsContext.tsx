/**
 * PermissionsContext - Manages tool permission mode state
 *
 * Provides:
 * - Current permission mode (default, acceptEdits, dontAsk, bypassPermissions)
 * - Permission mode persistence to localStorage
 * - Allowed tools list for "Always allow" feature
 *
 * @see FR-020: System MUST display permissions chip with four modes
 * @see FR-021: System MUST allow cycling through permission modes
 */

"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import type { PermissionMode } from "@/types";

/** Context value type for permission management */
export interface PermissionsContextType {
  /** Current permission mode */
  mode: PermissionMode;
  /** Update the permission mode and persist to localStorage */
  setMode: (mode: PermissionMode) => void;
  /** Cycle to the next permission mode */
  cycleMode: () => void;
  /** Set of tool names that are always allowed */
  alwaysAllowedTools: Set<string>;
  /** Add a tool to the always-allowed list */
  addAlwaysAllowedTool: (toolName: string) => void;
  /** Remove a tool from the always-allowed list */
  removeAlwaysAllowedTool: (toolName: string) => void;
  /** Clear all always-allowed tools */
  clearAlwaysAllowedTools: () => void;
  /** Check if a tool is always allowed */
  isToolAlwaysAllowed: (toolName: string) => boolean;
}

const PermissionsContext = createContext<PermissionsContextType | undefined>(undefined);

/** localStorage key for permission mode persistence */
const PERMISSION_MODE_STORAGE_KEY = "permissionMode";
/** localStorage key for always-allowed tools */
const ALWAYS_ALLOWED_STORAGE_KEY = "alwaysAllowedTools";

/** Order of permission modes for cycling */
const MODE_ORDER: PermissionMode[] = ["default", "acceptEdits", "dontAsk", "bypassPermissions"];

export function PermissionsProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<PermissionMode>("default");
  const [alwaysAllowedTools, setAlwaysAllowedTools] = useState<Set<string>>(new Set());
  const [isHydrated, setIsHydrated] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const storedMode = localStorage.getItem(PERMISSION_MODE_STORAGE_KEY);
      const storedAllowed = localStorage.getItem(ALWAYS_ALLOWED_STORAGE_KEY);

      if (storedMode) {
        const parsedMode = JSON.parse(storedMode) as PermissionMode;
        if (MODE_ORDER.includes(parsedMode)) {
          setModeState(parsedMode);
        }
      }

      if (storedAllowed) {
        const parsedAllowed = JSON.parse(storedAllowed) as string[];
        setAlwaysAllowedTools(new Set(parsedAllowed));
      }
    } catch {
      // Invalid JSON, use defaults
    }
    setIsHydrated(true);
  }, []);

  const setMode = useCallback((newMode: PermissionMode) => {
    setModeState(newMode);
    localStorage.setItem(PERMISSION_MODE_STORAGE_KEY, JSON.stringify(newMode));
  }, []);

  const cycleMode = useCallback(() => {
    setModeState((current) => {
      const currentIndex = MODE_ORDER.indexOf(current);
      const nextIndex = (currentIndex + 1) % MODE_ORDER.length;
      const nextMode = MODE_ORDER[nextIndex];
      localStorage.setItem(PERMISSION_MODE_STORAGE_KEY, JSON.stringify(nextMode));
      return nextMode;
    });
  }, []);

  const addAlwaysAllowedTool = useCallback((toolName: string) => {
    setAlwaysAllowedTools((prev) => {
      const next = new Set(prev);
      next.add(toolName);
      localStorage.setItem(ALWAYS_ALLOWED_STORAGE_KEY, JSON.stringify([...next]));
      return next;
    });
  }, []);

  const removeAlwaysAllowedTool = useCallback((toolName: string) => {
    setAlwaysAllowedTools((prev) => {
      const next = new Set(prev);
      next.delete(toolName);
      localStorage.setItem(ALWAYS_ALLOWED_STORAGE_KEY, JSON.stringify([...next]));
      return next;
    });
  }, []);

  const clearAlwaysAllowedTools = useCallback(() => {
    setAlwaysAllowedTools(new Set());
    localStorage.removeItem(ALWAYS_ALLOWED_STORAGE_KEY);
  }, []);

  const isToolAlwaysAllowed = useCallback(
    (toolName: string) => alwaysAllowedTools.has(toolName),
    [alwaysAllowedTools]
  );

  // Don't render until hydrated to prevent hydration mismatch
  if (!isHydrated) {
    return null;
  }

  return (
    <PermissionsContext.Provider
      value={{
        mode,
        setMode,
        cycleMode,
        alwaysAllowedTools,
        addAlwaysAllowedTool,
        removeAlwaysAllowedTool,
        clearAlwaysAllowedTools,
        isToolAlwaysAllowed,
      }}
    >
      {children}
    </PermissionsContext.Provider>
  );
}

export function usePermissions() {
  const context = useContext(PermissionsContext);
  if (!context) {
    throw new Error("usePermissions must be used within a PermissionsProvider");
  }
  return context;
}

/**
 * Optional variant of usePermissions that returns undefined if no provider is available
 * Use this when you want to render permission UI with a local fallback state
 */
export function usePermissionsOptional() {
  return useContext(PermissionsContext);
}
