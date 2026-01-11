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
 *
 * @example
 * ```tsx
 * function SessionManager() {
 *   const {
 *     sessions,
 *     isLoading,
 *     error,
 *     createSession,
 *     updateSession,
 *     deleteSession,
 *     forkSession,
 *     resumeSession,
 *   } = useSessions();
 *
 *   const handleCreate = async () => {
 *     const session = await createSession({
 *       mode: 'brainstorm',
 *       title: 'New Session',
 *     });
 *   };
 *
 *   return <div>...</div>;
 * }
 * ```
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Session, SessionMode } from '@/types';

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

/**
 * API client for sessions
 */
const sessionsApi = {
  /**
   * Fetch all sessions
   */
  async fetchAll(): Promise<Session[]> {
    const response = await fetch('/api/sessions');

    if (!response.ok) {
      throw new Error('Failed to fetch sessions');
    }

    const data = await response.json();
    return data.sessions || [];
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
    return data.session;
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
    return data.session;
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
    return data.session;
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
    return data.session;
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

/**
 * React Query hook for session management
 */
export function useSessions(): UseSessionsReturn {
  const queryClient = useQueryClient();

  // Fetch sessions query
  const {
    data: sessions,
    isLoading,
    error: queryError,
    refetch,
  } = useQuery({
    queryKey: ['sessions'],
    queryFn: sessionsApi.fetchAll,
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: true,
  });

  // Create session mutation
  const createMutation = useMutation({
    mutationFn: sessionsApi.create,
    onSuccess: (newSession) => {
      // Add new session to cache
      queryClient.setQueryData<Session[]>(['sessions'], (old) => {
        if (!old) return [newSession];
        return [newSession, ...old];
      });
    },
  });

  // Update session mutation
  const updateMutation = useMutation({
    mutationFn: ({
      sessionId,
      params,
    }: {
      sessionId: string;
      params: UpdateSessionParams;
    }) => sessionsApi.update(sessionId, params),
    onSuccess: (updatedSession) => {
      // Update session in cache
      queryClient.setQueryData<Session[]>(['sessions'], (old) => {
        if (!old) return [updatedSession];
        return old.map((s) =>
          s.id === updatedSession.id ? updatedSession : s
        );
      });
    },
  });

  // Delete session mutation
  const deleteMutation = useMutation({
    mutationFn: sessionsApi.delete,
    onSuccess: (_, sessionId) => {
      // Remove session from cache
      queryClient.setQueryData<Session[]>(['sessions'], (old) => {
        if (!old) return [];
        return old.filter((s) => s.id !== sessionId);
      });
    },
  });

  // Fork session mutation
  const forkMutation = useMutation({
    mutationFn: ({
      sessionId,
      params,
    }: {
      sessionId: string;
      params: ForkSessionParams;
    }) => sessionsApi.fork(sessionId, params),
    onSuccess: (forkedSession) => {
      // Add forked session to cache
      queryClient.setQueryData<Session[]>(['sessions'], (old) => {
        if (!old) return [forkedSession];
        return [forkedSession, ...old];
      });
    },
  });

  // Resume session mutation
  const resumeMutation = useMutation({
    mutationFn: sessionsApi.resume,
    onSuccess: (resumedSession) => {
      // Update session in cache
      queryClient.setQueryData<Session[]>(['sessions'], (old) => {
        if (!old) return [resumedSession];
        return old.map((s) =>
          s.id === resumedSession.id ? resumedSession : s
        );
      });
    },
  });

  return {
    sessions,
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
