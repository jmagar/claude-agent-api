/**
 * Unit tests for SessionSidebar component
 *
 * Tests the session management sidebar with:
 * - Display of sessions grouped by date (Brainstorm mode) or project (Code mode)
 * - Collapsible/expandable sections
 * - Session selection and navigation
 * - Empty, loading, and error states
 * - Session actions (resume, fork, delete)
 *
 * @see components/sidebar/SessionSidebar.tsx for implementation
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SessionSidebar } from '@/components/sidebar/SessionSidebar';
import type { Session, SessionMode } from '@/types';

// Mock useSessions hook
jest.mock('@/hooks/useSessions', () => ({
  useSessions: jest.fn(),
}));

import { useSessions } from '@/hooks/useSessions';

describe('SessionSidebar', () => {
  const mockSessions: Session[] = [
    {
      id: 'session-1',
      mode: 'brainstorm' as SessionMode,
      status: 'active',
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
      status: 'completed',
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
      status: 'active',
      project_id: 'project-1',
      title: 'Fix authentication bug',
      created_at: new Date('2026-01-11T09:00:00Z'),
      updated_at: new Date('2026-01-11T11:00:00Z'),
      last_message_at: new Date('2026-01-11T11:00:00Z'),
      total_turns: 8,
      tags: ['bug', 'auth'],
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders session sidebar', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions,
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      expect(screen.getByRole('complementary', { name: /sessions/i })).toBeInTheDocument();
    });

    it('renders sessions list', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions,
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      expect(screen.getByText('Product brainstorm')).toBeInTheDocument();
      expect(screen.getByText('API design discussion')).toBeInTheDocument();
    });

    it('displays empty state when no sessions', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: [],
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      expect(screen.getByText(/no sessions yet/i)).toBeInTheDocument();
    });

    it('displays loading state', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: [],
        isLoading: true,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      expect(screen.getByText(/loading sessions/i)).toBeInTheDocument();
    });

    it('displays error state', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: [],
        isLoading: false,
        error: 'Failed to fetch sessions',
      });

      render(<SessionSidebar mode="brainstorm" />);

      expect(screen.getByText(/failed to fetch sessions/i)).toBeInTheDocument();
    });
  });

  describe('Grouping - Brainstorm Mode', () => {
    it('groups sessions by date in brainstorm mode', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions.filter((s) => s.mode === 'brainstorm'),
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      expect(screen.getByText(/today/i)).toBeInTheDocument();
      expect(screen.getByText(/yesterday/i)).toBeInTheDocument();
    });

    it('displays sessions under correct date group', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions.filter((s) => s.mode === 'brainstorm'),
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      const todaySection = screen.getByText(/today/i).closest('section');
      expect(todaySection).toContainElement(screen.getByText('Product brainstorm'));

      const yesterdaySection = screen.getByText(/yesterday/i).closest('section');
      expect(yesterdaySection).toContainElement(screen.getByText('API design discussion'));
    });
  });

  describe('Grouping - Code Mode', () => {
    it('groups sessions by project in code mode', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions.filter((s) => s.mode === 'code'),
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="code" />);

      expect(screen.getByText(/project-1/i)).toBeInTheDocument();
    });

    it('displays sessions under correct project group', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions.filter((s) => s.mode === 'code'),
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="code" />);

      const projectSection = screen.getByText(/project-1/i).closest('section');
      expect(projectSection).toContainElement(screen.getByText('Fix authentication bug'));
    });
  });

  describe('Collapsible Sections', () => {
    it('renders sections as collapsible', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions.filter((s) => s.mode === 'brainstorm'),
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      const todayButton = screen.getByRole('button', { name: /today/i });
      expect(todayButton).toBeInTheDocument();
    });

    it('collapses section when header clicked', async () => {
      const user = userEvent.setup();
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions.filter((s) => s.mode === 'brainstorm'),
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      const todayButton = screen.getByRole('button', { name: /today/i });

      // Initially expanded, session is visible
      expect(screen.getByText('Product brainstorm')).toBeInTheDocument();

      // Click to collapse
      await user.click(todayButton);

      await waitFor(() => {
        expect(screen.queryByText('Product brainstorm')).not.toBeInTheDocument();
      });
    });

    it('expands section when collapsed header clicked', async () => {
      const user = userEvent.setup();
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions.filter((s) => s.mode === 'brainstorm'),
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      const todayButton = screen.getByRole('button', { name: /today/i });

      // Collapse first
      await user.click(todayButton);
      await waitFor(() => {
        expect(screen.queryByText('Product brainstorm')).not.toBeInTheDocument();
      });

      // Then expand
      await user.click(todayButton);
      await waitFor(() => {
        expect(screen.getByText('Product brainstorm')).toBeInTheDocument();
      });
    });
  });

  describe('Session Selection', () => {
    it('highlights selected session', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions,
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" currentSessionId="session-1" />);

      const selectedSession = screen.getByText('Product brainstorm').closest('button');
      expect(selectedSession).toHaveAttribute('aria-current', 'page');
    });

    it('calls onSessionSelect when session clicked', () => {
      const onSessionSelect = jest.fn();

      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions,
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" onSessionSelect={onSessionSelect} />);

      const sessionButton = screen.getByText('Product brainstorm');
      fireEvent.click(sessionButton);

      expect(onSessionSelect).toHaveBeenCalledWith('session-1');
    });
  });

  describe('Session Actions', () => {
    it('displays session action menu button', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions,
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      const actionButtons = screen.getAllByRole('button', { name: /session actions/i });
      expect(actionButtons.length).toBeGreaterThan(0);
    });

    it('shows fork option in action menu', async () => {
      const user = userEvent.setup();
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions,
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      const actionButton = screen.getAllByRole('button', { name: /session actions/i })[0];
      await user.click(actionButton);

      await waitFor(() => {
        expect(screen.getByText(/fork session/i)).toBeInTheDocument();
      });
    });

    it('shows delete option in action menu', async () => {
      const user = userEvent.setup();
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions,
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      const actionButton = screen.getAllByRole('button', { name: /session actions/i })[0];
      await user.click(actionButton);

      await waitFor(() => {
        expect(screen.getByText(/delete session/i)).toBeInTheDocument();
      });
    });
  });

  describe('Session Metadata', () => {
    it('displays session turn count', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions.slice(0, 1),
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      expect(screen.getByText(/5 turns/i)).toBeInTheDocument();
    });

    it('displays session tags', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions.slice(0, 1),
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      expect(screen.getByText('product')).toBeInTheDocument();
      expect(screen.getByText('ideas')).toBeInTheDocument();
    });

    it('displays last message time', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions.slice(0, 1),
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      expect(screen.getByText(/10:30/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions,
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      expect(screen.getByRole('complementary', { name: /sessions/i })).toBeInTheDocument();
    });

    it('marks session items with proper roles', () => {
      (useSessions as jest.Mock).mockReturnValue({
        sessions: mockSessions,
        isLoading: false,
        error: null,
      });

      render(<SessionSidebar mode="brainstorm" />);

      const sessionButtons = screen.getAllByRole('button', { name: /product brainstorm|api design|fix authentication/i });
      expect(sessionButtons.length).toBeGreaterThan(0);
    });
  });
});
