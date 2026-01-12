import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SkillEditor } from '@/components/skills/SkillEditor';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const mockSkill = {
  id: '1',
  name: 'test-driven-development',
  description: 'Enforces TDD workflow with RED-GREEN-REFACTOR',
  content: `---
name: test-driven-development
description: Use when implementing features or bug fixes
---

# Test-Driven Development

Follow strict RED-GREEN-REFACTOR cycles.

## RED Phase
Write failing tests first.

## GREEN Phase
Write minimal code to pass.

## REFACTOR Phase
Improve code while keeping tests green.`,
  enabled: true,
  created_at: new Date(),
  updated_at: new Date(),
};

describe('SkillEditor', () => {
  beforeEach(() => {
    queryClient.clear();
  });

  describe('Rendering', () => {
    it('renders empty editor in create mode', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByLabelText(/name/i)).toHaveValue('');
      expect(screen.getByLabelText(/description/i)).toHaveValue('');
    });

    it('renders editor with skill data in edit mode', () => {
      render(<SkillEditor skill={mockSkill} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByLabelText(/name/i)).toHaveValue('test-driven-development');
      expect(screen.getByLabelText(/description/i)).toHaveValue('Enforces TDD workflow with RED-GREEN-REFACTOR');
    });

    it('shows correct title for create mode', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('heading', { name: /create skill/i })).toBeInTheDocument();
    });

    it('shows correct title for edit mode', () => {
      render(<SkillEditor skill={mockSkill} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('heading', { name: /edit skill/i })).toBeInTheDocument();
    });
  });

  describe('Form Fields', () => {
    it('has name input field', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      expect(nameInput).toBeInTheDocument();
      expect(nameInput).toHaveAttribute('type', 'text');
      expect(nameInput).toHaveAttribute('required');
    });

    it('has description textarea field', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const descInput = screen.getByLabelText(/description/i);
      expect(descInput).toBeInTheDocument();
      expect(descInput.tagName).toBe('TEXTAREA');
      expect(descInput).toHaveAttribute('required');
    });

    it('has content editor with PlateJS', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('textbox', { name: /content/i })).toBeInTheDocument();
    });

    it('has enabled toggle', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('switch', { name: /enabled/i })).toBeInTheDocument();
    });
  });

  describe('Validation', () => {
    it('shows error when name is empty on submit', async () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const submitButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      });
    });

    it('shows error when description is empty on submit', async () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      fireEvent.change(nameInput, { target: { value: 'test-skill' } });

      const submitButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/description is required/i)).toBeInTheDocument();
      });
    });

    it('validates name format (kebab-case)', async () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      fireEvent.change(nameInput, { target: { value: 'Invalid Name!' } });

      await waitFor(() => {
        expect(screen.getByText(/name must be kebab-case/i)).toBeInTheDocument();
      });
    });
  });

  describe('PlateJS Content Editor', () => {
    it('loads PlateJS editor', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('textbox', { name: /content/i })).toBeInTheDocument();
    });

    it('updates content on change', async () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const contentEditor = screen.getByRole('textbox', { name: /content/i });
      fireEvent.change(contentEditor, { target: { value: '# New Content' } });

      await waitFor(() => {
        expect(contentEditor).toHaveValue('# New Content');
      });
    });

    it('supports markdown formatting', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('button', { name: /bold/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /italic/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /heading/i })).toBeInTheDocument();
    });

    it('supports code blocks', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const codeBlockButton = screen.getByRole('button', { name: /code block/i });
      expect(codeBlockButton).toBeInTheDocument();
    });
  });

  describe('YAML Frontmatter', () => {
    it('allows toggling between visual and YAML views', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const toggleButton = screen.getByRole('tab', { name: /yaml view/i });
      fireEvent.click(toggleButton);

      const yamlEditor = screen.getByRole('textbox', { name: /yaml/i }) as HTMLTextAreaElement;
      expect(yamlEditor.value).toContain('---');
    });

    it('shows YAML frontmatter in edit mode', () => {
      render(<SkillEditor skill={mockSkill} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const toggleButton = screen.getByRole('tab', { name: /yaml view/i });
      fireEvent.click(toggleButton);

      const yamlEditor = screen.getByRole('textbox', { name: /yaml/i }) as HTMLTextAreaElement;
      expect(yamlEditor.value).toContain('name: test-driven-development');
    });

    it('validates YAML frontmatter syntax', async () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const toggleButton = screen.getByRole('tab', { name: /yaml view/i });
      fireEvent.click(toggleButton);

      const yamlEditor = screen.getByRole('textbox', { name: /yaml/i });
      fireEvent.change(yamlEditor, { target: { value: 'invalid: yaml: syntax:' } });

      await waitFor(() => {
        expect(screen.getByText(/invalid yaml/i)).toBeInTheDocument();
      });
    });

    it('syncs YAML frontmatter with form fields', async () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      fireEvent.change(nameInput, { target: { value: 'new-skill' } });

      const toggleButton = screen.getByRole('tab', { name: /yaml view/i });
      fireEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText(/name: new-skill/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Actions', () => {
    it('has save button', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
    });

    it('has cancel button', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('calls onSubmit with form data on save', async () => {
      const onSubmit = jest.fn();
      render(<SkillEditor onSubmit={onSubmit} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      const descInput = screen.getByLabelText(/description/i);
      const contentEditor = screen.getByRole('textbox', { name: /content/i });

      fireEvent.change(nameInput, { target: { value: 'new-skill' } });
      fireEvent.change(descInput, { target: { value: 'New skill description' } });
      fireEvent.change(contentEditor, { target: { value: '# New Skill Content' } });

      const submitButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
          name: 'new-skill',
          description: 'New skill description',
          content: expect.stringContaining('# New Skill Content'),
          enabled: true,
        }));
      });
    });

    it('calls onCancel when cancel button clicked', () => {
      const onCancel = jest.fn();
      render(<SkillEditor onSubmit={() => {}} onCancel={onCancel} />, { wrapper });

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(onCancel).toHaveBeenCalled();
    });
  });

  describe('Enabled Toggle', () => {
    it('defaults to enabled', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const enabledToggle = screen.getByRole('switch', { name: /enabled/i });
      expect(enabledToggle).toBeChecked();
    });

    it('reflects skill enabled state in edit mode', () => {
      const disabledSkill = { ...mockSkill, enabled: false };
      render(<SkillEditor skill={disabledSkill} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const enabledToggle = screen.getByRole('switch', { name: /enabled/i });
      expect(enabledToggle).not.toBeChecked();
    });

    it('toggles enabled state', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

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
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('tab', { name: /preview/i })).toBeInTheDocument();
    });

    it('shows rendered markdown in preview', async () => {
      render(<SkillEditor skill={mockSkill} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const previewTab = screen.getByRole('tab', { name: /preview/i });
      fireEvent.click(previewTab);

      await waitFor(() => {
        expect(screen.getByText('Test-Driven Development')).toBeInTheDocument();
        expect(screen.getByText('RED Phase')).toBeInTheDocument();
      });
    });

    it('updates preview when content changes', async () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const contentEditor = screen.getByRole('textbox', { name: /content/i });
      fireEvent.change(contentEditor, { target: { value: '# Updated Content' } });

      const previewTab = screen.getByRole('tab', { name: /preview/i });
      fireEvent.click(previewTab);

      await waitFor(() => {
        expect(screen.getByText('Updated Content')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('form', { name: /skill editor/i })).toBeInTheDocument();
    });

    it('supports keyboard navigation', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
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
      render(<SkillEditor onSubmit={onSubmit} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      const descInput = screen.getByLabelText(/description/i);

      fireEvent.change(nameInput, { target: { value: 'test' } });
      fireEvent.change(descInput, { target: { value: 'test' } });

      const submitButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(submitButton);

      expect(screen.getByText(/saving/i)).toBeInTheDocument();
    });
  });

  describe('Share Functionality', () => {
    it('has share button in edit mode', () => {
      render(<SkillEditor skill={mockSkill} onSubmit={() => {}} onCancel={() => {}} onShare={() => {}} />, { wrapper });

      expect(screen.getByRole('button', { name: /share/i })).toBeInTheDocument();
    });

    it('calls onShare when share button clicked', () => {
      const onShare = jest.fn();
      render(<SkillEditor skill={mockSkill} onSubmit={() => {}} onCancel={() => {}} onShare={onShare} />, { wrapper });

      const shareButton = screen.getByRole('button', { name: /share/i });
      fireEvent.click(shareButton);

      expect(onShare).toHaveBeenCalledWith(mockSkill);
    });

    it('does not show share button in create mode', () => {
      render(<SkillEditor onSubmit={() => {}} onCancel={() => {}} onShare={() => {}} />, { wrapper });

      expect(screen.queryByRole('button', { name: /share/i })).not.toBeInTheDocument();
    });
  });
});
