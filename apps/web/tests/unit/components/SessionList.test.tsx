/**
 * Unit tests for SessionList component
 *
 * Tests the session list display with:
 * - Rendering list of sessions
 * - Session item formatting and metadata
 * - Click handlers for session selection
 * - Empty state handling
 * - Session status indicators
 * - Forked session nesting
 *
 * @see components/sidebar/SessionList.tsx for implementation
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SessionList } from '@/components/sidebar/SessionList';
import type { Session, SessionMode, SessionStatus } from '@/types';

describe('SessionList', () => {
  const mockSessions: Session[] = [
    {
      id: 'session-1',
      mode: 'brainstorm' as SessionMode,
      status: 'active' as SessionStatus,
      title: 'Product brainstorm',
      created_at: new Date('2026-01-11T10:00:00Z'),
      updated_at: new Date('2026-01-11T10:30:00Z'),
      last_message_at: new Date('2026-01-11T10:30:00Z'),
      total_turns: 5,
      tags: ['product', 'ideas'],
    },
    {
      id: 'session-2',
      mode: 'brainstorm' as SessionMode,
      status: 'completed' as SessionStatus,
      title: 'API design discussion',
      created_at: new Date('2026-01-10T14:00:00Z'),
      updated_at: new Date('2026-01-10T15:00:00Z'),
      last_message_at: new Date('2026-01-10T15:00:00Z'),
      total_turns: 12,
      tags: ['api', 'design'],
    },
    {
      id: 'session-3',
      mode: 'code' as SessionMode,
      status: 'error' as SessionStatus,
      title: 'Fix authentication bug',
      created_at: new Date('2026-01-11T09:00:00Z'),
      updated_at: new Date('2026-01-11T11:00:00Z'),
      last_message_at: new Date('2026-01-11T11:00:00Z'),
      total_turns: 8,
      tags: ['bug', 'auth'],
      parent_session_id: 'session-1', // Forked from session-1
    },
  ];

  describe('Rendering', () => {
    it('renders list of sessions', () => {
      render(<SessionList sessions={mockSessions} />);

      expect(screen.getByText('Product brainstorm')).toBeInTheDocument();
      expect(screen.getByText('API design discussion')).toBeInTheDocument();
      expect(screen.getByText('Fix authentication bug')).toBeInTheDocument();
    });

    it('renders empty state when no sessions provided', () => {
      render(<SessionList sessions={[]} />);

      expect(screen.getByText(/no sessions/i)).toBeInTheDocument();
    });

    it('renders session titles', () => {
      render(<SessionList sessions={mockSessions.slice(0, 1)} />);

      expect(screen.getByText('Product brainstorm')).toBeInTheDocument();
    });

    it('renders all sessions as list items', () => {
      render(<SessionList sessions={mockSessions} />);

      const listItems = screen.getAllByRole('listitem');
      expect(listItems).toHaveLength(mockSessions.length);
    });
  });

  describe('Session Metadata', () => {
    it('displays turn count for each session', () => {
      render(<SessionList sessions={mockSessions.slice(0, 1)} />);

      expect(screen.getByText(/5 turns/i)).toBeInTheDocument();
    });

    it('displays last message time', () => {
      render(<SessionList sessions={mockSessions.slice(0, 1)} />);

      // Should show relative time (e.g., "2 hours ago") or absolute time
      expect(screen.getByText(/10:30|hours ago/i)).toBeInTheDocument();
    });

    it('displays session tags', () => {
      render(<SessionList sessions={mockSessions.slice(0, 1)} />);

      expect(screen.getByText('product')).toBeInTheDocument();
      expect(screen.getByText('ideas')).toBeInTheDocument();
    });

    it('displays session status indicator', () => {
      render(<SessionList sessions={mockSessions} />);

      expect(screen.getByText(/active/i)).toBeInTheDocument();
      expect(screen.getByText(/completed/i)).toBeInTheDocument();
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  describe('Session Selection', () => {
    it('highlights currently selected session', () => {
      render(<SessionList sessions={mockSessions} currentSessionId="session-1" />);

      const selectedSession = screen.getByText('Product brainstorm').closest('button');
      expect(selectedSession).toHaveAttribute('aria-current', 'page');
    });

    it('calls onSessionClick when session is clicked', () => {
      const onSessionClick = jest.fn();

      render(<SessionList sessions={mockSessions} onSessionClick={onSessionClick} />);

      const sessionButton = screen.getByText('Product brainstorm');
      fireEvent.click(sessionButton);

      expect(onSessionClick).toHaveBeenCalledWith('session-1');
    });

    it('calls onSessionClick with correct session ID', () => {
      const onSessionClick = jest.fn();

      render(<SessionList sessions={mockSessions} onSessionClick={onSessionClick} />);

      const secondSession = screen.getByText('API design discussion');
      fireEvent.click(secondSession);

      expect(onSessionClick).toHaveBeenCalledWith('session-2');
    });
  });

  describe('Session Actions', () => {
    it('displays action menu for each session', () => {
      render(<SessionList sessions={mockSessions} />);

      const actionMenus = screen.getAllByRole('button', { name: /actions/i });
      expect(actionMenus).toHaveLength(mockSessions.length);
    });

    it('calls onFork when fork action clicked', async () => {
      const user = userEvent.setup();
      const onFork = jest.fn();

      render(<SessionList sessions={mockSessions.slice(0, 1)} onFork={onFork} />);

      const actionButton = screen.getByRole('button', { name: /actions/i });
      await user.click(actionButton);

      await waitFor(() => {
        expect(screen.getByText(/fork session/i)).toBeInTheDocument();
      });

      const forkButton = screen.getByText(/fork session/i);
      await user.click(forkButton);

      expect(onFork).toHaveBeenCalledWith('session-1');
    });

    it('calls onDelete when delete action clicked', async () => {
      const user = userEvent.setup();
      const onDelete = jest.fn();

      render(<SessionList sessions={mockSessions.slice(0, 1)} onDelete={onDelete} />);

      const actionButton = screen.getByRole('button', { name: /actions/i });
      await user.click(actionButton);

      await waitFor(() => {
        expect(screen.getByText(/delete session/i)).toBeInTheDocument();
      });

      const deleteButton = screen.getByText(/delete session/i);
      await user.click(deleteButton);

      expect(onDelete).toHaveBeenCalledWith('session-1');
    });
  });

  describe('Forked Sessions', () => {
    it('displays forked sessions nested under parent', () => {
      render(<SessionList sessions={mockSessions} />);

      const forkedSession = screen.getByText('Fix authentication bug').closest('li');
      expect(forkedSession).toHaveClass(/nested|indented|forked/);
    });

    it('shows fork indicator for forked sessions', () => {
      render(<SessionList sessions={mockSessions} />);

      // Should have some visual indication that session-3 is forked from session-1
      const forkedSession = screen.getByText('Fix authentication bug').closest('li');
      expect(forkedSession).toHaveTextContent(/forked|branched/i);
    });
  });

  describe('Session Status', () => {
    it('displays active status badge', () => {
      render(<SessionList sessions={mockSessions.filter((s) => s.status === 'active')} />);

      expect(screen.getByText(/active/i)).toBeInTheDocument();
    });

    it('displays completed status badge', () => {
      render(<SessionList sessions={mockSessions.filter((s) => s.status === 'completed')} />);

      expect(screen.getByText(/completed/i)).toBeInTheDocument();
    });

    it('displays error status badge', () => {
      render(<SessionList sessions={mockSessions.filter((s) => s.status === 'error')} />);

      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  describe('Sorting', () => {
    it('displays sessions in most-recent-first order by default', () => {
      render(<SessionList sessions={mockSessions} />);

      const sessions = screen.getAllByRole('listitem');

      // session-1 and session-3 are from today, session-2 is from yesterday
      // session-3 (11:00) should come before session-1 (10:30) since it has later last_message_at
      expect(sessions[0]).toHaveTextContent('Fix authentication bug');
      expect(sessions[1]).toHaveTextContent('Product brainstorm');
      expect(sessions[2]).toHaveTextContent('API design discussion');
    });

    it('allows custom sorting order', () => {
      render(<SessionList sessions={mockSessions} sortBy="title" />);

      const sessions = screen.getAllByRole('listitem');

      // Alphabetically: API design, Fix authentication, Product brainstorm
      expect(sessions[0]).toHaveTextContent('API design discussion');
      expect(sessions[1]).toHaveTextContent('Fix authentication bug');
      expect(sessions[2]).toHaveTextContent('Product brainstorm');
    });
  });

  describe('Accessibility', () => {
    it('renders as a list with proper role', () => {
      render(<SessionList sessions={mockSessions} />);

      expect(screen.getByRole('list')).toBeInTheDocument();
    });

    it('has proper ARIA labels on session buttons', () => {
      render(<SessionList sessions={mockSessions.slice(0, 1)} />);

      const sessionButton = screen.getByRole('button', { name: /product brainstorm/i });
      expect(sessionButton).toBeInTheDocument();
    });

    it('marks selected session with aria-current', () => {
      render(<SessionList sessions={mockSessions} currentSessionId="session-1" />);

      const selectedSession = screen.getByText('Product brainstorm').closest('button');
      expect(selectedSession).toHaveAttribute('aria-current', 'page');
    });
  });
});
