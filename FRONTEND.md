# apps/web 

## Overview
Our web frontend serves as a comprehensive interface layer that seamlessly presents the Claude Agent Python SDK backend as a powerful agent management platform. Drawing inspiration from Google's Antigravity IDE workflow paradigm, the application is designed with a strong emphasis on multi-project orchestration and provides users with an intuitive, clean workspace for viewing, editing, and managing Claude Code agents, slash commands, skills, in addition to their code. The interface enables efficient code review workflows and empowers users to make quick, precise edits directly within the UI through the integration of PlateJS, creating a smooth and responsive developer experience that bridges the gap between AI-driven automation and hands-on code manipulation.



## Tech Stack
The frontend leverages a cohesive set of libraries from the AI SDK ecosystem:

- **AI SDK v6** - https://ai-sdk.dev/docs/introduction
- **AI Elements** - https://ai-sdk.dev/elements
- **Streamdown** - https://streamdown.ai/docs
- **AI SDK Custom Provider** - https://ai-sdk.dev/docs/reference/ai-sdk-core/custom-provider
- **PlateJS** - https://platejs.org/docs/getting-started

A custom AI SDK v6 provider bridges the frontend to our backend API (apps/api). AI Elements provides the complete UI component library, while Streamdown handles markdown rendering with native AI SDK support. PlateJS powers the rich text editing experience.

This unified stack ensures seamless integration and optimal compatibility across all components.

## UI/UX

### Layout
The UI is a multi-pane workspace where the sidebar, conversation, editor, and artifacts can be shown together or collapsed into simpler configurations. Users can resize panes to prioritize the workflow at hand.

**Pane Configurations**
- Sidebar + Conversation + Editor + Artifacts
- Collapsed Sidebar + Conversation + Editor + Artifacts
- Collapsed Sidebar + Conversation + Editor
- Collapsed Sidebar + Conversation

### Sidebar Structure
The sidebar is organized into vertically stacked sections with clear visual dividers:

**Top Section**
- Inbox header
- Primary "Start conversation" action

**Workspaces**
- Collapsible workspace groups, each containing:
  - Chevron toggle
  - Workspace label
  - Inline add button for creating new sessions
- "Open Workspace" action below the list

**Playground**
- Recent playground chats displayed as pill-style rows
- Small status indicator on the right of each row

**Bottom Utility Navigation**
- Compact vertical list of shortcuts:
  - Agents
  - Editor
  - MCP
  - Plugins
  - Slash Commands
  - Skills

### Main Content Area
The main content area is split into resizable panes:

**Conversation**
- Primary chat timeline and input surface
- Uses the AI Elements Chain of Thought component for step-by-step reasoning display
- Supports quick reactions and inline status controls

**Editor**
- Dedicated pane for reviewing and making quick code edits
- PlateJS-backed rich text editing for structured content

**Artifacts**
- Supplemental pane presented as a list/outline for quickly hopping between plans, diffs, and other generated assets
- Optional and collapsible when the user wants a narrower layout

The conversation pane centers a "Start new conversation in [workspace]" panel featuring:

**Input Row**
- Context shortcuts
- Planning/model selectors (Haiku, Sonnet, Opus)
- Send controls

**Quick Actions**
- "Open editor" link
- "Use Playground" link

**Context Menu**
- Plus-triggered dropdown beneath the input
- Options include:
  - Files
  - Images
  - Agents
  - Slash Commands
  - Skills
  - Tools (MCP)

### Inbox View
The inbox is a dedicated view for scanning and managing conversations.

- Dedicated inbox header with a pending toggle to filter active items
- Search field for conversations
- "Start conversation" action aligned to the right
- Conversation list entries show workspace context, timestamps, and status badges (e.g., Running, Idle)
