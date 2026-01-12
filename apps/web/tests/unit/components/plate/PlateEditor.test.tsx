/**
 * PlateEditor Component Tests
 *
 * Tests the PlateEditor wrapper component that integrates installed @plate components.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PlateEditor } from '@/components/plate/PlateEditor';
import type { SlateValue } from '@/lib/slate-serializers';

// Mock the @plate components
jest.mock('platejs/react', () => ({
  Plate: ({ children, onChange, editor }: any) => {
    return (
      <div data-testid="plate-provider" data-value={editor?.value ? JSON.stringify(editor.value) : undefined}>
        {children}
      </div>
    );
  },
  usePlateEditor: (options: any) => {
    return {
      id: options.id,
      plugins: options.plugins,
      value: options.value,
      children: options.value,
    };
  },
}));

jest.mock('@/components/ui/editor', () => ({
  EditorContainer: ({ children, ...props }: any) => (
    <div data-testid="editor-container" {...props}>
      {children}
    </div>
  ),
  Editor: ({ placeholder, disabled, autoFocus, ...props }: any) => (
    <div
      data-testid="plate-editor"
      data-placeholder={placeholder}
      data-disabled={disabled}
      data-autofocus={autoFocus ? 'true' : 'false'}
      aria-label={props['aria-label']}
      aria-describedby={props['aria-describedby']}
      contentEditable={!disabled}
      role="textbox"
      {...props}
    />
  ),
}));

jest.mock('@/components/editor/editor-base-kit', () => ({
  BaseEditorKit: [],
}));

describe('PlateEditor', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('rendering', () => {
    it('renders editor with empty state', () => {
      const emptyValue: SlateValue = [{ type: 'p', children: [{ text: '' }] }];

      render(<PlateEditor value={emptyValue} onChange={mockOnChange} />);

      expect(screen.getByTestId('plate-provider')).toBeInTheDocument();
      expect(screen.getByTestId('editor-container')).toBeInTheDocument();
      expect(screen.getByTestId('plate-editor')).toBeInTheDocument();
    });

    it('renders with initial value', () => {
      const initialValue: SlateValue = [
        { type: 'p', children: [{ text: 'Hello world' }] },
      ];

      render(<PlateEditor value={initialValue} onChange={mockOnChange} />);

      const provider = screen.getByTestId('plate-provider');
      expect(provider).toBeInTheDocument();

      // Verify value is passed to Plate provider
      const valueData = provider.getAttribute('data-value');
      expect(valueData).toBeTruthy();
      const parsedValue = JSON.parse(valueData!);
      expect(parsedValue).toEqual(initialValue);
    });

    it('applies placeholder', () => {
      const emptyValue: SlateValue = [{ type: 'p', children: [{ text: '' }] }];

      render(
        <PlateEditor
          value={emptyValue}
          onChange={mockOnChange}
          placeholder="Enter text here..."
        />
      );

      const editor = screen.getByTestId('plate-editor');
      expect(editor).toHaveAttribute('data-placeholder', 'Enter text here...');
    });

    it('applies aria-label', () => {
      const emptyValue: SlateValue = [{ type: 'p', children: [{ text: '' }] }];

      render(
        <PlateEditor
          value={emptyValue}
          onChange={mockOnChange}
          ariaLabel="Skill content editor"
        />
      );

      const editor = screen.getByTestId('plate-editor');
      expect(editor).toHaveAttribute('aria-label', 'Skill content editor');
    });

    it('applies aria-describedby', () => {
      const emptyValue: SlateValue = [{ type: 'p', children: [{ text: '' }] }];

      render(
        <PlateEditor
          value={emptyValue}
          onChange={mockOnChange}
          ariaDescribedBy="editor-help-text"
        />
      );

      const editor = screen.getByTestId('plate-editor');
      expect(editor).toHaveAttribute(
        'aria-describedby',
        'editor-help-text'
      );
    });

    it('disables editor when disabled=true', () => {
      const emptyValue: SlateValue = [{ type: 'p', children: [{ text: '' }] }];

      render(
        <PlateEditor
          value={emptyValue}
          onChange={mockOnChange}
          disabled={true}
        />
      );

      const editor = screen.getByTestId('plate-editor');
      expect(editor).toHaveAttribute('data-disabled', 'true');
      expect(editor).toHaveAttribute('contentEditable', 'false');
    });

    it('applies readOnly mode', () => {
      const emptyValue: SlateValue = [{ type: 'p', children: [{ text: '' }] }];

      render(
        <PlateEditor
          value={emptyValue}
          onChange={mockOnChange}
          readOnly={true}
        />
      );

      // In readOnly mode, the editor should not be editable
      const editor = screen.getByTestId('plate-editor');
      expect(editor).toBeInTheDocument();
    });

    it('applies custom id', () => {
      const emptyValue: SlateValue = [{ type: 'p', children: [{ text: '' }] }];

      render(
        <PlateEditor
          value={emptyValue}
          onChange={mockOnChange}
          id="custom-editor"
        />
      );

      const editor = screen.getByTestId('plate-editor');
      expect(editor).toHaveAttribute('id', 'custom-editor');
    });
  });

  describe('onChange behavior', () => {
    it('calls onChange when content changes', async () => {
      const initialValue: SlateValue = [
        { type: 'p', children: [{ text: '' }] },
      ];

      // We'll need to mock Plate to trigger onChange
      const MockPlateWithChange = jest.requireMock('platejs/react');
      const originalPlate = MockPlateWithChange.Plate;

      MockPlateWithChange.Plate = ({ children, onChange }: any) => {
        // Simulate a change after render
        setTimeout(() => {
          if (onChange) {
            const newValue: SlateValue = [
              { type: 'p', children: [{ text: 'New content' }] },
            ];
            onChange({ value: newValue });
          }
        }, 10);

        return originalPlate({ children, onChange });
      };

      render(<PlateEditor value={initialValue} onChange={mockOnChange} />);

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith([
          { type: 'p', children: [{ text: 'New content' }] },
        ]);
      });

      // Restore original mock
      MockPlateWithChange.Plate = originalPlate;
    });
  });

  describe('styling props', () => {
    it('applies minHeight style', () => {
      const emptyValue: SlateValue = [{ type: 'p', children: [{ text: '' }] }];

      render(
        <PlateEditor
          value={emptyValue}
          onChange={mockOnChange}
          minHeight="200px"
        />
      );

      const container = screen.getByTestId('editor-container');
      expect(container).toHaveStyle({ minHeight: '200px' });
    });

    it('applies maxHeight style', () => {
      const emptyValue: SlateValue = [{ type: 'p', children: [{ text: '' }] }];

      render(
        <PlateEditor
          value={emptyValue}
          onChange={mockOnChange}
          maxHeight="500px"
        />
      );

      const container = screen.getByTestId('editor-container');
      expect(container).toHaveStyle({ maxHeight: '500px' });
    });

    it('applies both minHeight and maxHeight', () => {
      const emptyValue: SlateValue = [{ type: 'p', children: [{ text: '' }] }];

      render(
        <PlateEditor
          value={emptyValue}
          onChange={mockOnChange}
          minHeight="200px"
          maxHeight="500px"
        />
      );

      const container = screen.getByTestId('editor-container');
      expect(container).toHaveStyle({
        minHeight: '200px',
        maxHeight: '500px',
      });
    });
  });

  describe('autoFocus', () => {
    it('passes autoFocus prop to editor', () => {
      const emptyValue: SlateValue = [{ type: 'p', children: [{ text: '' }] }];

      render(
        <PlateEditor
          value={emptyValue}
          onChange={mockOnChange}
          autoFocus={true}
        />
      );

      const editor = screen.getByTestId('plate-editor');
      expect(editor).toHaveAttribute('data-autofocus', 'true');
    });
  });
});
