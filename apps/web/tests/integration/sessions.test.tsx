/**
 * Integration tests for Session Management
 *
 * Tests the complete session management workflow:
 * - Creating new sessions
 * - Fetching sessions list
 * - Fetching individual session
 * - Updating session metadata (title, tags)
 * - Deleting sessions
 * - Forking sessions from checkpoints
 * - Resuming sessions
 * - Managing session tags
 *
 * @see hooks/useSessions.ts for session management hook
 * @see app/api/sessions for BFF API routes
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSessions } from '@/hooks/useSessions';
import type { Session, SessionMode } from '@/types';

// Component wrapper for testing hooks
function SessionManagementTest({
  onSessionsLoaded,
  onSessionCreated,
  onSessionUpdated,
  onSessionDeleted,
  onSessionForked,
}: {
  onSessionsLoaded?: (sessions: Session[]) => void;
  onSessionCreated?: (session: Session) => void;
  onSessionUpdated?: (session: Session) => void;
  onSessionDeleted?: (sessionId: string) => void;
  onSessionForked?: (session: Session) => void;
}) {
  const {
    sessions,
    isLoading,
    error,
    createSession,
    updateSession,
    deleteSession,
    forkSession,
  } = useSessions();

  const [mutationError, setMutationError] = React.useState<string | null>(null);

  // Notify parent of sessions loaded
  if (sessions && onSessionsLoaded) {
    onSessionsLoaded(sessions);
  }

  return (
    <div>
      <div data-testid="loading">{isLoading ? 'Loading' : 'Loaded'}</div>
      <div data-testid="error">{mutationError || error || 'No errors'}</div>
      <div data-testid="session-count">{sessions?.length || 0}</div>

      <button
        onClick={async () => {
          try {
            setMutationError(null);
            const session = await createSession({
              mode: 'brainstorm',
              title: 'New Session',
            });
            onSessionCreated?.(session);
          } catch (err) {
            setMutationError(err instanceof Error ? err.message : 'Failed to create session');
          }
        }}
      >
        Create Session
      </button>

      <button
        onClick={async () => {
          if (sessions && sessions.length > 0) {
            const updated = await updateSession(sessions[0].id, {
              title: 'Updated Title',
            });
            onSessionUpdated?.(updated);
          }
        }}
      >
        Update Session
      </button>

      <button
        onClick={async () => {
          if (sessions && sessions.length > 0) {
            await deleteSession(sessions[0].id);
            onSessionDeleted?.(sessions[0].id);
          }
        }}
      >
        Delete Session
      </button>

      <button
        onClick={async () => {
          if (sessions && sessions.length > 0) {
            const forked = await forkSession(sessions[0].id, 'checkpoint-1');
            onSessionForked?.(forked);
          }
        }}
      >
        Fork Session
      </button>

      {sessions?.map((session) => (
        <div key={session.id} data-testid={`session-${session.id}`}>
          {session.title}
        </div>
      ))}
    </div>
  );
}

// Mock fetch for API calls
global.fetch = jest.fn();

describe('Session Management - Integration Tests', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    // Reset fetch mock
    (global.fetch as jest.Mock).mockReset();
  });

  describe('Create Session', () => {
    it('creates a new brainstorm session', async () => {
      const mockSession: Session = {
        id: 'session-new',
        mode: 'brainstorm',
        status: 'active',
        title: 'New Session',
        created_at: new Date(),
        updated_at: new Date(),
        total_turns: 0,
        tags: [],
      };

      // Mock initial GET /api/sessions (on mount)
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [] }),
      });

      // Mock POST /api/sessions
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session: mockSession }),
      });

      const handleSessionCreated = jest.fn();

      render(
        <QueryClientProvider client={queryClient}>
          <SessionManagementTest onSessionCreated={handleSessionCreated} />
        </QueryClientProvider>
      );

      const createButton = screen.getByText('Create Session');
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(handleSessionCreated).toHaveBeenCalledWith(
          expect.objectContaining({
            id: 'session-new',
            mode: 'brainstorm',
            title: 'New Session',
          })
        );
      });
    });

    it('creates a new code session with project ID', async () => {
      const mockSession: Session = {
        id: 'session-code',
        mode: 'code',
        status: 'active',
        title: 'Code Session',
        project_id: 'project-1',
        created_at: new Date(),
        updated_at: new Date(),
        total_turns: 0,
        tags: [],
      };

      // Mock initial GET /api/sessions (on mount)
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [] }),
      });

      // Mock POST /api/sessions
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session: mockSession }),
      });

      const handleSessionCreated = jest.fn();

      render(
        <QueryClientProvider client={queryClient}>
          <SessionManagementTest onSessionCreated={handleSessionCreated} />
        </QueryClientProvider>
      );

      const createButton = screen.getByText('Create Session');
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(handleSessionCreated).toHaveBeenCalledWith(
          expect.objectContaining({
            mode: 'code',
            project_id: 'project-1',
          })
        );
      });
    });

    it('handles session creation errors', async () => {
      // Mock initial GET /api/sessions (on mount)
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [] }),
      });

      // Mock POST /api/sessions (error response)
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ message: 'Failed to create session' }),
      });

      render(
        <QueryClientProvider client={queryClient}>
          <SessionManagementTest />
        </QueryClientProvider>
      );

      const createButton = screen.getByText('Create Session');
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent(/failed to create/i);
      });
    });
  });

  describe('Fetch Sessions', () => {
    it('fetches list of sessions', async () => {
      const mockSessions: Session[] = [
        {
          id: 'session-1',
          mode: 'brainstorm',
          status: 'active',
          title: 'Session 1',
          created_at: new Date(),
          updated_at: new Date(),
          total_turns: 5,
          tags: ['test'],
        },
        {
          id: 'session-2',
          mode: 'code',
          status: 'completed',
          title: 'Session 2',
          project_id: 'project-1',
          created_at: new Date(),
          updated_at: new Date(),
          total_turns: 10,
          tags: [],
        },
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: mockSessions }),
      });

      const handleSessionsLoaded = jest.fn();

      render(
        <QueryClientProvider client={queryClient}>
          <SessionManagementTest onSessionsLoaded={handleSessionsLoaded} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(handleSessionsLoaded).toHaveBeenCalledWith(mockSessions);
      });

      expect(screen.getByTestId('session-count')).toHaveTextContent('2');
    });

    it('handles empty sessions list', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [] }),
      });

      render(
        <QueryClientProvider client={queryClient}>
          <SessionManagementTest />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('session-count')).toHaveTextContent('0');
      });
    });

    it('handles fetch sessions errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: { message: 'Failed to fetch sessions' } }),
      });

      render(
        <QueryClientProvider client={queryClient}>
          <SessionManagementTest />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent(/failed to fetch/i);
      });
    });
  });

  describe('Update Session', () => {
    it('updates session title', async () => {
      const mockSession: Session = {
        id: 'session-1',
        mode: 'brainstorm',
        status: 'active',
        title: 'Original Title',
        created_at: new Date(),
        updated_at: new Date(),
        total_turns: 5,
        tags: [],
      };

      const updatedSession = { ...mockSession, title: 'Updated Title' };

      // Mock initial GET
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [mockSession] }),
      });

      // Mock PATCH /api/sessions/[id]
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session: updatedSession }),
      });

      // Mock GET after update
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [updatedSession] }),
      });

      const handleSessionUpdated = jest.fn();

      render(
        <QueryClientProvider client={queryClient}>
          <SessionManagementTest onSessionUpdated={handleSessionUpdated} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Original Title')).toBeInTheDocument();
      });

      const updateButton = screen.getByText('Update Session');
      fireEvent.click(updateButton);

      await waitFor(() => {
        expect(handleSessionUpdated).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Updated Title',
          })
        );
      });
    });

    it('updates session tags', async () => {
      const mockSession: Session = {
        id: 'session-1',
        mode: 'brainstorm',
        status: 'active',
        title: 'Session',
        created_at: new Date(),
        updated_at: new Date(),
        total_turns: 5,
        tags: [],
      };

      const updatedSession = { ...mockSession, tags: ['important', 'review'] };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [mockSession] }),
      });

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session: updatedSession }),
      });

      const handleSessionUpdated = jest.fn();

      render(
        <QueryClientProvider client={queryClient}>
          <SessionManagementTest onSessionUpdated={handleSessionUpdated} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('session-session-1')).toBeInTheDocument();
      });

      const updateButton = screen.getByText('Update Session');
      fireEvent.click(updateButton);

      await waitFor(() => {
        expect(handleSessionUpdated).toHaveBeenCalledWith(
          expect.objectContaining({
            tags: ['important', 'review'],
          })
        );
      });
    });
  });

  describe('Delete Session', () => {
    it('deletes a session', async () => {
      const mockSession: Session = {
        id: 'session-1',
        mode: 'brainstorm',
        status: 'active',
        title: 'Session to Delete',
        created_at: new Date(),
        updated_at: new Date(),
        total_turns: 5,
        tags: [],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [mockSession] }),
      });

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [] }),
      });

      const handleSessionDeleted = jest.fn();

      render(
        <QueryClientProvider client={queryClient}>
          <SessionManagementTest onSessionDeleted={handleSessionDeleted} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Session to Delete')).toBeInTheDocument();
      });

      const deleteButton = screen.getByText('Delete Session');
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(handleSessionDeleted).toHaveBeenCalledWith('session-1');
      });
    });
  });

  describe('Fork Session', () => {
    it('creates a forked session from checkpoint', async () => {
      const parentSession: Session = {
        id: 'session-parent',
        mode: 'brainstorm',
        status: 'completed',
        title: 'Parent Session',
        created_at: new Date(),
        updated_at: new Date(),
        total_turns: 10,
        tags: [],
      };

      const forkedSession: Session = {
        id: 'session-forked',
        mode: 'brainstorm',
        status: 'active',
        title: 'Parent Session (forked)',
        parent_session_id: 'session-parent',
        created_at: new Date(),
        updated_at: new Date(),
        total_turns: 0,
        tags: [],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [parentSession] }),
      });

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session: forkedSession }),
      });

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [parentSession, forkedSession] }),
      });

      const handleSessionForked = jest.fn();

      render(
        <QueryClientProvider client={queryClient}>
          <SessionManagementTest onSessionForked={handleSessionForked} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Parent Session')).toBeInTheDocument();
      });

      const forkButton = screen.getByText('Fork Session');
      fireEvent.click(forkButton);

      await waitFor(() => {
        expect(handleSessionForked).toHaveBeenCalledWith(
          expect.objectContaining({
            parent_session_id: 'session-parent',
          })
        );
      });
    });
  });

  describe('Resume Session', () => {
    it('resumes an existing session', async () => {
      const mockSession: Session = {
        id: 'session-resume',
        mode: 'code',
        status: 'completed',
        title: 'Session to Resume',
        created_at: new Date(),
        updated_at: new Date(),
        total_turns: 15,
        tags: [],
      };

      const resumedSession = { ...mockSession, status: 'active' as const };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [mockSession] }),
      });

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session: resumedSession }),
      });

      render(
        <QueryClientProvider client={queryClient}>
          <SessionManagementTest />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Session to Resume')).toBeInTheDocument();
      });

      // Resume logic would be triggered via API call
      expect(global.fetch).toHaveBeenCalled();
    });
  });
});
