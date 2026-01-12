import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AgentList } from '@/components/agents/AgentList';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const mockAgents = [
  {
    id: '1',
    name: 'code-reviewer',
    description: 'Reviews code for quality and best practices',
    prompt: 'You are a code reviewer...',
    tools: ['Read', 'Grep', 'Glob'],
    model: 'sonnet' as const,
    created_at: new Date('2026-01-01'),
    updated_at: new Date('2026-01-01'),
  },
  {
    id: '2',
    name: 'test-writer',
    description: 'Writes unit tests for code',
    prompt: 'You are a test writer...',
    model: 'haiku' as const,
    created_at: new Date('2026-01-02'),
    updated_at: new Date('2026-01-02'),
  },
];

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('AgentList', () => {
  beforeEach(() => {
    queryClient.clear();
  });

  describe('Rendering', () => {
    it('renders empty state when no agents exist', () => {
      render(<AgentList agents={[]} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} />, { wrapper });

      expect(screen.getByText(/no agents/i)).toBeInTheDocument();
      expect(screen.getByText(/create your first agent/i)).toBeInTheDocument();
    });

    it('renders list of agents', () => {
      render(<AgentList agents={mockAgents} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} />, { wrapper });

      expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      expect(screen.getByText('test-writer')).toBeInTheDocument();
      expect(screen.getByText(/reviews code for quality/i)).toBeInTheDocument();
    });

    it('displays agent model badges', () => {
      render(<AgentList agents={mockAgents} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} />, { wrapper });

      expect(screen.getByText('sonnet')).toBeInTheDocument();
      expect(screen.getByText('haiku')).toBeInTheDocument();
    });

    it('displays tool count for each agent', () => {
      render(<AgentList agents={mockAgents} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} />, { wrapper });

      expect(screen.getByText(/3 tools/i)).toBeInTheDocument();
    });
  });

  describe('Search and Filter', () => {
    it('filters agents by search query', async () => {
      render(<AgentList agents={mockAgents} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} />, { wrapper });

      const searchInput = screen.getByPlaceholderText(/search agents/i);
      fireEvent.change(searchInput, { target: { value: 'reviewer' } });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
        expect(screen.queryByText('test-writer')).not.toBeInTheDocument();
      });
    });

    it('shows no results message when search matches nothing', async () => {
      render(<AgentList agents={mockAgents} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} />, { wrapper });

      const searchInput = screen.getByPlaceholderText(/search agents/i);
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      await waitFor(() => {
        expect(screen.getByText(/no agents match/i)).toBeInTheDocument();
      });
    });

    it('filters agents by model', async () => {
      render(<AgentList agents={mockAgents} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} />, { wrapper });

      const modelFilter = screen.getByRole('combobox', { name: /model/i });
      fireEvent.change(modelFilter, { target: { value: 'sonnet' } });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
        expect(screen.queryByText('test-writer')).not.toBeInTheDocument();
      });
    });
  });

  describe('Actions', () => {
    it('calls onEdit when edit button clicked', () => {
      const onEdit = jest.fn();
      render(<AgentList agents={mockAgents} onEdit={onEdit} onDelete={() => {}} onShare={() => {}} />, { wrapper });

      // Default sort is by date (newest first), so test-writer (2026-01-02) is first
      const editButton = screen.getByRole('button', { name: /edit test-writer/i });
      fireEvent.click(editButton);

      expect(onEdit).toHaveBeenCalledWith(mockAgents[1]);
    });

    it('calls onDelete with confirmation when delete button clicked', async () => {
      const onDelete = jest.fn();
      render(<AgentList agents={mockAgents} onEdit={() => {}} onDelete={onDelete} onShare={() => {}} />, { wrapper });

      // Default sort is by date (newest first), so test-writer (2026-01-02) is first
      const deleteButton = screen.getByRole('button', { name: /delete test-writer/i });
      fireEvent.click(deleteButton);

      // Confirmation dialog should appear
      await waitFor(() => {
        expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      fireEvent.click(confirmButton);

      expect(onDelete).toHaveBeenCalledWith('2');
    });

    it('calls onShare when share button clicked', () => {
      const onShare = jest.fn();
      render(<AgentList agents={mockAgents} onEdit={() => {}} onDelete={() => {}} onShare={onShare} />, { wrapper });

      // Default sort is by date (newest first), so test-writer (2026-01-02) is first
      const shareButton = screen.getByRole('button', { name: /share test-writer/i });
      fireEvent.click(shareButton);

      expect(onShare).toHaveBeenCalledWith(mockAgents[1]);
    });

    it('shows create button', () => {
      render(<AgentList agents={mockAgents} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} onCreate={() => {}} />, { wrapper });

      expect(screen.getByRole('button', { name: /create agent/i })).toBeInTheDocument();
    });

    it('calls onCreate when create button clicked', () => {
      const onCreate = jest.fn();
      render(<AgentList agents={mockAgents} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} onCreate={onCreate} />, { wrapper });

      const createButton = screen.getByRole('button', { name: /create agent/i });
      fireEvent.click(createButton);

      expect(onCreate).toHaveBeenCalled();
    });
  });

  describe('Sorting', () => {
    it('sorts agents by name', async () => {
      render(<AgentList agents={mockAgents} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} />, { wrapper });

      // Default is sorted by date, clicking toggles to name
      const sortButton = screen.getByRole('button', { name: /sort/i });
      fireEvent.click(sortButton);

      await waitFor(() => {
        const agentNames = screen.getAllByRole('heading', { level: 3 });
        expect(agentNames[0]).toHaveTextContent('code-reviewer');
      });
    });

    it('sorts agents by date', async () => {
      render(<AgentList agents={mockAgents} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} />, { wrapper });

      const sortButton = screen.getByRole('button', { name: /sort/i });
      fireEvent.click(sortButton);

      const dateOption = screen.getByText(/date/i);
      fireEvent.click(dateOption);

      await waitFor(() => {
        const agentNames = screen.getAllByRole('heading', { level: 3 });
        expect(agentNames[0]).toHaveTextContent('test-writer');
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(<AgentList agents={mockAgents} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} />, { wrapper });

      expect(screen.getByRole('list', { name: /agents/i })).toBeInTheDocument();
      expect(screen.getByRole('search', { name: /search agents/i })).toBeInTheDocument();
    });

    it('supports keyboard navigation', () => {
      render(<AgentList agents={mockAgents} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} />, { wrapper });

      const firstAgent = screen.getAllByRole('listitem')[0];
      firstAgent.focus();

      expect(firstAgent).toHaveFocus();
    });
  });

  describe('Loading States', () => {
    it('shows loading skeleton when loading prop is true', () => {
      render(<AgentList agents={[]} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} isLoading={true} />, { wrapper });

      expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument();
    });
  });

  describe('Error States', () => {
    it('shows error message when error prop is provided', () => {
      const error = new Error('Failed to load agents');
      render(<AgentList agents={[]} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} error={error} />, { wrapper });

      expect(screen.getByText(/failed to load agents/i)).toBeInTheDocument();
    });

    it('shows retry button on error', () => {
      const error = new Error('Failed to load agents');
      const onRetry = jest.fn();
      render(<AgentList agents={[]} onEdit={() => {}} onDelete={() => {}} onShare={() => {}} error={error} onRetry={onRetry} />, { wrapper });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      fireEvent.click(retryButton);

      expect(onRetry).toHaveBeenCalled();
    });
  });
});
