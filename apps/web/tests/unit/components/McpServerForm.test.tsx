/**
 * Unit tests for McpServerForm component
 *
 * Tests the MCP server configuration form with:
 * - Create and edit modes
 * - Transport type selection (stdio, sse, http)
 * - Field validation
 * - JSON configuration editor (PlateJS)
 * - Environment variables editor
 * - Form submission and cancellation
 * - Error handling
 *
 * @see components/mcp/McpServerForm.tsx for implementation
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { McpServerForm } from '@/components/mcp/McpServerForm';
import type { McpServerConfig } from '@/types';

// Mock the PlateEditor component used by PlateJsonEditor
jest.mock('@/components/plate/PlateEditor', () => ({
  PlateEditor: ({ value, onChange, placeholder, ariaLabel }: {
    value: Array<{ type: string; lang?: string; children: Array<{ text: string }> }>;
    onChange: (value: Array<{ type: string; lang?: string; children: Array<{ text: string }> }>) => void;
    placeholder?: string;
    ariaLabel?: string;
  }) => {
    // Extract text from code_block node
    const getText = (nodes: Array<{ type: string; children: Array<{ text: string }> }>) => {
      if (nodes.length === 0) return '';
      const firstNode = nodes[0];
      return firstNode.children[0]?.text || '';
    };

    return (
      <textarea
        data-testid="plate-editor"
        aria-label={ariaLabel}
        placeholder={placeholder}
        value={getText(value)}
        onChange={(e) => {
          // Convert text back to code_block node for JSON editor
          const text = e.target.value;
          const nodes = [{
            type: 'code_block',
            lang: 'json',
            children: [{ text }]
          }];
          onChange(nodes);
        }}
      />
    );
  },
}));

// Mock PlateMarkdownToolbar to avoid platejs imports
jest.mock('@/components/plate/PlateMarkdownToolbar', () => ({
  PlateMarkdownToolbar: () => <div data-testid="plate-toolbar">Toolbar (mocked)</div>,
}));

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

  // Radix UI Select items have role="option" when using the default setup
  // Wait for the dropdown to appear then click the option by text
  // Use getAllByText and click the last one (the option in the dropdown, not the trigger)
  const options = await screen.findAllByText(optionText);
  fireEvent.click(options[options.length - 1]);
}

describe('McpServerForm', () => {
  const mockOnSubmit = jest.fn();
  const mockOnCancel = jest.fn();

  const existingServer: McpServerConfig = {
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
    created_at: new Date('2026-01-10T00:00:00Z'),
    updated_at: new Date('2026-01-11T10:00:00Z'),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders form in create mode by default', () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      expect(screen.getByRole('heading', { name: /add mcp server/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/server name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/transport type/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /create server/i })).toBeInTheDocument();
    });

    it('renders form in edit mode with existing server', () => {
      render(
        <McpServerForm
          server={existingServer}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByRole('heading', { name: /edit mcp server/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/server name/i)).toHaveValue('postgres');
      expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
    });

    it('disables name field in edit mode', () => {
      render(
        <McpServerForm
          server={existingServer}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      const nameInput = screen.getByLabelText(/server name/i);
      expect(nameInput).toBeDisabled();
    });

    it('renders cancel button', () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });
  });

  describe('Transport Type Selection', () => {
    it('shows stdio fields by default', () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      expect(screen.getByLabelText(/command/i)).toBeInTheDocument();
      expect(screen.getAllByLabelText(/mcp server arguments/i)[0]).toBeInTheDocument();
      expect(screen.queryByLabelText(/url/i)).not.toBeInTheDocument();
    });

    it('switches to sse fields when transport type changes', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      await selectTransportType('sse');

      await waitFor(() => {
        expect(screen.getByLabelText(/url/i)).toBeInTheDocument();
        expect(screen.queryByLabelText(/command/i)).not.toBeInTheDocument();
      });
    });

    it('switches to http fields when transport type changes', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      await selectTransportType('http');

      await waitFor(() => {
        expect(screen.getByLabelText(/url/i)).toBeInTheDocument();
        expect(screen.queryByLabelText(/command/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Form Fields', () => {
    it('displays name input field', () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const nameInput = screen.getByLabelText(/server name/i);
      expect(nameInput).toHaveAttribute('type', 'text');
      expect(nameInput).toHaveAttribute('placeholder', expect.any(String));
    });

    it('displays command input for stdio type', () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const commandInput = screen.getByLabelText(/command/i);
      expect(commandInput).toBeInTheDocument();
    });

    it('displays arguments editor with PlateJsonEditor for stdio type', () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      // PlateJsonEditor should be present (get the first one, which is the wrapper div)
      const argsEditors = screen.getAllByLabelText(/mcp server arguments/i);
      expect(argsEditors.length).toBeGreaterThan(0);
      expect(argsEditors[0]).toBeInTheDocument();
    });

    it('displays environment variables editor', () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      expect(screen.getAllByText(/environment variables/i)[0]).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /add variable/i })).toBeInTheDocument();
    });

    it('displays enabled toggle', () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      expect(screen.getByLabelText(/enabled/i)).toBeInTheDocument();
    });
  });

  describe('Validation', () => {
    it('shows error when name is empty on submit', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const submitButton = screen.getByRole('button', { name: /create server/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      });
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('shows error when command is empty for stdio type', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const nameInput = screen.getByLabelText(/server name/i);
      fireEvent.change(nameInput, { target: { value: 'test-server' } });

      const submitButton = screen.getByRole('button', { name: /create server/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/command is required/i)).toBeInTheDocument();
      });
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('shows error when URL is empty for sse type', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      await selectTransportType('sse');

      const nameInput = screen.getByLabelText(/server name/i);
      fireEvent.change(nameInput, { target: { value: 'test-server' } });

      const submitButton = screen.getByRole('button', { name: /create server/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/url is required/i)).toBeInTheDocument();
      });
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('validates URL format', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      await selectTransportType('sse');

      const nameInput = screen.getByLabelText(/server name/i);
      fireEvent.change(nameInput, { target: { value: 'test-server' } });

      const urlInput = screen.getByLabelText(/url/i);
      fireEvent.change(urlInput, { target: { value: 'not-a-url' } });

      const submitButton = screen.getByRole('button', { name: /create server/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/invalid url format/i)).toBeInTheDocument();
      });
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('validates server name uniqueness', async () => {
      render(
        <McpServerForm
          existingNames={['postgres', 'filesystem']}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      const nameInput = screen.getByLabelText(/server name/i);
      fireEvent.change(nameInput, { target: { value: 'postgres' } });

      const submitButton = screen.getByRole('button', { name: /create server/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/server name already exists/i)).toBeInTheDocument();
      });
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  describe('Environment Variables', () => {
    it('displays environment variable inputs', () => {
      render(
        <McpServerForm
          server={existingServer}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByDisplayValue('POSTGRES_URL')).toBeInTheDocument();
      expect(screen.getByDisplayValue('postgresql://localhost/mydb')).toBeInTheDocument();
    });

    it('adds new environment variable when Add Variable clicked', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const addButton = screen.getByRole('button', { name: /add variable/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        const keyInputs = screen.getAllByPlaceholderText(/key/i);
        expect(keyInputs).toHaveLength(1);
      });
    });

    it('removes environment variable when delete clicked', async () => {
      render(
        <McpServerForm
          server={existingServer}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      const deleteButtons = screen.getAllByRole('button', { name: /remove/i });
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.queryByDisplayValue('POSTGRES_URL')).not.toBeInTheDocument();
      });
    });

    it('allows editing environment variable key and value', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const addButton = screen.getByRole('button', { name: /add variable/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        const keyInputs = screen.getAllByPlaceholderText(/key/i);
        const valueInputs = screen.getAllByPlaceholderText(/value/i);

        fireEvent.change(keyInputs[0], { target: { value: 'API_KEY' } });
        fireEvent.change(valueInputs[0], { target: { value: 'secret-key' } });

        expect(keyInputs[0]).toHaveValue('API_KEY');
        expect(valueInputs[0]).toHaveValue('secret-key');
      });
    });
  });

  describe('Arguments Editor', () => {
    it('displays arguments as JSON array with PlateJsonEditor', () => {
      render(
        <McpServerForm
          server={existingServer}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      // Get the textarea element (second element with aria-label)
      const argsEditors = screen.getAllByLabelText(/mcp server arguments/i);
      const argsEditor = argsEditors.find(el => el.tagName === 'TEXTAREA');
      expect(argsEditor).toHaveValue(
        JSON.stringify(existingServer.args, null, 2)
      );
    });

    it('validates JSON format for arguments', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const nameInput = screen.getByLabelText(/server name/i);
      fireEvent.change(nameInput, { target: { value: 'test-server' } });

      const commandInput = screen.getByLabelText(/command/i);
      fireEvent.change(commandInput, { target: { value: 'npx' } });

      // Get the textarea element
      const argsEditors = screen.getAllByLabelText(/mcp server arguments/i);
      const argsEditor = argsEditors.find(el => el.tagName === 'TEXTAREA')!;
      fireEvent.change(argsEditor, { target: { value: 'not valid json' } });

      const submitButton = screen.getByRole('button', { name: /create server/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/invalid json format/i)).toBeInTheDocument();
      });
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  describe('Headers Editor (HTTP)', () => {
    it('displays headers editor for http transport type', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      await selectTransportType('http');

      await waitFor(() => {
        expect(screen.getByText('No headers configured')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /add header/i })).toBeInTheDocument();
      });
    });

    it('adds new header when Add Header clicked', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      await selectTransportType('http');

      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /add header/i });
        fireEvent.click(addButton);
      });

      await waitFor(() => {
        const keyInputs = screen.getAllByPlaceholderText(/header key/i);
        expect(keyInputs).toHaveLength(1);
      });
    });
  });

  describe('Form Submission', () => {
    it('calls onSubmit with form data for stdio server', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const nameInput = screen.getByLabelText(/server name/i);
      fireEvent.change(nameInput, { target: { value: 'test-server' } });

      const commandInput = screen.getByLabelText(/command/i);
      fireEvent.change(commandInput, { target: { value: 'npx' } });

      // Get the textarea element
      const argsEditors = screen.getAllByLabelText(/mcp server arguments/i);
      const argsEditor = argsEditors.find(el => el.tagName === 'TEXTAREA')!;
      fireEvent.change(argsEditor, {
        target: { value: '["--version"]' },
      });

      const submitButton = screen.getByRole('button', { name: /create server/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'test-server',
            type: 'stdio',
            command: 'npx',
            args: ['--version'],
            enabled: true,
          })
        );
      });
    });

    it('calls onSubmit with form data for sse server', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const nameInput = screen.getByLabelText(/server name/i);
      fireEvent.change(nameInput, { target: { value: 'test-server' } });

      await selectTransportType('sse');

      await waitFor(() => {
        const urlInput = screen.getByLabelText(/url/i);
        fireEvent.change(urlInput, { target: { value: 'http://localhost:3000/sse' } });
      });

      const submitButton = screen.getByRole('button', { name: /create server/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'test-server',
            type: 'sse',
            url: 'http://localhost:3000/sse',
            enabled: true,
          })
        );
      });
    });

    it('includes environment variables in submission', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const nameInput = screen.getByLabelText(/server name/i);
      fireEvent.change(nameInput, { target: { value: 'test-server' } });

      const commandInput = screen.getByLabelText(/command/i);
      fireEvent.change(commandInput, { target: { value: 'npx' } });

      const addButton = screen.getByRole('button', { name: /add variable/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        const keyInputs = screen.getAllByPlaceholderText(/key/i);
        const valueInputs = screen.getAllByPlaceholderText(/value/i);

        fireEvent.change(keyInputs[0], { target: { value: 'API_KEY' } });
        fireEvent.change(valueInputs[0], { target: { value: 'test-key' } });
      });

      const submitButton = screen.getByRole('button', { name: /create server/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            env: { API_KEY: 'test-key' },
          })
        );
      });
    });

    it('disables submit button while submitting', async () => {
      mockOnSubmit.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const nameInput = screen.getByLabelText(/server name/i);
      fireEvent.change(nameInput, { target: { value: 'test-server' } });

      const commandInput = screen.getByLabelText(/command/i);
      fireEvent.change(commandInput, { target: { value: 'npx' } });

      const submitButton = screen.getByRole('button', { name: /create server/i });
      fireEvent.click(submitButton);

      expect(submitButton).toBeDisabled();

      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
    });
  });

  describe('Form Cancellation', () => {
    it('calls onCancel when cancel button clicked', () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    });

    it('does not call onSubmit when cancelling', () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has proper labels for all form fields', () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      expect(screen.getByLabelText(/server name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/transport type/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/command/i)).toBeInTheDocument();
      expect(screen.getAllByLabelText(/mcp server arguments/i)[0]).toBeInTheDocument();
      expect(screen.getByLabelText(/enabled/i)).toBeInTheDocument();
    });

    it('displays validation errors with proper ARIA attributes', async () => {
      render(<McpServerForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const submitButton = screen.getByRole('button', { name: /create server/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        const errorMessage = screen.getByText(/name is required/i);
        expect(errorMessage).toHaveAttribute('role', 'alert');
      });
    });
  });
});
