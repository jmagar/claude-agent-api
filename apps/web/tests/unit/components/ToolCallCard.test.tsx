/**
 * Unit tests for ToolCallCard component
 *
 * Tests the collapsible tool call card component that displays:
 * - Tool name and status badge
 * - Collapsible input/output sections
 * - Retry button for failed tools
 * - Approval/deny buttons for pending tools
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { ToolCallCard } from '@/components/chat/ToolCallCard';
import type { ToolCall } from '@/types';

describe('ToolCallCard', () => {
  const mockToolCall: ToolCall = {
    id: 'tool-1',
    name: 'ReadFile',
    status: 'success',
    input: { path: '/src/index.ts' },
    output: 'const hello = "world";',
    started_at: new Date('2026-01-10T10:00:00Z'),
    duration_ms: 150,
  };

  it('renders tool name and status badge', () => {
    render(<ToolCallCard toolCall={mockToolCall} />);

    expect(screen.getByText('ReadFile')).toBeInTheDocument();
    expect(screen.getByText('success')).toBeInTheDocument();
  });

  it('displays collapsed by default', () => {
    render(<ToolCallCard toolCall={mockToolCall} collapsed={true} />);

    // Input/output should not be visible when collapsed
    expect(screen.queryByText('/src/index.ts')).not.toBeInTheDocument();
    expect(screen.queryByText('const hello = "world";')).not.toBeInTheDocument();
  });

  it('expands when clicked', () => {
    const onToggle = jest.fn();
    render(<ToolCallCard toolCall={mockToolCall} collapsed={true} onToggle={onToggle} />);

    // Click the card header to expand
    const header = screen.getByText('ReadFile').closest('button');
    fireEvent.click(header!);

    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it('shows input and output when expanded', () => {
    render(<ToolCallCard toolCall={mockToolCall} collapsed={false} />);

    // Should show both input and output (formatted as JSON)
    expect(screen.getByText(/path/i)).toBeInTheDocument();
    expect(screen.getByText(/\/src\/index\.ts/)).toBeInTheDocument();
    expect(screen.getByText(/const hello/)).toBeInTheDocument();
  });

  it('displays error state with error message', () => {
    const errorToolCall: ToolCall = {
      ...mockToolCall,
      status: 'error',
      error: 'File not found: /src/index.ts',
    };

    render(<ToolCallCard toolCall={errorToolCall} collapsed={false} />);

    expect(screen.getByText('error')).toBeInTheDocument();
    expect(screen.getByText(/File not found/)).toBeInTheDocument();
  });

  it('shows retry button for failed tools', () => {
    const onRetry = jest.fn();
    const errorToolCall: ToolCall = {
      ...mockToolCall,
      status: 'error',
      error: 'Network timeout',
    };

    render(
      <ToolCallCard
        toolCall={errorToolCall}
        collapsed={false}
        onRetry={onRetry}
      />
    );

    const retryButton = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryButton);

    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('shows approval buttons when needs approval', () => {
    const onApprove = jest.fn();
    const onDeny = jest.fn();

    render(
      <ToolCallCard
        toolCall={mockToolCall}
        needsApproval={true}
        onApprove={onApprove}
        onDeny={onDeny}
        collapsed={false}
      />
    );

    const approveButton = screen.getByRole('button', { name: /approve/i });
    const denyButton = screen.getByRole('button', { name: /deny/i });

    fireEvent.click(approveButton);
    expect(onApprove).toHaveBeenCalledTimes(1);

    fireEvent.click(denyButton);
    expect(onDeny).toHaveBeenCalledTimes(1);
  });

  it('displays running state with loading indicator', () => {
    const runningToolCall: ToolCall = {
      ...mockToolCall,
      status: 'running',
      output: undefined,
    };

    render(<ToolCallCard toolCall={runningToolCall} collapsed={false} />);

    expect(screen.getByText('running')).toBeInTheDocument();
    // Should show loading indicator (spinner or skeleton)
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('formats duration correctly', () => {
    render(<ToolCallCard toolCall={mockToolCall} collapsed={false} />);

    // Duration: 150ms
    expect(screen.getByText(/150ms/)).toBeInTheDocument();
  });

  it('renders JSON input/output in code blocks', () => {
    const jsonToolCall: ToolCall = {
      ...mockToolCall,
      input: { query: 'SELECT * FROM users', limit: 10 },
      output: { rows: [{ id: 1, name: 'Alice' }], count: 1 },
    };

    render(<ToolCallCard toolCall={jsonToolCall} collapsed={false} />);

    // Should render code blocks with formatted JSON
    const codeBlocks = screen.getAllByTestId('code-block');
    expect(codeBlocks.length).toBeGreaterThanOrEqual(2); // Input and output

    // Should contain the query text
    expect(screen.getByText(/SELECT \* FROM users/)).toBeInTheDocument();
  });

  it('renders output section for empty string output', () => {
    const emptyOutputToolCall: ToolCall = {
      ...mockToolCall,
      output: '',
    };

    render(<ToolCallCard toolCall={emptyOutputToolCall} collapsed={false} />);

    expect(screen.getByText('Output')).toBeInTheDocument();
    const codeBlocks = screen.getAllByTestId('code-block');
    expect(codeBlocks.length).toBeGreaterThanOrEqual(2);
  });
});
