/**
 * McpServerCard Component
 *
 * Displays a single MCP server configuration card with:
 * - Status indicator (active, disabled, failed)
 * - Server name and type
 * - Command/URL details
 * - Tools and resources count
 * - Last updated timestamp
 * - Action buttons (Edit, Delete, Share)
 * - Error message display (for failed servers)
 *
 * @example
 * ```tsx
 * <McpServerCard
 *   server={mcpServer}
 *   onEdit={() => handleEdit(server)}
 *   onDelete={() => handleDelete(server.name)}
 *   onShare={() => handleShare(server)}
 * />
 * ```
 */

'use client';

import { formatDistanceToNow } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { AlertCircleIcon } from 'lucide-react';
import type { McpServerConfig } from '@/types';

export interface McpServerCardProps {
  /**
   * The MCP server configuration to display
   */
  server: McpServerConfig;

  /**
   * Callback when Edit button is clicked
   */
  onEdit?: () => void;

  /**
   * Callback when Delete button is clicked
   */
  onDelete?: () => void;

  /**
   * Callback when Share button is clicked
   */
  onShare?: () => void;
}

export function McpServerCard({
  server,
  onEdit,
  onDelete,
  onShare,
}: McpServerCardProps) {
  return (
    <article
      className="border border-border rounded-lg p-4 hover:bg-accent/5 transition-colors"
      role="article"
    >
      <div className="flex items-start justify-between gap-4">
        {/* Server info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            {/* Server name */}
            <h3 className="text-base font-semibold truncate">{server.name}</h3>

            {/* Status badge */}
            <Badge
              variant="outline"
              className={cn(
                'inline-flex items-center',
                server.status === 'active' && 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 border-green-200',
                server.status === 'disabled' && 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
                server.status === 'failed' && 'bg-destructive/10 text-destructive border-destructive/20'
              )}
            >
              <span
                className={cn(
                  'inline-block w-2 h-2 rounded-full mr-2',
                  server.status === 'active' && 'bg-green-500',
                  server.status === 'disabled' && 'bg-gray-400',
                  server.status === 'failed' && 'bg-destructive'
                )}
                aria-hidden="true"
              />
              {server.status.charAt(0).toUpperCase() + server.status.slice(1)}
            </Badge>
          </div>

          {/* Error message for failed servers */}
          {server.status === 'failed' && server.error && (
            <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 rounded-md p-2 mt-2">
              <AlertCircleIcon className="h-4 w-4 mt-0.5 shrink-0" />
              <span>{server.error}</span>
            </div>
          )}

          {/* Server details */}
          <div className="text-sm text-muted-foreground space-y-1">
            {server.command && (
              <p className="font-mono text-xs">
                <span className="font-medium">Command:</span> {server.command}
                {server.args && server.args.length > 0 && ` ${server.args.join(' ')}`}
              </p>
            )}
            {server.url && (
              <p className="text-xs text-muted-foreground">
                URL: {server.url}
              </p>
            )}
          </div>

          {/* Server capabilities */}
          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
            <span>{server.tools_count ?? 0} tools</span>
            <span>•</span>
            <span>{server.resources_count ?? 0} resources</span>
            <span>•</span>
            <span>Updated {formatDistanceToNow(new Date(server.updated_at), { addSuffix: true })}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 ml-auto">
          {onEdit && (
            <Button
              variant="outline"
              size="sm"
              onClick={onEdit}
              aria-label={`Edit ${server.name}`}
            >
              Edit
            </Button>
          )}
          {onShare && (
            <Button
              variant="outline"
              size="sm"
              onClick={onShare}
              aria-label={`Share ${server.name}`}
            >
              Share
            </Button>
          )}
          {onDelete && (
            <Button
              variant="destructive"
              size="sm"
              onClick={onDelete}
              aria-label={`Delete ${server.name}`}
            >
              Delete
            </Button>
          )}
        </div>
      </div>
    </article>
  );
}
