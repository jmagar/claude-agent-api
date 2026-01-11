/**
 * McpServerList Component
 *
 * Displays a list of configured MCP (Model Context Protocol) servers with:
 * - Server status indicators (active, disabled, failed)
 * - Server details (command, tools, resources count)
 * - Action buttons (Add, Edit, Delete, Share)
 * - Search/filter functionality
 * - Loading, error, and empty states
 *
 * @example
 * ```tsx
 * <McpServerList
 *   onAdd={() => setShowForm(true)}
 *   onEdit={(server) => editServer(server)}
 *   onDelete={(name) => deleteServer(name)}
 *   onShare={(server) => shareServer(server)}
 * />
 * ```
 */

'use client';

import { useState, useMemo } from 'react';
import { useMcpServers } from '@/hooks/useMcpServers';
import { McpServerCard } from './McpServerCard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PlusIcon, SearchIcon, AlertCircleIcon } from 'lucide-react';
import type { McpServerConfig } from '@/types';

export interface McpServerListProps {
  /**
   * Callback when Add Server button is clicked
   */
  onAdd?: () => void;

  /**
   * Callback when Edit button is clicked for a server
   * @param server - The server to edit
   */
  onEdit?: (server: McpServerConfig) => void;

  /**
   * Callback when Delete button is clicked for a server
   * @param name - The name of the server to delete
   */
  onDelete?: (name: string) => void;

  /**
   * Callback when Share button is clicked for a server
   * @param server - The server to share
   */
  onShare?: (server: McpServerConfig) => void;
}

export function McpServerList({
  onAdd,
  onEdit,
  onDelete,
  onShare,
}: McpServerListProps) {
  const { servers, isLoading, error } = useMcpServers();
  const [searchQuery, setSearchQuery] = useState('');

  // Filter and sort servers
  const filteredServers = useMemo(() => {
    if (!servers) return [];

    let filtered = servers;

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (server) =>
          server.name.toLowerCase().includes(query) ||
          server.command?.toLowerCase().includes(query)
      );
    }

    // Sort by status (active first) then by name
    return filtered.sort((a, b) => {
      // Status priority: active > disabled > failed
      const statusPriority = { active: 0, disabled: 1, failed: 2 };
      const statusDiff =
        statusPriority[a.status] - statusPriority[b.status];

      if (statusDiff !== 0) return statusDiff;

      // If same status, sort by name
      return a.name.localeCompare(b.name);
    });
  }, [servers, searchQuery]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-sm text-muted-foreground">Loading MCP servers...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <AlertCircleIcon className="h-12 w-12 text-destructive mx-auto mb-4" />
          <p className="text-sm text-destructive font-medium mb-2">
            {error}
          </p>
          <p className="text-xs text-muted-foreground">
            Failed to fetch MCP servers. Please try again.
          </p>
        </div>
      </div>
    );
  }

  // Empty state (no servers configured)
  if (!servers || servers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12">
        <div className="text-center max-w-md">
          <div className="bg-muted rounded-full h-16 w-16 flex items-center justify-center mx-auto mb-4">
            <PlusIcon className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No MCP servers configured</h3>
          <p className="text-sm text-muted-foreground mb-6">
            Get started by adding your first MCP server. MCP servers provide tools and resources for Claude to interact with external systems.
          </p>
          {onAdd && (
            <Button onClick={onAdd}>
              <PlusIcon className="h-4 w-4 mr-2" />
              Add Server
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with search and Add button */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search servers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
            aria-label="Search MCP servers"
          />
        </div>
        {onAdd && (
          <Button onClick={onAdd}>
            <PlusIcon className="h-4 w-4 mr-2" />
            Add Server
          </Button>
        )}
      </div>

      {/* Server list */}
      {filteredServers.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-sm text-muted-foreground">
            No servers match your search.
          </p>
        </div>
      ) : (
        <ul className="space-y-3" aria-label="MCP Servers" role="list">
          {filteredServers.map((server) => (
            <li key={server.id}>
              <McpServerCard
                server={server}
                onEdit={onEdit ? () => onEdit(server) : undefined}
                onDelete={onDelete ? () => onDelete(server.name) : undefined}
                onShare={onShare ? () => onShare(server) : undefined}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
