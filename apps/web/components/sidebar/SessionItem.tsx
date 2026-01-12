/**
 * SessionItem Component
 *
 * Renders an individual session item with:
 * - Session title and metadata (turns, tags, last message time)
 * - Status indicator (active, completed, error)
 * - Selection highlighting
 * - Action menu (fork, delete)
 * - Forked session indicator
 *
 * Performance optimizations:
 * - React.memo to prevent re-renders when props haven't changed
 *
 * @example
 * ```tsx
 * <SessionItem
 *   session={session}
 *   isSelected={true}
 *   isForked={false}
 *   onClick={() => handleClick(session.id)}
 *   onFork={() => handleFork(session.id)}
 *   onDelete={() => handleDelete(session.id)}
 * />
 * ```
 */

'use client';

import { memo } from 'react';
import { MoreVerticalIcon, GitBranchIcon } from 'lucide-react';
import type { Session } from '@/types';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export interface SessionItemProps {
  /**
   * Session data to display
   */
  session: Session;

  /**
   * Whether this session is currently selected
   */
  isSelected?: boolean;

  /**
   * Whether this is a forked session
   */
  isForked?: boolean;

  /**
   * Callback when session is clicked
   */
  onClick?: () => void;

  /**
   * Callback when fork action is triggered
   */
  onFork?: () => void;

  /**
   * Callback when delete action is triggered
   */
  onDelete?: () => void;
}

/**
 * Format absolute time from date (UTC)
 */
function formatAbsoluteTime(date: Date | string): string {
  try {
    const parsedDate = typeof date === 'string' ? new Date(date) : date;
    return parsedDate.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: 'UTC',
    });
  } catch {
    return '--:--';
  }
}

/**
 * Get status badge variant
 */
function getStatusVariant(
  status: Session['status']
): 'default' | 'secondary' | 'destructive' {
  switch (status) {
    case 'active':
      return 'default';
    case 'completed':
      return 'secondary';
    case 'error':
      return 'destructive';
    default:
      return 'secondary';
  }
}

/**
 * SessionItem component with React.memo for performance
 */
export const SessionItem = memo(function SessionItem({
  session,
  isSelected = false,
  isForked = false,
  onClick,
  onFork,
  onDelete,
}: SessionItemProps) {
  const handleActionClick = (e: React.MouseEvent, action: () => void) => {
    e.stopPropagation();
    action();
  };

  return (
    <div
      className={cn(
        'group relative flex items-start gap-2 rounded-md p-2 transition-colors hover:bg-accent',
        isSelected && 'bg-accent'
      )}
    >
      {/* Main session button */}
      <Button
        variant="ghost"
        className={cn(
          'flex h-auto w-full flex-col items-start gap-2 p-2 text-left',
          isSelected && 'font-medium'
        )}
        onClick={onClick}
        aria-current={isSelected ? 'page' : undefined}
        aria-label={session.title || 'Untitled session'}
      >
        {/* Title and forked indicator */}
        <div className="flex w-full items-center gap-2">
          {isForked && (
            <GitBranchIcon className="h-3 w-3 shrink-0 text-muted-foreground" />
          )}
          <span className="flex-1 truncate text-sm">
            {session.title || 'Untitled session'}
          </span>
        </div>

        {/* Metadata row */}
        <div className="flex w-full items-center gap-2 text-xs text-muted-foreground">
          {/* Turn count */}
          <span>{session.total_turns} turns</span>

          {/* Last message time */}
          {session.last_message_at && (
            <>
              <span>•</span>
              <span>
                {formatAbsoluteTime(session.last_message_at)}
              </span>
            </>
          )}

          {/* Status badge */}
          <Badge
            variant={getStatusVariant(session.status)}
            className="ml-auto text-xs capitalize"
          >
            {session.status}
          </Badge>
        </div>

        {/* Tags */}
        {session.tags && session.tags.length > 0 && (
          <div className="flex w-full flex-wrap gap-1">
            {session.tags.map((tag) => (
              <Badge
                key={tag}
                variant="outline"
                className="text-xs"
              >
                {tag}
              </Badge>
            ))}
          </div>
        )}

        {/* Forked indicator text */}
        {isForked && (
          <span className="text-xs italic text-muted-foreground">
            Forked session
          </span>
        )}
      </Button>

      {/* Action menu */}
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 shrink-0 p-0"
            aria-label="Session actions"
            onClick={(e) => e.stopPropagation()}
          >
            <MoreVerticalIcon className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" container={null}>
          <DropdownMenuItem
            onClick={(e) => handleActionClick(e, onFork || (() => {}))}
            disabled={!onFork}
          >
            Fork session
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={(e) => handleActionClick(e, onDelete || (() => {}))}
            disabled={!onDelete}
            className="text-destructive focus:text-destructive"
          >
            Delete session
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
});
