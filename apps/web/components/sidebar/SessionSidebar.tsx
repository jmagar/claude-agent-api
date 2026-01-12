/**
 * SessionSidebar Component
 *
 * Displays a collapsible sidebar of sessions organized by:
 * - Date groups (Brainstorm mode): Today, Yesterday, Last 7 days, etc.
 * - Project groups (Code mode): By project name
 *
 * Features:
 * - Collapsible section headers
 * - Session selection with highlighting
 * - Session actions menu (fork, delete)
 * - Empty, loading, and error states
 * - Keyboard navigation
 *
 * Performance optimizations:
 * - useMemo for expensive grouping operations
 * - useCallback for stable callback references
 *
 * @example
 * ```tsx
 * <SessionSidebar
 *   mode="brainstorm"
 *   currentSessionId="session-123"
 *   onSessionSelect={(id) => navigateToSession(id)}
 * />
 * ```
 */

'use client';

import { useState, useMemo, useCallback } from 'react';
import { SessionList } from './SessionList';
import { useSessions } from '@/hooks/useSessions';
import type { Session, SessionMode } from '@/types';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { ChevronDownIcon, ChevronRightIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface SessionSidebarProps {
  /**
   * Current mode (brainstorm or code)
   */
  mode: SessionMode;

  /**
   * Currently selected session ID
   */
  currentSessionId?: string;

  /**
   * Callback when session is selected
   */
  onSessionSelect?: (sessionId: string) => void;
}

/**
 * Group sessions by date (for Brainstorm mode)
 */
function groupByDate(sessions: Session[]): Record<string, Session[]> {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const lastWeek = new Date(today);
  lastWeek.setDate(lastWeek.getDate() - 7);

  const groups: Record<string, Session[]> = {
    Today: [],
    Yesterday: [],
    'Last 7 days': [],
    Older: [],
  };

  for (const session of sessions) {
    const sessionDate = new Date(session.created_at);
    const sessionDay = new Date(
      sessionDate.getFullYear(),
      sessionDate.getMonth(),
      sessionDate.getDate()
    );

    if (sessionDay.getTime() === today.getTime()) {
      groups['Today'].push(session);
    } else if (sessionDay.getTime() === yesterday.getTime()) {
      groups['Yesterday'].push(session);
    } else if (sessionDay >= lastWeek) {
      groups['Last 7 days'].push(session);
    } else {
      groups['Older'].push(session);
    }
  }

  // Remove empty groups
  return Object.fromEntries(
    Object.entries(groups).filter(([_, sessions]) => sessions.length > 0)
  );
}

/**
 * Group sessions by project (for Code mode)
 */
function groupByProject(sessions: Session[]): Record<string, Session[]> {
  const groups: Record<string, Session[]> = {};

  for (const session of sessions) {
    const projectId = session.project_id || 'No Project';

    if (!groups[projectId]) {
      groups[projectId] = [];
    }

    groups[projectId].push(session);
  }

  return groups;
}

export function SessionSidebar({
  mode,
  currentSessionId,
  onSessionSelect,
}: SessionSidebarProps) {
  const { sessions, isLoading, error } = useSessions();

  // Memoize filtered sessions to prevent recalculation
  const filteredSessions = useMemo(
    () => sessions?.filter((s) => s.mode === mode) || [],
    [sessions, mode]
  );

  // Memoize grouped sessions (expensive operation)
  const groups = useMemo(
    () =>
      mode === 'brainstorm'
        ? groupByDate(filteredSessions)
        : groupByProject(filteredSessions),
    [mode, filteredSessions]
  );

  // Set default expanded groups based on mode
  const getDefaultExpandedGroups = useCallback(() => {
    if (mode === 'brainstorm') {
      return new Set(['Today', 'Yesterday']);
    } else {
      // In code mode, expand all project groups by default
      return new Set(Object.keys(groups));
    }
  }, [mode, groups]);

  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(() =>
    getDefaultExpandedGroups()
  );

  // Memoize toggle function to prevent recreation
  const toggleGroup = useCallback((groupName: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupName)) {
        next.delete(groupName);
      } else {
        next.add(groupName);
      }
      return next;
    });
  }, []);

  // Loading state
  if (isLoading) {
    return (
      <aside
        role="complementary"
        aria-label="Sessions"
        className="flex flex-col gap-2 p-4"
      >
        <div className="text-sm text-muted-foreground">Loading sessions...</div>
      </aside>
    );
  }

  // Error state
  if (error) {
    return (
      <aside
        role="complementary"
        aria-label="Sessions"
        className="flex flex-col gap-2 p-4"
      >
        <div className="text-sm text-destructive">{error}</div>
      </aside>
    );
  }

  // Empty state
  if (filteredSessions.length === 0) {
    return (
      <aside
        role="complementary"
        aria-label="Sessions"
        className="flex flex-col gap-2 p-4"
      >
        <div className="text-sm text-muted-foreground">
          No sessions yet. Start a conversation to create one!
        </div>
      </aside>
    );
  }

  return (
    <aside
      role="complementary"
      aria-label="Sessions"
      className="flex flex-col gap-2 overflow-y-auto"
    >
      {Object.entries(groups).map(([groupName, groupSessions]) => {
        const isExpanded = expandedGroups.has(groupName);

        return (
          <Collapsible key={groupName} open={isExpanded}>
            <section className="flex flex-col">
              <CollapsibleTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="flex w-full items-center justify-between px-4 py-2 text-sm font-semibold"
                  onClick={() => toggleGroup(groupName)}
                  aria-label={`${groupName} sessions`}
                >
                  <span>{groupName}</span>
                  {isExpanded ? (
                    <ChevronDownIcon className="h-4 w-4" />
                  ) : (
                    <ChevronRightIcon className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>

              <CollapsibleContent>
                <SessionList
                  sessions={groupSessions}
                  currentSessionId={currentSessionId}
                  onSessionClick={onSessionSelect}
                />
              </CollapsibleContent>
            </section>
          </Collapsible>
        );
      })}
    </aside>
  );
}
