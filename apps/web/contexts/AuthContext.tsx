"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface AuthContextType {
  apiKey: string | null;
  setApiKey: (key: string | null) => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [apiKey, setApiKeyState] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Load API key from localStorage on mount
    const storedKey = localStorage.getItem("auth.apiKey");
    if (storedKey) {
      setApiKeyState(storedKey);
    }
    setIsLoaded(true);
  }, []);

  const setApiKey = (key: string | null) => {
    if (key) {
      localStorage.setItem("auth.apiKey", key);
      setApiKeyState(key);
    } else {
      localStorage.removeItem("auth.apiKey");
      setApiKeyState(null);
    }
  };

  if (!isLoaded) {
    return null; // Or a loading spinner
  }

  return (
    <AuthContext.Provider
      value={{
        apiKey,
        setApiKey,
        isAuthenticated: !!apiKey,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
