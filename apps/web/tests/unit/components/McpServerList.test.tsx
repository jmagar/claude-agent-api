/**
 * Unit tests for McpServerList component
 *
 * Tests the MCP server management list view with:
 * - Display of configured MCP servers
 * - Server status indicators (connected, disconnected, error)
 * - Add new server button
 * - Edit and delete actions
 * - Empty state when no servers configured
 * - Loading and error states
 *
 * @see components/mcp/McpServerList.tsx for implementation
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { McpServerList } from '@/components/mcp/McpServerList';
import type { McpServerConfig } from '@/types';

// Mock useMcpServers hook
jest.mock('@/hooks/useMcpServers', () => ({
  useMcpServers: jest.fn(),
}));

import { useMcpServers } from '@/hooks/useMcpServers';

describe('McpServerList', () => {
  const mockServers: McpServerConfig[] = [
    {
      id: 'mcp-1',
      name: 'postgres',
      type: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-postgres'],
      env: {
        POSTGRES_URL: 'postgresql://localhost/mydb',
      },
      enabled: true,
      status: 'active',
      tools_count: 5,
      resources_count: 2,
      created_at: new Date('2026-01-10T00:00:00Z'),
      updated_at: new Date('2026-01-11T10:00:00Z'),
    },
    {
      id: 'mcp-2',
      name: 'filesystem',
      type: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-filesystem', '/workspace'],
      enabled: true,
      status: 'disabled',
      tools_count: 0,
      resources_count: 1,
      created_at: new Date('2026-01-09T00:00:00Z'),
      updated_at: new Date('2026-01-10T00:00:00Z'),
    },
    {
      id: 'mcp-3',
      name: 'browser',
      type: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-puppeteer'],
      enabled: false,
      status: 'failed',
      error: 'Connection timeout',
      tools_count: 3,
      resources_count: 0,
      created_at: new Date('2026-01-08T00:00:00Z'),
      updated_at: new Date('2026-01-11T09:45:00Z'),
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders list of MCP servers', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList />);

      expect(screen.getByText('postgres')).toBeInTheDocument();
      expect(screen.getByText('filesystem')).toBeInTheDocument();
      expect(screen.getByText('browser')).toBeInTheDocument();
    });

    it('renders Add Server button', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList onAdd={jest.fn()} />);

      expect(screen.getByRole('button', { name: /add server/i })).toBeInTheDocument();
    });

    it('displays server status indicators', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList />);

      expect(screen.getByText(/active/i)).toBeInTheDocument();
      expect(screen.getByText(/disabled/i)).toBeInTheDocument();
      expect(screen.getByText(/failed/i)).toBeInTheDocument();
    });

    it('displays empty state when no servers configured', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: [],
        isLoading: false,
        error: null,
      });

      render(<McpServerList />);

      expect(screen.getByText(/no mcp servers configured/i)).toBeInTheDocument();
    });

    it('displays loading state', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: [],
        isLoading: true,
        error: null,
      });

      render(<McpServerList />);

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('displays error state', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: [],
        isLoading: false,
        error: 'Failed to fetch MCP servers',
      });

      render(<McpServerList />);

      expect(screen.getByText('Failed to fetch MCP servers')).toBeInTheDocument();
    });
  });

  describe('Server Actions', () => {
    it('calls onAdd when Add Server button clicked', () => {
      const onAdd = jest.fn();

      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList onAdd={onAdd} />);

      const addButton = screen.getByRole('button', { name: /add server/i });
      fireEvent.click(addButton);

      expect(onAdd).toHaveBeenCalledTimes(1);
    });

    it('displays edit button for each server', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList onEdit={jest.fn()} />);

      const editButtons = screen.getAllByRole('button', { name: /edit/i });
      expect(editButtons).toHaveLength(mockServers.length);
    });

    it('calls onEdit with server when edit button clicked', () => {
      const onEdit = jest.fn();

      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList onEdit={onEdit} />);

      const editButtons = screen.getAllByRole('button', { name: /edit/i });
      fireEvent.click(editButtons[0]);

      expect(onEdit).toHaveBeenCalledWith(mockServers[0]);
    });

    it('displays delete button for each server', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList onDelete={jest.fn()} />);

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
      expect(deleteButtons).toHaveLength(mockServers.length);
    });

    it('calls onDelete with server name when delete button clicked', () => {
      const onDelete = jest.fn();

      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList onDelete={onDelete} />);

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
      fireEvent.click(deleteButtons[0]);

      expect(onDelete).toHaveBeenCalledWith(mockServers[0].name);
    });

    it('displays share button for each server', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList onShare={jest.fn()} />);

      const shareButtons = screen.getAllByRole('button', { name: /share/i });
      expect(shareButtons).toHaveLength(mockServers.length);
    });

    it('calls onShare with server when share button clicked', () => {
      const onShare = jest.fn();

      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList onShare={onShare} />);

      const shareButtons = screen.getAllByRole('button', { name: /share/i });
      fireEvent.click(shareButtons[0]);

      expect(onShare).toHaveBeenCalledWith(mockServers[0]);
    });
  });

  describe('Server Details', () => {
    it('displays server command and args', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: [mockServers[0]],
        isLoading: false,
        error: null,
      });

      render(<McpServerList />);

      expect(screen.getByText(/npx/i)).toBeInTheDocument();
      expect(screen.getByText(/@modelcontextprotocol\/server-postgres/i)).toBeInTheDocument();
    });

    it('displays server capabilities count', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: [mockServers[0]],
        isLoading: false,
        error: null,
      });

      render(<McpServerList />);

      expect(screen.getByText(/5 tools/i)).toBeInTheDocument();
      expect(screen.getByText(/2 resources/i)).toBeInTheDocument();
    });

    it('displays last updated time', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: [mockServers[0]],
        isLoading: false,
        error: null,
      });

      render(<McpServerList />);

      expect(screen.getByText(/updated/i)).toBeInTheDocument();
    });

    it('displays error message for failed status servers', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: [mockServers[2]],
        isLoading: false,
        error: null,
      });

      render(<McpServerList />);

      expect(screen.getByText(/connection timeout/i)).toBeInTheDocument();
    });
  });

  describe('Filtering and Sorting', () => {
    it('displays search input for filtering servers', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList />);

      expect(screen.getByPlaceholderText(/search servers/i)).toBeInTheDocument();
    });

    it('filters servers by name', async () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList />);

      const searchInput = screen.getByPlaceholderText(/search servers/i);
      fireEvent.change(searchInput, { target: { value: 'post' } });

      await waitFor(() => {
        expect(screen.getByText('postgres')).toBeInTheDocument();
        expect(screen.queryByText('filesystem')).not.toBeInTheDocument();
        expect(screen.queryByText('browser')).not.toBeInTheDocument();
      });
    });

    it('sorts servers by status (active first)', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList />);

      const serverCards = screen.getAllByRole('article');
      // First card should be active server (postgres)
      expect(serverCards[0]).toHaveTextContent('postgres');
      expect(serverCards[0]).toHaveTextContent(/active/i);
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList />);

      expect(screen.getByRole('list')).toHaveAttribute('aria-label', 'MCP Servers');
    });

    it('marks server cards as articles', () => {
      (useMcpServers as jest.Mock).mockReturnValue({
        servers: mockServers,
        isLoading: false,
        error: null,
      });

      render(<McpServerList />);

      const articles = screen.getAllByRole('article');
      expect(articles).toHaveLength(mockServers.length);
    });
  });
});
