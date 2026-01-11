/**
 * CheckpointMarker Component
 *
 * Inline component that marks checkpoint positions in the conversation.
 * Displays a visual indicator where users can fork the session.
 *
 * Features:
 * - Visual checkpoint indicator
 * - Message number and timestamp
 * - Fork action button
 * - Hover state for interaction
 *
 * @example
 * ```tsx
 * <CheckpointMarker
 *   messageIndex={5}
 *   timestamp={new Date('2026-01-11T10:30:00Z')}
 *   onFork={() => handleFork(5)}
 * />
 * ```
 */

'use client';

import { GitBranchIcon, ClockIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export interface CheckpointMarkerProps {
  /**
   * Message index where checkpoint occurs
   */
  messageIndex: number;

  /**
   * Timestamp of the checkpoint
   */
  timestamp?: Date | string;

  /**
   * Whether this checkpoint is the current active fork point
   */
  isActive?: boolean;

  /**
   * Callback when fork action is triggered
   */
  onFork?: () => void;

  /**
   * Optional className for custom styling
   */
  className?: string;
}

/**
 * Format checkpoint timestamp
 */
function formatCheckpointTime(timestamp: Date | string): string {
  try {
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  } catch {
    return 'Unknown time';
  }
}

export function CheckpointMarker({
  messageIndex,
  timestamp,
  isActive = false,
  onFork,
  className,
}: CheckpointMarkerProps) {
  return (
    <div
      className={cn(
        'group relative flex items-center gap-3 border-l-2 py-2 pl-4 pr-2',
        isActive ? 'border-l-primary' : 'border-l-border',
        'transition-colors hover:border-l-primary',
        className
      )}
      role="separator"
      aria-label={`Checkpoint at message ${messageIndex}`}
    >
      {/* Checkpoint indicator */}
      <div
        className={cn(
          'flex h-6 w-6 shrink-0 items-center justify-center rounded-full',
          isActive
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted text-muted-foreground'
        )}
      >
        <GitBranchIcon className="h-3 w-3" />
      </div>

      {/* Checkpoint info */}
      <div className="flex flex-1 items-center gap-2 text-xs text-muted-foreground">
        <span className="font-medium">Checkpoint #{messageIndex}</span>

        {timestamp && (
          <>
            <span>•</span>
            <ClockIcon className="h-3 w-3" />
            <span>{formatCheckpointTime(timestamp)}</span>
          </>
        )}
      </div>

      {/* Fork action button */}
      {onFork && (
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            'h-7 gap-1 text-xs',
            'opacity-0 transition-opacity group-hover:opacity-100',
            isActive && 'opacity-100'
          )}
          onClick={onFork}
          aria-label={`Fork from checkpoint ${messageIndex}`}
        >
          <GitBranchIcon className="h-3 w-3" />
          <span>Fork here</span>
        </Button>
      )}
    </div>
  );
}

/**
 * Compact variant for inline display
 */
export function CheckpointMarkerCompact({
  messageIndex,
  onFork,
  className,
}: Pick<CheckpointMarkerProps, 'messageIndex' | 'onFork' | 'className'>) {
  return (
    <div
      className={cn(
        'group inline-flex items-center gap-1 rounded-md px-2 py-1',
        'bg-muted/50 text-xs text-muted-foreground',
        'transition-colors hover:bg-muted',
        className
      )}
      role="button"
      tabIndex={0}
      onClick={onFork}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onFork?.();
        }
      }}
      aria-label={`Checkpoint ${messageIndex}`}
    >
      <GitBranchIcon className="h-3 w-3" />
      <span>CP #{messageIndex}</span>
    </div>
  );
}
