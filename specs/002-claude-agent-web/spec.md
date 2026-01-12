# Feature Specification: Claude Agent Web Interface

**Feature Branch**: `002-claude-agent-web`
**Created**: 2026-01-10
**Status**: Draft
**Input**: User requirements: "Create a beautiful, modern AI assistant web interface with full Claude Agent SDK feature parity - MCP servers, agents, skills, slash commands, tool visualization, mobile-first responsive design"

## Overview

This specification defines a Next.js 16+ web application that provides a comprehensive frontend interface for the Claude Agent API. The application delivers a beautiful, modern chat experience with full feature parity including agents, skills, MCP servers, tool calls, rich execution visualization, and mobile-first responsive design.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Chat Interaction (Priority: P1)

A user wants to have a conversation with Claude through a clean, intuitive chat interface with streaming responses.

**Why this priority**: Core functionality - without basic chat, no other features matter. Delivers immediate value by enabling AI interactions.

**Independent Test**: Can be fully tested by sending a message and verifying streaming response display.

**Acceptance Scenarios**:

1. **Given** a valid API key, **When** the user sends a message, **Then** the system displays streaming response token-by-token.
2. **Given** an ongoing response, **When** tokens arrive, **Then** the UI updates in real-time without flickering or layout shifts.
3. **Given** a multiline message input, **When** the user presses `Shift+Enter`, **Then** a newline is inserted (not sent).
4. **Given** a message in the input field, **When** the user presses `Enter`, **Then** the message is sent and input clears.

---

### User Story 2 - Tool Call Visualization (Priority: P1)

A user wants to see when Claude uses tools, what inputs are provided, and what results are returned, displayed as collapsible cards in the message flow.

**Why this priority**: Essential for understanding agent behavior and building trust in autonomous operations.

**Independent Test**: Can be tested by sending a prompt requiring tool use and verifying card display.

**Acceptance Scenarios**:

1. **Given** Claude uses a tool, **When** the tool call occurs, **Then** a collapsible card appears showing tool name, status, and duration.
2. **Given** a tool call card, **When** the user expands it, **Then** formatted input parameters and output results are displayed.
3. **Given** multiple tool calls, **When** they execute, **Then** visual connection lines show the execution flow.
4. **Given** a tool call fails, **When** an error occurs, **Then** the card displays error state with retry button.

---

### User Story 3 - Mode System (Brainstorm vs Code) (Priority: P1)

A user wants to switch between casual research/planning (Brainstorm mode) and project-based development work (Code mode) with different sidebar organization.

**Why this priority**: Fundamental UX pattern that determines how users organize and navigate their work.

**Independent Test**: Can be tested by creating sessions in each mode and verifying sidebar grouping.

**Acceptance Scenarios**:

1. **Given** a new session, **When** Brainstorm mode is active, **Then** sidebar groups conversations by date.
2. **Given** a Brainstorm session, **When** user toggles to Code mode, **Then** a project picker appears.
3. **Given** Code mode is active, **When** user selects a project, **Then** agent gains filesystem access to that project folder.
4. **Given** Code mode, **When** viewing sidebar, **Then** conversations are grouped by project.

---

### User Story 4 - Tool Management & Permissions (Priority: P1)

A user wants granular control over which tools Claude can use and what level of autonomy to grant.

**Why this priority**: Security and control are essential - users must be able to restrict agent capabilities.

**Independent Test**: Can be tested by configuring tools and permissions and verifying enforcement.

**Acceptance Scenarios**:

1. **Given** the tool badge is clicked, **When** the modal opens, **Then** all available tools are listed grouped by MCP server.
2. **Given** individual tool toggles, **When** a tool is disabled, **Then** Claude cannot use that tool in the session.
3. **Given** a tool preset is saved, **When** selected from dropdown, **Then** all preset tools are enabled.
4. **Given** "Ask before Edits" permission mode, **When** Claude attempts file write, **Then** inline approval card appears.

---

### User Story 5 - Universal Autocomplete (@/Menu) (Priority: P2)

A user wants to quickly reference agents, MCP servers, tools, files, skills, and commands using @ and / triggers.

**Why this priority**: Significantly improves UX by reducing friction in accessing powerful features.

**Independent Test**: Can be tested by typing @ and verifying autocomplete menu with all entity types.

**Acceptance Scenarios**:

1. **Given** user types `@` in input, **When** the character appears, **Then** autocomplete dropdown shows all mentionable entities.
2. **Given** autocomplete is open, **When** user types filter text, **Then** results filter in real-time.
3. **Given** autocomplete has results, **When** user navigates with arrow keys, **Then** selection highlights move.
4. **Given** an item is selected, **When** user presses `Enter`, **Then** the entity is inserted into message.
5. **Given** user types `/`, **When** the character appears, **Then** slash commands and skills are shown.

---

### User Story 6 - MCP Server Management (Priority: P2)

A user wants to configure and manage MCP servers through three interfaces: admin panel, inline commands, and @ menu.

**Why this priority**: MCP servers enable extensibility - critical for enterprise integrations.

**Independent Test**: Can be tested by configuring an MCP server and verifying tool availability.

**Acceptance Scenarios**:

1. **Given** settings page, **When** user clicks "MCP Servers", **Then** list of configured servers with status appears.
2. **Given** a server configuration, **When** user clicks "Edit", **Then** PlateJS JSON editor opens.
3. **Given** user types `/mcp connect`, **When** command is sent, **Then** inline modal prompts for server config.
4. **Given** user types `@mcp-server-name`, **When** sent, **Then** server connects and tools become available.
5. **Given** tool management modal, **When** opened, **Then** MCP server tools are grouped by server.

---

### User Story 7 - Session Management & History (Priority: P2)

A user wants to access previous conversations, resume sessions, and fork conversations at specific points.

**Why this priority**: Essential for maintaining context and exploring alternative conversation paths.

**Independent Test**: Can be tested by creating multiple sessions and verifying sidebar organization.

**Acceptance Scenarios**:

1. **Given** multiple sessions, **When** viewing sidebar, **Then** sessions are grouped appropriately by mode (date or project).
2. **Given** a session in sidebar, **When** user clicks it, **Then** full conversation history loads.
3. **Given** an active session, **When** user clicks checkpoint marker, **Then** fork and restore options appear.
4. **Given** fork is selected, **When** confirmed, **Then** new session branch is created from that point.

---

### User Story 8 - Agent & Configuration Management (Priority: P2)

A user wants to create, edit, and manage custom agents, skills, and slash commands using a rich text editor.

**Why this priority**: Enables customization and extensibility, essential for power users.

**Independent Test**: Can be tested by creating an agent and verifying it appears in autocomplete.

**Acceptance Scenarios**:

1. **Given** settings page, **When** user clicks "Agents", **Then** list of configured agents appears.
2. **Given** "Create Agent" is clicked, **When** PlateJS editor opens, **Then** YAML frontmatter and markdown editor are shown.
3. **Given** an agent is configured, **When** saved, **Then** agent appears in @ autocomplete menu.
4. **Given** an agent configuration, **When** user clicks "Share", **Then** view-only URL is generated with credentials sanitized.

---

### User Story 9 - Mobile-First Responsive Design (Priority: P2)

A user on a mobile device wants full access to all features with touch-optimized controls.

**Why this priority**: Mobile users represent significant portion of potential users.

**Independent Test**: Can be tested on mobile viewport (320px-767px) verifying all features work.

**Acceptance Scenarios**:

1. **Given** mobile viewport, **When** page loads, **Then** sidebar collapses and hamburger menu appears.
2. **Given** mobile view, **When** user taps input field, **Then** composer expands to full-screen mode.
3. **Given** tool call cards, **When** displayed on mobile, **Then** simplified threading (no connection lines) is used.
4. **Given** bottom navigation, **When** user taps icons, **Then** appropriate actions trigger (new chat, search, settings).

---

### User Story 10 - Command Palette & Global Search (Priority: P3)

A user wants unified `Cmd+K` interface for commands and global search across all entities.

**Why this priority**: Power user feature that significantly improves navigation efficiency.

**Independent Test**: Can be tested by pressing `Cmd+K` and verifying search results across entities.

**Acceptance Scenarios**:

1. **Given** user presses `Cmd+K`, **When** key combination is detected, **Then** command palette modal opens.
2. **Given** command palette is open, **When** user types search query, **Then** results from all categories appear.
3. **Given** search results, **When** user navigates with arrow keys and presses `Enter`, **Then** selected item action executes.
4. **Given** command palette, **When** user types command name, **Then** matching commands are shown with shortcuts.

---

### User Story 11 - PlateJS Artifacts Editor (Priority: P3)

A user wants to view and edit generated code, diagrams, and documents in a rich editor that slides in from the right.

**Why this priority**: Enhances editing experience for generated content but builds on core chat functionality.

**Independent Test**: Can be tested by having Claude generate code and verifying editor opens.

**Acceptance Scenarios**:

1. **Given** Claude generates an artifact, **When** displayed in chat, **Then** inline preview with "Open in editor" appears.
2. **Given** "Open in editor" is clicked, **When** triggered, **Then** right-side slide-in panel with PlateJS editor opens.
3. **Given** artifact editor is open, **When** user edits content, **Then** live syntax highlighting is applied.
4. **Given** edited artifact, **When** user clicks "Save to project", **Then** file is written to workspace (Code mode only).

---

### User Story 12 - Checkpoint & Branching Visualization (Priority: P3)

A user wants to see inline checkpoint markers in the message flow and easily fork conversations.

**Why this priority**: Advanced feature for power users exploring conversation alternatives.

**Independent Test**: Can be tested by creating checkpoints and verifying markers appear.

**Acceptance Scenarios**:

1. **Given** file checkpointing is enabled, **When** file modifications occur, **Then** checkpoint markers appear inline.
2. **Given** a checkpoint marker, **When** user clicks it, **Then** modal shows fork/restore options.
3. **Given** restore is selected, **When** confirmed, **Then** files revert to checkpoint state.
4. **Given** forked sessions, **When** viewing sidebar, **Then** branches appear nested under parent session.

---

### Edge Cases

- What happens when SSE connection drops mid-stream? → Client automatically reconnects and resumes session via API
- How does the UI handle very long conversations (1000+ messages)? → Virtualized scrolling with react-window loads only visible messages
- What happens when file upload fails? → Inline error message with retry button, preserves draft message
- How does autocomplete handle slow MCP server responses? → Loading state with timeout (3s), shows partial results
- What happens when user closes browser with active session? → Session persists in backend, auto-resumes on page reload
- How does mobile UI handle keyboard appearing/disappearing? → Fixed bottom padding with viewport height adjustments
- What happens when PlateJS editor has unsaved changes and user navigates away? → Confirmation modal warns of unsaved changes
- How does threading visualization handle deeply nested subagents (5+ levels)? → Simplified view with expand/collapse controls for nested sections
- What happens when tool approval times out? → Auto-deny after 5 minutes with notification
- How does the UI handle API key expiration mid-session? → Error banner with "Update API key" link, preserves session state

## Requirements *(mandatory)*

### Functional Requirements

#### Core Chat Interface

- **FR-001**: System MUST render streaming text responses token-by-token with no visible lag
- **FR-002**: System MUST support multiline input with `Shift+Enter` for newlines and `Enter` to send
- **FR-003**: System MUST display conversation history with infinite scroll (virtualized for performance)
- **FR-004**: System MUST preserve draft messages in localStorage during session navigation
- **FR-005**: System MUST show typing indicators during agent response generation

#### Tool Visualization

- **FR-006**: System MUST display tool calls as collapsible cards showing name, status, and duration
- **FR-007**: System MUST show visual connection lines between messages, tool calls, and thinking blocks
- **FR-008**: System MUST format tool input/output as syntax-highlighted JSON in expanded cards
- **FR-009**: System MUST show inline error cards with retry buttons for failed tool calls
- **FR-010**: System MUST collapse subagent activity cards by default with expand option

#### Mode System

- **FR-011**: System MUST support Brainstorm mode with date-grouped sidebar (Today, Yesterday, Last 7 days, Last 30 days)
- **FR-012**: System MUST support Code mode with project-grouped sidebar
- **FR-013**: System MUST show mode toggle button in sidebar to switch between Brainstorm and Code
- **FR-014**: System MUST display project picker when toggling from Brainstorm to Code mode
- **FR-015**: System MUST preserve mode preference in localStorage per session

#### Tool Management & Permissions

- **FR-016**: System MUST display tool badge showing active tool count
- **FR-017**: System MUST show tool management modal with tools grouped by MCP server
- **FR-018**: System MUST support individual tool toggles and server-level toggles
- **FR-019**: System MUST support saving tool configurations as named presets
- **FR-020**: System MUST display permissions chip with four modes: Default, Accept Edits, Don't Ask, Bypass Permissions
- **FR-021**: System MUST show inline approval cards for tool calls requiring permission in Default mode
- **FR-022**: System MUST support "Always allow this tool" checkbox in approval cards

#### Autocomplete System

- **FR-023**: System MUST trigger autocomplete dropdown on `@` character with all mentionable entities
- **FR-024**: System MUST trigger autocomplete dropdown on `/` character with slash commands and skills
- **FR-025**: System MUST filter autocomplete results in real-time as user types
- **FR-026**: System MUST support keyboard navigation in autocomplete (arrow keys, Enter, Esc)
- **FR-027**: System MUST show recently used items at top of autocomplete results
- **FR-028**: System MUST display icons, descriptions, and categories for autocomplete items

#### MCP Server Management

- **FR-029**: System MUST provide admin panel in settings showing all configured MCP servers with status
- **FR-030**: System MUST support inline `/mcp connect` command for quick server configuration
- **FR-031**: System MUST support `@mcp-server-name` mention to enable server in current session
- **FR-032**: System MUST show PlateJS JSON editor for creating/editing MCP server configs
- **FR-033**: System MUST display MCP tools grouped by server in tool management modal
- **FR-034**: System MUST sanitize credentials (API keys, tokens) when sharing MCP configs

#### Session Management

- **FR-035**: System MUST display session list in collapsible sidebar
- **FR-036**: System MUST support session search/filter within sidebar
- **FR-037**: System MUST show checkpoint markers inline in message flow
- **FR-038**: System MUST support session forking from checkpoint markers
- **FR-039**: System MUST display forked sessions nested under parent in sidebar
- **FR-040**: System MUST preserve session state across page refreshes

#### Configuration Management

- **FR-041**: System MUST provide settings page with sections: Account, Appearance, Visualization, Defaults, MCP Servers, Agents/Skills/Slash Commands, Keyboard Shortcuts, Advanced
- **FR-042**: System MUST support creating/editing agents with PlateJS editor (YAML frontmatter + markdown body)
- **FR-043**: System MUST support creating/editing skills with PlateJS editor
- **FR-044**: System MUST support creating/editing slash commands with PlateJS editor
- **FR-045**: System MUST generate view-only shareable URLs for agents, skills, and MCP configs
- **FR-046**: System MUST provide download and copy-to-clipboard buttons for shared configurations

#### Mobile-First Responsive

- **FR-047**: System MUST collapse sidebar on mobile with hamburger menu access
- **FR-048**: System MUST expand composer to full-screen when focused on mobile
- **FR-049**: System MUST show simplified threading (indent-only, no lines) on mobile viewports
- **FR-050**: System MUST provide bottom navigation bar on mobile (home, search, settings, new chat)
- **FR-051**: System MUST support swipe gestures (swipe left to delete session, swipe to collapse cards)
- **FR-052**: System MUST enforce minimum 44px touch targets for all interactive elements

#### Command Palette & Search

- **FR-053**: System MUST open command palette on `Cmd+K` (or `Ctrl+K` on Windows/Linux)
- **FR-054**: System MUST search across sessions, agents, MCP servers, skills, slash commands, and files
- **FR-055**: System MUST categorize search results by entity type
- **FR-056**: System MUST support keyboard navigation and execution in command palette

#### Artifacts Editor

- **FR-057**: System MUST display artifacts in right-side slide-in panel with PlateJS editor
- **FR-058**: System MUST support syntax highlighting for code artifacts
- **FR-059**: System MUST provide live preview for rendered content
- **FR-060**: System MUST support "Save to project" button (Code mode only) to write artifact to filesystem
- **FR-061**: System MUST support multiple artifacts open as tabs within slide-in panel

#### Theming & Appearance

- **FR-062**: System MUST support light and dark themes
- **FR-063**: System MUST persist theme preference in localStorage
- **FR-064**: System MUST adjust syntax highlighting themes based on current theme
- **FR-065**: System MUST provide smooth transitions when switching themes

#### Performance

- **FR-066**: System MUST virtualize long conversation lists to prevent performance degradation
- **FR-067**: System MUST lazy load PlateJS editor and heavy components via code splitting
- **FR-068**: System MUST debounce autocomplete search queries (300ms)
- **FR-069**: System MUST memoize parsed markdown blocks to prevent unnecessary re-renders

#### Accessibility

- **FR-070**: System MUST provide ARIA labels for all interactive elements
- **FR-071**: System MUST support full keyboard navigation (Tab, Enter, Esc, arrow keys)
- **FR-072**: System MUST announce streaming messages and status changes to screen readers
- **FR-073**: System MUST trap focus in modals and restore on close
- **FR-074**: System MUST maintain WCAG AA compliant color contrast ratios

### Key Entities

- **Session**: A conversation with persistent history, mode (Brainstorm/Code), and project association
- **Message**: A chat message (user, assistant, system) with content blocks
- **Tool Call Card**: Visual representation of tool execution with status, inputs, outputs
- **Checkpoint Marker**: Inline indicator for session branching points
- **Agent**: Custom subagent configuration with system prompt and tool restrictions
- **Skill**: Autonomous invokable functionality defined in markdown
- **Slash Command**: User-invoked command defined in markdown
- **MCP Server**: External tool provider connected via Model Context Protocol
- **Tool Preset**: Named collection of enabled tools
- **Artifact**: Generated content (code, diagram, document) editable in PlateJS
- **Project**: Filesystem directory for Code mode sessions
- **Permission Mode**: Level of autonomy (Default: ask for each tool, Accept Edits: auto-approve file edits, Don't Ask: non-interactive auto-approve all, Bypass Permissions: skip all checks)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can send messages and receive streaming responses with time-to-first-token under 500ms
- **SC-002**: Tool call visualization renders all tool types (built-in + MCP) with accurate status
- **SC-003**: Mode toggle switches between Brainstorm and Code with sidebar regrouping under 100ms
- **SC-004**: Autocomplete dropdown appears within 50ms of typing @ or / trigger character
- **SC-005**: Tool management modal displays 100+ tools organized by server without lag
- **SC-006**: Mobile viewport (320px) renders all features with touch targets ≥44px
- **SC-007**: Command palette searches 1000+ entities and returns results within 200ms
- **SC-008**: PlateJS editor loads and displays syntax highlighting within 500ms
- **SC-009**: Session list with 500+ conversations renders using virtualization without jank
- **SC-010**: All user flows achieve WCAG AA accessibility compliance

## Clarifications

### Session 2026-01-10

- Q: Should the web app support both streaming and single-response modes? → A: Only streaming mode (SSE) since we want real-time interactivity
- Q: How should the app handle session persistence across page refreshes? → A: Store session ID in URL and localStorage, auto-resume on load
- Q: Should PlateJS editor support collaborative editing? → A: No, single-user editing only for MVP
- Q: How should connection errors be displayed? → A: Persistent error banner at top with retry button and reconnection status
- Q: Should tool presets be shareable? → A: Yes, generate view-only URLs with copy-to-clipboard
- Q: How should deeply nested subagent calls be visualized? → A: Simplified/collapsible view after 3 levels of nesting
- Q: Should the app support offline mode? → A: No, requires live connection to Claude Agent API
- Q: How should the app handle multiple tabs/windows? → A: Each tab is independent, no cross-tab synchronization

## Assumptions

- Claude Agent API is available and running on port 54000
- PostgreSQL backend (port 53432) is available for session persistence
- Redis (port 53380) is available for caching
- Users have modern browsers supporting ES6+, SSE, and localStorage
- Users have valid API key for Claude Agent API
- File system access in Code mode is restricted to configured workspace base directory
- MCP servers expose tools via standard Model Context Protocol
- Network latency to API is under 100ms for optimal streaming experience
