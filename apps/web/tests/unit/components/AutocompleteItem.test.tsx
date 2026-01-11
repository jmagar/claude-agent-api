/**
 * Unit tests for AutocompleteItem component
 *
 * Tests individual autocomplete item component that displays:
 * - Icon, label, and description
 * - Entity type badge
 * - Recently used indicator
 * - Hover and selected states
 * - Keyboard accessibility
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { AutocompleteItem } from '@/components/autocomplete/AutocompleteItem';
import type { AutocompleteItem as AutocompleteItemType } from '@/types';

describe('AutocompleteItem', () => {
  const mockItem: AutocompleteItemType = {
    type: 'agent',
    id: 'agent-1',
    label: 'code-reviewer',
    description: 'Reviews code for best practices',
    icon: '🤖',
    category: 'Agents',
    recently_used: true,
    insert_text: '@code-reviewer',
  };

  it('renders label', () => {
    render(<AutocompleteItem item={mockItem} onSelect={jest.fn()} />);

    expect(screen.getByText('code-reviewer')).toBeInTheDocument();
  });

  it('renders description', () => {
    render(<AutocompleteItem item={mockItem} onSelect={jest.fn()} />);

    expect(screen.getByText('Reviews code for best practices')).toBeInTheDocument();
  });

  it('renders icon', () => {
    render(<AutocompleteItem item={mockItem} onSelect={jest.fn()} />);

    expect(screen.getByText('🤖')).toBeInTheDocument();
  });

  it('renders without description if not provided', () => {
    const itemWithoutDesc = { ...mockItem, description: undefined };
    render(<AutocompleteItem item={itemWithoutDesc} onSelect={jest.fn()} />);

    expect(screen.getByText('code-reviewer')).toBeInTheDocument();
    // Should not have description element
    expect(screen.queryByText(/Reviews/)).not.toBeInTheDocument();
  });

  it('renders without icon if not provided', () => {
    const itemWithoutIcon = { ...mockItem, icon: undefined };
    render(<AutocompleteItem item={itemWithoutIcon} onSelect={jest.fn()} />);

    expect(screen.getByText('code-reviewer')).toBeInTheDocument();
    expect(screen.queryByText('🤖')).not.toBeInTheDocument();
  });

  it('displays entity type badge', () => {
    render(<AutocompleteItem item={mockItem} onSelect={jest.fn()} />);

    expect(screen.getByText('Agent')).toBeInTheDocument();
  });

  it('displays recently used indicator', () => {
    render(<AutocompleteItem item={mockItem} onSelect={jest.fn()} />);

    expect(screen.getByLabelText(/recently used/i)).toBeInTheDocument();
  });

  it('does not display recently used indicator when false', () => {
    const itemNotRecentlyUsed = { ...mockItem, recently_used: false };
    render(<AutocompleteItem item={itemNotRecentlyUsed} onSelect={jest.fn()} />);

    expect(screen.queryByLabelText(/recently used/i)).not.toBeInTheDocument();
  });

  it('calls onSelect when clicked', () => {
    const onSelect = jest.fn();
    render(<AutocompleteItem item={mockItem} onSelect={onSelect} />);

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(onSelect).toHaveBeenCalledWith(mockItem);
  });

  it('applies selected styling when isSelected is true', () => {
    render(<AutocompleteItem item={mockItem} onSelect={jest.fn()} isSelected={true} />);

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('data-selected', 'true');
    expect(button).toHaveClass(/selected|highlight|active/);
  });

  it('does not apply selected styling when isSelected is false', () => {
    render(<AutocompleteItem item={mockItem} onSelect={jest.fn()} isSelected={false} />);

    const button = screen.getByRole('button');
    expect(button).not.toHaveAttribute('data-selected', 'true');
  });

  it('displays different type badges correctly', () => {
    const testCases: Array<{ type: AutocompleteItemType['type']; expected: string }> = [
      { type: 'agent', expected: 'Agent' },
      { type: 'mcp_server', expected: 'MCP' },
      { type: 'file', expected: 'File' },
      { type: 'skill', expected: 'Skill' },
      { type: 'slash_command', expected: 'Command' },
    ];

    testCases.forEach(({ type, expected }) => {
      const item = { ...mockItem, type };
      const { unmount } = render(<AutocompleteItem item={item} onSelect={jest.fn()} />);

      expect(screen.getByText(expected)).toBeInTheDocument();
      unmount();
    });
  });

  it('has proper ARIA attributes for accessibility', () => {
    render(<AutocompleteItem item={mockItem} onSelect={jest.fn()} />);

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('role', 'button');
    expect(button).toHaveAttribute('aria-label', expect.stringContaining('code-reviewer'));
  });

  it('supports keyboard interaction (Enter)', () => {
    const onSelect = jest.fn();
    render(<AutocompleteItem item={mockItem} onSelect={onSelect} />);

    const button = screen.getByRole('button');
    fireEvent.keyDown(button, { key: 'Enter' });

    expect(onSelect).toHaveBeenCalledWith(mockItem);
  });

  it('supports keyboard interaction (Space)', () => {
    const onSelect = jest.fn();
    render(<AutocompleteItem item={mockItem} onSelect={onSelect} />);

    const button = screen.getByRole('button');
    fireEvent.keyDown(button, { key: ' ' });

    expect(onSelect).toHaveBeenCalledWith(mockItem);
  });

  it('displays hover state on mouse over', () => {
    render(<AutocompleteItem item={mockItem} onSelect={jest.fn()} />);

    const button = screen.getByRole('button');
    fireEvent.mouseEnter(button);

    expect(button).toHaveClass(/hover/);
  });

  it('renders with custom className', () => {
    render(
      <AutocompleteItem
        item={mockItem}
        onSelect={jest.fn()}
        className="custom-item"
      />
    );

    const button = screen.getByRole('button');
    expect(button).toHaveClass('custom-item');
  });

  it('displays category when provided', () => {
    render(<AutocompleteItem item={mockItem} onSelect={jest.fn()} showCategory={true} />);

    expect(screen.getByText('Agents')).toBeInTheDocument();
  });

  it('does not display category when showCategory is false', () => {
    render(<AutocompleteItem item={mockItem} onSelect={jest.fn()} showCategory={false} />);

    expect(screen.queryByText('Agents')).not.toBeInTheDocument();
  });

  it('truncates long labels', () => {
    const longLabel = 'a'.repeat(100);
    const itemWithLongLabel = { ...mockItem, label: longLabel };
    render(<AutocompleteItem item={itemWithLongLabel} onSelect={jest.fn()} />);

    const label = screen.getByTestId('label');
    // Check for Tailwind truncation classes
    expect(label).toHaveClass('overflow-hidden');
    expect(label).toHaveClass('text-ellipsis');
    expect(label).toHaveClass('whitespace-nowrap');
  });

  it('truncates long descriptions', () => {
    const longDesc = 'a'.repeat(200);
    const itemWithLongDesc = { ...mockItem, description: longDesc };
    render(<AutocompleteItem item={itemWithLongDesc} onSelect={jest.fn()} />);

    const description = screen.getByTestId('description');
    // Check for Tailwind truncation classes
    expect(description).toHaveClass('overflow-hidden');
    expect(description).toHaveClass('text-ellipsis');
    expect(description).toHaveClass('whitespace-nowrap');
  });

  it('displays shortcut hint for slash commands', () => {
    const slashCommand = {
      ...mockItem,
      type: 'slash_command' as const,
      label: 'commit',
      insert_text: '/commit',
    };
    render(<AutocompleteItem item={slashCommand} onSelect={jest.fn()} />);

    // Slash commands should show "/" prefix hint
    expect(screen.getByText(/\//)).toBeInTheDocument();
  });

  it('displays @ prefix hint for mention-based entities', () => {
    const mentionItem = {
      ...mockItem,
      type: 'agent' as const,
      insert_text: '@code-reviewer',
    };
    render(<AutocompleteItem item={mentionItem} onSelect={jest.fn()} />);

    // Should show "@" prefix hint
    expect(screen.getByText(/@/)).toBeInTheDocument();
  });

  it('handles items with missing required fields gracefully', () => {
    const minimalItem: AutocompleteItemType = {
      type: 'file',
      id: 'file-1',
      label: 'test.txt',
      insert_text: '@test.txt',
    };
    render(<AutocompleteItem item={minimalItem} onSelect={jest.fn()} />);

    expect(screen.getByText('test.txt')).toBeInTheDocument();
  });

  it('prevents default click behavior', () => {
    render(<AutocompleteItem item={mockItem} onSelect={jest.fn()} />);

    const button = screen.getByRole('button');
    const event = new MouseEvent('click', { bubbles: true, cancelable: true });
    const preventDefaultSpy = jest.spyOn(event, 'preventDefault');

    button.dispatchEvent(event);

    expect(preventDefaultSpy).toHaveBeenCalled();
  });
});
