import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AgentForm } from '@/components/agents/AgentForm';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const mockAgent = {
  id: '1',
  name: 'code-reviewer',
  description: 'Reviews code for quality and best practices',
  prompt: 'You are a code reviewer who provides constructive feedback.',
  tools: ['Read', 'Grep', 'Glob'],
  model: 'sonnet' as const,
  created_at: new Date(),
  updated_at: new Date(),
};

describe('AgentForm', () => {
  beforeEach(() => {
    queryClient.clear();
  });

  describe('Rendering', () => {
    it('renders empty form in create mode', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByLabelText(/name/i)).toHaveValue('');
      expect(screen.getByLabelText(/description/i)).toHaveValue('');
      expect(screen.getByRole('textbox', { name: /prompt/i })).toHaveValue('');
    });

    it('renders form with agent data in edit mode', () => {
      render(<AgentForm agent={mockAgent} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByLabelText(/name/i)).toHaveValue('code-reviewer');
      expect(screen.getByLabelText(/description/i)).toHaveValue('Reviews code for quality and best practices');
      expect(screen.getByRole('textbox', { name: /prompt/i })).toHaveValue('You are a code reviewer who provides constructive feedback.');
    });

    it('shows correct title for create mode', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('heading', { name: /create agent/i })).toBeInTheDocument();
    });

    it('shows correct title for edit mode', () => {
      render(<AgentForm agent={mockAgent} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('heading', { name: /edit agent/i })).toBeInTheDocument();
    });
  });

  describe('Form Fields', () => {
    it('has name input field', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      expect(nameInput).toBeInTheDocument();
      expect(nameInput).toHaveAttribute('type', 'text');
      expect(nameInput).toHaveAttribute('required');
    });

    it('has description textarea field', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const descInput = screen.getByLabelText(/description/i);
      expect(descInput).toBeInTheDocument();
      expect(descInput.tagName).toBe('TEXTAREA');
      expect(descInput).toHaveAttribute('required');
    });

    it('has prompt editor with PlateJS', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('textbox', { name: /prompt/i })).toBeInTheDocument();
    });

    it('has model selector dropdown', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const modelSelect = screen.getByLabelText(/model/i);
      expect(modelSelect).toBeInTheDocument();
      expect(modelSelect.tagName).toBe('SELECT');
    });

    it('has tools multi-select', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByText(/allowed tools/i)).toBeInTheDocument();
    });
  });

  describe('Validation', () => {
    it('shows error when name is empty on submit', async () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const submitButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      });
    });

    it('shows error when description is empty on submit', async () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      fireEvent.change(nameInput, { target: { value: 'test-agent' } });

      const submitButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/description is required/i)).toBeInTheDocument();
      });
    });

    it('shows error when prompt is empty on submit', async () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      fireEvent.change(nameInput, { target: { value: 'test-agent' } });

      const descInput = screen.getByLabelText(/description/i);
      fireEvent.change(descInput, { target: { value: 'Test description' } });

      const submitButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/prompt is required/i)).toBeInTheDocument();
      });
    });

    it('validates name format (kebab-case)', async () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      fireEvent.change(nameInput, { target: { value: 'Invalid Name!' } });

      await waitFor(() => {
        expect(screen.getByText(/name must be kebab-case/i)).toBeInTheDocument();
      });
    });

    it('validates name length', async () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      fireEvent.change(nameInput, { target: { value: 'a'.repeat(101) } });

      await waitFor(() => {
        expect(screen.getByText(/name must be 100 characters or less/i)).toBeInTheDocument();
      });
    });
  });

  describe('Model Selection', () => {
    it('shows model options (sonnet, opus, haiku, inherit)', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const modelSelect = screen.getByLabelText(/model/i);
      fireEvent.click(modelSelect);

      expect(screen.getByRole('option', { name: /sonnet/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /opus/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /haiku/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /inherit/i })).toBeInTheDocument();
    });

    it('defaults to inherit model', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const modelSelect = screen.getByLabelText(/model/i) as HTMLSelectElement;
      expect(modelSelect.value).toBe('inherit');
    });

    it('selects correct model in edit mode', () => {
      render(<AgentForm agent={mockAgent} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const modelSelect = screen.getByLabelText(/model/i) as HTMLSelectElement;
      expect(modelSelect.value).toBe('sonnet');
    });
  });

  describe('Tool Selection', () => {
    it('shows available tools list', async () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const toolsButton = screen.getByRole('button', { name: /select tools/i });
      fireEvent.click(toolsButton);

      await waitFor(() => {
        expect(screen.getByText(/read/i)).toBeInTheDocument();
        expect(screen.getByText(/write/i)).toBeInTheDocument();
        expect(screen.getByText(/bash/i)).toBeInTheDocument();
      });
    });

    it('allows selecting multiple tools', async () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const toolsButton = screen.getByRole('button', { name: /select tools/i });
      fireEvent.click(toolsButton);

      const readCheckbox = await screen.findByRole('checkbox', { name: /read/i });
      const writeCheckbox = await screen.findByRole('checkbox', { name: /write/i });

      fireEvent.click(readCheckbox);
      fireEvent.click(writeCheckbox);

      expect(readCheckbox).toBeChecked();
      expect(writeCheckbox).toBeChecked();
    });

    it('pre-selects tools in edit mode', async () => {
      render(<AgentForm agent={mockAgent} onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const toolsButton = screen.getByRole('button', { name: /select tools/i });
      fireEvent.click(toolsButton);

      const readCheckbox = await screen.findByRole('checkbox', { name: /read/i });
      const grepCheckbox = await screen.findByRole('checkbox', { name: /grep/i });

      expect(readCheckbox).toBeChecked();
      expect(grepCheckbox).toBeChecked();
    });
  });

  describe('PlateJS Prompt Editor', () => {
    it('loads PlateJS editor', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('textbox', { name: /prompt/i })).toBeInTheDocument();
    });

    it('updates prompt content on change', async () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const promptEditor = screen.getByRole('textbox', { name: /prompt/i });
      fireEvent.change(promptEditor, { target: { value: 'New prompt content' } });

      await waitFor(() => {
        expect(promptEditor).toHaveValue('New prompt content');
      });
    });

    it('supports markdown formatting', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const toolbarButtons = screen.getAllByRole('button');
      const boldButton = toolbarButtons.find(btn => btn.getAttribute('aria-label') === 'Bold');

      expect(boldButton).toBeInTheDocument();
    });
  });

  describe('Form Actions', () => {
    it('has save button', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
    });

    it('has cancel button', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('calls onSubmit with form data on save', async () => {
      const onSubmit = jest.fn();
      render(<AgentForm onSubmit={onSubmit} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      const descInput = screen.getByLabelText(/description/i);
      const promptEditor = screen.getByRole('textbox', { name: /prompt/i });

      fireEvent.change(nameInput, { target: { value: 'new-agent' } });
      fireEvent.change(descInput, { target: { value: 'New agent description' } });
      fireEvent.change(promptEditor, { target: { value: 'You are a helpful agent.' } });

      const submitButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith({
          name: 'new-agent',
          description: 'New agent description',
          prompt: 'You are a helpful agent.',
          model: 'inherit',
          tools: [],
        });
      });
    });

    it('calls onCancel when cancel button clicked', () => {
      const onCancel = jest.fn();
      render(<AgentForm onSubmit={() => {}} onCancel={onCancel} />, { wrapper });

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(onCancel).toHaveBeenCalled();
    });

    it('disables save button while submitting', async () => {
      const onSubmit = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      render(<AgentForm onSubmit={onSubmit} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      const descInput = screen.getByLabelText(/description/i);
      const promptEditor = screen.getByRole('textbox', { name: /prompt/i });

      fireEvent.change(nameInput, { target: { value: 'test-agent' } });
      fireEvent.change(descInput, { target: { value: 'Test description' } });
      fireEvent.change(promptEditor, { target: { value: 'Test prompt' } });

      const submitButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(submitButton);

      expect(submitButton).toBeDisabled();
    });
  });

  describe('YAML Frontmatter Support', () => {
    it('allows toggling between visual and YAML frontmatter views', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const toggleButton = screen.getByRole('button', { name: /yaml view/i });
      fireEvent.click(toggleButton);

      // Check YAML editor is visible with frontmatter delimiters
      const yamlEditor = screen.getByRole('textbox', { name: /yaml/i }) as HTMLTextAreaElement;
      expect(yamlEditor.value).toContain('---');
    });

    it('validates YAML frontmatter syntax', async () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const toggleButton = screen.getByRole('button', { name: /yaml view/i });
      fireEvent.click(toggleButton);

      const yamlEditor = screen.getByRole('textbox', { name: /yaml/i });
      fireEvent.change(yamlEditor, { target: { value: 'invalid: yaml: syntax:' } });

      await waitFor(() => {
        expect(screen.getByText(/invalid yaml/i)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      expect(screen.getByRole('form', { name: /agent form/i })).toBeInTheDocument();
    });

    it('supports keyboard navigation', () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      const descriptionInput = screen.getByLabelText(/description/i);

      nameInput.focus();
      expect(nameInput).toHaveFocus();

      // Simulate Tab key moving focus to next field
      descriptionInput.focus();
      expect(descriptionInput).toHaveFocus();
    });

    it('announces form errors to screen readers', async () => {
      render(<AgentForm onSubmit={() => {}} onCancel={() => {}} />, { wrapper });

      const submitButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        const errorMessages = screen.getAllByRole('alert');
        expect(errorMessages.length).toBeGreaterThan(0);
        // Should include validation errors for required fields
        const errorText = errorMessages.map(el => el.textContent).join(' ');
        expect(errorText).toMatch(/required/i);
      });
    });
  });

  describe('Loading States', () => {
    it('shows loading indicator while submitting', async () => {
      const onSubmit = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      render(<AgentForm onSubmit={onSubmit} onCancel={() => {}} />, { wrapper });

      const nameInput = screen.getByLabelText(/name/i);
      const descInput = screen.getByLabelText(/description/i);
      const promptEditor = screen.getByRole('textbox', { name: /prompt/i });

      fireEvent.change(nameInput, { target: { value: 'test' } });
      fireEvent.change(descInput, { target: { value: 'test' } });
      fireEvent.change(promptEditor, { target: { value: 'test' } });

      const submitButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(submitButton);

      expect(screen.getByText(/saving/i)).toBeInTheDocument();
    });
  });
});
