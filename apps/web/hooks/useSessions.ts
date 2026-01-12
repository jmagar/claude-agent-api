/**
 * useSessions Hook
 *
 * React Query hook for managing sessions with:
 * - Fetching sessions list
 * - Creating new sessions
 * - Updating session metadata
 * - Deleting sessions
 * - Forking sessions from checkpoints
 * - Resuming sessions
 * - Optimistic updates for mutations
 */

'use client';

import { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { v4 as uuidv4 } from 'uuid';
import type { Session, SessionFilters, SessionMode } from '@/types';
import { buildSessionQueryParams } from '@/lib/session-filters';
import { queryKeys } from '@/lib/query-keys';
import { createOptimisticHandlers } from '@/lib/react-query/optimistic';

/**
 * Session creation parameters
 */
export interface CreateSessionParams {
  mode: SessionMode;
  title?: string;
  project_id?: string;
  tags?: string[];
}

/**
 * Session update parameters
 */
export interface UpdateSessionParams {
  title?: string;
  tags?: string[];
}

/**
 * Session fork parameters
 */
export interface ForkSessionParams {
  checkpoint_index: number;
  title?: string;
}

export interface SessionListResponse {
  sessions: Session[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * API client for sessions
 */
const sessionsApi = {
  /**
   * Fetch all sessions
   */
  async fetchAll(filters?: SessionFilters): Promise<SessionListResponse> {
    const params = filters ? buildSessionQueryParams(filters) : new URLSearchParams();
    const queryString = params.toString();
    const response = await fetch(`/api/sessions${queryString ? `?${queryString}` : ''}`);

    if (!response.ok) {
      throw new Error('Failed to fetch sessions');
    }

    const data = await response.json();
    return {
      sessions: data.sessions || [],
      total: data.total ?? data.sessions?.length ?? 0,
      page: data.page ?? filters?.page ?? 1,
      page_size: data.page_size ?? filters?.page_size ?? (data.sessions?.length ?? 0),
    };
  },

  /**
   * Create a new session
   */
  async create(params: CreateSessionParams): Promise<Session> {
    const response = await fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to create session');
    }

    const data = await response.json();
    return data.session ?? data;
  },

  /**
   * Update session metadata
   */
  async update(
    sessionId: string,
    params: UpdateSessionParams
  ): Promise<Session> {
    const response = await fetch(`/api/sessions/${sessionId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to update session');
    }

    const data = await response.json();
    return data.session ?? data;
  },

  /**
   * Delete a session
   */
  async delete(sessionId: string): Promise<void> {
    const response = await fetch(`/api/sessions/${sessionId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to delete session');
    }
  },

  /**
   * Fork a session from checkpoint
   */
  async fork(
    sessionId: string,
    params: ForkSessionParams
  ): Promise<Session> {
    const response = await fetch(`/api/sessions/${sessionId}/fork`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fork session');
    }

    const data = await response.json();
    return data.session ?? data;
  },

  /**
   * Resume a session
   */
  async resume(sessionId: string): Promise<Session> {
    const response = await fetch(`/api/sessions/${sessionId}/resume`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to resume session');
    }

    const data = await response.json();
    return data.session ?? data;
  },
};

/**
 * Hook return type
 */
export interface UseSessionsReturn {
  /**
   * List of sessions
   */
  sessions: Session[] | undefined;

  /**
   * Total sessions count (server-side)
   */
  total: number;

  /**
   * Current page
   */
  page: number;

  /**
   * Page size
   */
  pageSize: number;

  /**
   * Whether sessions are being loaded
   */
  isLoading: boolean;

  /**
   * Error message if fetch failed
   */
  error: string | null;

  /**
   * Create a new session
   */
  createSession: (params: CreateSessionParams) => Promise<Session>;

  /**
   * Update session metadata
   */
  updateSession: (
    sessionId: string,
    params: UpdateSessionParams
  ) => Promise<Session>;

  /**
   * Delete a session
   */
  deleteSession: (sessionId: string) => Promise<void>;

  /**
   * Fork a session from checkpoint
   */
  forkSession: (
    sessionId: string,
    params: ForkSessionParams
  ) => Promise<Session>;

  /**
   * Resume a session
   */
  resumeSession: (sessionId: string) => Promise<Session>;

  /**
   * Manually refetch sessions
   */
  refetch: () => void;
}

function buildOptimisticList(
  current: SessionListResponse | undefined,
  updater: (sessions: Session[]) => Session[]
): SessionListResponse {
  const base: SessionListResponse =
    current ?? { sessions: [], total: 0, page: 1, page_size: 0 };
  const nextSessions = updater(base.sessions);
  const delta = nextSessions.length - base.sessions.length;

  return {
    ...base,
    sessions: nextSessions,
    total: Math.max(0, base.total + delta),
  };
}

function matchesFilters(session: Session, filters?: SessionFilters) {
  if (!filters) return true;
  if (filters.mode && session.mode !== filters.mode) return false;
  if (filters.project_id && session.project_id !== filters.project_id) return false;
  if (filters.tags && filters.tags.length > 0) {
    if (!filters.tags.every((tag) => session.tags.includes(tag))) return false;
  }
  if (filters.search) {
    const query = filters.search.toLowerCase();
    if (!session.title?.toLowerCase().includes(query)) return false;
  }
  return true;
}

/**
 * React Query hook for session management
 */
export function useSessions(filters?: SessionFilters): UseSessionsReturn {
  const queryClient = useQueryClient();
  const queryKey = useMemo(
    () => (filters ? queryKeys.sessions.list(filters) : queryKeys.sessions.lists()),
    [filters]
  );

  // Fetch sessions query
  const {
    data,
    isLoading,
    error: queryError,
    refetch,
  } = useQuery({
    queryKey,
    queryFn: () => sessionsApi.fetchAll(filters),
    refetchOnWindowFocus: true,
  });

  const createMutation = useMutation({
    mutationFn: sessionsApi.create,
    ...createOptimisticHandlers<SessionListResponse, CreateSessionParams>({
      queryClient,
      queryKey,
      updater: (current, variables) =>
        buildOptimisticList(current, (sessions) => {
          const now = new Date().toISOString();
          const optimistic: Session = {
            id: uuidv4(),
            mode: variables.mode,
            status: 'active',
            project_id: variables.project_id,
            title: variables.title,
            created_at: now,
            updated_at: now,
            last_message_at: now,
            total_turns: 0,
            tags: variables.tags ?? [],
            duration_ms: undefined,
            total_cost_usd: undefined,
            parent_session_id: undefined,
          };

          if (!matchesFilters(optimistic, filters)) {
            return sessions;
          }

          return [optimistic, ...sessions];
        }),
    }),
  });

  const updateMutation = useMutation({
    mutationFn: ({
      sessionId,
      params,
    }: {
      sessionId: string;
      params: UpdateSessionParams;
    }) => sessionsApi.update(sessionId, params),
    ...createOptimisticHandlers<SessionListResponse, { sessionId: string; params: UpdateSessionParams }>(
      {
        queryClient,
        queryKey,
        updater: (current, variables) =>
          buildOptimisticList(current, (sessions) =>
            sessions.map((session) =>
              session.id === variables.sessionId
                ? {
                    ...session,
                    ...variables.params,
                    updated_at: new Date().toISOString(),
                  }
                : session
            )
          ),
      }
    ),
  });

  const deleteMutation = useMutation({
    mutationFn: sessionsApi.delete,
    ...createOptimisticHandlers<SessionListResponse, string>({
      queryClient,
      queryKey,
      updater: (current, sessionId) =>
        buildOptimisticList(current, (sessions) =>
          sessions.filter((session) => session.id !== sessionId)
        ),
    }),
  });

  const forkMutation = useMutation({
    mutationFn: ({
      sessionId,
      params,
    }: {
      sessionId: string;
      params: ForkSessionParams;
    }) => sessionsApi.fork(sessionId, params),
    ...createOptimisticHandlers<SessionListResponse, { sessionId: string; params: ForkSessionParams }>(
      {
        queryClient,
        queryKey,
        updater: (current, variables) =>
          buildOptimisticList(current, (sessions) => {
            const parent = sessions.find((session) => session.id === variables.sessionId);
            const now = new Date().toISOString();
            const optimistic: Session = {
              id: uuidv4(),
              mode: parent?.mode ?? 'brainstorm',
              status: 'active',
              project_id: parent?.project_id,
              title: variables.params.title ?? parent?.title,
              created_at: now,
              updated_at: now,
              last_message_at: now,
              total_turns: 0,
              tags: parent?.tags ?? [],
              duration_ms: undefined,
              total_cost_usd: undefined,
              parent_session_id: variables.sessionId,
            };

            if (!matchesFilters(optimistic, filters)) {
              return sessions;
            }

            return [optimistic, ...sessions];
          }),
      }
    ),
  });

  const resumeMutation = useMutation({
    mutationFn: sessionsApi.resume,
    ...createOptimisticHandlers<SessionListResponse, string>({
      queryClient,
      queryKey,
      updater: (current, sessionId) =>
        buildOptimisticList(current, (sessions) =>
          sessions.map((session) =>
            session.id === sessionId
              ? {
                  ...session,
                  status: 'active',
                  updated_at: new Date().toISOString(),
                }
              : session
          )
        ),
    }),
  });

  return {
    sessions: data?.sessions,
    total: data?.total ?? 0,
    page: data?.page ?? 1,
    pageSize: data?.page_size ?? 0,
    isLoading,
    error: queryError ? (queryError as Error).message : null,
    createSession: createMutation.mutateAsync,
    updateSession: (sessionId, params) =>
      updateMutation.mutateAsync({ sessionId, params }),
    deleteSession: deleteMutation.mutateAsync,
    forkSession: (sessionId, params) =>
      forkMutation.mutateAsync({ sessionId, params }),
    resumeSession: resumeMutation.mutateAsync,
    refetch: () => {
      refetch();
    },
  };
}
