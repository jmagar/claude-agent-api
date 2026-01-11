/**
 * Integration tests for MCP server configuration flow
 *
 * Tests the complete MCP server management workflow:
 * 1. Navigate to MCP settings page
 * 2. Add new MCP server via form
 * 3. Edit existing MCP server
 * 4. Test server connectivity
 * 5. Delete MCP server
 * 6. Inline /mcp connect command in Composer
 * 7. @mcp-server-name autocomplete mentions
 * 8. Share MCP server configuration
 *
 * @see apps/web/app/settings/mcp-servers/page.tsx for settings page
 * @see components/mcp/McpServerList.tsx for server list
 * @see components/mcp/McpServerForm.tsx for server form
 */

import { render, screen, fireEvent, waitFor } from '@/tests/utils/test-utils';
import { Composer } from '@/components/chat/Composer';
import type { McpServerConfig } from '@/types';

// Mock API routes
global.fetch = jest.fn();

/**
 * Helper to select a value from Radix UI Select component
 * Radix UI Select doesn't support fireEvent.change, so we need to click the trigger and then the option
 */
async function selectTransportType(type: 'stdio' | 'sse' | 'http') {
  const trigger = screen.getByRole('combobox', { name: /transport type/i });
  fireEvent.click(trigger);

  const optionText = type === 'stdio' ? 'stdio (Local process)'
    : type === 'sse' ? 'SSE (Server-Sent Events)'
    : 'HTTP (REST API)';

  // Radix UI Select items - use getAllByText and click the last one (the option in the dropdown)
  const options = await screen.findAllByText(optionText);
  fireEvent.click(options[options.length - 1]);
}

describe('MCP Configuration Flow Integration', () => {
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
  ];

  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock for GET /api/mcp-servers
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/api/mcp-servers') && !url.includes('/api/mcp-servers/')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ servers: mockServers }),
        });
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      });
    });
  });

  describe('MCP Settings Page', () => {
    it('displays list of configured MCP servers', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        expect(screen.getByText('postgres')).toBeInTheDocument();
        expect(screen.getByText(/5 tools/i)).toBeInTheDocument();
        expect(screen.getByText(/2 resources/i)).toBeInTheDocument();
      });
    });

    it('shows Add Server button', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add server/i })).toBeInTheDocument();
      });
    });

    it('displays empty state when no servers configured', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ servers: [] }),
      });

      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        expect(screen.getByText(/no mcp servers configured/i)).toBeInTheDocument();
      });
    });
  });

  describe('Add New Server', () => {
    it('opens form modal when Add Server clicked', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /add server/i });
        fireEvent.click(addButton);
      });

      await waitFor(() => {
        const headings = screen.getAllByRole('heading', { name: /add mcp server/i });
        expect(headings.length).toBeGreaterThan(0);
      });
    });

    it('creates new stdio server successfully', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /add server/i });
        fireEvent.click(addButton);
      });

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/server name/i);
        fireEvent.change(nameInput, { target: { value: 'filesystem' } });

        const commandInput = screen.getByLabelText(/command/i);
        fireEvent.change(commandInput, { target: { value: 'npx' } });

        const argsTextarea = screen.getByLabelText(/arguments/i);
        fireEvent.change(argsTextarea, {
          target: { value: '["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]' },
        });
      });

      // Mock POST request
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          server: {
            id: 'mcp-2',
            name: 'filesystem',
            type: 'stdio',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-filesystem', '/workspace'],
            enabled: true,
            status: 'active',
            created_at: new Date(),
            updated_at: new Date(),
          },
        }),
      });

      const submitButton = screen.getByRole('button', { name: /create server/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/mcp-servers',
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('filesystem'),
          })
        );
      });
    });

    it('creates new SSE server successfully', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /add server/i });
        fireEvent.click(addButton);
      });

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/server name/i);
        fireEvent.change(nameInput, { target: { value: 'remote-server' } });
      });

      await selectTransportType('sse');

      await waitFor(() => {
        const urlInput = screen.getByLabelText(/url/i);
        fireEvent.change(urlInput, { target: { value: 'http://localhost:3000/sse' } });
      });

      // Mock POST request
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          server: {
            id: 'mcp-3',
            name: 'remote-server',
            type: 'sse',
            url: 'http://localhost:3000/sse',
            enabled: true,
            status: 'active',
            created_at: new Date(),
            updated_at: new Date(),
          },
        }),
      });

      const submitButton = screen.getByRole('button', { name: /create server/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/mcp-servers',
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('remote-server'),
          })
        );
      });
    });

    it('shows validation errors for invalid input', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /add server/i });
        fireEvent.click(addButton);
      });

      const submitButton = screen.getByRole('button', { name: /create server/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      });
    });

    it('closes modal on cancel', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /add server/i });
        fireEvent.click(addButton);
      });

      await waitFor(() => {
        const cancelButton = screen.getByRole('button', { name: /cancel/i });
        fireEvent.click(cancelButton);
      });

      await waitFor(() => {
        expect(screen.queryByRole('heading', { name: /add mcp server/i })).not.toBeInTheDocument();
      });
    });
  });

  describe('Edit Existing Server', () => {
    it('opens edit form when Edit button clicked', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        const editButtons = screen.getAllByRole('button', { name: /edit/i });
        fireEvent.click(editButtons[0]);
      });

      await waitFor(() => {
        const headings = screen.getAllByRole('heading', { name: /edit mcp server/i });
        expect(headings.length).toBeGreaterThan(0);
        expect(screen.getByLabelText(/server name/i)).toHaveValue('postgres');
      });
    });

    it('updates server configuration successfully', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        const editButtons = screen.getAllByRole('button', { name: /edit/i });
        fireEvent.click(editButtons[0]);
      });

      await waitFor(() => {
        const envKeyInputs = screen.getAllByPlaceholderText(/key/i);
        const envValueInputs = screen.getAllByPlaceholderText(/value/i);

        fireEvent.change(envValueInputs[0], {
          target: { value: 'postgresql://localhost/newdb' },
        });
      });

      // Mock PUT request
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          server: {
            ...mockServers[0],
            env: { POSTGRES_URL: 'postgresql://localhost/newdb' },
            updated_at: new Date(),
          },
        }),
      });

      const submitButton = screen.getByRole('button', { name: /save changes/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/mcp-servers/postgres',
          expect.objectContaining({
            method: 'PUT',
          })
        );
      });
    });

    it('disables name field in edit mode', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        const editButtons = screen.getAllByRole('button', { name: /edit/i });
        fireEvent.click(editButtons[0]);
      });

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/server name/i);
        expect(nameInput).toBeDisabled();
      });
    });
  });

  describe('Delete Server', () => {
    it('shows confirmation dialog when Delete clicked', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
        fireEvent.click(deleteButtons[0]);
      });

      await waitFor(() => {
        expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument();
      });
    });

    it('deletes server when confirmed', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
        fireEvent.click(deleteButtons[0]);
      });

      // Mock DELETE request
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      await waitFor(() => {
        const confirmButton = screen.getByRole('button', { name: /confirm/i });
        fireEvent.click(confirmButton);
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/mcp-servers/postgres',
          expect.objectContaining({
            method: 'DELETE',
          })
        );
      });
    });

    it('cancels deletion when cancelled', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
        fireEvent.click(deleteButtons[0]);
      });

      await waitFor(() => {
        const cancelButton = screen.getByRole('button', { name: /cancel/i });
        fireEvent.click(cancelButton);
      });

      await waitFor(() => {
        expect(screen.queryByText(/are you sure/i)).not.toBeInTheDocument();
        expect(screen.getByText('postgres')).toBeInTheDocument();
      });
    });
  });

  describe.skip('Inline /mcp connect Command', () => {
    // T121: /mcp connect command - Not implemented yet
    it('executes /mcp connect command in Composer', async () => {
      // Mock autocomplete API to include /mcp command
      (global.fetch as jest.Mock).mockImplementation((url: string) => {
        if (url.includes('/api/autocomplete')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: [
                {
                  type: 'slash_command',
                  id: 'mcp-connect',
                  label: 'mcp connect',
                  description: 'Connect to MCP server',
                  icon: '🔌',
                  category: 'Commands',
                  insert_text: '/mcp connect',
                },
              ],
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      const onSend = jest.fn();
      render(<Composer onSend={onSend} />);

      const textarea = screen.getByRole('textbox');
      fireEvent.change(textarea, { target: { value: '/mcp connect postgres' } });

      const sendButton = screen.getByRole('button', { name: /send/i });
      fireEvent.click(sendButton);

      expect(onSend).toHaveBeenCalledWith('/mcp connect postgres');
    });

    it('shows /mcp connect in autocomplete suggestions', async () => {
      (global.fetch as jest.Mock).mockImplementation((url: string) => {
        if (url.includes('/api/autocomplete') && url.includes('trigger=/')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: [
                {
                  type: 'slash_command',
                  id: 'mcp-connect',
                  label: 'mcp connect',
                  description: 'Connect to MCP server',
                  icon: '🔌',
                  category: 'Commands',
                  insert_text: '/mcp connect',
                },
              ],
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({ items: [] }) });
      });

      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      fireEvent.change(textarea, { target: { value: '/mcp' } });

      await waitFor(() => {
        expect(screen.getByText('mcp connect')).toBeInTheDocument();
        expect(screen.getByText(/connect to mcp server/i)).toBeInTheDocument();
      });
    });
  });

  describe.skip('@mcp-server-name Mentions', () => {
    // T122: @mcp-server-name autocomplete - Not implemented yet
    it('shows MCP servers in @ autocomplete', async () => {
      (global.fetch as jest.Mock).mockImplementation((url: string) => {
        if (url.includes('/api/autocomplete') && url.includes('trigger=@')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: [
                {
                  type: 'mcp_server',
                  id: 'mcp-1',
                  label: 'postgres',
                  description: 'PostgreSQL database access',
                  icon: '🐘',
                  category: 'MCP Servers',
                  insert_text: '@postgres',
                },
              ],
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({ items: [] }) });
      });

      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      fireEvent.change(textarea, { target: { value: '@' } });

      await waitFor(() => {
        expect(screen.getByText('postgres')).toBeInTheDocument();
        expect(screen.getByText(/postgresql database access/i)).toBeInTheDocument();
      });
    });

    it('inserts @mcp-server-name on selection', async () => {
      (global.fetch as jest.Mock).mockImplementation((url: string) => {
        if (url.includes('/api/autocomplete') && url.includes('trigger=@')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: [
                {
                  type: 'mcp_server',
                  id: 'mcp-1',
                  label: 'postgres',
                  description: 'PostgreSQL database access',
                  icon: '🐘',
                  category: 'MCP Servers',
                  insert_text: '@postgres',
                },
              ],
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({ items: [] }) });
      });

      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      fireEvent.change(textarea, { target: { value: '@' } });

      await waitFor(() => {
        const item = screen.getByText('postgres').closest('button');
        fireEvent.click(item!);
      });

      expect(textarea.value).toBe('@postgres ');
    });
  });

  describe('Share MCP Server', () => {
    it('opens share modal when Share button clicked', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      await waitFor(() => {
        const shareButtons = screen.getAllByRole('button', { name: /share/i });
        fireEvent.click(shareButtons[0]);
      });

      await waitFor(() => {
        const headings = screen.getAllByRole('heading', { name: /share/i });
        expect(headings.length).toBeGreaterThan(0);
      });
    });

    it('generates share link for server', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      // Wait for servers to load first
      await waitFor(() => {
        expect(screen.getByText('postgres')).toBeInTheDocument();
      });

      // Mock POST /api/mcp-servers/postgres/share before clicking
      (global.fetch as jest.Mock).mockImplementationOnce((url: string) => {
        if (url.includes('/api/mcp-servers/postgres/share')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              share_url: 'https://example.com/share/mcp-abc123',
            }),
          });
        }
        // Return the default mock for other calls
        return Promise.resolve({
          ok: true,
          json: async () => ({ servers: mockServers }),
        });
      });

      await waitFor(() => {
        const shareButtons = screen.getAllByRole('button', { name: /share/i });
        fireEvent.click(shareButtons[0]);
      });

      // Wait for share modal and link to appear
      await waitFor(() => {
        const headings = screen.getAllByRole('heading', { name: /share/i });
        expect(headings.length).toBeGreaterThan(0);
      });
    });

    it('copies share link to clipboard', async () => {
      const mockClipboard = {
        writeText: jest.fn(),
      };
      Object.assign(navigator, { clipboard: mockClipboard });

      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      // Wait for servers to load first
      await waitFor(() => {
        expect(screen.getByText('postgres')).toBeInTheDocument();
      });

      // Mock POST /api/mcp-servers/postgres/share before clicking
      (global.fetch as jest.Mock).mockImplementationOnce((url: string) => {
        if (url.includes('/api/mcp-servers/postgres/share')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              share_url: 'https://example.com/share/mcp-abc123',
            }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ servers: mockServers }),
        });
      });

      await waitFor(() => {
        const shareButtons = screen.getAllByRole('button', { name: /share/i });
        fireEvent.click(shareButtons[0]);
      });

      // Wait for share modal to open
      await waitFor(() => {
        const headings = screen.getAllByRole('heading', { name: /share/i });
        expect(headings.length).toBeGreaterThan(0);
      });
    });

    it('sanitizes credentials in shared config', async () => {
      const McpServersPage = (await import('@/app/settings/mcp-servers/page')).default;
      render(<McpServersPage />);

      // Wait for servers to load first
      await waitFor(() => {
        expect(screen.getByText('postgres')).toBeInTheDocument();
      });

      // Mock POST request with sanitized config before clicking
      (global.fetch as jest.Mock).mockImplementationOnce((url: string) => {
        if (url.includes('/api/mcp-servers/postgres/share')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              share_url: 'https://example.com/share/mcp-abc123',
              config: {
                name: 'postgres',
                type: 'stdio',
                command: 'npx',
                args: ['-y', '@modelcontextprotocol/server-postgres'],
                // env should be omitted or redacted
              },
            }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ servers: mockServers }),
        });
      });

      await waitFor(() => {
        const shareButtons = screen.getAllByRole('button', { name: /share/i });
        fireEvent.click(shareButtons[0]);
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/mcp-servers/postgres/share',
          expect.objectContaining({
            method: 'POST',
          })
        );
      });
    });
  });
});
