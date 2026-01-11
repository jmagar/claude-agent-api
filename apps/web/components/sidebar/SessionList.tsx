/**
 * SessionList Component
 *
 * Renders a list of session items with:
 * - Session title and metadata
 * - Selection highlighting
 * - Action menus (fork, delete)
 * - Forked session nesting
 * - Status indicators
 *
 * @example
 * ```tsx
 * <SessionList
 *   sessions={sessions}
 *   currentSessionId="session-123"
 *   onSessionClick={(id) => navigate(`/chat/${id}`)}
 *   onFork={(id) => handleFork(id)}
 *   onDelete={(id) => handleDelete(id)}
 * />
 * ```
 */

'use client';

import { SessionItem } from './SessionItem';
import type { Session } from '@/types';

export interface SessionListProps {
  /**
   * List of sessions to display
   */
  sessions: Session[];

  /**
   * Currently selected session ID
   */
  currentSessionId?: string;

  /**
   * Callback when session is clicked
   */
  onSessionClick?: (sessionId: string) => void;

  /**
   * Callback when fork action is triggered
   */
  onFork?: (sessionId: string) => void;

  /**
   * Callback when delete action is triggered
   */
  onDelete?: (sessionId: string) => void;

  /**
   * Sort order for sessions
   * @default 'recent' (most recent first by last_message_at)
   */
  sortBy?: 'recent' | 'title' | 'created';
}

/**
 * Sort sessions by specified criteria
 */
function sortSessions(sessions: Session[], sortBy: 'recent' | 'title' | 'created'): Session[] {
  const sorted = [...sessions];

  switch (sortBy) {
    case 'recent':
      return sorted.sort((a, b) => {
        const aTime = a.last_message_at ? new Date(a.last_message_at).getTime() : 0;
        const bTime = b.last_message_at ? new Date(b.last_message_at).getTime() : 0;
        return bTime - aTime; // Most recent first
      });

    case 'title':
      return sorted.sort((a, b) => {
        const aTitle = a.title || '';
        const bTitle = b.title || '';
        return aTitle.localeCompare(bTitle);
      });

    case 'created':
      return sorted.sort((a, b) => {
        const aTime = new Date(a.created_at).getTime();
        const bTime = new Date(b.created_at).getTime();
        return bTime - aTime; // Most recent first
      });

    default:
      return sorted;
  }
}

export function SessionList({
  sessions,
  currentSessionId,
  onSessionClick,
  onFork,
  onDelete,
  sortBy = 'recent',
}: SessionListProps) {
  // Empty state
  if (sessions.length === 0) {
    return (
      <div className="px-4 py-8 text-center text-sm text-muted-foreground">
        No sessions to display
      </div>
    );
  }

  // Sort sessions
  const sortedSessions = sortSessions(sessions, sortBy);

  return (
    <ul role="list" className="flex flex-col">
      {sortedSessions.map((session) => {
        const isSelected = session.id === currentSessionId;
        const isForked = !!session.parent_session_id;

        return (
          <li
            key={session.id}
            className={isForked ? 'nested forked ml-4' : ''}
          >
            <SessionItem
              session={session}
              isSelected={isSelected}
              isForked={isForked}
              onClick={() => onSessionClick?.(session.id)}
              onFork={() => onFork?.(session.id)}
              onDelete={() => onDelete?.(session.id)}
            />
          </li>
        );
      })}
    </ul>
  );
}
