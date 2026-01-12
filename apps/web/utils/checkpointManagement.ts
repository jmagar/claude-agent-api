/**
 * Checkpoint Management Utilities
 *
 * Utilities for managing session checkpoints, including:
 * - Formatting checkpoint display information
 * - Handling checkpoint-based session forking
 * - Checkpoint state management
 */

import type { Checkpoint, Session } from '@/types';

/**
 * Format checkpoint timestamp for display
 *
 * @param timestamp - Date or ISO string timestamp
 * @returns Formatted time string (e.g., "Jan 11, 14:30")
 */
export function formatCheckpointTime(timestamp: Date | string): string {
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

/**
 * Get checkpoint display label
 *
 * @param checkpoint - Checkpoint object
 * @param messageIndex - Optional message index override
 * @returns Display label (e.g., "Checkpoint #5" or custom label)
 */
export function getCheckpointLabel(
  checkpoint: Checkpoint,
  messageIndex?: number
): string {
  if (checkpoint.label) {
    return checkpoint.label;
  }
  return `Checkpoint #${messageIndex ?? 'Unknown'}`;
}

/**
 * Check if a checkpoint is active (most recent in the session)
 *
 * @param checkpoint - Checkpoint to check
 * @param allCheckpoints - All checkpoints in the session
 * @returns True if this is the most recent checkpoint
 */
export function isActiveCheckpoint(
  checkpoint: Checkpoint,
  allCheckpoints: Checkpoint[]
): boolean {
  if (allCheckpoints.length === 0) return false;

  // Sort by created_at descending
  const sorted = [...allCheckpoints].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return sorted[0]?.id === checkpoint.id;
}

/**
 * Get files modified at a specific checkpoint
 *
 * @param checkpoint - Checkpoint object
 * @returns Array of file paths modified at this checkpoint
 */
export function getModifiedFiles(checkpoint: Checkpoint): string[] {
  return checkpoint.files_modified || [];
}

/**
 * Calculate files changed between two checkpoints
 *
 * @param fromCheckpoint - Starting checkpoint
 * @param toCheckpoint - Ending checkpoint
 * @returns Object with added, removed, and modified file paths
 */
export function calculateCheckpointDiff(
  fromCheckpoint: Checkpoint,
  toCheckpoint: Checkpoint
): {
  added: string[];
  removed: string[];
  modified: string[];
} {
  const fromFiles = new Set(fromCheckpoint.files_modified || []);
  const toFiles = new Set(toCheckpoint.files_modified || []);

  const added: string[] = [];
  const removed: string[] = [];
  const modified: string[] = [];

  // Find added files
  for (const file of toFiles) {
    if (!fromFiles.has(file)) {
      added.push(file);
    } else {
      modified.push(file);
    }
  }

  // Find removed files
  for (const file of fromFiles) {
    if (!toFiles.has(file)) {
      removed.push(file);
    }
  }

  return { added, removed, modified };
}

/**
 * Sort checkpoints by creation time
 *
 * @param checkpoints - Array of checkpoints
 * @param order - Sort order ('asc' or 'desc')
 * @returns Sorted array of checkpoints
 */
export function sortCheckpoints(
  checkpoints: Checkpoint[],
  order: 'asc' | 'desc' = 'desc'
): Checkpoint[] {
  return [...checkpoints].sort((a, b) => {
    const aTime = new Date(a.created_at).getTime();
    const bTime = new Date(b.created_at).getTime();
    return order === 'desc' ? bTime - aTime : aTime - bTime;
  });
}

/**
 * Find checkpoint by message UUID
 *
 * @param checkpoints - Array of checkpoints
 * @param messageUuid - Message UUID to find
 * @returns Checkpoint if found, undefined otherwise
 */
export function findCheckpointByMessage(
  checkpoints: Checkpoint[],
  messageUuid: string
): Checkpoint | undefined {
  return checkpoints.find((cp) => cp.user_message_uuid === messageUuid);
}

/**
 * Group checkpoints by time periods
 *
 * @param checkpoints - Array of checkpoints
 * @returns Object with checkpoints grouped by time period
 */
export function groupCheckpointsByTime(
  checkpoints: Checkpoint[]
): Record<string, Checkpoint[]> {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const lastWeek = new Date(today);
  lastWeek.setDate(lastWeek.getDate() - 7);

  const groups: Record<string, Checkpoint[]> = {
    Today: [],
    Yesterday: [],
    'Last 7 days': [],
    Older: [],
  };

  for (const checkpoint of checkpoints) {
    const checkpointDate = new Date(checkpoint.created_at);
    const checkpointDay = new Date(
      checkpointDate.getFullYear(),
      checkpointDate.getMonth(),
      checkpointDate.getDate()
    );

    if (checkpointDay.getTime() === today.getTime()) {
      groups['Today'].push(checkpoint);
    } else if (checkpointDay.getTime() === yesterday.getTime()) {
      groups['Yesterday'].push(checkpoint);
    } else if (checkpointDay >= lastWeek) {
      groups['Last 7 days'].push(checkpoint);
    } else {
      groups['Older'].push(checkpoint);
    }
  }

  // Remove empty groups
  return Object.fromEntries(
    Object.entries(groups).filter(([_, cps]) => cps.length > 0)
  );
}

/**
 * Validate checkpoint data
 *
 * @param checkpoint - Checkpoint to validate
 * @returns Object with isValid flag and error messages
 */
export function validateCheckpoint(checkpoint: Partial<Checkpoint>): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!checkpoint.session_id) {
    errors.push('Session ID is required');
  }

  if (!checkpoint.user_message_uuid) {
    errors.push('User message UUID is required');
  }

  if (!checkpoint.created_at) {
    errors.push('Created timestamp is required');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Check if file checkpointing is enabled
 *
 * Checks environment variable CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING
 *
 * @returns True if file checkpointing is enabled
 */
export function isFileCheckpointingEnabled(): boolean {
  if (typeof window === 'undefined') {
    // Server-side: check process.env
    return (
      process.env.CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING === '1' ||
      process.env.NEXT_PUBLIC_FILE_CHECKPOINTING_ENABLED === 'true'
    );
  }

  // Client-side: check Next.js public env var
  return (
    process.env.NEXT_PUBLIC_FILE_CHECKPOINTING_ENABLED === 'true'
  );
}

/**
 * Get checkpoint summary for display
 *
 * @param checkpoint - Checkpoint object
 * @returns Summary object with display-friendly information
 */
export function getCheckpointSummary(checkpoint: Checkpoint): {
  label: string;
  timeFormatted: string;
  filesCount: number;
  hasFiles: boolean;
} {
  return {
    label: checkpoint.label || `Checkpoint`,
    timeFormatted: formatCheckpointTime(checkpoint.created_at),
    filesCount: checkpoint.files_modified?.length || 0,
    hasFiles: (checkpoint.files_modified?.length || 0) > 0,
  };
}
