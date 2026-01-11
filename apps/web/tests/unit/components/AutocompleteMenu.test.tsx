/**
 * Unit tests for AutocompleteMenu component
 *
 * Tests the autocomplete dropdown menu that appears when user types @ or / triggers.
 * Displays filtered suggestions with keyboard navigation, icons, and categories.
 *
 * Features tested:
 * - Rendering autocomplete items
 * - Filtering by search query
 * - Keyboard navigation (ArrowUp, ArrowDown, Enter, Escape)
 * - Recently used items displayed first
 * - Item selection (click and keyboard)
 * - Empty states
 * - Category grouping
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { AutocompleteMenu } from '@/components/autocomplete/AutocompleteMenu';
import type { AutocompleteItem } from '@/types';

describe('AutocompleteMenu', () => {
  const mockItems: AutocompleteItem[] = [
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
      type: 'mcp_tool',
      id: 'tool-1',
      label: 'query',
      description: 'Execute SQL query',
      icon: '🔧',
      category: 'Tools',
      recently_used: false,
      insert_text: '@postgres/query',
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
  ];

  it('renders all autocomplete items', () => {
    render(<AutocompleteMenu items={mockItems} onSelect={jest.fn()} />);

    expect(screen.getByText('code-reviewer')).toBeInTheDocument();
    expect(screen.getByText('postgres')).toBeInTheDocument();
    expect(screen.getByText('query')).toBeInTheDocument();
    expect(screen.getByText('README.md')).toBeInTheDocument();
    expect(screen.getByText('debugging')).toBeInTheDocument();
  });

  it('displays item descriptions', () => {
    render(<AutocompleteMenu items={mockItems} onSelect={jest.fn()} />);

    expect(screen.getByText('Reviews code for best practices')).toBeInTheDocument();
    expect(screen.getByText('PostgreSQL database access')).toBeInTheDocument();
  });

  it('displays item icons', () => {
    render(<AutocompleteMenu items={mockItems} onSelect={jest.fn()} />);

    expect(screen.getByText('🤖')).toBeInTheDocument();
    expect(screen.getByText('🐘')).toBeInTheDocument();
    expect(screen.getByText('🔧')).toBeInTheDocument();
  });

  it('shows recently used items at the top', () => {
    render(<AutocompleteMenu items={mockItems} onSelect={jest.fn()} />);

    const items = screen.getAllByRole('button');
    // First items should be recently used ones: code-reviewer and README.md
    expect(items[0]).toHaveTextContent('code-reviewer');
    expect(items[1]).toHaveTextContent('README.md');
  });

  it('groups items by category', () => {
    render(<AutocompleteMenu items={mockItems} onSelect={jest.fn()} groupByCategory={true} />);

    expect(screen.getByText('Agents')).toBeInTheDocument();
    expect(screen.getByText('MCP Servers')).toBeInTheDocument();
    expect(screen.getByText('Tools')).toBeInTheDocument();
    expect(screen.getByText('Files')).toBeInTheDocument();
    expect(screen.getByText('Skills')).toBeInTheDocument();
  });

  it('filters items by search query', () => {
    render(
      <AutocompleteMenu
        items={mockItems}
        onSelect={jest.fn()}
        searchQuery="post"
      />
    );

    // Should show only postgres (MCP server)
    expect(screen.getByText('postgres')).toBeInTheDocument();
    expect(screen.queryByText('code-reviewer')).not.toBeInTheDocument();
    expect(screen.queryByText('query')).not.toBeInTheDocument();
  });

  it('filters items case-insensitively', () => {
    render(
      <AutocompleteMenu
        items={mockItems}
        onSelect={jest.fn()}
        searchQuery="CODE"
      />
    );

    expect(screen.getByText('code-reviewer')).toBeInTheDocument();
  });

  it('shows empty state when no items match', () => {
    render(
      <AutocompleteMenu
        items={mockItems}
        onSelect={jest.fn()}
        searchQuery="xyz123"
      />
    );

    expect(screen.getByText(/no results found/i)).toBeInTheDocument();
  });

  it('shows empty state when no items provided', () => {
    render(<AutocompleteMenu items={[]} onSelect={jest.fn()} />);

    expect(screen.getByText(/no suggestions available/i)).toBeInTheDocument();
  });

  it('calls onSelect when item is clicked', () => {
    const onSelect = jest.fn();
    render(<AutocompleteMenu items={mockItems} onSelect={onSelect} />);

    const item = screen.getByText('code-reviewer').closest('button');
    fireEvent.click(item!);

    expect(onSelect).toHaveBeenCalledWith(mockItems[0]);
  });

  it('highlights selected item on keyboard navigation', () => {
    render(<AutocompleteMenu items={mockItems} onSelect={jest.fn()} />);

    const menu = screen.getByRole('menu');

    // Press ArrowDown to select first item
    fireEvent.keyDown(menu, { key: 'ArrowDown' });

    const firstItem = screen.getByText('code-reviewer').closest('button');
    expect(firstItem).toHaveAttribute('data-selected', 'true');
  });

  it('navigates down with ArrowDown key', () => {
    render(<AutocompleteMenu items={mockItems} onSelect={jest.fn()} />);

    const menu = screen.getByRole('menu');

    // Press ArrowDown twice to select second item
    fireEvent.keyDown(menu, { key: 'ArrowDown' });
    fireEvent.keyDown(menu, { key: 'ArrowDown' });

    const secondItem = screen.getByText('README.md').closest('button');
    expect(secondItem).toHaveAttribute('data-selected', 'true');
  });

  it('navigates up with ArrowUp key', () => {
    render(<AutocompleteMenu items={mockItems} onSelect={jest.fn()} />);

    const menu = screen.getByRole('menu');

    // Navigate down twice then up once
    fireEvent.keyDown(menu, { key: 'ArrowDown' });
    fireEvent.keyDown(menu, { key: 'ArrowDown' });
    fireEvent.keyDown(menu, { key: 'ArrowUp' });

    const firstItem = screen.getByText('code-reviewer').closest('button');
    expect(firstItem).toHaveAttribute('data-selected', 'true');
  });

  it('wraps around at the end when navigating down', () => {
    render(<AutocompleteMenu items={mockItems} onSelect={jest.fn()} />);

    const menu = screen.getByRole('menu');

    // Navigate down past the last item
    for (let i = 0; i < mockItems.length + 1; i++) {
      fireEvent.keyDown(menu, { key: 'ArrowDown' });
    }

    // Should wrap to first item
    const firstItem = screen.getByText('code-reviewer').closest('button');
    expect(firstItem).toHaveAttribute('data-selected', 'true');
  });

  it('wraps around at the beginning when navigating up', () => {
    render(<AutocompleteMenu items={mockItems} onSelect={jest.fn()} />);

    const menu = screen.getByRole('menu');
    const allButtons = screen.getAllByRole('button');

    // Press ArrowUp when no item selected (should select last item)
    fireEvent.keyDown(menu, { key: 'ArrowUp' });

    // Check that the last button in the sorted list is selected
    const lastButton = allButtons[allButtons.length - 1];
    expect(lastButton).toHaveAttribute('data-selected', 'true');
  });

  it('calls onSelect when Enter is pressed on selected item', () => {
    const onSelect = jest.fn();
    render(<AutocompleteMenu items={mockItems} onSelect={onSelect} />);

    const menu = screen.getByRole('menu');

    // Select first item and press Enter
    fireEvent.keyDown(menu, { key: 'ArrowDown' });
    fireEvent.keyDown(menu, { key: 'Enter' });

    expect(onSelect).toHaveBeenCalledWith(mockItems[0]);
  });

  it('calls onClose when Escape is pressed', () => {
    const onClose = jest.fn();
    render(<AutocompleteMenu items={mockItems} onSelect={jest.fn()} onClose={onClose} />);

    const menu = screen.getByRole('menu');
    fireEvent.keyDown(menu, { key: 'Escape' });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('positions below the trigger element', () => {
    render(
      <AutocompleteMenu
        items={mockItems}
        onSelect={jest.fn()}
        position={{ top: 100, left: 50 }}
      />
    );

    const menu = screen.getByRole('menu');
    expect(menu).toHaveStyle({ top: '100px', left: '50px' });
  });

  it('renders with max height and scrolls if too many items', () => {
    const manyItems = Array.from({ length: 50 }, (_, i) => ({
      type: 'agent' as const,
      id: `agent-${i}`,
      label: `Agent ${i}`,
      description: 'Test agent',
      insert_text: `@agent-${i}`,
    }));

    render(<AutocompleteMenu items={manyItems} onSelect={jest.fn()} />);

    const menu = screen.getByRole('menu');
    // Check for Tailwind overflow classes
    expect(menu).toHaveClass('max-h-300');
    expect(menu).toHaveClass('overflow-y-auto');
  });

  it('does not steal focus from a focused textarea on mount', () => {
    const { rerender } = render(
      <div>
        <textarea aria-label="composer" />
      </div>
    );

    const composer = screen.getByLabelText('composer');
    composer.focus();
    expect(document.activeElement).toBe(composer);

    rerender(
      <div>
        <textarea aria-label="composer" />
        <AutocompleteMenu items={mockItems} onSelect={jest.fn()} />
      </div>
    );

    expect(document.activeElement).toBe(screen.getByLabelText('composer'));
  });

  it('displays loading state', () => {
    render(<AutocompleteMenu items={[]} onSelect={jest.fn()} isLoading={true} />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('displays error state', () => {
    render(
      <AutocompleteMenu
        items={[]}
        onSelect={jest.fn()}
        error="Failed to load suggestions"
      />
    );

    expect(screen.getByText('Failed to load suggestions')).toBeInTheDocument();
  });

  it('supports custom className', () => {
    render(
      <AutocompleteMenu
        items={mockItems}
        onSelect={jest.fn()}
        className="custom-menu"
      />
    );

    const menu = screen.getByRole('menu');
    expect(menu).toHaveClass('custom-menu');
  });

  it('prevents default behavior on ArrowDown/ArrowUp to avoid scrolling', () => {
    render(<AutocompleteMenu items={mockItems} onSelect={jest.fn()} />);

    const menu = screen.getByRole('menu');

    const arrowDownEvent = new KeyboardEvent('keydown', { key: 'ArrowDown' });
    const preventDefaultSpy = jest.spyOn(arrowDownEvent, 'preventDefault');

    fireEvent(menu, arrowDownEvent);

    expect(preventDefaultSpy).toHaveBeenCalled();
  });
});
