# Quickstart: Claude Agent Web Interface

**Feature Branch**: `002-claude-agent-web`
**Date**: 2026-01-10

## Prerequisites

- **Node.js 20+** and **pnpm 9+**
- **Claude Agent API** running on port 54000
- **PostgreSQL** database (shared with API backend, port 53432)
- **Redis** cache (shared with API backend, port 53380)
- **API key** for Claude Agent API
- Modern browser with ES6+ support

## Quick Setup

### 1. Install Dependencies

```bash
# Navigate to web app directory
cd apps/web

# Install dependencies with pnpm
pnpm install
```

### 2. Configure Environment

Create `.env.local` in `apps/web/`:

```bash
# Claude Agent API
NEXT_PUBLIC_API_URL=http://localhost:54000/api/v1
NEXT_PUBLIC_API_KEY=your-api-key-here

# Database (shared with backend)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@100.120.242.29:53432/claude_agent

# Redis (shared with backend)
REDIS_URL=redis://100.120.242.29:53380/0

# Next.js
NEXT_PUBLIC_APP_URL=http://localhost:53002

# Optional
NODE_ENV=development
```

**Port Assignment**: Web app runs on port **53002** (following high port convention).

### 3. Run Database Migrations

```bash
# Run migrations (if not already done by backend API)
pnpm db:migrate
```

### 4. Start Development Server

```bash
# Start Next.js dev server with hot reload
pnpm dev

# Or with custom port
pnpm dev --port 53002
```

### 5. Verify Installation

Open browser to: http://localhost:53002

**Expected:**
- Login page with API key input field
- After entering API key, redirect to chat interface
- Empty sidebar (no sessions yet)
- Chat input ready to accept messages

---

## Basic Usage

### Send Your First Message

1. **Enter API key** when prompted (stored in localStorage)
2. **Type a message** in the chat input
3. **Press Enter** to send
4. **Watch streaming response** appear token-by-token

### Create a Brainstorm Session

```
Default mode is Brainstorm. Simply start chatting:

User: "What are the best practices for API design?"

Claude will respond with streaming text, and the session
will automatically appear in the sidebar under "Today".
```

### Promote to Code Mode

1. **Click mode toggle** in sidebar
2. **Select "Code Mode"**
3. **Choose or create project** from picker
4. **Continue chatting** with filesystem access enabled

### Use Autocomplete

```
Type @ in chat input:

@code-reviewer    → Invoke code-reviewer agent
@mcp-postgres     → Connect to MCP server
@readme.md        → Reference file

Type / in chat input:

/compact          → Run compact command
/clear            → Clear conversation
```

### Configure Tools

1. **Click tool badge** (shows active count, e.g., "12")
2. **Tool management modal** opens
3. **Toggle tools** on/off by MCP server group
4. **Save as preset** for reuse

### Adjust Permissions

Click **permissions chip** to cycle through modes:
- **Plan Mode**: Show plan for approval before execution
- **Edit Automatically**: Auto-approve all tools including file edits
- **Ask before Edits**: Auto-approve reads, require approval for writes
- **YOLO**: Auto-approve everything, no confirmations

---

## Development Commands

### Core Commands

```bash
# Development
pnpm dev            # Start dev server with hot reload
pnpm build          # Production build
pnpm start          # Start production server
pnpm lint           # Run ESLint
pnpm format         # Run Prettier

# Database
pnpm db:migrate     # Run migrations
pnpm db:seed        # Seed database with sample data
pnpm db:reset       # Reset database (dev only)

# Testing
pnpm test           # Run Jest unit tests
pnpm test:watch     # Run tests in watch mode
pnpm test:e2e       # Run Playwright E2E tests
pnpm test:a11y      # Run accessibility tests

# Type Checking
pnpm typecheck      # Run TypeScript compiler check

# Component Library
pnpm ui:add button  # Add shadcn/ui component
```

### Adding shadcn/ui Components

```bash
# Initialize shadcn/ui (first time only)
npx shadcn-ui@latest init

# Add components as needed
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add command
npx shadcn-ui@latest add sheet
```

---

## Project Structure

```
apps/web/
├── app/
│   ├── layout.tsx              # Root layout with providers
│   ├── page.tsx                # Home page
│   ├── (auth)/
│   │   └── login/
│   │       └── page.tsx        # Login page
│   ├── (chat)/
│   │   ├── layout.tsx          # Chat layout with sidebar
│   │   ├── page.tsx            # Chat home (new session)
│   │   └── [sessionId]/
│   │       └── page.tsx        # Existing session
│   ├── settings/
│   │   └── page.tsx            # Settings page
│   └── api/                    # BFF API routes
│       ├── streaming/
│       │   └── route.ts
│       ├── sessions/
│       │   ├── route.ts
│       │   └── [id]/
│       │       └── route.ts
│       └── ...
├── components/
│   ├── ui/                     # shadcn/ui components
│   ├── chat/
│   │   ├── ChatInterface.tsx
│   │   ├── MessageList.tsx
│   │   ├── MessageItem.tsx
│   │   ├── ToolCallCard.tsx
│   │   └── Composer.tsx
│   ├── sidebar/
│   │   ├── SessionSidebar.tsx
│   │   └── SessionList.tsx
│   └── modals/
│       ├── ToolManagementModal.tsx
│       └── CommandPalette.tsx
├── lib/
│   ├── api.ts                  # API client functions
│   ├── streaming.ts            # SSE streaming utilities
│   └── utils.ts                # Utility functions
├── hooks/
│   ├── useStreamingQuery.ts
│   ├── useSessions.ts
│   └── useSettings.ts
├── contexts/
│   ├── AuthContext.tsx
│   ├── SettingsContext.tsx
│   └── ActiveSessionContext.tsx
├── types/
│   └── index.ts                # Type definitions
└── public/
    └── images/
```

---

## Configuration

### API Key Storage

By default, API key is stored in `localStorage`:

```typescript
// Stored as
localStorage.setItem('auth.apiKey', 'your-api-key');

// Retrieved in API calls
const apiKey = localStorage.getItem('auth.apiKey');
```

**For production**, consider using HTTP-only cookies for enhanced security.

### Theme Configuration

Theme is managed via `SettingsContext`:

```typescript
import { useSettings } from '@/contexts/SettingsContext';

function MyComponent() {
  const { theme, toggleTheme } = useSettings();
  // theme: 'light' | 'dark'
}
```

### Workspace Base Directory

Configure workspace base directory for Code mode:

```typescript
// In settings page or .env.local
NEXT_PUBLIC_WORKSPACE_BASE_DIR=/workspaces
```

All Code mode projects are sandboxed to subdirectories of this base path.

---

## Browser Client Examples

### TypeScript/React: Send Message with Streaming

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source';

async function streamQuery(prompt: string, apiKey: string) {
  const messages: Message[] = [];

  await fetchEventSource('http://localhost:53002/api/streaming', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
    },
    body: JSON.stringify({ prompt }),
    onmessage(event) {
      const data = JSON.parse(event.data);

      if (event.event === 'init') {
        console.log('Session started:', data.session_id);
      } else if (event.event === 'message') {
        messages.push({
          id: crypto.randomUUID(),
          role: data.type,
          content: data.content,
          created_at: new Date(),
        });
        console.log('New message:', data);
      } else if (event.event === 'result') {
        console.log('Completed:', data);
      }
    },
  });

  return messages;
}

// Usage
streamQuery('List the files in the current directory', 'your-api-key');
```

### React Hook: useStreamingQuery

```typescript
import { useState, useCallback } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';

export function useStreamingQuery(apiKey: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const sendQuery = useCallback(async (prompt: string) => {
    setIsStreaming(true);

    try {
      await fetchEventSource('/api/streaming', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify({ prompt, session_id: sessionId }),
        onmessage(event) {
          const data = JSON.parse(event.data);

          if (event.event === 'init') {
            setSessionId(data.session_id);
          } else if (event.event === 'message') {
            setMessages(prev => [...prev, {
              id: crypto.randomUUID(),
              role: data.type,
              content: data.content,
              created_at: new Date(),
            }]);
          }
        },
      });
    } finally {
      setIsStreaming(false);
    }
  }, [apiKey, sessionId]);

  return { messages, isStreaming, sendQuery, sessionId };
}

// Usage in component
function ChatInterface() {
  const apiKey = localStorage.getItem('auth.apiKey')!;
  const { messages, isStreaming, sendQuery } = useStreamingQuery(apiKey);

  return (
    <div>
      {messages.map(msg => <MessageItem key={msg.id} message={msg} />)}
      <Composer onSend={sendQuery} disabled={isStreaming} />
    </div>
  );
}
```

---

## Testing

### Unit Tests

```bash
# Run Jest tests
pnpm test

# Run with coverage
pnpm test --coverage

# Run specific test file
pnpm test MessageItem.test.tsx
```

**Example Test:**

```typescript
import { render, screen } from '@testing-library/react';
import { MessageItem } from '@/components/chat/MessageItem';

describe('MessageItem', () => {
  it('renders text message', () => {
    const message = {
      id: '1',
      role: 'assistant',
      content: [{ type: 'text', text: 'Hello!' }],
      created_at: new Date(),
    };

    render(<MessageItem message={message} />);

    expect(screen.getByText('Hello!')).toBeInTheDocument();
  });
});
```

### E2E Tests

```bash
# Run Playwright tests
pnpm test:e2e

# Run in headed mode (see browser)
pnpm test:e2e --headed

# Run specific test
pnpm test:e2e tests/chat.spec.ts
```

**Example E2E Test:**

```typescript
import { test, expect } from '@playwright/test';

test('send message and receive response', async ({ page }) => {
  await page.goto('http://localhost:53002');

  // Enter API key
  await page.fill('input[name="apiKey"]', 'test-api-key');
  await page.click('button:has-text("Continue")');

  // Send message
  await page.fill('textarea[placeholder*="message"]', 'Hello');
  await page.press('textarea', 'Enter');

  // Wait for response
  await expect(page.locator('text=assistant')).toBeVisible({ timeout: 10000 });
});
```

---

## Troubleshooting

### SSE Connection Drops

**Symptom:** Stream disconnects mid-response

**Solution:**
```typescript
// Enable retry in fetchEventSource
await fetchEventSource('/api/streaming', {
  // ... other options
  openWhenHidden: true,
  async onopen(response) {
    if (!response.ok) throw new Error('Connection failed');
  },
  onerror(err) {
    console.error('Stream error:', err);
    // Retry automatically
    return 1000; // Retry after 1 second
  },
});
```

### API Key Not Persisting

**Symptom:** API key lost on page refresh

**Solution:**
Check localStorage is enabled in browser:

```typescript
// Test localStorage
try {
  localStorage.setItem('test', 'test');
  localStorage.removeItem('test');
} catch (e) {
  console.error('localStorage not available');
}
```

### Slow Autocomplete

**Symptom:** Autocomplete dropdown takes >500ms to appear

**Solution:**
- Ensure Redis cache is running
- Check network latency to backend API
- Implement debouncing (already done, check 300ms delay)

### PlateJS Editor Not Loading

**Symptom:** Editor shows loading spinner indefinitely

**Solution:**
```typescript
// Check dynamic import
const PlateEditor = dynamic(() => import('@/components/PlateEditor'), {
  ssr: false, // Disable SSR
  loading: () => <div>Loading editor...</div>,
});
```

### Port Already in Use

**Symptom:** Error: `EADDRINUSE: address already in use`

**Solution:**
```bash
# Check what's using port 53002
ss -tuln | grep 53002

# Kill the process
kill -9 <PID>

# Or use different port
pnpm dev --port 53003
```

### Threading Visualization Not Showing

**Symptom:** No connection lines between messages

**Solution:**
- Check threading mode in settings (should be "always" for testing)
- Ensure CSS is loaded properly
- Check browser console for errors

---

## Deployment

### Production Build

```bash
# Build for production
pnpm build

# Start production server
pnpm start
```

### Environment Variables for Production

```bash
# .env.production
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
NEXT_PUBLIC_APP_URL=https://yourdomain.com
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# Never commit real API keys to version control!
```

### Docker Deployment

```bash
# Build Docker image
docker build -t claude-agent-web:latest .

# Run container
docker run -p 53002:53002 \
  -e NEXT_PUBLIC_API_URL=http://api:54000/api/v1 \
  -e DATABASE_URL=postgresql://... \
  claude-agent-web:latest
```

---

## Next Steps

1. **Explore the UI**: Try different modes, autocomplete, tool management
2. **Create an Agent**: Go to Settings → Agents → Create New
3. **Configure MCP Server**: Settings → MCP Servers → Add Server
4. **Test Code Mode**: Toggle to Code mode, create a project, and run filesystem operations
5. **Customize Theme**: Switch between light/dark mode in settings
6. **Review Wireframes**: Check `docs/wireframes/index.html` for UI reference
7. **Read Design Document**: `docs/plans/2026-01-10-frontend-ai-chat-interface-design.md`

---

## Resources

- **Design Document**: [docs/plans/2026-01-10-frontend-ai-chat-interface-design.md](../../docs/plans/2026-01-10-frontend-ai-chat-interface-design.md)
- **Wireframes**: [docs/wireframes/index.html](../../docs/wireframes/index.html)
- **BFF API Routes**: [contracts/bff-routes.md](contracts/bff-routes.md)
- **Backend API Documentation**: [../001-claude-agent-api/contracts/openapi.yaml](../001-claude-agent-api/contracts/openapi.yaml)
- **Next.js Documentation**: https://nextjs.org/docs
- **Assistant UI**: https://github.com/assistant-ui/assistant-ui
- **shadcn/ui**: https://ui.shadcn.com/
