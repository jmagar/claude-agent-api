"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { MessageDensity, PermissionMode, ThemeMode, ThreadingMode } from "@/types";

interface SettingsState {
  theme: ThemeMode;
  threadingMode: ThreadingMode;
  defaultPermissionMode: PermissionMode;
  workspaceBaseDir: string;
  messageDensity: MessageDensity;
  showTimestamps: boolean;
}

export interface SettingsContextType extends SettingsState {
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
  setThreadingMode: (mode: ThreadingMode) => void;
  setDefaultPermissionMode: (mode: PermissionMode) => void;
  setWorkspaceBaseDir: (dir: string) => void;
  setMessageDensity: (density: MessageDensity) => void;
  toggleShowTimestamps: () => void;
}

const SETTINGS_STORAGE_KEY = "settings";

const defaultSettings: SettingsState = {
  theme: "light",
  threadingMode: "adaptive",
  defaultPermissionMode: "default",
  workspaceBaseDir: "/workspaces",
  messageDensity: "comfortable",
  showTimestamps: true,
};

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

function applyTheme(theme: ThemeMode) {
  if (typeof window === "undefined") {
    return;
  }

  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
}

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<SettingsState>(defaultSettings);

  useEffect(() => {
    const stored = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as Partial<SettingsState>;
        setSettings({ ...defaultSettings, ...parsed });
      } catch {
        setSettings(defaultSettings);
      }
    }
  }, []);

  useEffect(() => {
    applyTheme(settings.theme);
  }, [settings.theme]);

  const updateSettings = (updater: (prev: SettingsState) => SettingsState) => {
    setSettings((prev) => {
      const next = updater(prev);
      localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  const contextValue = useMemo<SettingsContextType>(
    () => ({
      ...settings,
      setTheme: (theme) => updateSettings((prev) => ({ ...prev, theme })),
      toggleTheme: () =>
        updateSettings((prev) => ({
          ...prev,
          theme: prev.theme === "light" ? "dark" : "light",
        })),
      setThreadingMode: (threadingMode) =>
        updateSettings((prev) => ({ ...prev, threadingMode })),
      setDefaultPermissionMode: (defaultPermissionMode) =>
        updateSettings((prev) => ({ ...prev, defaultPermissionMode })),
      setWorkspaceBaseDir: (workspaceBaseDir) =>
        updateSettings((prev) => ({ ...prev, workspaceBaseDir })),
      setMessageDensity: (messageDensity) =>
        updateSettings((prev) => ({ ...prev, messageDensity })),
      toggleShowTimestamps: () =>
        updateSettings((prev) => ({
          ...prev,
          showTimestamps: !prev.showTimestamps,
        })),
    }),
    [settings]
  );

  return (
    <SettingsContext.Provider value={contextValue}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return context;
}
