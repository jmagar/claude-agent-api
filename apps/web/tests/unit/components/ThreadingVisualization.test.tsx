/**
 * Unit tests for ThreadingVisualization component
 *
 * Tests the visual threading system that displays connection lines
 * between parent/child tool calls and subagent messages.
 *
 * Threading modes:
 * - always: Always show connection lines
 * - hover: Show lines only on hover
 * - adaptive: Show for complex threads, hide for simple
 * - toggle: Manual toggle button
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { ThreadingVisualization } from '@/components/chat/ThreadingVisualization';
import type { ToolCall } from '@/types';

describe('ThreadingVisualization', () => {
  const childToolCalls: ToolCall[] = [
    {
      id: 'tool-2',
      name: 'WebSearch',
      status: 'success',
      input: { query: 'REST API best practices' },
      output: '10 results found',
      parent_tool_use_id: 'tool-1',
    },
    {
      id: 'tool-3',
      name: 'WebFetch',
      status: 'success',
      input: { url: 'https://example.com/api-guide' },
      output: 'Article content...',
      parent_tool_use_id: 'tool-1',
    },
  ];

  it('renders parent-child connection lines', () => {
    render(
      <ThreadingVisualization
        children={childToolCalls}
        mode="always"
      />
    );

    // Should render SVG connection lines
    const svg = screen.getByRole('img', { hidden: true });
    expect(svg).toBeInTheDocument();
    expect(svg.tagName).toBe('svg');

    // Should have 2 path elements (one for each child)
    const paths = svg.querySelectorAll('path');
    expect(paths).toHaveLength(2);
  });

  it('hides lines in hover mode by default', () => {
    const { container } = render(
      <ThreadingVisualization
        children={childToolCalls}
        mode="hover"
      />
    );

    // SVG should be hidden initially
    const svg = container.querySelector('svg');
    expect(svg).toHaveClass('opacity-0');
  });

  it('shows lines on hover in hover mode', () => {
    const { container } = render(
      <ThreadingVisualization
        children={childToolCalls}
        mode="hover"
      />
    );

    const wrapper = screen.getByTestId('threading-wrapper');
    fireEvent.mouseEnter(wrapper);

    const svg = container.querySelector('svg');
    expect(svg).toHaveClass('opacity-100');
  });

  it('hides lines for simple threads in adaptive mode', () => {
    // Single child = simple thread
    const simpleChildren = [childToolCalls[0]];

    render(
      <ThreadingVisualization
        children={simpleChildren}
        mode="adaptive"
      />
    );

    // Should not render threading for simple cases
    expect(screen.queryByRole('img', { hidden: true })).not.toBeInTheDocument();
  });

  it('shows lines for complex threads in adaptive mode', () => {
    // Multiple children = complex thread
    render(
      <ThreadingVisualization
        children={childToolCalls}
        mode="adaptive"
      />
    );

    // Should render threading for complex cases
    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
  });

  it('includes toggle button in toggle mode', () => {
    render(
      <ThreadingVisualization
        children={childToolCalls}
        mode="toggle"
      />
    );

    const toggleButton = screen.getByRole('button', { name: /toggle threading/i });
    expect(toggleButton).toBeInTheDocument();
  });

  it('toggles visibility when button clicked', () => {
    render(
      <ThreadingVisualization
        children={childToolCalls}
        mode="toggle"
      />
    );

    const toggleButton = screen.getByRole('button', { name: /toggle threading/i });
    const svg = screen.getByTestId('threading-svg');

    // Initial state (not toggled, should have hidden class)
    expect(svg).toHaveClass('hidden');

    // Click to show
    fireEvent.click(toggleButton);
    expect(svg).not.toHaveClass('hidden');

    // Click to hide again
    fireEvent.click(toggleButton);
    expect(svg).toHaveClass('hidden');
  });

  it('draws curved connection lines', () => {
    const { container } = render(
      <ThreadingVisualization
        children={childToolCalls}
        mode="always"
      />
    );

    const path = container.querySelector('path');
    const d = path?.getAttribute('d');

    // Bezier curve path should contain 'C' command
    expect(d).toMatch(/C/);
  });

  it('colors lines based on tool status', () => {
    const mixedChildren: ToolCall[] = [
      { ...childToolCalls[0], status: 'success' },
      { ...childToolCalls[1], status: 'error' },
    ];

    const { container } = render(
      <ThreadingVisualization
        children={mixedChildren}
        mode="always"
      />
    );

    const paths = container.querySelectorAll('path');

    // First path (success) should be green
    expect(paths[0]).toHaveClass('stroke-green-500');

    // Second path (error) should be red
    expect(paths[1]).toHaveClass('stroke-red-500');
  });

  it('handles deeply nested threading (3+ levels)', () => {
    const grandchildToolCall: ToolCall = {
      id: 'tool-4',
      name: 'Read',
      status: 'success',
      input: { path: 'example.md' },
      output: 'File contents',
      parent_tool_use_id: 'tool-2', // Child of tool-2
    };

    render(
      <>
        <ThreadingVisualization
          children={childToolCalls}
          mode="always"
        />
        <ThreadingVisualization
          children={[grandchildToolCall]}
          mode="always"
        />
      </>
    );

    // Should render 2 threading SVG elements (one for each level)
    const threadingSvgs = screen.getAllByTestId('threading-svg');
    expect(threadingSvgs).toHaveLength(2);
  });

  it('simplifies threading on mobile (indent-only, no lines)', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });
    global.dispatchEvent(new Event('resize'));

    render(
      <ThreadingVisualization
        children={childToolCalls}
        mode="always"
      />
    );

    // On mobile, should use indentation instead of SVG lines
    expect(screen.queryByRole('img', { hidden: true })).not.toBeInTheDocument();

    // Wrapper should have left margin for indentation
    const wrapper = screen.getByTestId('threading-wrapper');
    expect(wrapper).toHaveClass('ml-16'); // Tailwind margin
  });
});
