# Implementation Plan: Claude Agent Web Interface

**Branch**: `002-claude-agent-web` | **Date**: 2026-01-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-claude-agent-web/spec.md`

## Summary

Build a Next.js 15+ web application providing a comprehensive frontend interface for the Claude Agent API. The application delivers a beautiful, modern chat experience with full feature parity including agents, skills, MCP servers, tool visualization, and mobile-first responsive design.

## Technical Context

**Language/Version**: TypeScript 5.7+, Node.js 20+
**Primary Framework**: Next.js 15+ with App Router
**Primary Dependencies**: @assistant-ui/react, @udecode/plate, @tanstack/react-query, shadcn/ui, @radix-ui/*, @microsoft/fetch-event-source, tailwindcss v4+
**Storage**: PostgreSQL (sessions, configs) + Redis (caching, real-time)
**Testing**: Jest, React Testing Library, Playwright, @axe-core/playwright
**Target Platform**: Modern browsers (Chrome 120+, Firefox 120+, Safari 17+, Edge 120+)
**Project Type**: Next.js 15 App Router application (React 19)
**Performance Goals**: Time-to-first-token <500ms, First Contentful Paint <1s, Autocomplete latency <50ms
**Constraints**: Mobile-first responsive (320px+ viewports), WCAG AA compliance
**Scale/Scope**: Single-page application, 1000+ sessions/user, real-time streaming

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Research-Driven Development** | PASS | Next.js, Assistant UI, PlateJS researched, SSE patterns documented |
| **II. Verification-First** | PASS | TDD methodology enforced, test requirements in spec |
| **III. Security by Default** | PASS | API keys in localStorage (planned: HTTP-only cookies), credential sanitization |
| **IV. Modularity and Simplicity** | PASS | Component-based architecture, hooks for logic, <50 line functions |
| **V. Test-Driven Development** | PASS | RED-GREEN-REFACTOR enforced per spec guidelines |
| **VI. Self-Hosted Infrastructure** | PASS | PostgreSQL + Redis via Docker Compose, no cloud services |
| **VII. Permission-Based Operations** | PASS | Four permission modes, inline approvals, tool management |
| **VIII. Tactical Revisions** | PASS | Minimal scope, feature parity with API, no feature creep |

**Gate Status**: PASS - All constitution principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/002-claude-agent-web/
├── plan.md                           # This file
├── spec.md                           # Feature specification
├── research.md                       # Phase 0 research output
├── data-model.md                     # TypeScript types, Zod schemas
├── quickstart.md                     # Setup and usage guide
└── contracts/
    ├── openapi-extensions.yaml       # API extensions for frontend
    └── bff-routes.md                 # Next.js BFF API routes
```

### Source Code (repository root)

```text
apps/web/
├── app/
│   ├── layout.tsx                    # Root layout with providers
│   ├── page.tsx                      # Home/landing page
│   ├── globals.css                   # Global styles, Tailwind directives
│   ├── (auth)/
│   │   └── login/
│   │       └── page.tsx              # Login page (API key entry)
│   ├── (chat)/
│   │   ├── layout.tsx                # Chat layout with sidebar
│   │   ├── page.tsx                  # New chat session
│   │   └── [sessionId]/
│   │       └── page.tsx              # Existing session
│   ├── settings/
│   │   ├── page.tsx                  # Settings home
│   │   └── [...path]/
│   │       └── page.tsx              # Settings sections (dynamic routes)
│   └── api/                          # BFF API routes
│       ├── streaming/
│       │   └── route.ts              # SSE proxy to backend
│       ├── sessions/
│       │   ├── route.ts              # List/create sessions
│       │   └── [id]/
│       │       ├── route.ts          # Session CRUD
│       │       ├── resume/
│       │       │   └── route.ts      # Resume session
│       │       ├── fork/
│       │       │   └── route.ts      # Fork session
│       │       └── tags/
│       │           └── route.ts      # Update tags
│       ├── projects/
│       │   ├── route.ts              # List/create projects
│       │   └── [id]/
│       │       └── route.ts          # Project CRUD
│       ├── agents/
│       │   ├── route.ts              # List/create agents
│       │   └── [id]/
│       │       ├── route.ts          # Agent CRUD
│       │       └── share/
│       │           └── route.ts      # Generate share link
│       ├── skills/
│       ├── tool-presets/
│       ├── mcp-servers/
│       ├── autocomplete/
│       │   └── route.ts              # Autocomplete suggestions
│       ├── search/
│       │   └── route.ts              # Global search
│       └── health/
│           └── route.ts              # Health check
├── components/
│   ├── ui/                           # shadcn/ui components (copied)
│   │   ├── button.tsx
│   │   ├── dialog.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── command.tsx
│   │   ├── sheet.tsx
│   │   └── ...
│   ├── chat/
│   │   ├── ChatInterface.tsx         # Main chat container
│   │   ├── MessageList.tsx           # Virtualized message list
│   │   ├── MessageItem.tsx           # Single message component
│   │   ├── ToolCallCard.tsx          # Collapsible tool call
│   │   ├── ThinkingBlock.tsx         # Collapsible thinking
│   │   ├── Composer.tsx              # Chat input with autocomplete
│   │   └── ThreadingVisualization.tsx # Connection lines
│   ├── sidebar/
│   │   ├── SessionSidebar.tsx        # Collapsible sidebar
│   │   ├── SessionList.tsx           # Grouped session list
│   │   ├── SessionItem.tsx           # Single session item
│   │   └── ModeToggle.tsx            # Brainstorm/Code toggle
│   ├── modals/
│   │   ├── ToolManagementModal.tsx   # Tool configuration
│   │   ├── CommandPalette.tsx        # Cmd+K interface
│   │   └── ProjectPickerModal.tsx    # Project selection
│   ├── editor/
│   │   ├── PlateEditor.tsx           # PlateJS wrapper
│   │   └── ArtifactPanel.tsx         # Slide-in artifact editor
│   ├── autocomplete/
│   │   ├── AutocompleteMenu.tsx      # Dropdown menu
│   │   └── AutocompleteItem.tsx      # Single suggestion item
│   └── shared/
│       ├── ToolBadge.tsx             # Active tool count badge
│       ├── PermissionsChip.tsx       # Permission mode toggle
│       ├── CheckpointMarker.tsx      # Inline checkpoint
│       └── ErrorCard.tsx             # Error display
├── lib/
│   ├── api.ts                        # API client utilities
│   ├── streaming.ts                  # SSE streaming helpers
│   ├── utils.ts                      # Utility functions (cn, etc.)
│   ├── validation.ts                 # Zod schemas
│   └── constants.ts                  # App constants
├── hooks/
│   ├── useStreamingQuery.ts          # SSE streaming hook
│   ├── useSessions.ts                # Sessions query hooks
│   ├── useProjects.ts                # Projects query hooks
│   ├── useAgents.ts                  # Agents query hooks
│   ├── useSettings.ts                # Settings context hook
│   └── useAutocomplete.ts            # Autocomplete hook
├── contexts/
│   ├── AuthContext.tsx               # API key auth
│   ├── SettingsContext.tsx           # App settings
│   └── ActiveSessionContext.tsx      # Current session state
├── types/
│   └── index.ts                      # TypeScript definitions
└── public/
    ├── images/
    └── fonts/

tests/
├── unit/
│   ├── components/
│   │   ├── MessageItem.test.tsx
│   │   ├── ToolCallCard.test.tsx
│   │   └── Composer.test.tsx
│   └── hooks/
│       └── useStreamingQuery.test.ts
├── integration/
│   ├── chat-flow.test.tsx            # Full chat flow
│   └── tool-approval.test.tsx        # Tool approval flow
└── e2e/
    ├── chat.spec.ts                  # E2E chat scenarios
    ├── mode-toggle.spec.ts           # Brainstorm/Code toggle
    └── accessibility.spec.ts         # A11y tests
```

**Structure Decision**: Next.js 15 App Router with React Server Components for data fetching, Client Components for interactivity. BFF pattern via Next.js API routes proxying to Claude Agent API.

## Complexity Tracking

No constitution violations requiring justification. Design follows established patterns:
- Next.js 15 App Router (standard for new React apps)
- BFF pattern via API routes (standard Next.js pattern)
- shadcn/ui + Radix UI (copy-paste components, not package dependency)
- TanStack Query for server state (industry standard)

## Key Design Decisions

### 1. Framework Choice: Next.js 15 with App Router

- **Rationale**: Built-in SSR/SSG, API routes for BFF, excellent TypeScript support, automatic code splitting
- **Trade-offs**: Larger framework vs SPA, but benefits outweigh complexity
- **Pattern**: Server Components for data fetching, Client Components for UI interactivity

### 2. Chat Component Foundation: Assistant UI

- **Rationale**: Purpose-built for AI chat, composable primitives, streaming support
- **Trade-offs**: Newer library vs established options, but best fit for requirements
- **Pattern**: Extend primitives with custom components for threading, subagents, checkpoints

### 3. Rich Text Editor: PlateJS

- **Rationale**: Extensible plugin architecture, syntax highlighting, TypeScript-first
- **Trade-offs**: Heavier bundle vs simpler editors, but needed for YAML + markdown editing
- **Pattern**: Lazy load with Next.js dynamic imports, disable SSR

### 4. State Management: React Query + Context

- **Rationale**: React Query for server state, Context for UI state (theme, settings)
- **Trade-offs**: No Redux/Zustand needed, simpler architecture
- **Pattern**: Query hooks for data fetching, Context for global UI state

### 5. SSE Streaming: @microsoft/fetch-event-source

- **Rationale**: Better error handling than native EventSource, supports POST
- **Trade-offs**: Extra dependency, but native EventSource insufficient
- **Pattern**: Custom hook wrapping fetchEventSource with retry logic

### 6. Styling: Tailwind v4 + shadcn/ui

- **Rationale**: Utility-first CSS, mobile-first responsive, copy-paste components
- **Trade-offs**: Larger HTML but smaller CSS, excellent DX
- **Pattern**: Mobile-first breakpoints (sm, md, lg, xl)

---

## Post-Design Constitution Check

*Re-evaluated after Phase 1 design completion.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Research-Driven** | PASS | research.md complete with Next.js patterns, Assistant UI integration, SSE streaming |
| **II. Verification-First** | PASS | Test structure defined, Jest + Playwright + axe-core planned |
| **III. Security by Default** | PASS | API key in localStorage (upgrade to HTTP-only cookies), credential sanitization for shares |
| **IV. Modularity** | PASS | Component-based architecture, hooks for logic reuse, <50 line components |
| **V. TDD** | PASS | Test directories planned, RED-GREEN-REFACTOR methodology |
| **VI. Self-Hosted** | PASS | PostgreSQL + Redis via Docker Compose, no cloud services |
| **VII. Permission-Based** | PASS | Four permission modes with inline approvals |
| **VIII. Tactical** | PASS | Scope matches spec requirements, no feature creep |

**Post-Design Gate Status**: PASS - Design adheres to all constitution principles.

---

## Implementation Phases

### Phase 1: Core Infrastructure & Authentication
**Goal**: Set up Next.js app with basic routing and API key authentication

**Tasks**:
1. Initialize Next.js 15 app with TypeScript
2. Configure Tailwind v4, ESLint, Prettier
3. Set up authentication flow (API key entry, localStorage)
4. Create AuthContext and protected routes
5. Implement BFF health check endpoint
6. Connect to PostgreSQL and Redis
7. Write unit tests for auth flow

**Deliverable**: User can enter API key and access protected routes

---

### Phase 2: Basic Chat Interface
**Goal**: Implement core chat functionality with streaming

**Tasks**:
1. Install and configure Assistant UI
2. Create ChatInterface component
3. Implement SSE streaming hook (useStreamingQuery)
4. Create MessageList with basic message rendering
5. Build Composer component (input field + send button)
6. Implement `/api/streaming` BFF route (proxy to backend)
7. Add basic error handling
8. Write tests for chat flow

**Deliverable**: User can send messages and receive streaming responses

---

### Phase 3: Session Management
**Goal**: Implement session persistence and sidebar

**Tasks**:
1. Create SessionSidebar component
2. Implement session list with date grouping (Brainstorm mode)
3. Create `/api/sessions` BFF routes (list, create, get)
4. Build SessionList component with virtualization
5. Add session navigation (click to load)
6. Implement session search/filter
7. Write tests for session management

**Deliverable**: Sessions persist and appear in sidebar grouped by date

---

### Phase 4: Tool Visualization
**Goal**: Display tool calls, thinking blocks, and errors as cards

**Tasks**:
1. Create ToolCallCard component (collapsible)
2. Implement ThinkingBlock component (collapsible)
3. Build ErrorCard component with retry button
4. Add threading visualization (connection lines)
5. Create subagent activity cards (collapsed by default)
6. Implement status badges (running, success, error)
7. Write tests for tool visualization

**Deliverable**: Tool calls and thinking display as collapsible cards with visual flow

---

### Phase 5: Tool Management & Permissions
**Goal**: Granular tool control and permission modes

**Tasks**:
1. Create ToolManagementModal component
2. Implement tool list grouped by MCP server
3. Build ToolBadge component (active tool count)
4. Create PermissionsChip component (mode toggle)
5. Implement tool preset save/load functionality
6. Add inline approval cards for tool use
7. Create `/api/tool-presets` BFF routes
8. Write tests for tool management

**Deliverable**: Users can configure tools and set permission modes

---

### Phase 6: Autocomplete System
**Goal**: Universal @ and / autocomplete for all entities

**Tasks**:
1. Create AutocompleteMenu component
2. Implement autocomplete triggers (@ and /)
3. Build `/api/autocomplete` BFF route
4. Add keyboard navigation (arrow keys, Enter, Esc)
5. Implement recently used items tracking
6. Create AutocompleteItem component with icons/descriptions
7. Write tests for autocomplete

**Deliverable**: Typing @ or / shows autocomplete dropdown with all entities

---

### Phase 7: Mode System (Brainstorm vs Code)
**Goal**: Implement two-mode system with project management

**Tasks**:
1. Create ModeToggle component
2. Implement project picker modal
3. Build `/api/projects` BFF routes (list, create)
4. Add project-grouped sidebar for Code mode
5. Implement mode promotion flow (Brainstorm → Code)
6. Create Project management UI
7. Write tests for mode system

**Deliverable**: Users can toggle modes and select/create projects

---

### Phase 8: Configuration Management (Agents, Skills, MCP)
**Goal**: CRUD operations for agents, skills, slash commands, MCP servers

**Tasks**:
1. Install and configure PlateJS
2. Create PlateEditor component wrapper
3. Build agent/skill/command management UI (settings pages)
4. Implement `/api/agents`, `/api/skills` BFF routes
5. Add YAML frontmatter parsing for agents
6. Create MCP server configuration UI
7. Implement credential sanitization for sharing
8. Add share link generation
9. Write tests for configuration management

**Deliverable**: Users can create/edit/share agents, skills, and MCP servers via PlateJS

---

### Phase 9: Command Palette & Global Search
**Goal**: Cmd+K interface for commands and search

**Tasks**:
1. Install cmdk library (shadcn/ui Command)
2. Create CommandPalette component
3. Implement `/api/search` BFF route
4. Add keyboard shortcut detection (Cmd+K)
5. Build categorized search results
6. Implement command execution
7. Write tests for command palette

**Deliverable**: Cmd+K opens command palette with search across all entities

---

### Phase 10: Artifacts & PlateJS Editor
**Goal**: Slide-in editor for generated artifacts

**Tasks**:
1. Create ArtifactPanel component (slide-in from right)
2. Implement artifact detection in message stream
3. Add syntax highlighting for code artifacts
4. Build live preview for rendered content
5. Implement "Save to project" functionality (Code mode)
6. Add multiple artifact tabs
7. Write tests for artifact editor

**Deliverable**: Generated artifacts open in slide-in PlateJS editor

---

### Phase 11: Checkpoint & Branching
**Goal**: Inline checkpoint markers and session forking

**Tasks**:
1. Create CheckpointMarker component
2. Implement checkpoint list fetching
3. Build fork session flow
4. Add restore to checkpoint functionality
5. Show forked sessions nested in sidebar
6. Create `/api/sessions/[id]/fork` BFF route
7. Write tests for checkpointing

**Deliverable**: Users can fork sessions from checkpoint markers

---

### Phase 12: Mobile-First Responsive
**Goal**: Touch-optimized mobile experience

**Tasks**:
1. Implement responsive breakpoints (Tailwind)
2. Add hamburger menu for mobile sidebar
3. Create bottom navigation bar (mobile)
4. Implement swipe gestures (swipe to delete)
5. Build full-screen composer for mobile
6. Simplify threading visualization on mobile
7. Ensure 44px minimum touch targets
8. Test on mobile viewports (320px-767px)
9. Write mobile-specific E2E tests

**Deliverable**: All features work on mobile with touch-optimized controls

---

### Phase 13: Theming & Accessibility
**Goal**: Light/Dark themes and WCAG AA compliance

**Tasks**:
1. Implement theme toggle (light/dark)
2. Add theme persistence (localStorage)
3. Adjust syntax highlighting themes
4. Add ARIA labels to all interactive elements
5. Implement keyboard navigation throughout
6. Add screen reader announcements for streaming
7. Ensure WCAG AA color contrast
8. Run axe-core accessibility tests
9. Write accessibility E2E tests

**Deliverable**: App supports light/dark themes and meets WCAG AA standards

---

### Phase 14: Performance Optimization
**Goal**: Fast load times and smooth interactions

**Tasks**:
1. Implement virtualization for session/message lists
2. Add code splitting with Next.js dynamic imports
3. Memoize expensive computations (markdown parsing)
4. Optimize image loading (next/image)
5. Implement debouncing for autocomplete
6. Add service worker for offline support (optional)
7. Run Lighthouse performance audits
8. Write performance tests

**Deliverable**: Time-to-first-token <500ms, FCP <1s, no jank

---

## Generated Artifacts

| Artifact | Status | Description |
|----------|--------|-------------|
| [spec.md](spec.md) | Complete | Feature specification with user stories, requirements |
| [research.md](research.md) | Complete | Technology research, decisions, patterns |
| [data-model.md](data-model.md) | Complete | TypeScript types, Zod schemas, database entities |
| [contracts/openapi-extensions.yaml](contracts/openapi-extensions.yaml) | Complete | API extensions for frontend features |
| [contracts/bff-routes.md](contracts/bff-routes.md) | Complete | Next.js BFF API routes documentation |
| [quickstart.md](quickstart.md) | Complete | Setup guide, usage examples, troubleshooting |

---

## Next Steps

1. **Initialize Next.js 15 App**: Run `pnpm create next-app@latest apps/web --typescript --tailwind --app --src-dir=false`
2. **Install Core Dependencies**: Add @assistant-ui/react, @tanstack/react-query, zod
3. **Configure shadcn/ui**: Run `npx shadcn-ui@latest init`
4. **Set Up Database Migrations**: Create tables for projects, agents, skills, tool presets
5. **Begin Phase 1**: Implement authentication flow
6. **Follow TDD**: Write tests before implementation for each feature

---

## Dependencies on Backend API

The frontend requires the following backend API endpoints (some may need implementation):

### Existing Endpoints (from specs/001-claude-agent-api)
- `POST /api/v1/query` - Streaming query (existing)
- `GET /api/v1/sessions/{id}` - Get session (existing)
- `POST /api/v1/sessions/{id}/resume` - Resume session (existing)
- `POST /api/v1/sessions/{id}/fork` - Fork session (existing)
- `GET /api/v1/health` - Health check (existing)

### New Endpoints Required (documented in openapi-extensions.yaml)
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/agents` - List agents
- `POST /api/v1/agents` - Create agent
- `GET /api/v1/skills` - List skills
- `POST /api/v1/skills` - Create skill
- `GET /api/v1/tool-presets` - List tool presets
- `POST /api/v1/tool-presets` - Create tool preset
- `GET /api/v1/sessions?mode=&project_id=&tags=` - List sessions with filtering
- `PATCH /api/v1/sessions/{id}/tags` - Update session tags
- `POST /api/v1/sessions/{id}/promote` - Promote to Code mode

**Action Required**: Backend API must implement these new endpoints before or during frontend development.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| SSE connection instability | Implement retry logic, exponential backoff, connection monitoring |
| PlateJS bundle size | Lazy load with dynamic imports, disable SSR |
| Mobile performance | Virtualization, code splitting, debouncing |
| Assistant UI learning curve | Review examples, start with basic components, extend gradually |
| Accessibility compliance | Run axe-core tests early, iterate on issues |
| API latency affecting UX | Optimistic UI updates, skeleton loaders, cached data |
