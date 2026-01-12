/**
 * Application providers
 */

"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { ActiveSessionProvider } from "@/contexts/ActiveSessionContext";
import { AuthProvider } from "@/contexts/AuthContext";
import { ModeProvider } from "@/contexts/ModeContext";
import { PermissionsProvider } from "@/contexts/PermissionsContext";
import { SettingsProvider } from "@/contexts/SettingsContext";
import { queryClient } from "@/lib/query-client";

export function AppProviders({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <QueryClientProvider client={queryClient}>
      <SettingsProvider>
        <AuthProvider>
          <ModeProvider>
            <PermissionsProvider>
              <ActiveSessionProvider>{children}</ActiveSessionProvider>
            </PermissionsProvider>
          </ModeProvider>
        </AuthProvider>
      </SettingsProvider>
    </QueryClientProvider>
  );
}
