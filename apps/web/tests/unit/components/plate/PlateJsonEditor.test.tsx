/**
 * Tests for PlateJsonEditor component
 *
 * Verifies JSON-specific editor with validation for MCP Server args.
 */

import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PlateJsonEditor } from '@/components/plate/PlateJsonEditor';
import { z } from 'zod';

// Mock the PlateEditor component
jest.mock('@/components/plate/PlateEditor', () => ({
  PlateEditor: ({
    value,
    onChange,
    placeholder,
    ariaLabel,
  }: {
    value: Array<{ type: string; children: Array<{ text: string }> }>;
    onChange: (value: Array<{ type: string; children: Array<{ text: string }> }>) => void;
    placeholder?: string;
    ariaLabel?: string;
  }) => (
    <div data-testid="plate-editor" aria-label={ariaLabel} data-placeholder={placeholder}>
      <textarea
        data-testid="plate-editor-textarea"
        value={JSON.stringify(value)}
        onChange={(e) => {
          try {
            const parsed = JSON.parse(e.target.value);
            onChange(parsed);
          } catch {
            // Ignore invalid JSON
          }
        }}
      />
    </div>
  ),
}));

describe('PlateJsonEditor', () => {
  it('should render code block editor with JSON syntax', () => {
    const jsonValue = '{"name": "test", "value": 42}';

    render(<PlateJsonEditor value={jsonValue} onChange={jest.fn()} />);

    expect(screen.getByTestId('plate-editor')).toBeInTheDocument();
    expect(screen.getByTestId('plate-editor')).toHaveAttribute('aria-label', 'JSON editor');
  });

  it('should display valid JSON in the editor', () => {
    const jsonValue = '{"name": "test", "value": 42}';

    render(<PlateJsonEditor value={jsonValue} onChange={jest.fn()} />);

    const textarea = screen.getByTestId('plate-editor-textarea') as HTMLTextAreaElement;
    const slateValue = JSON.parse(textarea.value);

    // Should have code_block node with JSON content
    expect(slateValue).toHaveLength(1);
    expect(slateValue[0].type).toBe('code_block');
    expect(slateValue[0].children[0].text).toBe(jsonValue);
  });

  it('should validate JSON on change and show no errors for valid JSON', () => {
    const onChange = jest.fn();
    const jsonValue = '{"name": "test"}';

    render(<PlateJsonEditor value={jsonValue} onChange={onChange} />);

    // No error should be shown
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('should show validation errors for invalid JSON', async () => {
    const onChange = jest.fn();
    const invalidJson = '{invalid json}';

    render(<PlateJsonEditor value={invalidJson} onChange={onChange} />);

    // Should show error
    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
    expect(alert.textContent).toBeTruthy();
  });

  it('should validate against Zod schema if provided', () => {
    const schema = z.object({
      name: z.string(),
      age: z.number(),
    });

    const validJson = '{"name": "John", "age": 30}';

    render(<PlateJsonEditor value={validJson} onChange={jest.fn()} schema={schema} />);

    // Should not show schema validation error
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('should show Zod validation errors if schema validation fails', () => {
    const schema = z.object({
      name: z.string(),
      age: z.number(),
    });

    const invalidJson = '{"name": "John", "age": "thirty"}';

    render(<PlateJsonEditor value={invalidJson} onChange={jest.fn()} schema={schema} />);

    // Should show schema validation error
    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveTextContent(/expected number/i);
  });

  it('should render Format button that is enabled for valid JSON', () => {
    const jsonValue = '{"name":"test","value":42}';

    render(<PlateJsonEditor value={jsonValue} onChange={jest.fn()} />);

    const formatButton = screen.getByRole('button', { name: /format/i });
    expect(formatButton).toBeInTheDocument();
    expect(formatButton).not.toBeDisabled();
  });

  it('should disable Format button for invalid JSON', () => {
    const invalidJson = '{invalid}';

    render(<PlateJsonEditor value={invalidJson} onChange={jest.fn()} />);

    const formatButton = screen.getByRole('button', { name: /format/i });
    expect(formatButton).toBeDisabled();
  });

  it('should prettify JSON when Format button is clicked', async () => {
    const user = userEvent.setup();
    const onChange = jest.fn();
    const compactJson = '{"name":"test","value":42}';
    const expectedFormatted = '{\n  "name": "test",\n  "value": 42\n}';

    render(<PlateJsonEditor value={compactJson} onChange={onChange} />);

    const formatButton = screen.getByRole('button', { name: /format/i });
    await user.click(formatButton);

    // Should call onChange with formatted JSON
    expect(onChange).toHaveBeenCalledWith(expectedFormatted);
  });

  it('should pass custom aria-label to editor', () => {
    const jsonValue = '{"name": "test"}';

    render(
      <PlateJsonEditor
        value={jsonValue}
        onChange={jest.fn()}
        ariaLabel="MCP server arguments"
      />
    );

    const editor = screen.getByTestId('plate-editor');
    expect(editor).toHaveAttribute('aria-label', 'MCP server arguments');
  });

  it('should pass custom placeholder to editor', () => {
    const jsonValue = '{}';

    render(
      <PlateJsonEditor
        value={jsonValue}
        onChange={jest.fn()}
        placeholder="Enter JSON arguments"
      />
    );

    const editor = screen.getByTestId('plate-editor');
    expect(editor).toHaveAttribute('data-placeholder', 'Enter JSON arguments');
  });

  it('should call onChange when editor content changes', async () => {
    const onChange = jest.fn();
    const initialJson = '{"name": "test"}';

    render(<PlateJsonEditor value={initialJson} onChange={onChange} />);

    const textarea = screen.getByTestId('plate-editor-textarea') as HTMLTextAreaElement;
    const newSlateValue = [
      { type: 'code_block', children: [{ text: '{"name": "updated"}' }] },
    ];

    fireEvent.change(textarea, {
      target: { value: JSON.stringify(newSlateValue) },
    });

    // Should call onChange with updated JSON
    expect(onChange).toHaveBeenCalled();
  });

  it('should handle empty JSON object', () => {
    const jsonValue = '{}';

    render(<PlateJsonEditor value={jsonValue} onChange={jest.fn()} />);

    // Should not show error for valid empty object
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('should handle empty JSON array', () => {
    const jsonValue = '[]';

    render(<PlateJsonEditor value={jsonValue} onChange={jest.fn()} />);

    // Should not show error for valid empty array
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('should show clear error message for common JSON mistakes', () => {
    const jsonWithTrailingComma = '{"name": "test",}';

    render(<PlateJsonEditor value={jsonWithTrailingComma} onChange={jest.fn()} />);

    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
    expect(alert.textContent).toBeTruthy();
  });

  it('should prioritize JSON parse errors over Zod validation errors', () => {
    const schema = z.object({
      name: z.string(),
    });

    const invalidJson = '{invalid}';

    render(<PlateJsonEditor value={invalidJson} onChange={jest.fn()} schema={schema} />);

    const alert = screen.getByRole('alert');
    // Should show JSON parse error, not Zod error
    expect(alert).toBeInTheDocument();
    expect(alert.textContent).toBeTruthy();
  });
});
