/**
 * Integration tests for autocomplete flow
 *
 * Tests the full autocomplete interaction flow:
 * 1. User types @ or / trigger in Composer
 * 2. AutocompleteMenu appears with suggestions
 * 3. User filters suggestions by typing more characters
 * 4. User selects suggestion (click or keyboard)
 * 5. Selected text is inserted into Composer
 * 6. Menu closes after selection
 *
 * Features tested:
 * - @ trigger for mentions (agents, MCP servers, files, etc.)
 * - / trigger for slash commands and skills
 * - Real-time filtering as user types
 * - Keyboard navigation and selection
 * - Mouse click selection
 * - Recently used items prioritization
 * - API integration with /api/autocomplete
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Composer } from '@/components/chat/Composer';
import type { AutocompleteItem } from '@/types';

// Mock fetch for autocomplete API
global.fetch = jest.fn();

describe('Autocomplete Flow Integration', () => {
  const mockMentionItems: AutocompleteItem[] = [
    {
      type: 'agent',
      id: 'agent-1',
      label: 'code-reviewer',
      description: 'Reviews code for best practices',
      icon: '🤖',
      category: 'Agents',
      recently_used: true,
      insert_text: '@code-reviewer',
    },
    {
      type: 'mcp_server',
      id: 'mcp-1',
      label: 'postgres',
      description: 'PostgreSQL database access',
      icon: '🐘',
      category: 'MCP Servers',
      recently_used: false,
      insert_text: '@postgres',
    },
    {
      type: 'file',
      id: 'file-1',
      label: 'README.md',
      description: 'Project documentation',
      icon: '📄',
      category: 'Files',
      recently_used: true,
      insert_text: '@README.md',
    },
  ];

  const mockCommandItems: AutocompleteItem[] = [
    {
      type: 'skill',
      id: 'skill-1',
      label: 'debugging',
      description: 'Systematic debugging approach',
      icon: '🐛',
      category: 'Skills',
      recently_used: false,
      insert_text: '/debugging',
    },
    {
      type: 'slash_command',
      id: 'cmd-1',
      label: 'commit',
      description: 'Create git commit with Claude',
      icon: '✅',
      category: 'Commands',
      recently_used: false,
      insert_text: '/commit',
    },
  ];

  const setTextareaValue = (
    textarea: HTMLElement,
    value: string,
    selectionStart?: number
  ) => {
    const element = textarea as HTMLTextAreaElement;
    const cursorPosition = selectionStart ?? value.length;
    element.focus();
    element.setSelectionRange(cursorPosition, cursorPosition);
    fireEvent.change(element, {
      target: { value, selectionStart: cursorPosition },
    });
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock fetch to return different items based on trigger parameter
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      const urlObj = new URL(url, 'http://localhost');
      const trigger = urlObj.searchParams.get('trigger');
      const query = urlObj.searchParams.get('query') || '';

      let items = trigger === '@' ? mockMentionItems : mockCommandItems;

      // Filter by query if provided
      if (query) {
        items = items.filter((item) =>
          item.label.toLowerCase().includes(query.toLowerCase())
        );
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({ items }),
      });
    });
  });

  describe('@ trigger (mentions)', () => {
    it('shows autocomplete menu when @ is typed', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });
    });

    it('fetches autocomplete suggestions from API', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/autocomplete'),
          expect.objectContaining({
            method: 'GET',
          })
        );
      });
    });

    it('displays filtered suggestions as user types', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');

      // Type "@"
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
        expect(screen.getByText('postgres')).toBeInTheDocument();
        expect(screen.getByText('README.md')).toBeInTheDocument();
        // Should not show slash commands
        expect(screen.queryByText('debugging')).not.toBeInTheDocument();
        expect(screen.queryByText('commit')).not.toBeInTheDocument();
      });

      // Type "@code" to filter
      setTextareaValue(textarea, '@code');

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
        expect(screen.queryByText('postgres')).not.toBeInTheDocument();
      });
    });

    it('inserts selected item on click', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      // Click on code-reviewer
      const item = screen.getByText('code-reviewer').closest('button');
      fireEvent.click(item!);

      // Should insert @code-reviewer into textarea
      expect(textarea.value).toBe('@code-reviewer ');
    });

    it('inserts selected item on Enter key', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      const menu = screen.getByRole('menu');

      // Navigate to first item and press Enter
      fireEvent.keyDown(menu, { key: 'ArrowDown' });
      fireEvent.keyDown(menu, { key: 'Enter' });

      // Should insert selected item into textarea
      expect(textarea.value).toMatch(/@code-reviewer|@README\.md/);
    });

    it('closes menu after selection', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Click on an item
      const item = screen.getByText('code-reviewer').closest('button');
      fireEvent.click(item!);

      // Menu should close
      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument();
      });
    });

    it('closes menu on Escape key', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      const menu = screen.getByRole('menu');
      fireEvent.keyDown(menu, { key: 'Escape' });

      // Menu should close
      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument();
      });

      // Text should remain
      expect((textarea as HTMLTextAreaElement).value).toBe('@');
    });

    it('positions menu below cursor', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        const menu = screen.getByRole('menu');
        const style = window.getComputedStyle(menu);
        expect(style.position).toBe('absolute');
      });
    });

    it('shows recently used items first', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        const items = screen.getAllByRole('button');
        // Recently used items should be first (code-reviewer and README.md)
        // Items are sorted: recently_used first, then alphabetically
        expect(items.length).toBeGreaterThan(0);
        expect(items[0]).toHaveTextContent(/code-reviewer|README\.md/);
      });
    });

    it('handles @ in middle of text', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      setTextareaValue(textarea, 'Hello @');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Click on an item
      const item = screen.getByText('code-reviewer').closest('button');
      fireEvent.click(item!);

      // Should insert at cursor position
      expect(textarea.value).toBe('Hello @code-reviewer ');
    });
  });

  describe('/ trigger (slash commands)', () => {
    it('shows autocomplete menu when / is typed', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '/');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });
    });

    it('shows only slash commands and skills', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '/');

      await waitFor(() => {
        expect(screen.getByText('debugging')).toBeInTheDocument();
        expect(screen.getByText('commit')).toBeInTheDocument();
        // Should not show agents or MCP servers
        expect(screen.queryByText('code-reviewer')).not.toBeInTheDocument();
        expect(screen.queryByText('postgres')).not.toBeInTheDocument();
      });
    });

    it('inserts slash command on selection', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      setTextareaValue(textarea, '/');

      await waitFor(() => {
        expect(screen.getByText('commit')).toBeInTheDocument();
      });

      // Click on /commit
      const item = screen.getByText('commit').closest('button');
      fireEvent.click(item!);

      // Should insert /commit into textarea
      expect(textarea.value).toBe('/commit ');
    });

    it('only triggers at start of line or after space', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');

      // Typing "/" in middle of word should NOT trigger autocomplete
      setTextareaValue(textarea, 'http://example.com');

      // Menu should not appear
      expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    });
  });

  describe('Keyboard navigation', () => {
    it('navigates through items with arrow keys from the textarea', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '@', 1);

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      fireEvent.keyDown(textarea, { key: 'ArrowDown' });
      fireEvent.keyDown(textarea, { key: 'ArrowDown' });

      const items = screen.getAllByRole('button');
      expect(items[1]).toHaveAttribute('data-selected', 'true');
    });

    it('navigates through items with arrow keys', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      const menu = screen.getByRole('menu');

      // Navigate down twice
      fireEvent.keyDown(menu, { key: 'ArrowDown' });
      fireEvent.keyDown(menu, { key: 'ArrowDown' });

      // Second item should be selected
      const items = screen.getAllByRole('button');
      expect(items[1]).toHaveAttribute('data-selected', 'true');
    });

    it('wraps around when reaching end', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      const menu = screen.getByRole('menu');
      const items = screen.getAllByRole('button');

      // Navigate down past the last item
      for (let i = 0; i < items.length + 1; i++) {
        fireEvent.keyDown(menu, { key: 'ArrowDown' });
      }

      // Should wrap to first item
      expect(items[0]).toHaveAttribute('data-selected', 'true');
    });
  });

  describe('API error handling', () => {
    it('shows error state when API fails', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
      });
    });

    it('shows loading state while fetching', async () => {
      (global.fetch as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '@');

      // Should show loading state immediately
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });
  });

  describe('Debouncing', () => {
    it('debounces API calls when typing quickly', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');

      // Type quickly
      setTextareaValue(textarea, '@');
      setTextareaValue(textarea, '@c');
      setTextareaValue(textarea, '@co');
      setTextareaValue(textarea, '@cod');

      // Wait for debounce
      await waitFor(
        () => {
          // Should only call API once (or a few times, not for every keystroke)
          expect((global.fetch as jest.Mock).mock.calls.length).toBeLessThan(4);
        },
        { timeout: 500 }
      );
    });
  });

  describe('Edge cases', () => {
    it('opens menu when selectionStart is null', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      fireEvent.change(textarea, { target: { value: '@', selectionStart: null } });

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });
    });

    it('handles empty autocomplete results', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [] }),
      });

      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '@xyz123');

      await waitFor(() => {
        expect(screen.getByText(/no results found/i)).toBeInTheDocument();
      });
    });

    it('handles rapid trigger changes (@  -> /)', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');

      // Type @ then quickly change to /
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      setTextareaValue(textarea, '/');

      await waitFor(() => {
        // Should show slash commands, not mention items
        expect(screen.getByText('commit')).toBeInTheDocument();
        expect(screen.queryByText('code-reviewer')).not.toBeInTheDocument();
      });
    });

    it('closes menu when trigger is deleted', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox');
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Delete the @
      setTextareaValue(textarea, '');

      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument();
      });
    });

    it('maintains cursor position after insertion', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      setTextareaValue(textarea, '@');

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      // Click on code-reviewer
      const item = screen.getByText('code-reviewer').closest('button');
      fireEvent.click(item!);

      // Cursor should be after inserted text
      expect(textarea.selectionStart).toBe('@code-reviewer '.length);
    });

    it('maintains cursor position when insert text already exists', async () => {
      render(<Composer onSend={jest.fn()} />);

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      const startingValue = '@code-reviewer hello @';

      fireEvent.change(textarea, {
        target: {
          value: startingValue,
          selectionStart: startingValue.length,
        },
      });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      const item = screen.getByText('code-reviewer').closest('button');
      fireEvent.click(item!);

      const expectedValue = '@code-reviewer hello @code-reviewer ';
      expect(textarea.value).toBe(expectedValue);

      await waitFor(() => {
        expect(textarea.selectionStart).toBe(expectedValue.length);
      });
    });
  });
});
