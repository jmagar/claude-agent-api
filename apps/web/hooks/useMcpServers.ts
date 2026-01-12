/**
 * useMcpServers Hook
 *
 * React Query hook for fetching and managing MCP server configurations.
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { v4 as uuidv4 } from 'uuid';
import type { McpServerConfig } from '@/types';
import { queryKeys } from '@/lib/query-keys';
import { createOptimisticHandlers } from '@/lib/react-query/optimistic';

interface McpServersResponse {
  servers: McpServerConfig[];
}

const API_BASE = '/api/mcp-servers';

/**
 * Fetch all MCP servers
 */
async function fetchMcpServers(): Promise<McpServerConfig[]> {
  const response = await fetch(API_BASE);

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { message: 'Failed to fetch MCP servers' },
    }));
    throw new Error(error.error?.message ?? 'Failed to fetch MCP servers');
  }

  const data: McpServersResponse = await response.json();
  return data.servers ?? (data as unknown as McpServerConfig[]);
}

/**
 * Create a new MCP server
 */
async function createMcpServer(
  config: Partial<McpServerConfig>
): Promise<McpServerConfig> {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { message: 'Failed to create MCP server' },
    }));
    throw new Error(error.error?.message ?? 'Failed to create MCP server');
  }

  const data = await response.json();
  return data.server ?? data;
}

/**
 * Update an existing MCP server
 */
async function updateMcpServer(
  name: string,
  config: Partial<McpServerConfig>
): Promise<McpServerConfig> {
  const response = await fetch(`${API_BASE}/${encodeURIComponent(name)}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { message: 'Failed to update MCP server' },
    }));
    throw new Error(error.error?.message ?? 'Failed to update MCP server');
  }

  const data = await response.json();
  return data.server ?? data;
}

/**
 * Delete an MCP server
 */
async function deleteMcpServer(name: string): Promise<void> {
  const response = await fetch(`${API_BASE}/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { message: 'Failed to delete MCP server' },
    }));
    throw new Error(error.error?.message ?? 'Failed to delete MCP server');
  }
}

/**
 * Hook for managing MCP servers
 */
export function useMcpServers() {
  const queryClient = useQueryClient();
  const queryKey = queryKeys.mcpServers.lists();

  // Fetch servers query
  const {
    data: servers,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey,
    queryFn: fetchMcpServers,
    gcTime: 5 * 60 * 1000,
  });

  // Create server mutation
  const createMutation = useMutation({
    mutationFn: createMcpServer,
    ...createOptimisticHandlers<McpServerConfig[], Partial<McpServerConfig>>({
      queryClient,
      queryKey,
      updater: (current, variables) => {
        const now = new Date().toISOString();
        const optimistic: McpServerConfig = {
          id: uuidv4(),
          name: variables.name ?? 'new-server',
          transport_type: variables.transport_type ?? 'stdio',
          command: variables.command,
          args: variables.args,
          url: variables.url,
          headers: variables.headers,
          env: variables.env,
          enabled: variables.enabled ?? true,
          status: variables.status ?? 'disabled',
          error: variables.error,
          created_at: now,
          updated_at: now,
          tools_count: variables.tools_count,
          resources_count: variables.resources_count,
        };

        return [optimistic, ...(current ?? [])];
      },
    }),
  });

  // Update server mutation
  const updateMutation = useMutation({
    mutationFn: ({ name, config }: { name: string; config: Partial<McpServerConfig> }) =>
      updateMcpServer(name, config),
    ...createOptimisticHandlers<McpServerConfig[], { name: string; config: Partial<McpServerConfig> }>({
      queryClient,
      queryKey,
      updater: (current, variables) =>
        (current ?? []).map((server) =>
          server.name === variables.name
            ? { ...server, ...variables.config, updated_at: new Date().toISOString() }
            : server
        ),
    }),
  });

  // Delete server mutation
  const deleteMutation = useMutation({
    mutationFn: deleteMcpServer,
    ...createOptimisticHandlers<McpServerConfig[], string>({
      queryClient,
      queryKey,
      updater: (current, name) =>
        (current ?? []).filter((server) => server.name !== name),
    }),
  });

  return {
    servers: servers ?? null,
    isLoading,
    error: error?.message ?? null,
    refetch,
    createServer: createMutation.mutateAsync,
    updateServer: (name: string, config: Partial<McpServerConfig>) =>
      updateMutation.mutateAsync({ name, config }),
    deleteServer: deleteMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
