"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { MessageDensity, PermissionMode, ThemeMode, ThreadingMode } from "@/types";

interface SettingsState {
  theme: ThemeMode;
  threadingMode: ThreadingMode;
  defaultPermissionMode: PermissionMode;
  workspaceBaseDir: string;
  messageDensity: MessageDensity;
  defaultModel: string;
  autoCompactThreshold: number;
  showTimestamps: boolean;
}

export interface SettingsContextType extends SettingsState {
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
  setThreadingMode: (mode: ThreadingMode) => void;
  setDefaultPermissionMode: (mode: PermissionMode) => void;
  setWorkspaceBaseDir: (dir: string) => void;
  setMessageDensity: (density: MessageDensity) => void;
  setDefaultModel: (model: string) => void;
  setAutoCompactThreshold: (threshold: number) => void;
  toggleShowTimestamps: () => void;
}

const SETTINGS_STORAGE_KEY = "settings";

const defaultSettings: SettingsState = {
  theme: "system",
  threadingMode: "adaptive",
  defaultPermissionMode: "default",
  workspaceBaseDir: "/workspaces",
  messageDensity: "comfortable",
  defaultModel: "sonnet",
  autoCompactThreshold: 100,
  showTimestamps: true,
};

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

function applyTheme(theme: ThemeMode) {
  if (typeof window === "undefined") {
    return;
  }

  const root = document.documentElement;

  if (theme === "system") {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    root.classList.toggle("dark", prefersDark);
  } else {
    root.classList.toggle("dark", theme === "dark");
  }
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

  const updateSettings = (partial: Partial<SettingsState>) => {
    setSettings((prev) => {
      const next = { ...prev, ...partial };
      localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  const contextValue = useMemo<SettingsContextType>(
    () => ({
      ...settings,
      setTheme: (theme) => updateSettings({ theme }),
      toggleTheme: () =>
        updateSettings({
          theme: settings.theme === "light" ? "dark" : "light",
        }),
      setThreadingMode: (threadingMode) => updateSettings({ threadingMode }),
      setDefaultPermissionMode: (defaultPermissionMode) =>
        updateSettings({ defaultPermissionMode }),
      setWorkspaceBaseDir: (workspaceBaseDir) =>
        updateSettings({ workspaceBaseDir }),
      setMessageDensity: (messageDensity) => updateSettings({ messageDensity }),
      setDefaultModel: (defaultModel) => updateSettings({ defaultModel }),
      setAutoCompactThreshold: (autoCompactThreshold) =>
        updateSettings({ autoCompactThreshold }),
      toggleShowTimestamps: () =>
        updateSettings({ showTimestamps: !settings.showTimestamps }),
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
