# Frontend AI Chat Interface Design

**Created**: 2026-01-10
**Status**: Design Complete - Ready for Implementation
**Context**: Web UI for Claude Agent API with full feature parity

## Overview

This document outlines the complete frontend design for an AI chat assistant interface powered by the Claude Agent API. The interface provides a beautiful, modern, and highly configurable chat experience with support for agents, skills, MCP servers, tool calls, and rich execution visualization.

## Design Principles

- **Mobile-First**: Touch-optimized controls, responsive design, progressive enhancement
- **Visual Clarity**: Threaded execution visualization showing causal relationships
- **Configurability**: Granular control over tools, permissions, agents, and MCP servers
- **Developer Experience**: Powerful features accessible through intuitive UI and keyboard shortcuts
- **Mode Flexibility**: Separate Brainstorm and Code modes for different workflows

---

## 1. Tech Stack & Architecture

### Core Framework
- **Next.js 15+** with App Router for modern React patterns
- **React 19+** with hooks and server components
- **shadcn/ui** components built on Radix UI primitives
- **Tailwind v4+** for styling with mobile-first responsive design
- **Assistant UI** (`@assistant-ui/react`) as foundation for AI chat components
- **PlateJS** for rich text editing (configuration files, artifacts, documents)

### State Management
- React Context + hooks for global state (auth, user settings, active tools)
- TanStack Query (React Query) for server state management and caching
- localStorage for API key persistence

### API Communication
- **Server-Sent Events (SSE)** for streaming chat responses via Claude Agent API (port 54000)
- **REST endpoints** for session management, checkpoints, skills, MCP servers
- **WebSocket** fallback for real-time updates if needed

### Authentication & Persistence
- **API key-based** authentication (stored in localStorage)
- Simple onboarding flow: "Enter your API key to get started"
- **PostgreSQL backend** (port 53432) persists:
  - Sessions and conversation history
  - Checkpoints and session branches
  - Agent/skill/MCP server configurations
  - Tags and metadata
  - All searchable via `Cmd+K` interface

---

## 2. Layout & Navigation Structure

### Two-Panel Layout
- **Left Sidebar (collapsible)**: Session/conversation list
- **Main Area**: Chat interface with threaded execution visualization
- **Modals/Slide-overs**: Tools config, settings, artifacts editor (PlateJS)

### Mode System

#### Brainstorm Mode
- **Purpose**: Research, planning, casual chat
- **Sidebar**: Grouped by date ("Today", "Yesterday", "Last 7 days", "Last 30 days")
- **Features**: PlateJS editor for creating docs/plans
- **Filesystem**: No direct filesystem access
- **Promotion**: Can toggle to Code mode to gain workspace access

#### Code Mode
- **Purpose**: Project-based development work
- **Sidebar**: Grouped by project
- **Project Selection**: Inline picker in chat header for selection/creation
- **Filesystem**: Agent sandboxed to `${WORKSPACE_BASE_DIR}/${PROJECT_NAME}`
- **Features**: Full filesystem access for creating/editing files

#### Mode Toggle
- Small toggle button in sidebar to switch Brainstorm ↔ Code
- Promotes current session to Code mode (gains workspace context)
- PlateJS docs from Brainstorm serve as reference/planning context

### Navigation
- **`Cmd+K`**: Unified command palette + global search
  - Search across: sessions, configs, messages, files
  - Execute commands: slash commands, actions
  - Navigate to: agents, skills, MCP servers, settings
- **Sidebar search**: Quick filter within current view
- **Tags**: All conversations can be tagged, filterable in sidebar

---

## 3. Chat Input & Autocomplete System

### Input Area Components
- **Rich text input field** with multi-line support
- **Attach button**: Upload images + trigger autocomplete menu
- **Tool badge**: Simple badge/chip displaying active tool count (e.g., "12")
- **Permissions chip**: Toggle between modes:
  - **Plan Mode**: No auto-execution, show plan for approval
  - **Edit Automatically**: Auto-approve all tools including file edits/writes
  - **Ask before Edits**: Auto-approve reads, require approval for writes
  - **YOLO (Bypass Permissions)**: Auto-approve everything, no confirmations
- **Send button**: Submit message (`Enter` to send, `Shift+Enter` for newline)

### Autocomplete Triggers
- **`/` (slash)**: Commands and skills
- **`@` (mention)**: Universal autocomplete for:
  - Agents
  - MCP servers
  - MCP tools
  - MCP resources
  - Files/folders
  - Slash commands
  - Skills
  - Presets

### Autocomplete UI
- Dropdown menu appears below cursor position
- Searchable/filterable list
- Keyboard navigation (`↑↓` to select, `Enter` to insert, `Esc` to close)
- Shows icons, descriptions, and categories for each item
- Recently used items appear at top

### Tool Management Modal (via tool badge)
- List of all available tools (built-in + MCP tools)
- **Grouped by MCP server** (built-in tools as one group, each MCP server as separate groups)
- Toggle switches to enable/disable individual tools
- Search/filter tools by name or category
- **"Save as preset"** button to create named tool loadouts
- Quick preset selector dropdown
- Shows which tools are currently active

---

## 4. Message Flow & Execution Visualization

### Threading & Connection Visualization

**Visual Execution Graph** showing causal flow with connecting lines and indentation:

```
User Message
  ↓ (connecting line)
Tool Call: Read config.py
  ↓ (indented/connected)
  Thinking: "Need to check dependencies..."
    ↓ (flows into)
    Tool Call: Bash npm list
      ↓ (connects to)
      Subagent: dependency-analyzer
        [Activity card - collapsed]
          ↓ (result feeds back)
          Response: "Found 3 outdated packages..."
```

**Configuration Options** (in settings):
- **Always visible** (default): Lines/indentation always shown
- **Hover-activated**: Hover over element to highlight connections
- **Toggleable**: "Flow view" (threaded) vs "Chat view" (flat) modes
- **Smart/adaptive**: Simple conversations flat, complex multi-tool sequences show connections

### Message Components

#### User Messages
- Standard chat bubble

#### Assistant Text
- Streaming token-by-token with typing indicator
- Live token stream for text responses

#### Tool Call Cards
- **Collapsible cards** showing:
  - **Header**: tool name, status badge (running/success/error), duration
  - **Expanded**: inputs (formatted JSON), outputs, streaming progress
  - Connected via visual lines to parent message
- **Card-based timeline**: Each tool call is a distinct card in message flow

#### Thinking Blocks
- Collapsible sections connected in execution flow
- Shows agent's reasoning process

#### Subagent Activity Cards
- **Collapsed by default** - don't spam main thread
- Shows:
  - Subagent name
  - Task summary
  - Status indicator
- Expandable to see subagent's full execution trace
- Activity feed card format ("Running subagent: code-reviewer...")

### Streaming Visualization
- **Hybrid approach**:
  - Live token stream for text responses
  - Activity feed cards for tool execution ("Reading file...", "Running bash command...")
  - Subagent cards show activity status without flooding chat

---

## 5. Tool Approvals & Error Handling

### Tool Approval Workflow

**Inline blocking** when tools require human confirmation:
- Tool card appears in message stream with:
  - Tool name and description
  - Input parameters (formatted JSON)
  - **Approve** / **Deny** buttons
  - "Always allow this tool" checkbox option
- Chat is blocked until user makes decision
- Approval state influenced by **Permissions chip** settings

### Error Handling

**Inline error cards** in message stream:
- Red-bordered cards showing:
  - Error type and message
  - Stack trace (collapsible)
  - Retry button
  - "Report issue" link
- Errors maintain position in execution flow (connected to parent tool/message)
- Transient errors auto-dismiss after user acknowledges
- Critical failures persist until explicitly dismissed

### Checkpoint & Branching

**Inline markers** at checkpoint moments:
- Small branch icon in message flow
- Click marker to:
  - Fork from this point (creates new session branch)
  - View checkpoint metadata (timestamp, message count)
  - Restore to this state
- Branched sessions appear as nested items in sidebar

---

## 6. Configuration Management UI (PlateJS Integration)

### PlateJS Rich Editor For:
- **Agents** (markdown + YAML frontmatter)
- **Skills** (markdown + YAML frontmatter)
- **Slash commands** (markdown + YAML frontmatter)
- **MCP server configs** (JSON with credential sanitization)

### Editor Features
- Full-screen slide-in from right
- Syntax highlighting for YAML frontmatter and JSON
- Live preview for markdown content
- Version history with diff view
- Save/Cancel/Delete buttons
- Share button (generates shareable view-only link)

### Agent Configuration
- **YAML frontmatter**: name, description, tools allowed, assigned skills, assigned slash commands
- **Markdown body**: system prompt/instructions
- **Tool preset selector**: assign saved tool loadouts
- **Preview pane**: shows how agent appears in autocomplete

### MCP Server Configuration
- JSON editor with schema validation
- **Credential sanitization toggle** (strips API keys/tokens before sharing)
- Test connection button
- Shows which tools/resources this server provides

### Sharing System
- Click "Share" → generates **view-only URL**
- Shareable page shows rendered content
- **Download button** (saves as `.md` or `.json`)
- **Copy to clipboard button** (copies raw content)
- Credentials **auto-sanitized** for MCP configs when sharing

---

## 7. MCP Server Management

### 1. Admin Panel (Settings Page)

**Dedicated "MCP Servers" settings section:**
- List view of all configured servers with status indicators (connected/failed/idle)
- Add/Edit/Delete server configurations
- Each server card shows:
  - Server name and type (stdio/SSE/HTTP)
  - Connection status and health
  - List of exposed tools and resources
  - Edit and Delete buttons
- Opens PlateJS editor for creating/editing server configs (JSON)

### 2. Inline Contextual (Mid-Conversation)

**Slash commands:**
- `/mcp connect <server-name>` or `/mcp add`
- Triggers inline flow to configure new MCP server
- Modal with quick config form (name, type, command/URL, env vars)
- "Save to library" option adds to permanent server list
- Immediate connection attempt with status feedback in chat

### 3. `@` Menu Integration (Dynamic Per-Session)

**Type to enable:**
- `@mcp-server-name` to enable/connect to that server in current session
- `@mcp-tool-name` to invoke specific MCP tool
- `@mcp-resource-name` to inject MCP resource
- Servers auto-connect on first `@` mention
- Session remembers which servers were used, auto-reconnects on resume

### MCP Server Grouping (in tool management modal)
- Servers shown as collapsible sections
- Each server shows its tools as sub-items
- Individual tool toggles within each server group
- Server-level toggle (enable/disable all tools from that server)

---

## 8. Artifacts, Settings & Theming

### Artifacts (Generated Content)

**Right-side slide-in modal/fullscreen editor** powered by PlateJS:
- Triggered when agent generates code, diagrams, documents
- Features:
  - Syntax highlighting for code artifacts
  - Live preview for rendered content
  - Edit capabilities (PlateJS rich editor)
  - Download button
  - Copy to clipboard
  - "Save to project" (in Code mode, writes to filesystem)
- Can be opened from inline artifact preview in chat
- Multiple artifacts open as tabs within the slide-in panel

### Settings Panel

**Accessible via** `Cmd+K` → "Settings" or gear icon in header

**Organized sections:**

1. **Account**
   - API key management
   - Usage stats

2. **Appearance**
   - Light/Dark mode toggle
   - Font size
   - Message density

3. **Visualization**
   - Threading toggle (always/hover/adaptive/flow view)
   - Flow view settings
   - Connection line styling

4. **Defaults**
   - Default permissions mode
   - Default tool preset
   - Workspace base directory (`${WORKSPACE_BASE_DIR}`)

5. **MCP Servers**
   - Links to admin panel (detailed in Section 7)

6. **Agents, Skills & Slash Commands/Plugins**
   - Links to library/management pages
   - Create new agents, skills, slash commands
   - Browse and edit existing configurations

7. **Keyboard Shortcuts**
   - Customizable hotkeys
   - View all shortcuts

8. **Advanced**
   - Debug mode
   - Logs viewer
   - Reset settings

### Theming
- **Light mode** and **Dark mode**
- System-level toggle in settings
- Persisted in localStorage
- Smooth transitions between modes
- Syntax highlighting themes adjust with mode (light variant for light mode, dark for dark mode)

---

## 9. Component Library & Assistant UI Integration

### Assistant UI as Foundation

**Use composable primitives from** `@assistant-ui/react`:

Core components:
- `<Thread>`: Main message container with streaming support
- `<Message>`: Individual message bubbles
- `<ToolCall>`: Tool execution cards with approval flows
- `<ComposerInput>`: Rich text input with autocomplete
- `<Attachment>`: File upload handling

### Custom Extensions on Assistant UI

**Custom components extending Assistant UI:**
- **Threading visualization**: Custom wrapper adding visual connection lines
- **Subagent cards**: Custom component extending `<ToolCall>` for collapsed subagent display
- **Checkpoint markers**: Custom inline markers integrated into message flow
- **Tool badge**: Custom component for active tool count display
- **Permissions chip**: Custom toggle component in composer area
- **Mode selector**: Custom Brainstorm/Code mode toggle in sidebar

### shadcn/ui Components

**UI primitives throughout:**
- Modal/Dialog for tool management, settings, MCP config
- Slide-over/Sheet for artifacts editor (PlateJS integration)
- Dropdown menus for autocomplete
- Command palette (`Cmd+K`) using shadcn Command component
- Toast notifications for system messages
- Badges, chips, buttons, form controls

### Mobile-First Responsive Design

**Touch-optimized experience:**
- Touch-optimized controls (min 44px touch targets)
- Collapsible sidebar on mobile (hamburger menu)
- Bottom navigation bar on mobile (home, search, settings, new chat)
- Swipe gestures:
  - Swipe left on session to delete
  - Swipe to collapse cards
- Full-screen composer on mobile (expands when focused)
- Simplified threading on small screens (indent-only, no connecting lines)

**Responsive breakpoints (Tailwind):**
- Mobile: 320px - 767px (default styles)
- Tablet: 768px - 1023px
- Desktop: 1024px+

---

## Key User Flows

### 1. Starting a Brainstorm Session
1. User opens app (or clicks "New Chat")
2. Mode defaults to Brainstorm
3. User types question or research topic
4. Agent responds with streaming text
5. User can create docs/plans using PlateJS editor
6. Session appears in sidebar under "Today"

### 2. Promoting to Code Mode
1. User toggles Brainstorm → Code mode
2. Inline picker appears to select/create project
3. User selects existing project or creates new folder
4. Agent gains filesystem access to `${WORKSPACE_BASE_DIR}/${PROJECT_NAME}`
5. PlateJS docs from Brainstorm serve as reference context
6. Session moves to project-grouped sidebar

### 3. Using `@` Autocomplete
1. User types `@` in chat input
2. Dropdown appears showing:
   - Agents (e.g., `@code-reviewer`)
   - MCP servers (e.g., `@mcp-postgres`)
   - MCP tools (e.g., `@mcp-postgres-query`)
   - Files (e.g., `@readme.md`)
   - Skills, slash commands, presets
3. User selects item with keyboard or click
4. Item inserted into message
5. On send, agent invokes/connects to referenced entity

### 4. Configuring Tools
1. User clicks tool badge (shows count, e.g., "12")
2. Tool management modal opens
3. Tools grouped by MCP server
4. User toggles individual tools on/off
5. User clicks "Save as preset" → names it "read-only-tools"
6. Preset now available in quick selector dropdown

### 5. Sharing an Agent Configuration
1. User opens agent in PlateJS editor
2. Clicks "Share" button
3. System generates view-only URL
4. Shareable page displays:
   - Rendered markdown (system prompt)
   - YAML frontmatter (name, tools, skills)
   - Download button (.md file)
   - Copy to clipboard button
5. Other users can view, download, or copy configuration

### 6. Tool Approval Flow
1. Agent attempts to use tool requiring approval
2. Inline tool card appears in chat with:
   - Tool name: "Edit file: config.py"
   - Input: `{ "file_path": "/app/config.py", "changes": "..." }`
   - Approve / Deny buttons
3. User reviews and clicks "Approve"
4. Agent proceeds with tool execution
5. Tool card updates to show success status and output

### 7. Checkpoint & Fork
1. User sees inline checkpoint marker in message flow
2. Clicks marker → options appear:
   - Fork from this point
   - Restore to this state
3. User clicks "Fork"
4. New session branch created
5. Original session preserved
6. Forked session appears nested in sidebar

---

## Technical Considerations

### Performance
- **Memoization**: Cache parsed markdown blocks to prevent re-rendering on each token
- **Virtualization**: Use `react-window` or `@tanstack/react-virtual` for long conversation lists
- **Code splitting**: Lazy load PlateJS editor, settings panel, and heavy components
- **Debouncing**: Debounce autocomplete search queries

### Accessibility
- **ARIA labels**: All interactive elements properly labeled
- **Keyboard navigation**: Full keyboard support (`Tab`, `Enter`, `Esc`, arrow keys)
- **Screen reader support**: Announce streaming messages, tool status changes
- **Focus management**: Trap focus in modals, restore on close
- **Color contrast**: WCAG AA compliant color ratios

### Security
- **API key storage**: localStorage with secure handling
- **Credential sanitization**: Auto-strip secrets when sharing configs
- **Sandbox enforcement**: Code mode restricted to `${WORKSPACE_BASE_DIR}`
- **Input validation**: Sanitize all user inputs before sending to API
- **CSP headers**: Content Security Policy to prevent XSS

### Testing Strategy
- **Unit tests**: React components with Jest + React Testing Library
- **Integration tests**: User flows with Playwright (autocomplete, tool approval, sharing)
- **E2E tests**: Full user scenarios (Brainstorm → Code promotion, MCP server config)
- **Visual regression**: Chromatic or Percy for UI consistency
- **Accessibility tests**: axe-core integration

---

## Implementation Phases

### Phase 1: Core Chat Interface
- Next.js app setup with shadcn/ui and Tailwind
- Assistant UI integration for basic chat
- SSE streaming from Claude Agent API
- Basic message rendering (text only)
- API key authentication

### Phase 2: Tool Visualization
- Tool call cards (collapsible)
- Inline error cards
- Threading/connection visualization
- Thinking blocks
- Subagent activity cards

### Phase 3: Input & Autocomplete
- Rich text input with attach button
- `/` and `@` autocomplete triggers
- Tool badge and permissions chip
- Tool management modal

### Phase 4: Mode System & Projects
- Brainstorm/Code mode toggle
- Project picker for Code mode
- Sidebar grouping (date vs project)
- Filesystem access in Code mode

### Phase 5: Configuration Management
- PlateJS editor integration
- Agent/skill/slash command CRUD
- MCP server configuration (admin panel, inline, `@` menu)
- Sharing system (view-only links)

### Phase 6: Advanced Features
- Checkpoint markers and forking
- Artifacts editor (PlateJS)
- `Cmd+K` command palette + global search
- Settings panel

### Phase 7: Polish & Mobile
- Mobile-first responsive design
- Touch gestures and bottom nav
- Light/Dark mode
- Performance optimization (memoization, virtualization)
- Accessibility audit

---

## Dependencies

### Core
```json
{
  "next": "^15.0.0",
  "react": "^19.0.0",
  "react-dom": "^19.0.0",
  "@assistant-ui/react": "latest",
  "@udecode/plate": "latest",
  "@tanstack/react-query": "^5.0.0"
}
```

### UI Components
```json
{
  "shadcn/ui": "via CLI",
  "@radix-ui/react-*": "latest",
  "tailwindcss": "^4.0.0",
  "class-variance-authority": "latest",
  "clsx": "latest",
  "tailwind-merge": "latest"
}
```

### Utilities
```json
{
  "eventsource-parser": "^1.1.0",
  "zod": "^3.22.0",
  "date-fns": "^3.0.0",
  "cmdk": "latest"
}
```

### Dev Dependencies
```json
{
  "typescript": "^5.3.0",
  "@types/react": "^19.0.0",
  "eslint": "^9.0.0",
  "prettier": "^3.1.0",
  "jest": "^29.0.0",
  "@testing-library/react": "^14.0.0",
  "playwright": "^1.40.0"
}
```

---

## Next Steps

1. **Review & Approve Design**: Stakeholder review of this document
2. **Create Implementation Plan**: Detailed technical plan following TDD principles
3. **Set up Project**: Initialize Next.js app in `apps/web/`
4. **Phase 1 Kickoff**: Begin with core chat interface and Assistant UI integration

---

## Sources & References

- [Assistant UI GitHub](https://github.com/assistant-ui/assistant-ui)
- [Assistant UI Template](https://www.shadcn.io/template/assistant-ui-assistant-ui)
- [Vercel AI SDK Elements](https://ai-sdk.dev/elements/components/message)
- [CopilotKit](https://github.com/CopilotKit/CopilotKit)
- [Chainlit React Client](https://docs.chainlit.io/deploy/react-frontend)
- [LibreChat Architecture](https://www.librechat.ai/)
- [Streamdown](https://www.kdjingpai.com/en/streamdown/)
- [PlateJS](https://platejs.org/)
- [shadcn/ui](https://ui.shadcn.com/)
