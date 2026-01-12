/**
 * PlateMarkdownEditor Component Tests
 *
 * Tests the complete markdown editor with tabs (Edit/YAML/Preview).
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PlateMarkdownEditor } from '@/components/plate/PlateMarkdownEditor';

// Mock PlateEditor
jest.mock('@/components/plate/PlateEditor', () => ({
  PlateEditor: ({
    value,
    onChange,
    placeholder,
    ariaLabel,
  }: {
    value: unknown;
    onChange: (value: unknown) => void;
    placeholder?: string;
    ariaLabel?: string;
  }) => (
    <div
      data-testid="plate-editor"
      data-placeholder={placeholder}
      aria-label={ariaLabel}
      onClick={() => {
        // Simulate Slate change
        onChange([{ type: 'p', children: [{ text: 'Updated content' }] }]);
      }}
    >
      Plate Editor (mocked)
    </div>
  ),
}));

// Mock PlateMarkdownToolbar
jest.mock('@/components/plate/PlateMarkdownToolbar', () => ({
  PlateMarkdownToolbar: () => (
    <div data-testid="plate-toolbar">Toolbar (mocked)</div>
  ),
}));

// Mock ReactMarkdown
jest.mock('react-markdown', () => {
  return function ReactMarkdown({ children }: { children: string }) {
    return <div data-testid="markdown-preview">{children}</div>;
  };
});

// Mock slate-serializers
jest.mock('@/lib/slate-serializers', () => ({
  markdownToSlate: (markdown: string) => {
    if (!markdown.trim()) {
      return [{ type: 'p', children: [{ text: '' }] }];
    }
    return [{ type: 'p', children: [{ text: markdown }] }];
  },
  slateToMarkdown: (value: unknown) => {
    const nodes = value as Array<{ children: Array<{ text: string }> }>;
    if (!nodes || nodes.length === 0) return '';
    return nodes.map((node) => node.children[0].text).join('\n') + '\n';
  },
}));

describe('PlateMarkdownEditor', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('rendering', () => {
    it('renders Edit tab by default', () => {
      render(
        <PlateMarkdownEditor value="" onChange={mockOnChange} />
      );

      expect(screen.getByRole('tab', { name: 'Edit' })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'Edit' })).toHaveAttribute(
        'aria-selected',
        'true'
      );
      expect(screen.getByTestId('plate-editor')).toBeInTheDocument();
      expect(screen.getByTestId('plate-toolbar')).toBeInTheDocument();
    });

    it('renders all three tabs when enabled', () => {
      render(
        <PlateMarkdownEditor
          value=""
          onChange={mockOnChange}
          showYamlTab={true}
          showPreviewTab={true}
        />
      );

      expect(screen.getByRole('tab', { name: 'Edit' })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /YAML view/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'Preview' })).toBeInTheDocument();
    });

    it('hides YAML tab when showYamlTab=false', () => {
      render(
        <PlateMarkdownEditor
          value=""
          onChange={mockOnChange}
          showYamlTab={false}
        />
      );

      expect(screen.getByRole('tab', { name: 'Edit' })).toBeInTheDocument();
      expect(screen.queryByRole('tab', { name: /YAML view/i })).not.toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'Preview' })).toBeInTheDocument();
    });

    it('hides Preview tab when showPreviewTab=false', () => {
      render(
        <PlateMarkdownEditor
          value=""
          onChange={mockOnChange}
          showPreviewTab={false}
        />
      );

      expect(screen.getByRole('tab', { name: 'Edit' })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /YAML view/i })).toBeInTheDocument();
      expect(screen.queryByRole('tab', { name: 'Preview' })).not.toBeInTheDocument();
    });
  });

  describe('tab switching', () => {
    it('switches to YAML View tab', async () => {
      const user = userEvent.setup();

      render(
        <PlateMarkdownEditor
          value="# Hello World"
          onChange={mockOnChange}
        />
      );

      const yamlTab = screen.getByRole('tab', { name: /YAML view/i });
      await user.click(yamlTab);

      expect(yamlTab).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByLabelText('Raw markdown editor')).toBeInTheDocument();
      expect(screen.queryByTestId('plate-editor')).not.toBeInTheDocument();
    });

    it('switches to Preview tab', async () => {
      const user = userEvent.setup();

      render(
        <PlateMarkdownEditor
          value="# Hello World"
          onChange={mockOnChange}
        />
      );

      const previewTab = screen.getByRole('tab', { name: 'Preview' });
      await user.click(previewTab);

      expect(previewTab).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByTestId('markdown-preview')).toBeInTheDocument();
      expect(screen.queryByTestId('plate-editor')).not.toBeInTheDocument();
    });

    it('switches back to Edit tab', async () => {
      const user = userEvent.setup();

      render(
        <PlateMarkdownEditor value="" onChange={mockOnChange} />
      );

      // Go to YAML View
      await user.click(screen.getByRole('tab', { name: /YAML view/i }));
      expect(screen.queryByTestId('plate-editor')).not.toBeInTheDocument();

      // Go back to Edit
      await user.click(screen.getByRole('tab', { name: 'Edit' }));
      expect(screen.getByTestId('plate-editor')).toBeInTheDocument();
      expect(screen.getByTestId('plate-toolbar')).toBeInTheDocument();
    });
  });

  describe('Edit tab', () => {
    it('shows PlateEditor and toolbar', () => {
      render(
        <PlateMarkdownEditor value="" onChange={mockOnChange} />
      );

      expect(screen.getByTestId('plate-editor')).toBeInTheDocument();
      expect(screen.getByTestId('plate-toolbar')).toBeInTheDocument();
    });

    it('passes placeholder to PlateEditor', () => {
      render(
        <PlateMarkdownEditor
          value=""
          onChange={mockOnChange}
          placeholder="Custom placeholder"
        />
      );

      const editor = screen.getByTestId('plate-editor');
      expect(editor).toHaveAttribute('data-placeholder', 'Custom placeholder');
    });

    it('passes ariaLabel to PlateEditor', () => {
      render(
        <PlateMarkdownEditor
          value=""
          onChange={mockOnChange}
          ariaLabel="Skill content editor"
        />
      );

      const editor = screen.getByTestId('plate-editor');
      expect(editor).toHaveAttribute('aria-label', 'Skill content editor');
    });

    it('syncs Slate changes to markdown', async () => {
      const user = userEvent.setup();

      render(
        <PlateMarkdownEditor value="" onChange={mockOnChange} />
      );

      // Click editor to trigger onChange
      const editor = screen.getByTestId('plate-editor');
      await user.click(editor);

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith('Updated content\n');
      });
    });
  });

  describe('YAML View tab', () => {
    it('shows raw markdown textarea', async () => {
      const user = userEvent.setup();

      render(
        <PlateMarkdownEditor
          value="# Hello World"
          onChange={mockOnChange}
        />
      );

      await user.click(screen.getByRole('tab', { name: /YAML view/i }));

      const textarea = screen.getByLabelText('Raw markdown editor');
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveValue('# Hello World');
    });

    it('handles raw markdown changes', async () => {
      const user = userEvent.setup();

      render(
        <PlateMarkdownEditor value="" onChange={mockOnChange} />
      );

      await user.click(screen.getByRole('tab', { name: /YAML view/i }));

      const textarea = screen.getByLabelText('Raw markdown editor');
      await user.clear(textarea);
      await user.type(textarea, '# New content');

      expect(mockOnChange).toHaveBeenCalled();
    });
  });

  describe('Preview tab', () => {
    it('renders markdown content', async () => {
      const user = userEvent.setup();

      render(
        <PlateMarkdownEditor
          value="# Hello World\n\nThis is a test."
          onChange={mockOnChange}
        />
      );

      await user.click(screen.getByRole('tab', { name: 'Preview' }));

      const preview = screen.getByTestId('markdown-preview');
      expect(preview).toBeInTheDocument();
      expect(preview).toHaveTextContent('# Hello World');
    });

    it('shows placeholder when no content', async () => {
      const user = userEvent.setup();

      render(
        <PlateMarkdownEditor value="" onChange={mockOnChange} />
      );

      await user.click(screen.getByRole('tab', { name: 'Preview' }));

      const preview = screen.getByTestId('markdown-preview');
      expect(preview).toHaveTextContent('*No content to preview*');
    });
  });

  describe('markdown sync', () => {
    it('converts initial markdown to Slate', () => {
      render(
        <PlateMarkdownEditor
          value="# Hello World"
          onChange={mockOnChange}
        />
      );

      // Editor should be rendered (indicating conversion happened)
      expect(screen.getByTestId('plate-editor')).toBeInTheDocument();
    });

    it('preserves content when switching tabs', async () => {
      const user = userEvent.setup();

      render(
        <PlateMarkdownEditor
          value="# Original content"
          onChange={mockOnChange}
        />
      );

      // Switch to YAML View
      await user.click(screen.getByRole('tab', { name: /YAML view/i }));
      const textarea = screen.getByLabelText('Raw markdown editor');
      expect(textarea).toHaveValue('# Original content');

      // Switch to Preview
      await user.click(screen.getByRole('tab', { name: 'Preview' }));
      const preview = screen.getByTestId('markdown-preview');
      expect(preview).toHaveTextContent('# Original content');

      // Switch back to Edit
      await user.click(screen.getByRole('tab', { name: 'Edit' }));
      expect(screen.getByTestId('plate-editor')).toBeInTheDocument();
    });
  });
});
