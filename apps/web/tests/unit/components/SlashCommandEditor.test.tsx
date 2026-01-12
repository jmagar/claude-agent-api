import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SlashCommandEditor } from '@/components/commands/SlashCommandEditor';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock PlateMarkdownEditor components
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
    <textarea
      data-testid="plate-editor"
      data-placeholder={placeholder}
      aria-label={ariaLabel}
      onChange={(e) => {
        // Simulate Slate change
        onChange([{ type: 'p', children: [{ text: e.target.value }] }]);
      }}
      role="textbox"
    />
  ),
}));

jest.mock('@/components/plate/PlateMarkdownToolbar', () => ({
  PlateMarkdownToolbar: () => (
    <div data-testid="plate-toolbar">
      <button role="button" aria-label="Bold">Bold</button>
      <button role="button" aria-label="Italic">Italic</button>
      <button role="button" aria-label="Heading">Heading</button>
      <button role="button" aria-label="Code Block">Code Block</button>
    </div>
  ),
}));

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
    return nodes.map((node) => node.children[0].text).join('\n');
  },
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const mockCommand = {
  id: '1',
  name: 'plan',
  description: 'Create implementation plans',
  content: `---
name: plan
description: Create detailed implementation plans
enabled: true
---

# Plan Command

Create detailed implementation plans.

## Usage
Type /plan followed by your task description.

## Output
Generates a structured plan with tasks and steps.`,
  enabled: true,
  created_at: new Date(),
  updated_at: new Date(),
};

describe('SlashCommandEditor', () => {
  beforeEach(() => {
    queryClient.clear();
  });

  describe('Rendering', () => {
    it('renders empty editor in create mode', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByLabelText(/command name/i)).toHaveValue('');
      expect(screen.getByLabelText(/description/i)).toHaveValue('');
    });

    it('renders editor with command data in edit mode', () => {
      render(<SlashCommandEditor command={mockCommand} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByLabelText(/command name/i)).toHaveValue('plan');
      expect(screen.getByLabelText(/description/i)).toHaveValue('Create implementation plans');
    });

    it('shows correct title for create mode', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('heading', { name: /create slash command/i })).toBeInTheDocument();
    });

    it('shows correct title for edit mode', () => {
      render(<SlashCommandEditor command={mockCommand} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('heading', { name: /edit slash command/i })).toBeInTheDocument();
    });

    it('displays slash prefix in name field', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByText('/')).toBeInTheDocument();
    });
  });

  describe('Form Fields', () => {
    it('has name input field', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/command name/i);
      expect(nameInput).toBeInTheDocument();
      expect(nameInput).toHaveAttribute('type', 'text');
      expect(nameInput).toHaveAttribute('required');
      expect(nameInput).toHaveAttribute('placeholder', 'my-command');
    });

    it('has description textarea field', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const descInput = screen.getByLabelText(/description/i);
      expect(descInput).toBeInTheDocument();
      expect(descInput.tagName).toBe('TEXTAREA');
      expect(descInput).toHaveAttribute('required');
    });

    it('has content editor with PlateJS', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('textbox', { name: /content/i })).toBeInTheDocument();
    });

    it('has enabled toggle', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('switch', { name: /enabled/i })).toBeInTheDocument();
    });
  });

  describe('Validation', () => {
    it('shows error when name is empty on submit', async () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const submitButton = screen.getByRole('button', { name: /save slash command/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      });
    });

    it('shows error when description is empty on submit', async () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/command name/i);
      fireEvent.change(nameInput, { target: { value: 'test-command' } });

      const submitButton = screen.getByRole('button', { name: /save slash command/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/description is required/i)).toBeInTheDocument();
      });
    });

    it('shows error when content is empty on submit', async () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/command name/i);
      const descInput = screen.getByLabelText(/description/i);

      fireEvent.change(nameInput, { target: { value: 'test-command' } });
      fireEvent.change(descInput, { target: { value: 'Test description' } });

      const submitButton = screen.getByRole('button', { name: /save slash command/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/content is required/i)).toBeInTheDocument();
      });
    });

    it('validates name format (kebab-case)', async () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/command name/i);
      fireEvent.change(nameInput, { target: { value: 'Invalid Name!' } });

      await waitFor(() => {
        expect(screen.getByText(/name must be kebab-case/i)).toBeInTheDocument();
      });
    });

    it('validates name length (max 50 characters)', async () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/command name/i);
      fireEvent.change(nameInput, { target: { value: 'a'.repeat(51) } });

      await waitFor(() => {
        expect(screen.getByText(/name must be 50 characters or less/i)).toBeInTheDocument();
      });
    });
  });

  describe('PlateJS Content Editor', () => {
    it('loads PlateJS editor', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('textbox', { name: /content/i })).toBeInTheDocument();
    });

    it('updates content on change', async () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const contentEditor = screen.getByRole('textbox', { name: /content/i });
      fireEvent.change(contentEditor, { target: { value: '# New Content' } });

      await waitFor(() => {
        expect(contentEditor).toHaveValue('# New Content');
      });
    });

    it('supports markdown formatting', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('button', { name: /bold/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /italic/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /heading/i })).toBeInTheDocument();
    });

    it('supports code blocks', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const codeBlockButton = screen.getByRole('button', { name: /code block/i });
      expect(codeBlockButton).toBeInTheDocument();
    });
  });

  describe('YAML Frontmatter', () => {
    it('allows toggling between visual and YAML views', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const toggleButton = screen.getByRole('tab', { name: /yaml view/i });
      fireEvent.click(toggleButton);

      const yamlEditor = screen.getByRole('textbox', { name: /yaml/i }) as HTMLTextAreaElement;
      expect(yamlEditor.value).toContain('---');
    });

    it('shows YAML frontmatter in edit mode', () => {
      render(<SlashCommandEditor command={mockCommand} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const toggleButton = screen.getByRole('tab', { name: /yaml view/i });
      fireEvent.click(toggleButton);

      const yamlEditor = screen.getByRole('textbox', { name: /yaml/i }) as HTMLTextAreaElement;
      expect(yamlEditor.value).toContain('name: plan');
    });

    it('validates YAML frontmatter syntax', async () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const toggleButton = screen.getByRole('tab', { name: /yaml view/i });
      fireEvent.click(toggleButton);

      const yamlEditor = screen.getByRole('textbox', { name: /yaml/i });
      fireEvent.change(yamlEditor, { target: { value: 'invalid: yaml: syntax:' } });

      await waitFor(() => {
        expect(screen.getByText(/invalid yaml/i)).toBeInTheDocument();
      });
    });

    it('syncs YAML frontmatter with form fields', async () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/command name/i);
      fireEvent.change(nameInput, { target: { value: 'new-command' } });

      const toggleButton = screen.getByRole('tab', { name: /yaml view/i });
      fireEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText(/name: new-command/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Actions', () => {
    it('has save button', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('button', { name: /save slash command/i })).toBeInTheDocument();
    });

    it('has cancel button', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('calls onSubmit with form data on save', async () => {
      const onSubmit = jest.fn();
      render(<SlashCommandEditor onSubmit={onSubmit} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/command name/i);
      const descInput = screen.getByLabelText(/description/i);
      const contentEditor = screen.getByRole('textbox', { name: /content/i });

      fireEvent.change(nameInput, { target: { value: 'new-command' } });
      fireEvent.change(descInput, { target: { value: 'New command description' } });
      fireEvent.change(contentEditor, { target: { value: '# New Command Content' } });

      const submitButton = screen.getByRole('button', { name: /save slash command/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
          name: 'new-command',
          description: 'New command description',
          content: '# New Command Content',
          enabled: true,
        }));
      });
    });

    it('calls onCancel when cancel button clicked', () => {
      const onCancel = jest.fn();
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={onCancel} />, { wrapper });

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(onCancel).toHaveBeenCalled();
    });
  });

  describe('Enabled Toggle', () => {
    it('defaults to enabled', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const enabledToggle = screen.getByRole('switch', { name: /enabled/i });
      expect(enabledToggle).toBeChecked();
    });

    it('reflects command enabled state in edit mode', () => {
      const disabledCommand = { ...mockCommand, enabled: false };
      render(<SlashCommandEditor command={disabledCommand} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const enabledToggle = screen.getByRole('switch', { name: /enabled/i });
      expect(enabledToggle).not.toBeChecked();
    });

    it('toggles enabled state', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const enabledToggle = screen.getByRole('switch', { name: /enabled/i });
      expect(enabledToggle).toBeChecked();

      fireEvent.click(enabledToggle);
      expect(enabledToggle).not.toBeChecked();

      fireEvent.click(enabledToggle);
      expect(enabledToggle).toBeChecked();
    });
  });

  describe('Preview Mode', () => {
    it('has preview tab', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('tab', { name: /preview/i })).toBeInTheDocument();
    });

    it('shows rendered markdown in preview', async () => {
      render(<SlashCommandEditor command={mockCommand} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const previewTab = screen.getByRole('tab', { name: /preview/i });
      fireEvent.click(previewTab);

      await waitFor(() => {
        expect(screen.getByText(/Plan Command/i)).toBeInTheDocument();
        expect(screen.getByText(/Usage/i)).toBeInTheDocument();
      });
    });

    it('updates preview when content changes', async () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const contentEditor = screen.getByRole('textbox', { name: /content/i });
      fireEvent.change(contentEditor, { target: { value: '# Updated Content' } });

      const previewTab = screen.getByRole('tab', { name: /preview/i });
      fireEvent.click(previewTab);

      await waitFor(() => {
        expect(screen.getByText('Updated Content')).toBeInTheDocument();
      });
    });

    it('displays command name with slash prefix in preview', () => {
      render(<SlashCommandEditor command={mockCommand} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const previewTab = screen.getByRole('tab', { name: /preview/i });
      fireEvent.click(previewTab);

      expect(screen.getByRole('heading', { name: /plan/i })).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('form', { name: /slash command editor/i })).toBeInTheDocument();
    });

    it('supports keyboard navigation', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/command name/i);
      const descriptionInput = screen.getByLabelText(/description/i);

      nameInput.focus();
      expect(nameInput).toHaveFocus();

      // Simulate Tab key moving focus to next field
      descriptionInput.focus();
      expect(descriptionInput).toHaveFocus();
    });
  });

  describe('Loading States', () => {
    it('shows loading indicator while submitting', async () => {
      const onSubmit = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      render(<SlashCommandEditor onSubmit={onSubmit} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/command name/i);
      const descInput = screen.getByLabelText(/description/i);
      const contentEditor = screen.getByRole('textbox', { name: /content/i });

      fireEvent.change(nameInput, { target: { value: 'test' } });
      fireEvent.change(descInput, { target: { value: 'test' } });
      fireEvent.change(contentEditor, { target: { value: 'test content' } });

      const submitButton = screen.getByRole('button', { name: /save slash command/i });
      fireEvent.click(submitButton);

      expect(screen.getByText(/saving/i)).toBeInTheDocument();
    });

    it('disables buttons while submitting', async () => {
      const onSubmit = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      render(<SlashCommandEditor onSubmit={onSubmit} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/command name/i);
      const descInput = screen.getByLabelText(/description/i);
      const contentEditor = screen.getByRole('textbox', { name: /content/i });

      fireEvent.change(nameInput, { target: { value: 'test' } });
      fireEvent.change(descInput, { target: { value: 'test' } });
      fireEvent.change(contentEditor, { target: { value: 'test content' } });

      const submitButton = screen.getByRole('button', { name: /save slash command/i });
      const cancelButton = screen.getByRole('button', { name: /cancel/i });

      fireEvent.click(submitButton);

      expect(submitButton).toBeDisabled();
      expect(cancelButton).toBeDisabled();
    });
  });

  describe('Tab Navigation', () => {
    it('switches between visual, YAML, and preview tabs', () => {
      render(<SlashCommandEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      // Visual tab (default)
      const editTab = screen.getAllByRole('tab').find(tab => tab.textContent === 'Edit');
      expect(editTab).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByRole('textbox', { name: /content/i })).toBeInTheDocument();

      // Switch to YAML tab
      const yamlTab = screen.getByRole('tab', { name: /yaml view/i });
      fireEvent.click(yamlTab);
      expect(yamlTab).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByRole('textbox', { name: /yaml/i })).toBeInTheDocument();

      // Switch to Preview tab
      const previewTab = screen.getAllByRole('tab').find(tab => tab.textContent === 'Preview');
      fireEvent.click(previewTab!);
      expect(previewTab).toHaveAttribute('aria-selected', 'true');

      // Switch back to visual tab
      const editTab2 = screen.getAllByRole('tab').find(tab => tab.textContent === 'Edit');
      fireEvent.click(editTab2!);
      expect(editTab2).toHaveAttribute('aria-selected', 'true');
    });
  });
});
