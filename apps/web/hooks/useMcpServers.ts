/**
 * useMcpServers Hook
 *
 * React Query hook for fetching and managing MCP server configurations.
 * Provides:
 * - List of configured MCP servers
 * - Loading and error states
 * - Automatic caching and revalidation
 * - Mutations for create, update, delete
 *
 * @example
 * ```tsx
 * const { servers, isLoading, error, createServer, updateServer, deleteServer } = useMcpServers();
 *
 * // Create new server
 * await createServer({ name: 'postgres', type: 'stdio', ... });
 *
 * // Update server
 * await updateServer('postgres', { enabled: false });
 *
 * // Delete server
 * await deleteServer('postgres');
 * ```
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { McpServerConfig } from '@/types';

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
  return data.servers;
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
  return data.server;
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
  return data.server;
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

  // Fetch servers query
  const {
    data: servers,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['mcp-servers'],
    queryFn: fetchMcpServers,
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
  });

  // Create server mutation
  const createMutation = useMutation({
    mutationFn: createMcpServer,
    onSuccess: () => {
      // Invalidate and refetch servers list
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
    },
  });

  // Update server mutation
  const updateMutation = useMutation({
    mutationFn: ({ name, config }: { name: string; config: Partial<McpServerConfig> }) =>
      updateMcpServer(name, config),
    onSuccess: () => {
      // Invalidate and refetch servers list
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
    },
  });

  // Delete server mutation
  const deleteMutation = useMutation({
    mutationFn: deleteMcpServer,
    onSuccess: () => {
      // Invalidate and refetch servers list
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
    },
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
