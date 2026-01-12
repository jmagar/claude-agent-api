/**
 * useMcpServerStatus Hook
 *
 * React Query hook for polling MCP server status with configurable intervals.
 * Provides real-time status updates for connection monitoring, health checks,
 * and automatic reconnection detection.
 *
 * @module hooks/useMcpServerStatus
 *
 * @example
 * ```tsx
 * // Poll all servers every 30 seconds
 * const { statusMap, isPolling } = useMcpServerStatus({
 *   enabled: true,
 *   refetchInterval: 30000
 * });
 *
 * // Check specific server status
 * const postgresStatus = statusMap?.postgres;
 * ```
 *
 * @example
 * ```tsx
 * // Poll single server with custom interval
 * const { status, lastChecked } = useMcpServerStatus({
 *   serverName: 'postgres',
 *   enabled: true,
 *   refetchInterval: 10000, // 10 seconds
 *   onStatusChange: (oldStatus, newStatus) => {
 *     if (oldStatus === 'active' && newStatus === 'failed') {
 *       toast.error('Server connection lost');
 *     }
 *   }
 * });
 * ```
 */

'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useRef } from 'react';
import type { McpServerConfig, McpServerStatus } from '@/types';

/**
 * Server status polling options
 */
export interface McpServerStatusOptions {
  /**
   * Server name to poll (if omitted, polls all servers)
   */
  serverName?: string;

  /**
   * Enable/disable status polling
   * @default false
   */
  enabled?: boolean;

  /**
   * Polling interval in milliseconds
   * @default 30000 (30 seconds)
   */
  refetchInterval?: number;

  /**
   * Callback when server status changes
   */
  onStatusChange?: (
    oldStatus: McpServerStatus,
    newStatus: McpServerStatus,
    serverName: string
  ) => void;

  /**
   * Callback when polling fails
   */
  onError?: (error: Error) => void;
}

/**
 * Server status map (server name -> status)
 */
export type ServerStatusMap = Record<string, McpServerStatus>;

/**
 * Single server status result
 */
export interface ServerStatusResult {
  status: McpServerStatus | null;
  lastChecked: Date | null;
  isPolling: boolean;
  error: string | null;
}

/**
 * All servers status result
 */
export interface AllServersStatusResult {
  statusMap: ServerStatusMap | null;
  lastChecked: Date | null;
  isPolling: boolean;
  error: string | null;
}

/**
 * Fetch status for all MCP servers
 */
async function fetchAllServerStatuses(): Promise<ServerStatusMap> {
  const response = await fetch('/api/mcp-servers');

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { message: 'Failed to fetch server statuses' },
    }));
    throw new Error(error.error?.message ?? 'Failed to fetch server statuses');
  }

  const data = await response.json();
  const servers = Array.isArray(data) ? data : data.servers ?? [];

  // Build status map from servers
  const statusMap: ServerStatusMap = {};
  for (const server of servers) {
    statusMap[server.name] = server.status ?? 'disabled';
  }

  return statusMap;
}

/**
 * Fetch status for a specific MCP server
 */
async function fetchServerStatus(serverName: string): Promise<McpServerStatus> {
  const response = await fetch(
    `/api/mcp-servers/${encodeURIComponent(serverName)}`
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { message: 'Failed to fetch server status' },
    }));
    throw new Error(error.error?.message ?? 'Failed to fetch server status');
  }

  const data = await response.json();
  const server = data.server ?? data;
  return server.status ?? 'disabled';
}

/**
 * Hook for polling MCP server status
 *
 * @param options - Polling configuration options
 * @returns Status data, polling state, and error information
 *
 * @example
 * ```tsx
 * // Monitor all servers
 * function ServerMonitor() {
 *   const { statusMap, isPolling } = useMcpServerStatus({
 *     enabled: true,
 *     refetchInterval: 15000,
 *     onStatusChange: (old, new, name) => {
 *       console.log(`${name}: ${old} -> ${new}`);
 *     }
 *   });
 *
 *   return (
 *     <div>
 *       {isPolling && <Spinner />}
 *       {Object.entries(statusMap || {}).map(([name, status]) => (
 *         <ServerStatusBadge key={name} name={name} status={status} />
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useMcpServerStatus(
  options: McpServerStatusOptions = {}
): AllServersStatusResult | ServerStatusResult {
  const {
    serverName,
    enabled = false,
    refetchInterval = 30000,
    onStatusChange,
    onError,
  } = options;

  const queryClient = useQueryClient();
  const previousStatusRef = useRef<ServerStatusMap | McpServerStatus | null>(
    null
  );

  // Determine query key and fetch function based on whether serverName is provided
  const queryKey = serverName
    ? ['mcp-server-status', serverName]
    : ['mcp-servers-status'];

  const queryFn = serverName
    ? () => fetchServerStatus(serverName)
    : fetchAllServerStatuses;

  // Query with polling
  const { data, isLoading, error, dataUpdatedAt } = useQuery({
    queryKey,
    queryFn,
    enabled,
    refetchInterval: enabled ? refetchInterval : false,
    refetchIntervalInBackground: true,
    staleTime: refetchInterval / 2, // Consider data stale after half the polling interval
    gcTime: refetchInterval * 2, // Cache for twice the polling interval
    retry: 1, // Only retry once to avoid overwhelming the server
    retryDelay: 5000, // Wait 5 seconds before retry
  });

  // Handle status changes
  const handleStatusChange = useCallback(() => {
    if (!data || !onStatusChange) return;

    const previousStatus = previousStatusRef.current;

    if (serverName) {
      // Single server status change
      const newStatus = data as McpServerStatus;
      if (previousStatus && previousStatus !== newStatus) {
        onStatusChange(
          previousStatus as McpServerStatus,
          newStatus,
          serverName
        );
      }
      previousStatusRef.current = newStatus;
    } else {
      // Multiple servers status changes
      const newStatusMap = data as ServerStatusMap;
      const oldStatusMap = previousStatus as ServerStatusMap | null;

      if (oldStatusMap) {
        // Check each server for status changes
        for (const [name, newStatus] of Object.entries(newStatusMap)) {
          const oldStatus = oldStatusMap[name];
          if (oldStatus && oldStatus !== newStatus) {
            onStatusChange(oldStatus, newStatus, name);
          }
        }
      }

      previousStatusRef.current = newStatusMap;
    }
  }, [data, onStatusChange, serverName]);

  // Trigger status change callback when data changes
  if (data !== previousStatusRef.current) {
    handleStatusChange();
  }

  // Handle errors
  if (error && onError) {
    onError(error as Error);
  }

  // Format last checked time
  const lastChecked = dataUpdatedAt ? new Date(dataUpdatedAt) : null;

  // Return result based on query type
  if (serverName) {
    return {
      status: (data as McpServerStatus) ?? null,
      lastChecked,
      isPolling: enabled && !isLoading,
      error: error ? (error as Error).message : null,
    } as ServerStatusResult;
  }

  return {
    statusMap: (data as ServerStatusMap) ?? null,
    lastChecked,
    isPolling: enabled && !isLoading,
    error: error ? (error as Error).message : null,
  } as AllServersStatusResult;
}

/**
 * Helper hook for monitoring a single server's status with toast notifications
 *
 * @param serverName - Name of server to monitor
 * @param options - Additional polling options
 * @returns Server status and polling state
 *
 * @example
 * ```tsx
 * function PostgresStatus() {
 *   const { status, isPolling } = useMonitorServerStatus('postgres', {
 *     enabled: true,
 *     refetchInterval: 10000
 *   });
 *
 *   return (
 *     <Badge variant={status === 'active' ? 'success' : 'destructive'}>
 *       {status} {isPolling && '•'}
 *     </Badge>
 *   );
 * }
 * ```
 */
export function useMonitorServerStatus(
  serverName: string,
  options: Omit<McpServerStatusOptions, 'serverName'> = {}
): ServerStatusResult {
  return useMcpServerStatus({
    ...options,
    serverName,
  }) as ServerStatusResult;
}

/**
 * Helper hook for monitoring all servers with automatic reconnection detection
 *
 * @param options - Polling options
 * @returns All servers status map and polling state
 *
 * @example
 * ```tsx
 * function ServersDashboard() {
 *   const { statusMap, isPolling } = useMonitorAllServers({
 *     enabled: true,
 *     refetchInterval: 30000,
 *     onStatusChange: (old, new, name) => {
 *       if (old === 'failed' && new === 'active') {
 *         toast.success(`${name} reconnected!`);
 *       }
 *     }
 *   });
 *
 *   return <ServerStatusGrid statusMap={statusMap} />;
 * }
 * ```
 */
export function useMonitorAllServers(
  options: Omit<McpServerStatusOptions, 'serverName'> = {}
): AllServersStatusResult {
  return useMcpServerStatus(options) as AllServersStatusResult;
}
