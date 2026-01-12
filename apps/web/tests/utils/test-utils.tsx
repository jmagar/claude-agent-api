/**
 * Test utilities and custom render function
 */
import { ReactElement } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ActiveSessionProvider } from "@/contexts/ActiveSessionContext";
import { AuthProvider } from "@/contexts/AuthContext";
import { ModeProvider } from "@/contexts/ModeContext";
import { PermissionsProvider } from "@/contexts/PermissionsContext";
import { SettingsProvider } from "@/contexts/SettingsContext";

// Create a test query client with no retries
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

interface AllProvidersProps {
  children: React.ReactNode;
}

function AllProviders({ children }: AllProvidersProps) {
  const queryClient = createTestQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <SettingsProvider>
          <ModeProvider>
            <PermissionsProvider>
              <ActiveSessionProvider>{children}</ActiveSessionProvider>
            </PermissionsProvider>
          </ModeProvider>
        </SettingsProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">
) {
  return render(ui, { wrapper: AllProviders, ...options });
}

// Re-export everything
export * from "@testing-library/react";
export { customRender as render };

// Mock localStorage for tests
export function mockLocalStorage() {
  const store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      Object.keys(store).forEach((key) => delete store[key]);
    },
  };
}
