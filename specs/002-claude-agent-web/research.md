# Research: Claude Agent Web Interface

**Feature Branch**: `002-claude-agent-web`
**Date**: 2026-01-10

## Executive Summary

This document consolidates research findings for building a Next.js 15+ web application that provides a comprehensive frontend interface for the Claude Agent API. All technical unknowns have been resolved through documentation review, library comparisons, and best practices analysis.

---

## 1. Framework Selection: Next.js 15+ with App Router

### Decision: Next.js 15+ with App Router

**Rationale**: Production-ready React framework with built-in SSR/SSG, API routes for BFF pattern, optimized bundle splitting, and excellent TypeScript support.

**Alternatives Considered**:
- **Vite + React SPA**: Faster dev server but requires separate backend for BFF, no SSR
- **Remix**: Strong SSR but smaller ecosystem, less mature tooling
- **Create React App**: Deprecated, poor performance

### Key Features Utilized

```typescript
// App Router file structure
app/
├── layout.tsx              // Root layout with providers
├── page.tsx                // Home page
├── (chat)/                 // Route group
│   ├── layout.tsx          // Chat layout with sidebar
│   ├── page.tsx            // Chat home
│   └── [sessionId]/        // Dynamic session route
│       └── page.tsx        // Session detail
├── settings/
│   └── page.tsx
└── api/                    // BFF API routes
    ├── sessions/
    │   ├── route.ts        // GET /api/sessions, POST /api/sessions
    │   └── [id]/
    │       └── route.ts    // GET /api/sessions/[id]
    └── projects/
        └── route.ts
```

### Server Components vs Client Components

```typescript
// Server Component (default in App Router)
// app/page.tsx
import { SessionList } from '@/components/SessionList';

export default async function HomePage() {
  // Can fetch data directly
  const sessions = await getSessions();
  return <SessionList sessions={sessions} />;
}

// Client Component (for interactivity)
// components/SessionList.tsx
'use client';

import { useState } from 'react';

export function SessionList({ sessions }) {
  const [filter, setFilter] = useState('');
  // Interactive UI logic
}
```

**Pattern**: Server Components for data fetching, Client Components for interactivity.

---

## 2. UI Component Library: Assistant UI

### Decision: `@assistant-ui/react` as Chat Foundation

**Rationale**: Purpose-built for AI chat interfaces, composable primitives matching shadcn/ui philosophy, streaming support, tool call handling.

**Alternatives Considered**:
- **Vercel AI SDK UI**: Good but less composable, tighter coupling to Vercel AI SDK
- **CopilotKit**: Too opinionated, requires specific backend structure
- **Custom from scratch**: Too much boilerplate, reinventing common patterns

### Core Components

```typescript
import {
  AssistantRuntimeProvider,
  Thread,
  ThreadWelcome,
  ThreadMessages,
  Composer,
  ToolCall,
} from '@assistant-ui/react';

// Basic setup
export function ChatInterface() {
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <Thread>
        <ThreadWelcome />
        <ThreadMessages />
        <Composer />
      </Thread>
    </AssistantRuntimeProvider>
  );
}
```

### Custom Runtime for Claude Agent API

```typescript
import { useAssistantRuntime } from '@assistant-ui/react';
import { EventSourceMessage, fetchEventSource } from '@microsoft/fetch-event-source';

function createClaudeAgentRuntime(apiKey: string) {
  return {
    async *streamMessages(messages) {
      const response = await fetchEventSource('/api/v1/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify({
          prompt: messages[messages.length - 1].content,
        }),
        async onmessage(event: EventSourceMessage) {
          // Parse SSE events and yield messages
          const data = JSON.parse(event.data);

          if (event.event === 'message') {
            yield {
              role: data.type,
              content: data.content,
            };
          }
        },
      });
    },
  };
}
```

---

## 3. Rich Text Editor: PlateJS

### Decision: PlateJS for Configuration & Artifacts

**Rationale**: Extensible, plugin-based editor built on Slate, excellent TypeScript support, syntax highlighting, live preview, customizable toolbars.

**Alternatives Considered**:
- **TipTap**: Good but less extensible for custom needs
- **Lexical (Meta)**: Powerful but more complex API
- **Monaco Editor**: Too heavy for markdown, code-focused

### Basic Integration

```typescript
import { Plate, PlateContent } from '@udecode/plate-common';
import { createPlugins } from '@udecode/plate-core';
import { createHeadingPlugin } from '@udecode/plate-heading';
import { createParagraphPlugin } from '@udecode/plate-paragraph';
import { createCodeBlockPlugin } from '@udecode/plate-code-block';

const plugins = createPlugins([
  createHeadingPlugin(),
  createParagraphPlugin(),
  createCodeBlockPlugin({
    options: {
      syntax: true, // Prism.js syntax highlighting
    },
  }),
]);

export function ArtifactEditor({ content, onChange }) {
  return (
    <Plate plugins={plugins} onChange={onChange} value={content}>
      <PlateContent />
    </Plate>
  );
}
```

### YAML Frontmatter + Markdown for Agents

```typescript
import yaml from 'yaml';

interface AgentContent {
  frontmatter: {
    name: string;
    description: string;
    tools?: string[];
    model?: string;
  };
  body: string;
}

function parseAgentMarkdown(content: string): AgentContent {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) throw new Error('Invalid agent format');

  return {
    frontmatter: yaml.parse(match[1]),
    body: match[2].trim(),
  };
}

function stringifyAgentMarkdown(agent: AgentContent): string {
  return `---\n${yaml.stringify(agent.frontmatter)}---\n${agent.body}`;
}
```

---

## 4. UI Primitives: shadcn/ui + Radix UI

### Decision: shadcn/ui Component Collection

**Rationale**: Copy-paste components (not npm package), full customization, built on Radix UI primitives, Tailwind styling, TypeScript support.

**Alternatives Considered**:
- **Material UI**: Too opinionated, bundle size
- **Chakra UI**: Good but less flexible styling
- **Ant Design**: Heavy, not Tailwind-based

### Installation Pattern

```bash
# Install shadcn/ui CLI
npx shadcn-ui@latest init

# Add individual components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add command
npx shadcn-ui@latest add sheet
```

### Example: Command Palette

```typescript
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';

export function CommandPalette() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen(true);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Search or run a command..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Sessions">
          {/* Session results */}
        </CommandGroup>
        <CommandGroup heading="Commands">
          {/* Command results */}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
```

---

## 5. State Management: React Query + Context

### Decision: TanStack Query (React Query) for Server State

**Rationale**: Best-in-class data fetching, caching, synchronization. Eliminates Redux boilerplate for async data.

**Alternatives Considered**:
- **Redux Toolkit + RTK Query**: More boilerplate, not async-first
- **SWR**: Good but less feature-rich than React Query
- **Zustand**: Great for client state, not ideal for server state

### Basic Setup

```typescript
// app/providers.tsx
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      cacheTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

export function Providers({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

### Example Query Hook

```typescript
import { useQuery } from '@tanstack/react-query';

export function useSessions(mode: 'brainstorm' | 'code') {
  return useQuery({
    queryKey: ['sessions', mode],
    queryFn: async () => {
      const res = await fetch(`/api/sessions?mode=${mode}`);
      if (!res.ok) throw new Error('Failed to fetch sessions');
      return res.json();
    },
  });
}

// Usage in component
function SessionSidebar() {
  const { data, isLoading, error } = useSessions('brainstorm');

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <ul>
      {data.sessions.map(session => (
        <li key={session.id}>{session.title}</li>
      ))}
    </ul>
  );
}
```

### React Context for Global UI State

```typescript
// contexts/SettingsContext.tsx
'use client';

import { createContext, useContext, useState, useEffect } from 'react';

interface SettingsContextType {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  threadingMode: 'always' | 'hover' | 'adaptive';
  setThreadingMode: (mode: 'always' | 'hover' | 'adaptive') => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [threadingMode, setThreadingMode] = useState<'always' | 'hover' | 'adaptive'>('always');

  useEffect(() => {
    // Load from localStorage
    const saved = localStorage.getItem('settings');
    if (saved) {
      const settings = JSON.parse(saved);
      setTheme(settings.theme ?? 'light');
      setThreadingMode(settings.threadingMode ?? 'always');
    }
  }, []);

  useEffect(() => {
    // Save to localStorage
    localStorage.setItem('settings', JSON.stringify({ theme, threadingMode }));
  }, [theme, threadingMode]);

  const toggleTheme = () => setTheme(prev => prev === 'light' ? 'dark' : 'light');

  return (
    <SettingsContext.Provider value={{ theme, toggleTheme, threadingMode, setThreadingMode }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (!context) throw new Error('useSettings must be used within SettingsProvider');
  return context;
}
```

---

## 6. SSE Client Implementation

### Decision: `@microsoft/fetch-event-source` for SSE

**Rationale**: Standard fetch API, better error handling than native EventSource, supports POST requests.

**Alternatives Considered**:
- **Native EventSource**: GET only, poor error handling
- **eventsource-parser**: Low-level, more manual work

### Basic Implementation

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source';

async function streamQuery(prompt: string, apiKey: string) {
  await fetchEventSource('http://localhost:54000/api/v1/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
    },
    body: JSON.stringify({ prompt }),
    async onopen(response) {
      if (response.ok) {
        return; // Connection established
      } else if (response.status >= 400 && response.status < 500 && response.status !== 429) {
        // Client error - don't retry
        throw new Error(`HTTP ${response.status}`);
      } else {
        // Server error or rate limit - retry
        throw new Error('Server error');
      }
    },
    onmessage(event) {
      const data = JSON.parse(event.data);

      switch (event.event) {
        case 'init':
          console.log('Session started:', data.session_id);
          break;
        case 'message':
          console.log('Message:', data);
          break;
        case 'result':
          console.log('Completed:', data);
          break;
        case 'error':
          console.error('Error:', data);
          break;
      }
    },
    onerror(err) {
      console.error('Stream error:', err);
      throw err; // Will trigger retry
    },
  });
}
```

### React Hook for SSE Streaming

```typescript
import { useState, useCallback } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';

export function useStreamingQuery(apiKey: string) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const sendQuery = useCallback(async (prompt: string) => {
    setIsStreaming(true);

    try {
      await fetchEventSource('/api/v1/query', {
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
        onerror(err) {
          console.error('Streaming error:', err);
          setIsStreaming(false);
        },
      });
    } finally {
      setIsStreaming(false);
    }
  }, [apiKey, sessionId]);

  return { messages, isStreaming, sendQuery, sessionId };
}
```

---

## 7. Styling: Tailwind CSS v4+

### Decision: Tailwind v4+ with Mobile-First Approach

**Rationale**: Utility-first CSS, mobile-first responsive design, purges unused styles, excellent DX with IntelliSense.

**Alternatives Considered**:
- **CSS Modules**: More boilerplate, harder to maintain consistency
- **Styled Components**: Runtime overhead, larger bundles
- **Vanilla CSS**: No design system, hard to scale

### Configuration

```javascript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        // shadcn/ui color system
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('tailwindcss-animate'),
  ],
};

export default config;
```

### Mobile-First Responsive Pattern

```tsx
<div className="
  w-full          // Mobile: full width
  p-4             // Mobile: 1rem padding
  md:w-1/2        // Tablet: half width
  md:p-6          // Tablet: 1.5rem padding
  lg:w-1/3        // Desktop: third width
  lg:p-8          // Desktop: 2rem padding
">
  Content
</div>
```

---

## 8. Performance Optimization

### Virtualization for Long Lists

**Decision**: `@tanstack/react-virtual` for session/message lists

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

export function VirtualSessionList({ sessions }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: sessions.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60, // Estimated row height
  });

  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px`, position: 'relative' }}>
        {virtualizer.getVirtualItems().map(virtualItem => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <SessionItem session={sessions[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Code Splitting

```typescript
// Lazy load heavy components
import dynamic from 'next/dynamic';

const PlateEditor = dynamic(() => import('@/components/PlateEditor'), {
  loading: () => <div>Loading editor...</div>,
  ssr: false, // Disable SSR for editor
});

const ArtifactPanel = dynamic(() => import('@/components/ArtifactPanel'), {
  loading: () => <div>Loading...</div>,
});
```

### Memoization

```typescript
import { memo, useMemo } from 'react';

export const MessageItem = memo(function MessageItem({ message }: { message: Message }) {
  const parsedContent = useMemo(() => {
    return message.content.map(block => {
      if (block.type === 'text') {
        return parseMarkdown(block.text);
      }
      return block;
    });
  }, [message.content]);

  return <div>{/* Render parsed content */}</div>;
});
```

---

## 9. Accessibility

### ARIA Annotations

```typescript
<button
  aria-label="Send message"
  aria-disabled={isStreaming}
  disabled={isStreaming}
>
  <SendIcon />
</button>

<div role="status" aria-live="polite" aria-atomic="true">
  {isStreaming && 'Claude is thinking...'}
</div>
```

### Focus Management

```typescript
import { useEffect, useRef } from 'react';
import { Dialog, DialogContent } from '@/components/ui/dialog';

export function ToolApprovalModal({ open, onClose }) {
  const approveButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) {
      // Focus approve button when modal opens
      approveButtonRef.current?.focus();
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <button ref={approveButtonRef}>Approve</button>
        <button onClick={onClose}>Deny</button>
      </DialogContent>
    </Dialog>
  );
}
```

---

## 10. Dependency Versions

Based on npm research (January 2026):

```json
{
  "dependencies": {
    "next": "^15.1.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@assistant-ui/react": "^0.5.0",
    "@udecode/plate-common": "^38.0.0",
    "@tanstack/react-query": "^5.62.0",
    "@tanstack/react-virtual": "^3.10.0",
    "@microsoft/fetch-event-source": "^2.0.1",
    "@radix-ui/react-dialog": "^1.1.0",
    "@radix-ui/react-dropdown-menu": "^2.1.0",
    "@radix-ui/react-slot": "^1.1.0",
    "tailwindcss": "^4.0.0",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.7.0",
    "cmdk": "^1.0.4",
    "zod": "^3.24.1",
    "date-fns": "^4.1.0",
    "yaml": "^2.6.1"
  },
  "devDependencies": {
    "@types/node": "^22.10.2",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "typescript": "^5.7.2",
    "eslint": "^9.17.0",
    "eslint-config-next": "^15.1.0",
    "prettier": "^3.4.2",
    "@testing-library/react": "^16.1.0",
    "@testing-library/jest-dom": "^6.6.3",
    "jest": "^29.7.0",
    "playwright": "^1.49.1",
    "@axe-core/playwright": "^4.10.0"
  }
}
```

---

## 11. Outstanding Considerations

### Handled by Implementation

1. **SSE reconnection**: Implement exponential backoff with `@microsoft/fetch-event-source` retry logic
2. **Draft message persistence**: Use localStorage with session ID as key
3. **Image upload handling**: Convert to base64 or upload to temporary storage
4. **Markdown rendering**: Use `react-markdown` with syntax highlighting via `react-syntax-highlighter`
5. **Tool approval timeout**: 5-minute timeout with auto-deny fallback

### Deferred to Operations

1. **CDN for static assets**: Configure in production deployment
2. **Error tracking**: Integrate Sentry or similar
3. **Analytics**: Integrate PostHog or similar
4. **A/B testing**: Implement feature flags

---

---

## 12. Architecture Patterns

### Hybrid Storage for Filesystem-Required Features

**Context**: Claude Agent SDK requires certain features to be filesystem-based:
- Skills must exist in `.claude/skills/` directory
- Slash commands must exist in `.claude/commands/` directory
- SDK has NO programmatic API to load these from memory

**Challenge**: Web UI users need database-backed CRUD operations for easy management, but SDK requires files.

**Solution**: Hybrid Storage Pattern

#### Implementation Strategy

1. **Database Storage**: Store skill/command content in PostgreSQL for web UI editing
2. **Session Initialization**: On session start, backend reads enabled skills/commands from database
3. **Filesystem Sync**: Backend writes files to session-scoped directories:
   - `/tmp/claude-sessions/{session_id}/.claude/skills/`
   - `/tmp/claude-sessions/{session_id}/.claude/commands/`
4. **SDK Loading**: Claude Agent SDK loads from filesystem as normal
5. **Isolation**: Each session gets its own directories for multi-tenancy
6. **Cleanup**: Directories deleted on session end

#### Benefits

- ✅ Web UI users get full CRUD experience
- ✅ Multi-tenancy supported (each user has own content)
- ✅ Backup/restore easy (content in database)
- ✅ SDK requirements satisfied (filesystem-based loading)
- ✅ Version control via database (track changes over time)

#### Backend Service Example

```typescript
// apps/api/services/skills_sync.ts
import { Path } from 'path';
import { writeFile } from 'fs/promises';

async function syncSkillsToFilesystem(sessionId: string, userId: string): Promise<Path> {
  const skillsDir = `/tmp/claude-sessions/${sessionId}/.claude/skills`;
  await mkdir(skillsDir, { recursive: true });

  const skills = await db.skills.findMany({
    where: { userId, enabled: true }
  });

  for (const skill of skills) {
    const skillFile = `${skillsDir}/${skill.name}.md`;
    await writeFile(skillFile, skill.content, 'utf-8');
  }

  return skillsDir;
}
```

### Permission Modes

**Official SDK Supported Modes:**
- `default` - Request approval via callback for each tool use
- `acceptEdits` - Auto-approve file edits (Read/Write/Edit tools)
- `dontAsk` - Non-interactive mode, auto-approve all tools without prompts
- `bypassPermissions` - Skip all permission checks entirely

**NOT Supported:**
- ~~`plan`~~ - This mode does NOT exist in the SDK (common misconception)

**UI Implementation:**
```typescript
type PermissionMode = 'default' | 'acceptEdits' | 'dontAsk' | 'bypassPermissions';

const permissionModeLabels = {
  default: 'Default (Ask for each tool)',
  acceptEdits: 'Accept Edits (Auto-approve file edits)',
  dontAsk: "Don't Ask (Non-interactive, auto-approve all)",
  bypassPermissions: 'Bypass Permissions (Skip all checks)',
};
```

**Security Considerations:**
- Default mode is safest for untrusted prompts
- Accept Edits balances usability and safety for file operations
- Don't Ask mode useful for automated workflows where user interaction is impossible
- Bypass Permissions should only be used in sandboxed environments

---

## Sources

- [Next.js 15 Documentation](https://nextjs.org/docs)
- [Assistant UI GitHub](https://github.com/assistant-ui/assistant-ui)
- [PlateJS Documentation](https://platejs.org/)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [Tailwind CSS v4](https://tailwindcss.com/)
- [Radix UI Primitives](https://www.radix-ui.com/)
- [@microsoft/fetch-event-source](https://github.com/Azure/fetch-event-source)
- [TanStack Virtual](https://tanstack.com/virtual/latest)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Claude Agent SDK Documentation](https://docs.claudecode.com/) - Official reference for permissions, skills, commands
