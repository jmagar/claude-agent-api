"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/contexts/AuthContext";
import { SettingsProvider } from "@/contexts/SettingsContext";
import { queryClient } from "@/lib/query-client";
import "./globals.css";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <QueryClientProvider client={queryClient}>
          <SettingsProvider>
            <AuthProvider>{children}</AuthProvider>
          </SettingsProvider>
        </QueryClientProvider>
      </body>
    </html>
  );
}
