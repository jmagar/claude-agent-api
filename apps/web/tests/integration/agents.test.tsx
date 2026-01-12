import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { rest } from 'msw';
import { setupServer } from 'msw/node';

// Mock components (will be implemented in GREEN phase)
const AgentManagementPage = () => <div>Agent Management Page</div>;

const server = setupServer(
  rest.get('/api/agents', (req, res, ctx) => {
    return res(
      ctx.json({
        agents: [
          {
            id: '1',
            name: 'code-reviewer',
            description: 'Reviews code for quality',
            prompt: 'You are a code reviewer...',
            tools: ['Read', 'Grep'],
            model: 'sonnet',
            created_at: '2026-01-01T00:00:00Z',
            updated_at: '2026-01-01T00:00:00Z',
          },
        ],
      })
    );
  }),

  rest.post('/api/agents', async (req, res, ctx) => {
    const body = await req.json();
    return res(
      ctx.json({
        agent: {
          id: '2',
          ...body,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      })
    );
  }),

  rest.get('/api/agents/:id', (req, res, ctx) => {
    const { id } = req.params;
    return res(
      ctx.json({
        agent: {
          id,
          name: 'code-reviewer',
          description: 'Reviews code for quality',
          prompt: 'You are a code reviewer...',
          tools: ['Read', 'Grep'],
          model: 'sonnet',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      })
    );
  }),

  rest.put('/api/agents/:id', async (req, res, ctx) => {
    const { id } = req.params;
    const body = await req.json();
    return res(
      ctx.json({
        agent: {
          id,
          ...body,
          updated_at: new Date().toISOString(),
        },
      })
    );
  }),

  rest.delete('/api/agents/:id', (req, res, ctx) => {
    return res(ctx.status(204));
  }),

  rest.post('/api/agents/:id/share', (req, res, ctx) => {
    const { id } = req.params;
    return res(
      ctx.json({
        share_url: `https://app.example.com/shared/agents/${id}`,
        share_token: 'abc123',
      })
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('Agent CRUD Integration', () => {
  beforeEach(() => {
    queryClient.clear();
  });

  describe('List Agents', () => {
    it('fetches and displays list of agents', async () => {
      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });
    });

    it('shows empty state when no agents exist', async () => {
      server.use(
        rest.get('/api/agents', (req, res, ctx) => {
          return res(ctx.json({ agents: [] }));
        })
      );

      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText(/no agents/i)).toBeInTheDocument();
      });
    });

    it('handles fetch error gracefully', async () => {
      server.use(
        rest.get('/api/agents', (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ error: 'Internal server error' }));
        })
      );

      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText(/failed to load agents/i)).toBeInTheDocument();
      });
    });

    it('includes retry button on error', async () => {
      server.use(
        rest.get('/api/agents', (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ error: 'Internal server error' }));
        })
      );

      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });
  });

  describe('Create Agent', () => {
    it('opens create form when create button clicked', async () => {
      render(<AgentManagementPage />, { wrapper });

      const createButton = await screen.findByRole('button', { name: /create agent/i });
      fireEvent.click(createButton);

      expect(screen.getByRole('heading', { name: /create agent/i })).toBeInTheDocument();
    });

    it('creates new agent with valid data', async () => {
      render(<AgentManagementPage />, { wrapper });

      const createButton = await screen.findByRole('button', { name: /create agent/i });
      fireEvent.click(createButton);

      const nameInput = screen.getByLabelText(/name/i);
      const descInput = screen.getByLabelText(/description/i);
      const promptInput = screen.getByRole('textbox', { name: /prompt/i });

      fireEvent.change(nameInput, { target: { value: 'new-agent' } });
      fireEvent.change(descInput, { target: { value: 'New agent description' } });
      fireEvent.change(promptInput, { target: { value: 'You are a helpful agent.' } });

      const saveButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText('new-agent')).toBeInTheDocument();
      });
    });

    it('shows validation errors for invalid data', async () => {
      render(<AgentManagementPage />, { wrapper });

      const createButton = await screen.findByRole('button', { name: /create agent/i });
      fireEvent.click(createButton);

      const saveButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      });
    });

    it('handles create error gracefully', async () => {
      server.use(
        rest.post('/api/agents', (req, res, ctx) => {
          return res(ctx.status(400), ctx.json({ error: 'Invalid agent data' }));
        })
      );

      render(<AgentManagementPage />, { wrapper });

      const createButton = await screen.findByRole('button', { name: /create agent/i });
      fireEvent.click(createButton);

      const nameInput = screen.getByLabelText(/name/i);
      const descInput = screen.getByLabelText(/description/i);
      const promptInput = screen.getByRole('textbox', { name: /prompt/i });

      fireEvent.change(nameInput, { target: { value: 'test' } });
      fireEvent.change(descInput, { target: { value: 'test' } });
      fireEvent.change(promptInput, { target: { value: 'test' } });

      const saveButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to create agent/i)).toBeInTheDocument();
      });
    });

    it('closes form after successful creation', async () => {
      render(<AgentManagementPage />, { wrapper });

      const createButton = await screen.findByRole('button', { name: /create agent/i });
      fireEvent.click(createButton);

      const nameInput = screen.getByLabelText(/name/i);
      const descInput = screen.getByLabelText(/description/i);
      const promptInput = screen.getByRole('textbox', { name: /prompt/i });

      fireEvent.change(nameInput, { target: { value: 'test-agent' } });
      fireEvent.change(descInput, { target: { value: 'Test description' } });
      fireEvent.change(promptInput, { target: { value: 'Test prompt' } });

      const saveButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.queryByRole('heading', { name: /create agent/i })).not.toBeInTheDocument();
      });
    });
  });

  describe('Update Agent', () => {
    it('opens edit form when edit button clicked', async () => {
      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      const editButton = screen.getByRole('button', { name: /edit/i });
      fireEvent.click(editButton);

      expect(screen.getByRole('heading', { name: /edit agent/i })).toBeInTheDocument();
    });

    it('pre-fills form with agent data', async () => {
      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      const editButton = screen.getByRole('button', { name: /edit/i });
      fireEvent.click(editButton);

      const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement;
      expect(nameInput.value).toBe('code-reviewer');
    });

    it('updates agent with modified data', async () => {
      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      const editButton = screen.getByRole('button', { name: /edit/i });
      fireEvent.click(editButton);

      const descInput = screen.getByLabelText(/description/i);
      fireEvent.change(descInput, { target: { value: 'Updated description' } });

      const saveButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText('Updated description')).toBeInTheDocument();
      });
    });

    it('handles update error gracefully', async () => {
      server.use(
        rest.put('/api/agents/:id', (req, res, ctx) => {
          return res(ctx.status(400), ctx.json({ error: 'Invalid data' }));
        })
      );

      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      const editButton = screen.getByRole('button', { name: /edit/i });
      fireEvent.click(editButton);

      const saveButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to update agent/i)).toBeInTheDocument();
      });
    });
  });

  describe('Delete Agent', () => {
    it('shows confirmation dialog when delete button clicked', async () => {
      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      fireEvent.click(deleteButton);

      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    });

    it('deletes agent when confirmed', async () => {
      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      fireEvent.click(deleteButton);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.queryByText('code-reviewer')).not.toBeInTheDocument();
      });
    });

    it('does not delete when cancelled', async () => {
      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      fireEvent.click(deleteButton);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(screen.getByText('code-reviewer')).toBeInTheDocument();
    });

    it('handles delete error gracefully', async () => {
      server.use(
        rest.delete('/api/agents/:id', (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ error: 'Failed to delete' }));
        })
      );

      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      fireEvent.click(deleteButton);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to delete agent/i)).toBeInTheDocument();
      });
    });
  });

  describe('Share Agent', () => {
    it('opens share dialog when share button clicked', async () => {
      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      const shareButton = screen.getByRole('button', { name: /share/i });
      fireEvent.click(shareButton);

      expect(screen.getByText(/share agent/i)).toBeInTheDocument();
    });

    it('generates share link', async () => {
      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      const shareButton = screen.getByRole('button', { name: /share/i });
      fireEvent.click(shareButton);

      await waitFor(() => {
        const shareLink = screen.getByRole('textbox', { name: /share link/i }) as HTMLInputElement;
        expect(shareLink.value).toContain('https://app.example.com/shared/agents/');
      });
    });

    it('copies share link to clipboard', async () => {
      const mockClipboard = {
        writeText: jest.fn(() => Promise.resolve()),
      };
      Object.assign(navigator, { clipboard: mockClipboard });

      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      const shareButton = screen.getByRole('button', { name: /share/i });
      fireEvent.click(shareButton);

      const copyButton = await screen.findByRole('button', { name: /copy/i });
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(mockClipboard.writeText).toHaveBeenCalled();
      });
    });

    it('handles share error gracefully', async () => {
      server.use(
        rest.post('/api/agents/:id/share', (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ error: 'Failed to generate share link' }));
        })
      );

      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      const shareButton = screen.getByRole('button', { name: /share/i });
      fireEvent.click(shareButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to generate share link/i)).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('shows loading skeleton while fetching agents', () => {
      render(<AgentManagementPage />, { wrapper });

      expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument();
    });

    it('shows loading indicator while creating agent', async () => {
      server.use(
        rest.post('/api/agents', (req, res, ctx) => {
          return res(ctx.delay(100), ctx.json({ agent: { id: '2' } }));
        })
      );

      render(<AgentManagementPage />, { wrapper });

      const createButton = await screen.findByRole('button', { name: /create agent/i });
      fireEvent.click(createButton);

      const nameInput = screen.getByLabelText(/name/i);
      const descInput = screen.getByLabelText(/description/i);
      const promptInput = screen.getByRole('textbox', { name: /prompt/i });

      fireEvent.change(nameInput, { target: { value: 'test' } });
      fireEvent.change(descInput, { target: { value: 'test' } });
      fireEvent.change(promptInput, { target: { value: 'test' } });

      const saveButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(saveButton);

      expect(screen.getByText(/saving/i)).toBeInTheDocument();
    });
  });

  describe('Query Invalidation', () => {
    it('refetches agents list after creating new agent', async () => {
      let requestCount = 0;
      server.use(
        rest.get('/api/agents', (req, res, ctx) => {
          requestCount++;
          return res(
            ctx.json({
              agents: requestCount === 1 ? [] : [{ id: '2', name: 'new-agent' }],
            })
          );
        })
      );

      render(<AgentManagementPage />, { wrapper });

      const createButton = await screen.findByRole('button', { name: /create agent/i });
      fireEvent.click(createButton);

      const nameInput = screen.getByLabelText(/name/i);
      const descInput = screen.getByLabelText(/description/i);
      const promptInput = screen.getByRole('textbox', { name: /prompt/i });

      fireEvent.change(nameInput, { target: { value: 'new-agent' } });
      fireEvent.change(descInput, { target: { value: 'test' } });
      fireEvent.change(promptInput, { target: { value: 'test' } });

      const saveButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText('new-agent')).toBeInTheDocument();
      });

      expect(requestCount).toBeGreaterThan(1);
    });

    it('refetches agents list after deleting agent', async () => {
      let agents = [{ id: '1', name: 'code-reviewer' }];

      server.use(
        rest.get('/api/agents', (req, res, ctx) => {
          return res(ctx.json({ agents }));
        }),
        rest.delete('/api/agents/:id', (req, res, ctx) => {
          agents = [];
          return res(ctx.status(204));
        })
      );

      render(<AgentManagementPage />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('code-reviewer')).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      fireEvent.click(deleteButton);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.queryByText('code-reviewer')).not.toBeInTheDocument();
      });
    });
  });
});
