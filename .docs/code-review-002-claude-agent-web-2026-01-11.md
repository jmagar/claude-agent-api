# Code Review Report: Claude Agent Web Interface (002-claude-agent-web)

**Date:** January 11, 2026
**Branch:** `002-claude-agent-web`
**Review Type:** Comprehensive Multi-Agent Parallel Review
**Reviewers:** 19 Specialized Code Review Agents
**Spec Version:** As of January 11, 2026

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Review Methodology](#review-methodology)
3. [Overall Assessment](#overall-assessment)
4. [Critical Issues (P0)](#critical-issues-p0)
5. [Important Issues (P1)](#important-issues-p1)
6. [Test Coverage Gaps (P2)](#test-coverage-gaps-p2)
7. [Detailed Findings by Area](#detailed-findings-by-area)
8. [Compliance Matrix](#compliance-matrix)
9. [Recommendations](#recommendations)
10. [Effort Estimates](#effort-estimates)

---

## Executive Summary

### Overview
A comprehensive code review was conducted on the Claude Agent Web Interface implementation using 19 parallelized specialized review agents. Each agent examined specific aspects of the implementation against the complete specification artifacts.

### Key Metrics
- **Overall Production Readiness:** 75%
- **Spec Compliance:** ~70% (estimated)
- **Critical Issues:** 10 (P0 - Must Fix)
- **Important Issues:** 9 (P1 - Should Fix)
- **Test Coverage:** Backend 85%, E2E 8%
- **Accessibility Compliance:** Partial (WCAG AA violations present)
- **Mobile Responsiveness:** 5% (critical gap)

### Verdict
**The implementation has strong technical foundations but requires significant work in 4 critical areas before production deployment:**

1. **Rich Text Editing** - PlateJS completely absent despite being core requirement
2. **Mobile-First Design** - Only 5% of components are responsive
3. **E2E Test Coverage** - 8% user story coverage (1/12 stories)
4. **Missing Core Context** - ActiveSessionContext not implemented

### Strengths
✅ Excellent TypeScript type safety and strict mode compliance
✅ Robust component architecture with proper separation of concerns
✅ Comprehensive backend API integration test coverage (85%)
✅ Proper SSE streaming implementation with EventSource
✅ Well-structured TanStack Query usage for server state
✅ Good error handling patterns
✅ Proper use of React Query for caching and optimistic updates (where implemented)

### Weaknesses
❌ PlateJS rich text editor missing entirely (affects 30+ requirements)
❌ Mobile-first responsive design not implemented (5% compliance)
❌ E2E test coverage severely lacking (8% vs. required 80%+)
❌ Missing critical contexts (ActiveSessionContext, wrong SettingsContext structure)
❌ Query key factory pattern not implemented
❌ Accessibility violations (focus trap, color contrast)
❌ No optimistic updates on mutations
❌ SSE retry logic missing exponential backoff

---

## Review Methodology

### Specification Artifacts Reviewed
1. `/mnt/cache/workspace/claude-agent-api/specs/002-claude-agent-web/data-model.md` - TypeScript types, Zod schemas, database entities, query keys factory
2. `/mnt/cache/workspace/claude-agent-api/specs/002-claude-agent-web/spec.md` - User stories, functional requirements, success criteria
3. `/mnt/cache/workspace/claude-agent-api/specs/002-claude-agent-web/contracts/openapi-extensions.yaml` - API contract definitions
4. `/mnt/cache/workspace/claude-agent-api/specs/002-claude-agent-web/research.md` - Technology decisions and patterns
5. `/mnt/cache/workspace/claude-agent-api/specs/002-claude-agent-web/plan.md` - Implementation plan and phases

### Review Agents Deployed
19 specialized code review agents were deployed in parallel, each focused on a specific area:

| Agent ID | Focus Area | Status | Issues Found |
|----------|------------|--------|--------------|
| 1 | Core Types & Schemas | ✅ Complete | 8 critical, 3 important |
| 2 | API Routes Compliance | ✅ Complete | 4 critical, 6 important |
| 3 | Chat Interface Components | ✅ Complete | 5 critical, 8 important |
| 4 | Session Management | ✅ Complete | 6 critical, 4 important |
| 5 | Mode System | ✅ Complete | 3 critical, 2 important |
| 6 | Tool Management | ✅ Complete | 0 critical, 1 important |
| 7 | Autocomplete System | ✅ Complete | 2 critical, 4 important |
| 8 | MCP Server Management | ✅ Complete | 4 critical, 3 important |
| 9 | Configuration (Agents/Skills/Commands) | ✅ Complete | 12 critical, 5 important |
| 10 | Mobile Responsiveness | ✅ Complete | 18 critical, 0 important |
| 11 | Accessibility Compliance | ✅ Complete | 8 critical, 12 important |
| 12 | Performance Optimizations | ✅ Complete | 3 critical, 6 important |
| 13 | SSE Streaming | ✅ Complete | 2 critical, 1 important |
| 14 | React Query Integration | ✅ Complete | 4 critical, 3 important |
| 15 | Context Providers | ✅ Complete | 5 critical, 2 important |
| 16 | Integration Test Coverage | ✅ Complete | 0 critical, 3 important |
| 17 | E2E Test Coverage | ✅ Complete | 11 critical, 0 important |
| 18 | Tailwind Styling Consistency | ✅ Complete | 2 critical, 4 important |
| 19 | Coding Standards Compliance | ✅ Complete | 0 critical, 2 important |

**Total Issues Identified:** 97 critical, 69 important, 45 suggestions

---

## Overall Assessment

### What's Working Well

#### 1. **Type Safety (95% Compliant)**
- Strict TypeScript mode properly configured
- Comprehensive type coverage across components
- Proper use of discriminated unions for event types
- No `any` types found in reviewed code
- Zod schemas properly integrated with TypeScript types

**Example - Excellent Type Safety:**
```typescript
// apps/web/types/index.ts
export type ChatEvent =
  | { type: 'message'; role: 'user' | 'assistant'; content: string }
  | { type: 'tool_call'; toolName: string; status: 'pending' | 'approved' | 'rejected' }
  | { type: 'error'; message: string; code?: string };
```

#### 2. **Component Architecture (85% Compliant)**
- Proper separation of concerns (UI vs. logic)
- Custom hooks for reusable logic
- Context providers for global state
- Compound component patterns where appropriate

**Example - Well-Structured Hook:**
```typescript
// apps/web/hooks/useSessions.ts
export function useSessions() {
  return useQuery({
    queryKey: ['sessions'],
    queryFn: fetchSessions,
    staleTime: 1000 * 60 * 5,
  });
}
```

#### 3. **Backend Integration (85% Test Coverage)**
- Comprehensive integration tests for all API routes
- Proper error handling and validation
- Good use of React Query for server state
- SSE streaming properly implemented

**Example - Excellent Test Coverage:**
```python
# tests/integration/test_sessions.py
def test_create_session(client):
    response = client.post("/api/sessions", json={"name": "Test Session"})
    assert response.status_code == 201
    assert response.json()["name"] == "Test Session"
```

#### 4. **Tool Management (100% Compliant)**
- ToolManagementModal fully implements FR-016 through FR-022
- Proper permission mode toggle (auto/manual)
- Clean UI with good UX patterns
- Proper state management

### What Needs Critical Attention

#### 1. **PlateJS Missing Entirely (0% Implemented)**
**Impact:** Affects 6 user stories and 30+ functional requirements

The specification explicitly requires PlateJS rich text editor for:
- Agent system prompt editing (US8, FR-055)
- Skill content editing (US9, FR-061)
- MCP server configuration (US10, FR-067)
- Slash command editing (US11)
- Artifact rendering (US12, FR-042)

**Current Implementation:** All editors use basic `<textarea>` elements

**Spec Quote (data-model.md):**
> "PlateJS is used for rich text editing of agent prompts, skill content, and MCP server configurations. It provides syntax highlighting, autocompletion, and markdown support."

**Decision Required:** Either:
1. Implement PlateJS across all specified editors (Est. 2-3 weeks)
2. Formally update spec to remove PlateJS requirement

#### 2. **Mobile-First Design Not Implemented (5% Compliant)**
**Impact:** Application is unusable on mobile devices

Only 5 out of 90+ components use responsive Tailwind breakpoints. The implementation is desktop-first, violating the core requirement for mobile-first responsive design.

**Spec Quote (spec.md):**
> "FR-087: Mobile-first responsive design with breakpoints at 320px, 768px, 1024px, 1440px"

**Current State:**
```typescript
// ❌ Current (desktop-only)
<div className="w-64 h-screen">

// ✅ Required (mobile-first)
<div className="w-full md:w-64 h-screen">
```

**Files Requiring Responsive Refactor:** 90+ components

#### 3. **E2E Test Coverage Critically Low (8%)**
**Impact:** High risk of regressions, poor quality assurance

Only 1 of 12 user stories has E2E test coverage:
- ✅ US1: Chat Input (chat-input.spec.ts)
- ❌ US2: Session Management (missing)
- ❌ US3: Mode Switching (missing)
- ❌ US4: Tool Approval (missing)
- ❌ US5: Session Sharing (missing)
- ❌ US6: MCP Management (missing)
- ❌ US7: Settings (missing)
- ❌ US8: Agents (missing)
- ❌ US9: Skills (missing)
- ❌ US10: MCP Servers (missing)
- ❌ US11: Slash Commands (missing)
- ❌ US12: Artifacts (missing)

**Additional Gaps:**
- No mobile viewport tests (320px, 375px, 414px)
- No accessibility tests (`@axe-core/playwright` not installed)
- No performance tests (LCP, FID, CLS)
- No SSE streaming tests

#### 4. **Missing Core Contexts**
**Impact:** Broken state management, scattered logic

**Missing:**
- `ActiveSessionContext` - Completely absent despite spec requirement
- `ModeProvider` - Exists but not in app layout
- `PermissionsProvider` - Not in app layout

**Wrong Structure:**
- `SettingsContext` - Uses single `updateSettings()` instead of individual setters per spec

---

## Critical Issues (P0)

### P0-001: PlateJS Rich Text Editor Missing
**Severity:** 🔴 CRITICAL
**Effort:** 2-3 weeks
**Impact:** 6 user stories, 30+ functional requirements

#### Description
The specification explicitly requires PlateJS for rich text editing across multiple areas, but the implementation uses basic HTML `<textarea>` elements everywhere.

#### Affected Requirements
- **FR-055:** Agent system prompt editing with syntax highlighting
- **FR-061:** Skill content editing with markdown support
- **FR-067:** MCP server configuration editing
- **FR-042:** Artifact rendering with rich text
- **FR-093:** YAML frontmatter editing with validation
- **FR-094:** Markdown content editing with preview

#### Files Affected
- `apps/web/components/settings/agents/AgentForm.tsx` (line 89)
- `apps/web/components/settings/skills/SkillEditor.tsx` (line 112)
- `apps/web/components/settings/mcp/McpConfigEditor.tsx` (line 67)
- `apps/web/components/chat/ArtifactRenderer.tsx` (line 45)

#### Current Implementation
```typescript
// apps/web/components/settings/agents/AgentForm.tsx:89
<textarea
  value={systemPrompt}
  onChange={(e) => setSystemPrompt(e.target.value)}
  className="w-full h-64 p-2 border rounded"
/>
```

#### Required Implementation
```typescript
import { Plate, PlateContent } from '@udecode/plate-common';
import { createYamlPlugin } from '@udecode/plate-yaml';
import { createMarkdownPlugin } from '@udecode/plate-markdown';

<Plate
  plugins={[
    createYamlPlugin(),
    createMarkdownPlugin(),
  ]}
  initialValue={initialValue}
  onChange={handleChange}
>
  <PlateContent
    className="min-h-[16rem] p-4 border rounded-md"
    placeholder="Enter system prompt..."
  />
</Plate>
```

#### Recommendation
**DECISION REQUIRED:** Implement PlateJS OR update spec to remove this requirement.

If implementing:
1. Install dependencies: `pnpm add @udecode/plate-common @udecode/plate-yaml @udecode/plate-markdown`
2. Create shared `<RichTextEditor>` component
3. Refactor all affected forms to use new component
4. Add unit tests for editor behavior
5. Add E2E tests for YAML validation and markdown rendering

---

### P0-002: ActiveSessionContext Missing
**Severity:** 🔴 CRITICAL
**Effort:** 3-5 days
**Impact:** Session management broken, scattered state logic

#### Description
The `ActiveSessionContext` specified in `data-model.md` Section 6.3 is completely missing from the implementation. This context should manage the currently active chat session state.

#### Spec Requirement (data-model.md Section 6.3)
```typescript
interface ActiveSessionContextType {
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
  messages: Message[];
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  isStreaming: boolean;
  setIsStreaming: (streaming: boolean) => void;
}
```

#### Current State
**File does not exist:** `apps/web/contexts/ActiveSessionContext.tsx`

Session state is currently scattered across:
- `ChatInterface.tsx` (local state)
- `useStreamMessages.ts` (hook-level state)
- URL params (partial state)

#### Impact
- No centralized session state management
- Cannot properly track active session across app
- Session switching logic is brittle
- Difficult to implement session persistence
- Cannot properly handle concurrent session operations

#### Implementation Required
```typescript
// apps/web/contexts/ActiveSessionContext.tsx
'use client';

import { createContext, useContext, useState, useCallback } from 'react';
import type { Message } from '@/types';

interface ActiveSessionContextType {
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
  messages: Message[];
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  isStreaming: boolean;
  setIsStreaming: (streaming: boolean) => void;
}

const ActiveSessionContext = createContext<ActiveSessionContextType | null>(null);

export function ActiveSessionProvider({ children }: { children: React.ReactNode }) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const addMessage = useCallback((message: Message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return (
    <ActiveSessionContext.Provider
      value={{
        sessionId,
        setSessionId,
        messages,
        addMessage,
        clearMessages,
        isStreaming,
        setIsStreaming,
      }}
    >
      {children}
    </ActiveSessionContext.Provider>
  );
}

export function useActiveSession() {
  const context = useContext(ActiveSessionContext);
  if (!context) {
    throw new Error('useActiveSession must be used within ActiveSessionProvider');
  }
  return context;
}
```

#### Files to Update
1. Create `apps/web/contexts/ActiveSessionContext.tsx`
2. Update `apps/web/app/layout.tsx` to add provider
3. Refactor `apps/web/components/chat/ChatInterface.tsx` to use context
4. Refactor `apps/web/hooks/useStreamMessages.ts` to use context
5. Update `apps/web/components/sidebar/SessionSidebar.tsx` to use context

---

### P0-003: Query Key Factory Pattern Not Implemented
**Severity:** 🔴 CRITICAL
**Effort:** 1 week
**Impact:** Cache invalidation bugs, performance issues

#### Description
The specification defines a comprehensive query key factory pattern in `data-model.md` Section 4, but the implementation uses hardcoded query key strings throughout.

#### Spec Requirement (data-model.md Section 4)
```typescript
export const sessionKeys = {
  all: ['sessions'] as const,
  lists: () => [...sessionKeys.all, 'list'] as const,
  list: (filters: SessionFilters) => [...sessionKeys.lists(), filters] as const,
  details: () => [...sessionKeys.all, 'detail'] as const,
  detail: (id: string) => [...sessionKeys.details(), id] as const,
  messages: (id: string) => [...sessionKeys.detail(id), 'messages'] as const,
};
```

#### Current Implementation (Wrong)
```typescript
// apps/web/hooks/useSessions.ts
export function useSessions() {
  return useQuery({
    queryKey: ['sessions'], // ❌ Hardcoded string
    queryFn: fetchSessions,
  });
}

export function useSession(id: string) {
  return useQuery({
    queryKey: ['session', id], // ❌ Hardcoded array
    queryFn: () => fetchSession(id),
  });
}
```

#### Required Implementation
```typescript
// apps/web/lib/query-keys.ts
export const sessionKeys = {
  all: ['sessions'] as const,
  lists: () => [...sessionKeys.all, 'list'] as const,
  list: (filters: SessionFilters) => [...sessionKeys.lists(), filters] as const,
  details: () => [...sessionKeys.all, 'detail'] as const,
  detail: (id: string) => [...sessionKeys.details(), id] as const,
  messages: (id: string) => [...sessionKeys.detail(id), 'messages'] as const,
};

export const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: (filters: ProjectFilters) => [...projectKeys.lists(), filters] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: string) => [...projectKeys.details(), id] as const,
};

export const agentKeys = {
  all: ['agents'] as const,
  lists: () => [...agentKeys.all, 'list'] as const,
  list: (filters: AgentFilters) => [...agentKeys.lists(), filters] as const,
  details: () => [...agentKeys.all, 'detail'] as const,
  detail: (id: string) => [...agentKeys.details(), id] as const,
};

// ... similar for skills, mcpServers, slashCommands
```

#### Files to Update
1. Create `apps/web/lib/query-keys.ts`
2. Refactor all hooks in `apps/web/hooks/`:
   - `useSessions.ts`
   - `useProjects.ts`
   - `useAgents.ts`
   - `useSkills.ts`
   - `useMcpServers.ts`
   - `useSlashCommands.ts`
3. Update mutation invalidation calls to use factory keys

#### Benefits
- Type-safe query keys
- Centralized cache management
- Easier cache invalidation
- Better performance through precise invalidation
- Prevents cache-related bugs

---

### P0-004: Mobile-First Responsive Design Missing
**Severity:** 🔴 CRITICAL
**Effort:** 3-4 weeks
**Impact:** Application unusable on mobile devices

#### Description
Only 5% of components implement mobile-first responsive design. The implementation is desktop-first, violating FR-087 requirement for mobile-first design with specific breakpoints.

#### Spec Requirement (spec.md FR-087)
> "Mobile-first responsive design with breakpoints at 320px (mobile), 768px (tablet), 1024px (desktop), 1440px (large desktop)"

#### Statistics
- **Total Components:** 93
- **Responsive Components:** 5 (5%)
- **Desktop-Only Components:** 88 (95%)

#### Examples of Non-Responsive Components

**ChatInterface.tsx:**
```typescript
// ❌ Current (desktop-only)
<div className="flex h-screen">
  <SessionSidebar className="w-64" />
  <main className="flex-1">
    <ChatMessages />
    <Composer className="h-20" />
  </main>
</div>

// ✅ Required (mobile-first)
<div className="flex flex-col md:flex-row h-screen">
  <SessionSidebar className="w-full md:w-64 h-16 md:h-screen" />
  <main className="flex-1 flex flex-col">
    <ChatMessages className="flex-1" />
    <Composer className="h-20 md:h-24" />
  </main>
</div>
```

**ToolManagementModal.tsx:**
```typescript
// ❌ Current (desktop-only)
<Dialog.Content className="max-w-2xl p-6">

// ✅ Required (mobile-first)
<Dialog.Content className="w-full max-w-full md:max-w-2xl p-4 md:p-6 h-screen md:h-auto">
```

**SessionSidebar.tsx:**
```typescript
// ❌ Current (always visible)
<aside className="w-64 border-r">

// ✅ Required (collapsible on mobile)
<aside className={cn(
  "fixed md:relative inset-0 md:inset-auto z-50 md:z-auto",
  "w-full md:w-64 border-r",
  "transform transition-transform",
  isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
)}>
```

#### Files Requiring Responsive Refactor
**High Priority (User-Facing):**
- `apps/web/components/chat/ChatInterface.tsx`
- `apps/web/components/chat/Composer.tsx`
- `apps/web/components/chat/MessageList.tsx`
- `apps/web/components/sidebar/SessionSidebar.tsx`
- `apps/web/components/modals/ToolManagementModal.tsx`
- `apps/web/components/modals/SessionShareModal.tsx`

**Medium Priority (Settings):**
- `apps/web/components/settings/agents/AgentList.tsx`
- `apps/web/components/settings/skills/SkillList.tsx`
- `apps/web/components/settings/mcp/McpServerList.tsx`

**Low Priority (Secondary UI):**
- All other components in `apps/web/components/`

#### Implementation Strategy
1. **Phase 1 (Week 1):** Core chat interface (ChatInterface, Composer, MessageList)
2. **Phase 2 (Week 2):** Sidebars and navigation (SessionSidebar, SettingsSidebar)
3. **Phase 3 (Week 3):** Modals and overlays (all modal components)
4. **Phase 4 (Week 4):** Settings and configuration screens

#### Testing Requirements
- Add E2E tests for 320px, 375px, 414px viewports
- Test touch targets (minimum 44px)
- Test swipe gestures for sidebar
- Test orientation changes

---

### P0-005: Focus Trap Missing in Modals
**Severity:** 🔴 CRITICAL
**Effort:** 2-3 days
**Impact:** WCAG AA violation, keyboard accessibility broken

#### Description
Modal components do not implement focus trapping, violating FR-073 (keyboard navigation) and WCAG 2.1 AA requirements.

#### Spec Requirement (spec.md FR-073)
> "Keyboard navigation support with focus management and focus trapping in modals"

#### Affected Files
- `apps/web/components/modals/ToolManagementModal.tsx`
- `apps/web/components/modals/SessionShareModal.tsx`
- `apps/web/components/modals/AgentFormModal.tsx`
- `apps/web/components/modals/SkillFormModal.tsx`
- `apps/web/components/modals/McpServerFormModal.tsx`

#### Current Implementation (Wrong)
```typescript
// apps/web/components/modals/ToolManagementModal.tsx
<Dialog.Portal>
  <Dialog.Overlay className="fixed inset-0 bg-black/50" />
  <Dialog.Content className="fixed top-1/2 left-1/2 ...">
    {/* modal content - keyboard focus can escape */}
  </Dialog.Content>
</Dialog.Portal>
```

#### Required Implementation
```typescript
import FocusTrap from 'focus-trap-react';

<Dialog.Portal>
  <Dialog.Overlay className="fixed inset-0 bg-black/50" />
  <FocusTrap>
    <Dialog.Content className="fixed top-1/2 left-1/2 ...">
      {/* modal content - keyboard focus trapped */}
    </Dialog.Content>
  </FocusTrap>
</Dialog.Portal>
```

#### Installation Required
```bash
pnpm add focus-trap-react
```

#### Testing Requirements
1. Open modal with keyboard (Enter/Space)
2. Tab through all focusable elements
3. Verify focus stays within modal
4. Verify Escape key closes modal
5. Verify focus returns to trigger element on close

---

### P0-006: Color Contrast Violations (WCAG AA)
**Severity:** 🔴 CRITICAL
**Effort:** 1 week
**Impact:** Legal compliance, accessibility requirements

#### Description
Multiple components use colors with insufficient contrast ratios, violating WCAG 2.1 AA requirements (4.5:1 for normal text, 3:1 for large text).

#### Violations Found

| Color Combination | Current Ratio | Required | Usage Count |
|-------------------|---------------|----------|-------------|
| `text-gray-400` on white | 2.8:1 | 4.5:1 | 32 components |
| `text-gray-300` on white | 1.9:1 | 4.5:1 | 18 components |
| `text-gray-500` on gray-100 | 3.2:1 | 4.5:1 | 15 components |
| `text-blue-400` on white | 4.1:1 | 4.5:1 | 8 components |

#### Files with Violations
```typescript
// ❌ apps/web/components/chat/MessageItem.tsx:45
<span className="text-gray-400 text-sm">
  {timestamp}
</span>

// ❌ apps/web/components/sidebar/SessionSidebar.tsx:67
<p className="text-gray-300 text-xs">
  Last active: {lastActive}
</p>

// ❌ apps/web/components/shared/ToolStatus.tsx:23
<span className="text-gray-500 bg-gray-100">
  Pending
</span>
```

#### Required Fixes
```typescript
// ✅ Fix 1: Use darker gray for text
<span className="text-gray-600 text-sm">
  {timestamp}
</span>

// ✅ Fix 2: Use darker gray for secondary text
<p className="text-gray-700 text-xs">
  Last active: {lastActive}
</p>

// ✅ Fix 3: Adjust background or text color
<span className="text-gray-700 bg-gray-100">
  Pending
</span>
```

#### Automated Testing
```typescript
// tests/e2e/accessibility.spec.ts
import AxeBuilder from '@axe-core/playwright';

test('should not have color contrast violations', async ({ page }) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2aa'])
    .analyze();

  expect(results.violations).toHaveLength(0);
});
```

#### Installation Required
```bash
pnpm add -D @axe-core/playwright
```

---

### P0-007: SettingsContext Wrong Structure
**Severity:** 🔴 CRITICAL
**Effort:** 2-3 days
**Impact:** Settings management broken, wrong API surface

#### Description
`SettingsContext` implementation uses a single `updateSettings()` method instead of individual setter methods as specified in `data-model.md`.

#### Spec Requirement (data-model.md Section 6.2)
```typescript
interface SettingsContextType {
  settings: UISettings;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setFontSize: (size: number) => void;
  setCodeTheme: (theme: string) => void;
  toggleSidebarCollapsed: () => void;
  toggleAutoScrollEnabled: () => void;
  toggleSendOnEnter: () => void;
  toggleShowTimestamps: () => void;
  toggleShowLineNumbers: () => void;
}
```

#### Current Implementation (Wrong)
```typescript
// apps/web/contexts/SettingsContext.tsx
interface SettingsContextType {
  settings: UISettings;
  updateSettings: (settings: Partial<UISettings>) => void; // ❌ Wrong
}
```

#### Required Implementation
```typescript
// apps/web/contexts/SettingsContext.tsx
'use client';

import { createContext, useContext, useState, useCallback } from 'react';
import type { UISettings } from '@/types';

interface SettingsContextType {
  settings: UISettings;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setFontSize: (size: number) => void;
  setCodeTheme: (theme: string) => void;
  toggleSidebarCollapsed: () => void;
  toggleAutoScrollEnabled: () => void;
  toggleSendOnEnter: () => void;
  toggleShowTimestamps: () => void;
  toggleShowLineNumbers: () => void;
}

const SettingsContext = createContext<SettingsContextType | null>(null);

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<UISettings>({
    theme: 'system',
    fontSize: 14,
    codeTheme: 'github-dark',
    sidebarCollapsed: false,
    autoScrollEnabled: true,
    sendOnEnter: true,
    showTimestamps: true,
    showLineNumbers: true,
  });

  const setTheme = useCallback((theme: 'light' | 'dark' | 'system') => {
    setSettings((prev) => ({ ...prev, theme }));
  }, []);

  const setFontSize = useCallback((fontSize: number) => {
    setSettings((prev) => ({ ...prev, fontSize }));
  }, []);

  const setCodeTheme = useCallback((codeTheme: string) => {
    setSettings((prev) => ({ ...prev, codeTheme }));
  }, []);

  const toggleSidebarCollapsed = useCallback(() => {
    setSettings((prev) => ({ ...prev, sidebarCollapsed: !prev.sidebarCollapsed }));
  }, []);

  const toggleAutoScrollEnabled = useCallback(() => {
    setSettings((prev) => ({ ...prev, autoScrollEnabled: !prev.autoScrollEnabled }));
  }, []);

  const toggleSendOnEnter = useCallback(() => {
    setSettings((prev) => ({ ...prev, sendOnEnter: !prev.sendOnEnter }));
  }, []);

  const toggleShowTimestamps = useCallback(() => {
    setSettings((prev) => ({ ...prev, showTimestamps: !prev.showTimestamps }));
  }, []);

  const toggleShowLineNumbers = useCallback(() => {
    setSettings((prev) => ({ ...prev, showLineNumbers: !prev.showLineNumbers }));
  }, []);

  return (
    <SettingsContext.Provider
      value={{
        settings,
        setTheme,
        setFontSize,
        setCodeTheme,
        toggleSidebarCollapsed,
        toggleAutoScrollEnabled,
        toggleSendOnEnter,
        toggleShowTimestamps,
        toggleShowLineNumbers,
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within SettingsProvider');
  }
  return context;
}
```

#### Files to Update
1. Refactor `apps/web/contexts/SettingsContext.tsx` (complete rewrite)
2. Update `apps/web/components/settings/GeneralSettings.tsx` to use new API
3. Update any components using `updateSettings()` to use specific setters

---

### P0-008: SSE Retry Logic Missing Exponential Backoff
**Severity:** 🔴 CRITICAL
**Effort:** 2-3 days
**Impact:** Poor UX during network issues, connection storms

#### Description
SSE streaming implementation does not include exponential backoff retry logic as specified in `research.md`.

#### Spec Requirement (research.md - SSE Pattern)
> "Implement exponential backoff with jitter for SSE reconnection: 100ms → 200ms → 400ms → 800ms → ... → max 30s"

#### Current Implementation (Wrong)
```typescript
// apps/web/hooks/useStreamMessages.ts
export function useStreamMessages(sessionId: string) {
  useEffect(() => {
    const eventSource = new EventSource(`/api/sessions/${sessionId}/stream`);

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
      // ❌ No retry logic
    };

    return () => eventSource.close();
  }, [sessionId]);
}
```

#### Required Implementation
```typescript
// apps/web/hooks/useStreamMessages.ts
import { useEffect, useRef, useState } from 'react';

interface RetryConfig {
  initialDelay: number;
  maxDelay: number;
  maxAttempts: number;
  backoffFactor: number;
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  initialDelay: 100,
  maxDelay: 30000,
  maxAttempts: 10,
  backoffFactor: 2,
};

export function useStreamMessages(sessionId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const retryCountRef = useRef(0);
  const retryTimeoutRef = useRef<NodeJS.Timeout>();
  const eventSourceRef = useRef<EventSource>();

  const connect = useCallback(() => {
    const eventSource = new EventSource(`/api/sessions/${sessionId}/stream`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      retryCountRef.current = 0; // Reset retry count on successful connection
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
      setIsConnected(false);

      // Calculate exponential backoff with jitter
      const baseDelay = Math.min(
        DEFAULT_RETRY_CONFIG.initialDelay * Math.pow(DEFAULT_RETRY_CONFIG.backoffFactor, retryCountRef.current),
        DEFAULT_RETRY_CONFIG.maxDelay
      );
      const jitter = Math.random() * 0.3 * baseDelay; // 30% jitter
      const delay = baseDelay + jitter;

      if (retryCountRef.current < DEFAULT_RETRY_CONFIG.maxAttempts) {
        console.log(`Retrying SSE connection in ${delay}ms (attempt ${retryCountRef.current + 1})`);
        retryTimeoutRef.current = setTimeout(() => {
          retryCountRef.current++;
          connect();
        }, delay);
      } else {
        console.error('Max retry attempts reached');
      }
    };

    eventSource.onmessage = (event) => {
      // Handle message
    };
  }, [sessionId]);

  useEffect(() => {
    connect();

    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [connect]);

  return { isConnected };
}
```

#### Testing Requirements
1. Simulate network failures in E2E tests
2. Verify exponential backoff timing
3. Verify jitter randomization
4. Verify max attempts limit
5. Verify connection reset on success

---

### P0-009: SubagentCard Not Integrated in Message Flow
**Severity:** 🔴 CRITICAL
**Effort:** 1-2 days
**Impact:** Subagent events not visible to users

#### Description
`SubagentCard.tsx` component exists but is not integrated into the message rendering flow. Users cannot see subagent start/end events.

#### Spec Requirement (spec.md FR-041)
> "Display subagent execution with start/end markers and status indicators"

#### Current State
- ✅ `apps/web/components/chat/SubagentCard.tsx` exists
- ❌ Not imported or used in `MessageItem.tsx`
- ❌ Subagent events not rendered

#### Files to Update

**apps/web/components/chat/MessageItem.tsx:**
```typescript
import { SubagentCard } from './SubagentCard';

export function MessageItem({ event }: { event: ChatEvent }) {
  if (event.type === 'subagent_start') {
    return (
      <SubagentCard
        type="start"
        subagentType={event.subagentType}
        description={event.description}
        timestamp={event.timestamp}
      />
    );
  }

  if (event.type === 'subagent_end') {
    return (
      <SubagentCard
        type="end"
        subagentType={event.subagentType}
        status={event.status}
        summary={event.summary}
        timestamp={event.timestamp}
      />
    );
  }

  // ... existing message rendering
}
```

#### Testing Requirements
1. Add E2E test for subagent events
2. Verify start marker displays correctly
3. Verify end marker displays status
4. Verify timestamps are accurate

---

### P0-010: Missing Context Providers in App Layout
**Severity:** 🔴 CRITICAL
**Effort:** 1 day
**Impact:** Context features not available, runtime errors

#### Description
Required context providers are missing from the app layout, preventing features from working.

#### Missing Providers
- `ModeProvider` - Exists in codebase but not in layout
- `PermissionsProvider` - Missing entirely
- `ActiveSessionProvider` - Missing entirely (see P0-002)

#### Current Layout (Wrong)
```typescript
// apps/web/app/layout.tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <SettingsProvider>
            <QueryClientProvider client={queryClient}>
              {children}
            </QueryClientProvider>
          </SettingsProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
```

#### Required Layout
```typescript
// apps/web/app/layout.tsx
import { ModeProvider } from '@/contexts/ModeContext';
import { PermissionsProvider } from '@/contexts/PermissionsContext';
import { ActiveSessionProvider } from '@/contexts/ActiveSessionContext';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <SettingsProvider>
            <QueryClientProvider client={queryClient}>
              <ModeProvider>
                <PermissionsProvider>
                  <ActiveSessionProvider>
                    {children}
                  </ActiveSessionProvider>
                </PermissionsProvider>
              </ModeProvider>
            </QueryClientProvider>
          </SettingsProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
```

#### Files to Create
1. `apps/web/contexts/PermissionsContext.tsx` (new file)
2. `apps/web/contexts/ActiveSessionContext.tsx` (see P0-002)

#### Files to Update
1. `apps/web/app/layout.tsx` (add providers)

---

## Important Issues (P1)

### P1-001: Session Search/Filter Missing
**Severity:** 🟡 IMPORTANT
**Effort:** 3-4 days
**Impact:** Poor UX with many sessions

#### Description
FR-036 requires session list search and filtering, but not implemented.

#### Spec Requirement (spec.md FR-036)
> "Search and filter sessions by name, date, mode (brainstorm/code)"

#### Current Implementation
`SessionSidebar.tsx` displays all sessions without search or filtering.

#### Required Implementation
```typescript
// apps/web/components/sidebar/SessionSidebar.tsx
const [searchQuery, setSearchQuery] = useState('');
const [modeFilter, setModeFilter] = useState<'all' | 'brainstorm' | 'code'>('all');

const filteredSessions = sessions?.filter((session) => {
  const matchesSearch = session.name.toLowerCase().includes(searchQuery.toLowerCase());
  const matchesMode = modeFilter === 'all' || session.mode === modeFilter;
  return matchesSearch && matchesMode;
});

return (
  <aside>
    <input
      type="search"
      placeholder="Search sessions..."
      value={searchQuery}
      onChange={(e) => setSearchQuery(e.target.value)}
    />
    <select value={modeFilter} onChange={(e) => setModeFilter(e.target.value)}>
      <option value="all">All Modes</option>
      <option value="brainstorm">Brainstorm</option>
      <option value="code">Code</option>
    </select>
    {filteredSessions?.map((session) => (
      <SessionItem key={session.id} session={session} />
    ))}
  </aside>
);
```

---

### P1-002: CheckpointMarker Not Integrated
**Severity:** 🟡 IMPORTANT
**Effort:** 2-3 days
**Impact:** Checkpoint functionality not visible

#### Description
FR-037 requires checkpoint markers in message flow, but not implemented.

#### Spec Requirement (spec.md FR-037)
> "Display checkpoint markers with restore functionality"

#### Required Implementation
```typescript
// apps/web/components/chat/MessageItem.tsx
import { CheckpointMarker } from './CheckpointMarker';

if (event.type === 'checkpoint') {
  return (
    <CheckpointMarker
      checkpointId={event.checkpointId}
      label={event.label}
      canRestore={true}
      onRestore={() => handleRestore(event.checkpointId)}
    />
  );
}
```

---

### P1-003: No Optimistic Updates
**Severity:** 🟡 IMPORTANT
**Effort:** 1 week
**Impact:** Slow perceived performance

#### Description
No mutations implement optimistic updates despite spec requirement in `research.md`.

#### Spec Requirement (research.md - React Query Patterns)
> "Use optimistic updates for all mutations to improve perceived performance"

#### Current Implementation (Wrong)
```typescript
// apps/web/hooks/useSessions.ts
export function useCreateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createSession,
    onSuccess: () => {
      queryClient.invalidateQueries(['sessions']); // ❌ No optimistic update
    },
  });
}
```

#### Required Implementation
```typescript
export function useCreateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createSession,
    onMutate: async (newSession) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries(sessionKeys.lists());

      // Snapshot previous value
      const previous = queryClient.getQueryData(sessionKeys.lists());

      // Optimistically update
      queryClient.setQueryData(sessionKeys.lists(), (old: Session[]) => [
        ...old,
        { ...newSession, id: 'temp-id', createdAt: new Date().toISOString() },
      ]);

      return { previous };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previous) {
        queryClient.setQueryData(sessionKeys.lists(), context.previous);
      }
    },
    onSettled: () => {
      // Refetch after mutation
      queryClient.invalidateQueries(sessionKeys.lists());
    },
  });
}
```

#### Mutations Requiring Optimistic Updates
- `useCreateSession`
- `useUpdateSession`
- `useDeleteSession`
- `useCreateProject`
- `useUpdateProject`
- `useDeleteProject`
- `useCreateAgent`
- `useUpdateAgent`
- `useDeleteAgent`
- Similar for skills, MCP servers, slash commands

---

### P1-004: MessageContent Not Memoized
**Severity:** 🟡 IMPORTANT
**Effort:** 1-2 days
**Impact:** Performance degradation with large sessions

#### Description
`MessageContent.tsx` renders markdown but is not memoized, causing unnecessary re-renders.

#### Current Implementation
```typescript
// apps/web/components/chat/MessageContent.tsx
export function MessageContent({ content }: { content: string }) {
  return (
    <div className="prose">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
```

#### Required Implementation
```typescript
import { memo } from 'react';

export const MessageContent = memo(function MessageContent({
  content
}: {
  content: string
}) {
  return (
    <div className="prose">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
});
```

---

### P1-005: `/mcp connect` Command Missing
**Severity:** 🟡 IMPORTANT
**Effort:** 2-3 days
**Impact:** Cannot connect MCP servers via slash command

#### Description
FR-030 requires `/mcp connect <server>` command, not implemented.

#### Spec Requirement (spec.md FR-030)
> "Slash command: /mcp connect <server-name> to connect MCP server"

#### Required Implementation
1. Add command handler in `apps/web/lib/slash-commands.ts`
2. Add autocomplete for server names
3. Add UI feedback for connection status
4. Add error handling for connection failures

---

### P1-006: `@mcp-server-name` Autocomplete Missing
**Severity:** 🟡 IMPORTANT
**Effort:** 2-3 days
**Impact:** Cannot reference MCP servers in chat

#### Description
FR-031 requires `@mcp-server-name` autocomplete, not implemented.

#### Spec Requirement (spec.md FR-031)
> "Autocomplete: @mcp-server-name to reference MCP server in chat"

#### Required Implementation
```typescript
// apps/web/hooks/useAutocomplete.ts
if (trigger === '@') {
  const mcpServers = await fetchMcpServers();
  return mcpServers
    .filter(server => server.name.includes(query))
    .map(server => ({
      type: 'mcp_server',
      value: server.name,
      label: server.name,
      description: server.description,
    }));
}
```

---

### P1-007: Missing Autocomplete Entity Types
**Severity:** 🟡 IMPORTANT
**Effort:** 3-4 days
**Impact:** Incomplete autocomplete functionality

#### Description
Autocomplete system missing entity types: `mcp_tool`, `mcp_resource`, `preset`.

#### Spec Requirement (data-model.md Section 3.1)
```typescript
type AutocompleteEntityType =
  | 'file'
  | 'agent'
  | 'skill'
  | 'slash_command'
  | 'mcp_server'
  | 'mcp_tool'     // ❌ Missing
  | 'mcp_resource' // ❌ Missing
  | 'preset';      // ❌ Missing
```

#### Required Implementation
Add handlers in `useAutocomplete.ts` for:
1. `@mcp-server:tool-name` - MCP tool references
2. `@mcp-server:resource-uri` - MCP resource references
3. `/preset-name` - Saved presets

---

### P1-008: API Contract Violations
**Severity:** 🟡 IMPORTANT
**Effort:** 1-2 days
**Impact:** Client-server contract mismatch

#### Description
DELETE endpoints return 200 instead of 204 as specified in OpenAPI contract.

#### Violations

**DELETE /api/sessions/{id}:**
```typescript
// ❌ Current
return NextResponse.json({ success: true }); // 200

// ✅ Required
return new NextResponse(null, { status: 204 }); // 204 No Content
```

**Similar issues in:**
- DELETE /api/projects/{id}
- DELETE /api/agents/{id}
- DELETE /api/skills/{id}
- DELETE /api/mcp-servers/{id}
- DELETE /api/slash-commands/{id}

#### Additional Violations
Response schemas have extra `{ data: ... }` wrapper not in spec.

---

### P1-009: Missing Zod Schemas
**Severity:** 🟡 IMPORTANT
**Effort:** 1 day
**Impact:** No runtime validation for some API requests

#### Description
Missing Zod schemas for request validation:
- `CreateSessionRequestSchema`
- `CreateProjectRequestSchema`
- `UpdateSessionRequestSchema`
- `UpdateProjectRequestSchema`

#### Required Implementation
```typescript
// apps/web/lib/schemas/index.ts
import { z } from 'zod';

export const CreateSessionRequestSchema = z.object({
  name: z.string().min(1).max(255),
  mode: z.enum(['brainstorm', 'code']),
  projectId: z.string().uuid().optional(),
});

export const CreateProjectRequestSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  path: z.string().optional(),
});

// ... similar for Update schemas
```

---

## Test Coverage Gaps (P2)

### P2-001: E2E Test Coverage Critically Low
**Severity:** 🟠 IMPORTANT
**Effort:** 3-4 weeks
**Impact:** High risk of regressions

#### Current Coverage: 8% (1/12 user stories)

**Existing:**
- ✅ US1: Chat Input (`chat-input.spec.ts`)

**Missing:**
- ❌ US2: Session Management
- ❌ US3: Mode Switching
- ❌ US4: Tool Approval
- ❌ US5: Session Sharing
- ❌ US6: MCP Management
- ❌ US7: Settings
- ❌ US8: Agents
- ❌ US9: Skills
- ❌ US10: MCP Servers
- ❌ US11: Slash Commands
- ❌ US12: Artifacts

#### Required Test Files
```
tests/e2e/
├── chat-input.spec.ts         ✅ Exists
├── session-management.spec.ts ❌ Missing
├── mode-switching.spec.ts     ❌ Missing
├── tool-approval.spec.ts      ❌ Missing
├── session-sharing.spec.ts    ❌ Missing
├── mcp-management.spec.ts     ❌ Missing
├── settings.spec.ts           ❌ Missing
├── agents.spec.ts             ❌ Missing
├── skills.spec.ts             ❌ Missing
├── mcp-servers.spec.ts        ❌ Missing
├── slash-commands.spec.ts     ❌ Missing
└── artifacts.spec.ts          ❌ Missing
```

---

### P2-002: No Mobile Viewport Tests
**Severity:** 🟠 IMPORTANT
**Effort:** 1 week
**Impact:** Cannot verify mobile responsiveness

#### Required Mobile Tests
```typescript
// tests/e2e/mobile.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Mobile Responsiveness', () => {
  test.use({ viewport: { width: 320, height: 568 } }); // iPhone SE

  test('should display mobile layout', async ({ page }) => {
    await page.goto('/');

    // Sidebar should be hidden on mobile
    const sidebar = page.locator('[data-testid="session-sidebar"]');
    await expect(sidebar).toHaveClass(/hidden md:block/);

    // Composer should be full width
    const composer = page.locator('[data-testid="composer"]');
    await expect(composer).toHaveClass(/w-full/);
  });

  test('should support touch gestures', async ({ page }) => {
    await page.goto('/');

    // Swipe to open sidebar
    await page.touchscreen.swipe({ x: 0, y: 300 }, { x: 200, y: 300 });
    const sidebar = page.locator('[data-testid="session-sidebar"]');
    await expect(sidebar).toBeVisible();
  });

  test('should have minimum touch targets', async ({ page }) => {
    await page.goto('/');

    const buttons = page.locator('button');
    const count = await buttons.count();

    for (let i = 0; i < count; i++) {
      const box = await buttons.nth(i).boundingBox();
      expect(box?.height).toBeGreaterThanOrEqual(44); // Minimum 44px
      expect(box?.width).toBeGreaterThanOrEqual(44);
    }
  });
});
```

#### Viewports to Test
- 320px (iPhone SE)
- 375px (iPhone 12/13)
- 414px (iPhone 12/13 Pro Max)
- 768px (iPad)
- 1024px (iPad Pro)

---

### P2-003: No Accessibility Tests
**Severity:** 🟠 IMPORTANT
**Effort:** 1 week
**Impact:** Cannot verify WCAG AA compliance

#### Installation Required
```bash
pnpm add -D @axe-core/playwright
```

#### Required Test File
```typescript
// tests/e2e/accessibility.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility', () => {
  test('should not have WCAG AA violations on home page', async ({ page }) => {
    await page.goto('/');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    expect(results.violations).toHaveLength(0);
  });

  test('should not have color contrast violations', async ({ page }) => {
    await page.goto('/');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .include('.text-gray-400') // Known violation
      .analyze();

    expect(results.violations).toHaveLength(0);
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/');

    // Tab through all focusable elements
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();

    // Should be able to activate buttons with Enter/Space
    await page.keyboard.press('Enter');
  });

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a'])
      .analyze();

    expect(results.violations).toHaveLength(0);
  });
});
```

---

### P2-004: No Performance Tests
**Severity:** 🟠 IMPORTANT
**Effort:** 1 week
**Impact:** Cannot verify performance requirements

#### Required Test File
```typescript
// tests/e2e/performance.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Performance', () => {
  test('should meet Core Web Vitals thresholds', async ({ page }) => {
    await page.goto('/');

    const metrics = await page.evaluate(() => ({
      lcp: performance.getEntriesByType('largest-contentful-paint')[0],
      fid: performance.getEntriesByType('first-input')[0],
      cls: performance.getEntriesByType('layout-shift'),
    }));

    // LCP should be < 2.5s
    expect(metrics.lcp.renderTime).toBeLessThan(2500);

    // FID should be < 100ms
    if (metrics.fid) {
      expect(metrics.fid.processingStart - metrics.fid.startTime).toBeLessThan(100);
    }

    // CLS should be < 0.1
    const cls = metrics.cls.reduce((sum, entry) => sum + entry.value, 0);
    expect(cls).toBeLessThan(0.1);
  });

  test('should render large message lists efficiently', async ({ page }) => {
    // Create session with 1000 messages
    await page.goto('/');
    // ... create large session

    const startTime = Date.now();
    await page.locator('[data-testid="message-list"]').scrollIntoViewIfNeeded();
    const endTime = Date.now();

    // Should render in < 1s
    expect(endTime - startTime).toBeLessThan(1000);
  });

  test('should handle rapid typing without lag', async ({ page }) => {
    await page.goto('/');

    const composer = page.locator('[data-testid="composer"]');
    const text = 'The quick brown fox jumps over the lazy dog';

    const startTime = Date.now();
    await composer.type(text, { delay: 0 });
    const endTime = Date.now();

    // Should handle rapid typing (< 500ms for 44 chars)
    expect(endTime - startTime).toBeLessThan(500);
  });
});
```

---

## Detailed Findings by Area

### 1. Core Types & Schemas

**Files Reviewed:**
- `apps/web/types/index.ts`
- `apps/web/lib/schemas/index.ts`

**Critical Issues:**
1. `ActiveSessionContext` interface missing from types
2. Query key factory types not defined
3. Type mismatches between frontend and API contract

**Important Issues:**
1. Missing Zod schemas for some request types
2. Discriminated union types could be stricter

**Suggestions:**
1. Add JSDoc comments to complex types
2. Create branded types for IDs (e.g., `SessionId`, `ProjectId`)

**Compliance:**
- TypeScript strict mode: ✅ 100%
- Zod validation: ⚠️ 75%
- Type-API contract alignment: ⚠️ 85%

---

### 2. API Routes (BFF Layer)

**Files Reviewed:**
- `apps/web/app/api/sessions/route.ts`
- `apps/web/app/api/projects/route.ts`
- `apps/web/app/api/agents/route.ts`
- `apps/web/app/api/skills/route.ts`
- `apps/web/app/api/mcp-servers/route.ts`
- `apps/web/app/api/slash-commands/route.ts`

**Critical Issues:**
1. DELETE endpoints return 200 instead of 204
2. Response schemas have extra wrapper layer
3. Error handling inconsistent across routes

**Important Issues:**
1. Missing input validation on some endpoints
2. No rate limiting
3. No request logging

**Suggestions:**
1. Extract common middleware
2. Add OpenAPI JSDoc comments
3. Implement request/response logging

**Compliance:**
- OpenAPI contract: ⚠️ 85%
- Error handling: ✅ 90%
- Input validation: ⚠️ 80%

---

### 3. Chat Interface Components

**Files Reviewed:**
- `apps/web/components/chat/ChatInterface.tsx`
- `apps/web/components/chat/MessageList.tsx`
- `apps/web/components/chat/MessageItem.tsx`
- `apps/web/components/chat/Composer.tsx`
- `apps/web/components/chat/ToolCallCard.tsx`
- `apps/web/components/chat/SubagentCard.tsx`

**Critical Issues:**
1. Not mobile-responsive (desktop-only)
2. SubagentCard not integrated in message flow
3. MessageContent not memoized (performance)
4. No virtualization config (using defaults)

**Important Issues:**
1. No loading skeletons
2. No empty state messaging
3. Timestamps not configurable

**Suggestions:**
1. Add keyboard shortcuts (Cmd+K for search)
2. Add message reactions
3. Add export chat feature

**Compliance:**
- Message rendering: ✅ 95%
- Tool call display: ✅ 100%
- Subagent display: ❌ 0% (not integrated)
- Performance: ⚠️ 70%
- Accessibility: ⚠️ 60%

---

### 4. Session Management

**Files Reviewed:**
- `apps/web/components/sidebar/SessionSidebar.tsx`
- `apps/web/hooks/useSessions.ts`
- `apps/web/app/api/sessions/route.ts`

**Critical Issues:**
1. No search/filter functionality (FR-036)
2. CheckpointMarker not integrated (FR-037)
3. No session sorting options

**Important Issues:**
1. No session export functionality
2. No session archiving
3. No session templates

**Suggestions:**
1. Add session tags
2. Add session favorites
3. Add session analytics

**Compliance:**
- Create session: ✅ 100%
- List sessions: ✅ 100%
- Update session: ✅ 100%
- Delete session: ✅ 100%
- Search/filter: ❌ 0%
- Checkpoints: ❌ 0%

---

### 5. Mode System

**Files Reviewed:**
- `apps/web/contexts/ModeContext.tsx`
- `apps/web/components/sidebar/ModeToggle.tsx`

**Critical Issues:**
1. ModeProvider not in app layout
2. Filesystem access not implemented for code mode
3. No mode-specific features implemented

**Important Issues:**
1. No mode persistence across sessions
2. No mode-specific UI changes
3. No mode documentation

**Suggestions:**
1. Add mode tooltips explaining differences
2. Add mode-specific keyboard shortcuts
3. Add mode analytics

**Compliance:**
- Mode toggle: ✅ 100%
- Mode context: ⚠️ 80%
- Mode-specific features: ❌ 0%

**Note:** ModeContext exists but is not documented in spec. Need clarification on whether this is intentional or should be added to spec.

---

### 6. Tool Management

**Files Reviewed:**
- `apps/web/components/modals/ToolManagementModal.tsx`
- `apps/web/components/shared/PermissionsChip.tsx`

**Critical Issues:**
None! This is the best-implemented feature.

**Important Issues:**
1. No tool usage analytics

**Suggestions:**
1. Add tool favorites
2. Add tool search
3. Add tool categories

**Compliance:**
- Tool list: ✅ 100%
- Permission toggle: ✅ 100%
- Tool approval: ✅ 100%
- Tool rejection: ✅ 100%
- Manual mode: ✅ 100%
- Auto mode: ✅ 100%

---

### 7. Autocomplete System

**Files Reviewed:**
- `apps/web/hooks/useAutocomplete.ts`
- `apps/web/components/autocomplete/AutocompleteMenu.tsx`

**Critical Issues:**
1. Missing entity types: `mcp_tool`, `mcp_resource`, `preset`
2. No fuzzy matching

**Important Issues:**
1. No autocomplete for `@mcp-server-name` (FR-031)
2. No autocomplete history
3. No autocomplete analytics

**Suggestions:**
1. Add autocomplete caching
2. Add autocomplete shortcuts
3. Add autocomplete previews

**Compliance:**
- File autocomplete: ✅ 100%
- Agent autocomplete: ✅ 100%
- Skill autocomplete: ✅ 100%
- Slash command autocomplete: ✅ 100%
- MCP server autocomplete: ❌ 0%
- MCP tool autocomplete: ❌ 0%
- MCP resource autocomplete: ❌ 0%
- Preset autocomplete: ❌ 0%

---

### 8. MCP Server Management

**Files Reviewed:**
- `apps/web/components/mcp/McpServerList.tsx`
- `apps/web/components/mcp/McpServerForm.tsx`

**Critical Issues:**
1. `/mcp connect` command not implemented (FR-030)
2. `@mcp-server-name` autocomplete missing (FR-031)
3. No MCP tool/resource browser

**Important Issues:**
1. No MCP server health checks
2. No MCP server logs viewer
3. No MCP server metrics

**Suggestions:**
1. Add MCP server marketplace
2. Add MCP server templates
3. Add MCP server analytics

**Compliance:**
- List servers: ✅ 100%
- Add server: ✅ 100%
- Edit server: ✅ 100%
- Delete server: ✅ 100%
- Connect command: ❌ 0%
- Autocomplete: ❌ 0%

---

### 9. Configuration Management (Agents, Skills, Commands)

**Files Reviewed:**
- `apps/web/components/settings/agents/AgentForm.tsx`
- `apps/web/components/settings/skills/SkillEditor.tsx`
- `apps/web/components/settings/commands/CommandEditor.tsx`

**Critical Issues:**
1. **PlateJS completely missing** (affects all editors)
2. No YAML frontmatter validation
3. No markdown preview

**Important Issues:**
1. No template library
2. No import/export functionality
3. No version history

**Suggestions:**
1. Add configuration templates
2. Add configuration sharing
3. Add configuration marketplace

**Compliance:**
- Agent CRUD: ✅ 100%
- Skill CRUD: ✅ 100%
- Command CRUD: ✅ 100%
- Rich text editing: ❌ 0% (PlateJS missing)
- YAML validation: ❌ 0%
- Markdown preview: ❌ 0%

---

### 10. Mobile Responsiveness

**Files Reviewed:** All 93 components

**Critical Issues:**
1. Only 5% of components are responsive
2. No mobile navigation patterns
3. No touch gesture support

**Important Issues:**
1. No mobile-specific components
2. No mobile performance optimization
3. No mobile E2E tests

**Suggestions:**
1. Add progressive web app (PWA) support
2. Add offline mode
3. Add mobile-specific shortcuts

**Compliance:**
- Mobile-first CSS: ❌ 5%
- Touch targets: ❌ 20%
- Mobile navigation: ❌ 0%
- Mobile E2E tests: ❌ 0%

---

### 11. Accessibility Compliance

**Files Reviewed:** All components

**Critical Issues:**
1. No focus trap in modals (WCAG violation)
2. Color contrast violations (32 instances)
3. Missing ARIA labels (15 instances)

**Important Issues:**
1. No screen reader testing
2. No keyboard navigation documentation
3. No accessibility E2E tests

**Suggestions:**
1. Add accessibility testing to CI
2. Add accessibility audit reports
3. Add accessibility documentation

**Compliance:**
- WCAG 2.1 AA: ⚠️ 70%
- Keyboard navigation: ⚠️ 80%
- Screen reader support: ⚠️ 60%
- Focus management: ❌ 40%
- Color contrast: ❌ 65%

---

### 12. Performance Optimizations

**Files Reviewed:** All components and hooks

**Critical Issues:**
1. MessageContent not memoized
2. No code splitting
3. No lazy loading

**Important Issues:**
1. No bundle size analysis
2. No performance monitoring
3. No performance E2E tests

**Suggestions:**
1. Add performance budgets
2. Add performance CI checks
3. Add performance documentation

**Compliance:**
- Component memoization: ⚠️ 60%
- Virtualization: ✅ 100% (MessageList)
- Code splitting: ❌ 0%
- Lazy loading: ❌ 0%
- Performance tests: ❌ 0%

---

### 13. SSE Streaming

**Files Reviewed:**
- `apps/web/hooks/useStreamMessages.ts`
- `apps/web/app/api/sessions/[id]/stream/route.ts`

**Critical Issues:**
1. No exponential backoff retry logic
2. No connection health monitoring

**Important Issues:**
1. No SSE analytics
2. No SSE error logging
3. No SSE E2E tests

**Suggestions:**
1. Add SSE connection indicator
2. Add SSE reconnection notifications
3. Add SSE performance metrics

**Compliance:**
- EventSource implementation: ✅ 100%
- Message handling: ✅ 100%
- Error handling: ⚠️ 60%
- Retry logic: ❌ 0%

---

### 14. React Query Integration

**Files Reviewed:** All hooks using React Query

**Critical Issues:**
1. Query key factory not implemented
2. No optimistic updates
3. Inconsistent stale time configuration

**Important Issues:**
1. No query devtools in production
2. No query error boundaries
3. No query retry configuration

**Suggestions:**
1. Add query analytics
2. Add query performance monitoring
3. Add query documentation

**Compliance:**
- Query hooks: ✅ 100%
- Mutation hooks: ✅ 100%
- Cache invalidation: ⚠️ 70%
- Optimistic updates: ❌ 0%
- Query key factory: ❌ 0%

---

### 15. Context Providers

**Files Reviewed:**
- `apps/web/contexts/AuthContext.tsx`
- `apps/web/contexts/SettingsContext.tsx`
- `apps/web/contexts/ModeContext.tsx`
- `apps/web/app/layout.tsx`

**Critical Issues:**
1. ActiveSessionContext missing entirely
2. SettingsContext wrong structure
3. ModeProvider not in layout
4. PermissionsProvider missing

**Important Issues:**
1. No context documentation
2. No context testing
3. No context performance optimization

**Suggestions:**
1. Add context devtools
2. Add context analytics
3. Add context migration guides

**Compliance:**
- Required contexts: ⚠️ 60%
- Context structure: ⚠️ 70%
- Context integration: ⚠️ 50%

---

### 16. Integration Test Coverage

**Files Reviewed:**
- `tests/integration/test_sessions.py`
- `tests/integration/test_projects.py`
- `tests/integration/test_agents.py`
- (and 12 more integration test files)

**Critical Issues:**
None! Backend integration test coverage is excellent.

**Important Issues:**
1. No frontend integration tests
2. No cross-browser testing
3. No integration test documentation

**Suggestions:**
1. Add integration test analytics
2. Add integration test performance tracking
3. Add integration test coverage badges

**Compliance:**
- Backend API coverage: ✅ 85%
- Frontend coverage: ❌ 0%
- Cross-browser: ❌ 0%

---

### 17. E2E Test Coverage

**Files Reviewed:**
- `tests/e2e/chat-input.spec.ts`

**Critical Issues:**
1. Only 8% user story coverage (1/12 stories)
2. No mobile E2E tests
3. No accessibility E2E tests
4. No performance E2E tests

**Important Issues:**
1. No E2E test CI pipeline
2. No E2E test documentation
3. No E2E test analytics

**Suggestions:**
1. Add E2E test screenshots on failure
2. Add E2E test videos
3. Add E2E test reports

**Compliance:**
- User story coverage: ❌ 8%
- Mobile testing: ❌ 0%
- Accessibility testing: ❌ 0%
- Performance testing: ❌ 0%

---

### 18. Tailwind Styling Consistency

**Files Reviewed:** All components

**Critical Issues:**
1. Color contrast violations (WCAG AA)
2. Inconsistent spacing scale usage

**Important Issues:**
1. No design system documentation
2. No custom Tailwind config
3. No CSS purging optimization

**Suggestions:**
1. Add design tokens
2. Add component variants documentation
3. Add Tailwind plugin for custom utilities

**Compliance:**
- Tailwind v4 usage: ✅ 100%
- Consistent spacing: ⚠️ 85%
- Color contrast: ❌ 65%
- Design system: ⚠️ 70%

---

### 19. Coding Standards Compliance

**Files Reviewed:** All TypeScript/TSX files

**Critical Issues:**
None!

**Important Issues:**
1. Inconsistent file naming (some PascalCase, some kebab-case)
2. Missing JSDoc comments on some public APIs

**Suggestions:**
1. Add ESLint custom rules
2. Add Prettier custom config
3. Add code style documentation

**Compliance:**
- TypeScript strict mode: ✅ 100%
- ESLint rules: ✅ 95%
- Prettier formatting: ✅ 100%
- File naming: ⚠️ 80%
- JSDoc comments: ⚠️ 70%

---

## Compliance Matrix

### Functional Requirements (FR)

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| FR-001 | Real-time message streaming | ✅ Complete | EventSource properly implemented |
| FR-002 | Message rendering with markdown | ✅ Complete | ReactMarkdown integration |
| FR-003 | Code syntax highlighting | ✅ Complete | Proper highlighting in code blocks |
| FR-016 | Tool approval modal | ✅ Complete | Fully functional |
| FR-017 | Tool permission toggle | ✅ Complete | Auto/manual modes working |
| FR-018 | Tool status indicators | ✅ Complete | Pending/approved/rejected states |
| FR-019 | Tool description display | ✅ Complete | Clear descriptions shown |
| FR-020 | Approve tool button | ✅ Complete | Working correctly |
| FR-021 | Reject tool button | ✅ Complete | Working correctly |
| FR-022 | Tool permission mode | ✅ Complete | Persistence working |
| FR-030 | /mcp connect command | ❌ Missing | Not implemented |
| FR-031 | @mcp-server autocomplete | ❌ Missing | Not implemented |
| FR-036 | Session search/filter | ❌ Missing | Not implemented |
| FR-037 | Checkpoint markers | ❌ Missing | Not integrated |
| FR-041 | Subagent display | ⚠️ Partial | Component exists but not integrated |
| FR-042 | Artifact rendering | ⚠️ Partial | Basic implementation, PlateJS missing |
| FR-055 | Agent prompt editing | ⚠️ Partial | Textarea only, PlateJS missing |
| FR-061 | Skill content editing | ⚠️ Partial | Textarea only, PlateJS missing |
| FR-067 | MCP config editing | ⚠️ Partial | Textarea only, PlateJS missing |
| FR-073 | Keyboard navigation | ⚠️ Partial | Basic support, focus trap missing |
| FR-087 | Mobile-first design | ❌ Missing | Only 5% compliance |
| FR-093 | YAML frontmatter editing | ❌ Missing | PlateJS required |
| FR-094 | Markdown preview | ❌ Missing | PlateJS required |

**Overall FR Compliance:** ~70%

---

### User Stories (US)

| ID | Story | Status | Completion |
|----|-------|--------|------------|
| US1 | Chat Input & Streaming | ✅ Complete | 100% |
| US2 | Session Management | ⚠️ Partial | 85% (search/filter missing) |
| US3 | Mode Switching | ⚠️ Partial | 80% (filesystem access missing) |
| US4 | Tool Approval | ✅ Complete | 100% |
| US5 | Session Sharing | ⚠️ Partial | 90% (minor issues) |
| US6 | MCP Server Management | ⚠️ Partial | 70% (commands/autocomplete missing) |
| US7 | Settings Management | ⚠️ Partial | 85% (context structure wrong) |
| US8 | Agent Management | ⚠️ Partial | 60% (PlateJS missing) |
| US9 | Skill Management | ⚠️ Partial | 60% (PlateJS missing) |
| US10 | MCP Configuration | ⚠️ Partial | 60% (PlateJS missing) |
| US11 | Slash Command Management | ⚠️ Partial | 60% (PlateJS missing) |
| US12 | Artifact Rendering | ⚠️ Partial | 60% (PlateJS missing) |

**Overall US Completion:** ~75%

---

### Non-Functional Requirements (NFR)

| Category | Requirement | Status | Notes |
|----------|-------------|--------|-------|
| Performance | LCP < 2.5s | ❓ Unknown | No performance tests |
| Performance | FID < 100ms | ❓ Unknown | No performance tests |
| Performance | CLS < 0.1 | ❓ Unknown | No performance tests |
| Performance | Virtualization | ✅ Complete | MessageList properly virtualized |
| Performance | Memoization | ⚠️ Partial | Some components not memoized |
| Accessibility | WCAG 2.1 AA | ⚠️ Partial | Color contrast & focus trap issues |
| Accessibility | Keyboard navigation | ⚠️ Partial | Basic support, gaps exist |
| Accessibility | Screen reader support | ⚠️ Partial | ARIA labels incomplete |
| Mobile | Responsive design | ❌ Missing | Only 5% compliance |
| Mobile | Touch targets 44px+ | ❌ Missing | Not verified |
| Security | API authentication | ✅ Complete | Working correctly |
| Security | Input validation | ⚠️ Partial | Some schemas missing |
| Testing | E2E coverage 80%+ | ❌ Missing | Only 8% coverage |
| Testing | Unit test coverage 85%+ | ⚠️ Unknown | No coverage reports |

**Overall NFR Compliance:** ~60%

---

## Recommendations

### Immediate Actions (Week 1)

#### 1. **Decision on PlateJS** (CRITICAL)
- **Option A:** Implement PlateJS across all editors (Est. 2-3 weeks)
  - Install dependencies
  - Create shared `<RichTextEditor>` component
  - Refactor 6 editor components
  - Add YAML/markdown plugins
  - Write tests

- **Option B:** Update spec to remove PlateJS requirement (Est. 1 day)
  - Update `data-model.md`
  - Update `spec.md`
  - Update affected functional requirements
  - Document decision rationale

**Recommendation:** Choose Option B for faster delivery, add PlateJS in future sprint.

---

#### 2. **Fix Critical Context Issues** (CRITICAL)
- **Day 1-2:** Implement `ActiveSessionContext`
  - Create context file
  - Add to app layout
  - Refactor ChatInterface to use context
  - Refactor useStreamMessages to use context

- **Day 3:** Fix `SettingsContext` structure
  - Refactor to individual setters
  - Update GeneralSettings component
  - Test all settings functionality

- **Day 4:** Add missing providers to layout
  - Add ModeProvider
  - Create and add PermissionsProvider
  - Test provider hierarchy

---

#### 3. **Fix WCAG AA Violations** (CRITICAL)
- **Day 1:** Install focus-trap-react and fix modals
- **Day 2:** Fix color contrast violations (32 instances)
- **Day 3:** Install @axe-core/playwright
- **Day 4:** Write accessibility E2E tests
- **Day 5:** Run full accessibility audit

---

#### 4. **Implement Query Key Factory** (CRITICAL)
- **Day 1-2:** Create `lib/query-keys.ts` with all factories
- **Day 3-5:** Refactor all hooks to use factories
- **Testing:** Verify cache invalidation works correctly

---

### Short-Term Actions (Weeks 2-4)

#### 1. **Mobile-First Responsive Design** (3-4 weeks)
- **Week 2:** Core chat interface (ChatInterface, Composer, MessageList)
- **Week 3:** Sidebars and navigation (SessionSidebar, SettingsSidebar)
- **Week 4:** Modals and settings screens

**Approach:**
1. Start with mobile (320px) first
2. Add breakpoints progressively (md:, lg:, xl:)
3. Test at each viewport before moving on
4. Write E2E tests for each viewport

---

#### 2. **Implement SSE Retry Logic** (1 week)
- Add exponential backoff with jitter
- Add connection health monitoring
- Add reconnection notifications
- Write SSE E2E tests

---

#### 3. **Integrate Missing Components** (1 week)
- Integrate SubagentCard in MessageItem
- Integrate CheckpointMarker in message flow
- Add session search/filter
- Implement `/mcp connect` command

---

#### 4. **Implement Optimistic Updates** (1 week)
- Refactor all mutations to use optimistic updates
- Add error rollback handling
- Test optimistic update edge cases

---

### Medium-Term Actions (Weeks 5-8)

#### 1. **E2E Test Coverage** (3-4 weeks)
- **Week 5:** Session management, mode switching, tool approval
- **Week 6:** Session sharing, MCP management, settings
- **Week 7:** Agents, skills, MCP servers
- **Week 8:** Slash commands, artifacts, edge cases

**Target:** 80%+ user story coverage

---

#### 2. **Mobile E2E Tests** (1 week)
- Add mobile viewport tests (320px, 375px, 414px)
- Test touch gestures
- Test touch targets (44px minimum)
- Test orientation changes

---

#### 3. **Performance Optimization** (1 week)
- Memoize all message components
- Implement code splitting
- Implement lazy loading
- Add performance E2E tests
- Verify Core Web Vitals

---

#### 4. **API Contract Compliance** (1 week)
- Fix DELETE endpoint status codes
- Remove extra response wrappers
- Add missing Zod schemas
- Verify all endpoints match OpenAPI spec

---

### Long-Term Actions (Weeks 9+)

#### 1. **Enhanced Features**
- Session templates
- Session export/import
- Tool analytics
- MCP server marketplace
- Configuration templates
- Keyboard shortcuts
- Offline mode (PWA)

#### 2. **Developer Experience**
- Comprehensive documentation
- Component storybook
- Design system documentation
- Contributing guidelines
- Architecture decision records (ADRs)

#### 3. **Quality Assurance**
- Automated performance monitoring
- Automated accessibility audits in CI
- Visual regression testing
- Load testing
- Security testing

---

## Effort Estimates

### Summary by Priority

| Priority | Total Issues | Estimated Effort |
|----------|--------------|------------------|
| P0 (Critical) | 10 | 4-5 weeks |
| P1 (Important) | 9 | 2-3 weeks |
| P2 (Testing) | 4 | 4-5 weeks |
| **Total** | **23** | **10-13 weeks** |

### Detailed Breakdown

#### P0 Critical Issues (Must Fix)
1. PlateJS Decision/Implementation: 2-3 weeks OR 1 day (spec update)
2. ActiveSessionContext: 3-5 days
3. Query Key Factory: 1 week
4. Mobile-First Design: 3-4 weeks
5. Focus Trap: 2-3 days
6. Color Contrast: 1 week
7. SettingsContext: 2-3 days
8. SSE Retry Logic: 2-3 days
9. SubagentCard Integration: 1-2 days
10. Missing Providers: 1 day

**Total P0:** 4-5 weeks (assuming PlateJS spec update, not full implementation)

---

#### P1 Important Issues (Should Fix)
1. Session Search/Filter: 3-4 days
2. CheckpointMarker Integration: 2-3 days
3. Optimistic Updates: 1 week
4. MessageContent Memoization: 1-2 days
5. /mcp connect Command: 2-3 days
6. @mcp-server Autocomplete: 2-3 days
7. Missing Autocomplete Types: 3-4 days
8. API Contract Fixes: 1-2 days
9. Missing Zod Schemas: 1 day

**Total P1:** 2-3 weeks

---

#### P2 Test Coverage (Quality Assurance)
1. E2E Test Coverage: 3-4 weeks
2. Mobile Viewport Tests: 1 week
3. Accessibility Tests: 1 week
4. Performance Tests: 1 week

**Total P2:** 4-5 weeks

---

### Recommended Phasing

#### Phase 1: Critical Path (4-5 weeks)
**Goal:** Fix production blockers

- Week 1: Contexts, WCAG fixes, query keys
- Week 2-4: Mobile-first responsive design
- Week 5: SSE retry, missing integrations

**Deliverable:** Production-ready core functionality

---

#### Phase 2: Quality & Features (3-4 weeks)
**Goal:** Improve UX and add missing features

- Week 6: Optimistic updates, session features
- Week 7: MCP commands, autocomplete enhancements
- Week 8-9: API contract fixes, missing schemas

**Deliverable:** Feature-complete implementation

---

#### Phase 3: Testing & Polish (4-5 weeks)
**Goal:** Comprehensive test coverage

- Week 10-12: E2E test coverage (80%+ target)
- Week 13: Mobile & accessibility tests
- Week 14: Performance tests & optimization

**Deliverable:** High-quality, well-tested application

---

## Appendix A: Review Agent Details

Each review agent followed this standardized process:

1. **Read Specification Artifacts**
   - Load all relevant spec files
   - Extract requirements for assigned area
   - Build compliance checklist

2. **Analyze Implementation**
   - Read all relevant source files
   - Compare against spec requirements
   - Identify gaps and violations

3. **Categorize Issues**
   - Critical (P0): Production blockers
   - Important (P1): Should fix before release
   - Suggestions: Nice-to-have improvements

4. **Provide Recommendations**
   - Specific file locations
   - Code examples
   - Effort estimates
   - Testing requirements

5. **Generate Report**
   - Compliance percentage
   - Issue count by severity
   - Detailed findings
   - Actionable next steps

---

## Appendix B: File Reference Index

### Critical Files Requiring Updates

**P0 - Must Fix:**
```
apps/web/contexts/ActiveSessionContext.tsx          [CREATE]
apps/web/contexts/SettingsContext.tsx               [REFACTOR]
apps/web/lib/query-keys.ts                          [CREATE]
apps/web/hooks/useStreamMessages.ts                 [UPDATE - SSE retry]
apps/web/components/chat/MessageItem.tsx            [UPDATE - SubagentCard]
apps/web/app/layout.tsx                             [UPDATE - providers]
apps/web/components/modals/*.tsx                    [UPDATE - focus trap]
All components with text-gray-400/300/500           [UPDATE - contrast]
90+ components                                       [UPDATE - responsive]
```

**P1 - Should Fix:**
```
apps/web/components/sidebar/SessionSidebar.tsx      [UPDATE - search/filter]
apps/web/components/chat/MessageContent.tsx         [UPDATE - memoization]
apps/web/lib/slash-commands.ts                      [UPDATE - /mcp connect]
apps/web/hooks/useAutocomplete.ts                   [UPDATE - MCP autocomplete]
apps/web/hooks/useSessions.ts                       [UPDATE - optimistic]
apps/web/hooks/useProjects.ts                       [UPDATE - optimistic]
apps/web/hooks/useAgents.ts                         [UPDATE - optimistic]
apps/web/app/api/*/route.ts                         [UPDATE - status codes]
apps/web/lib/schemas/index.ts                       [UPDATE - missing schemas]
```

**P2 - Testing:**
```
tests/e2e/session-management.spec.ts                [CREATE]
tests/e2e/mode-switching.spec.ts                    [CREATE]
tests/e2e/tool-approval.spec.ts                     [CREATE]
tests/e2e/mobile.spec.ts                            [CREATE]
tests/e2e/accessibility.spec.ts                     [CREATE]
tests/e2e/performance.spec.ts                       [CREATE]
... (7 more E2E test files)
```

---

## Appendix C: Compliance Checklist

Use this checklist to track progress on fixes:

### P0 Critical Issues
- [ ] P0-001: PlateJS decision made (implement vs. spec update)
- [ ] P0-002: ActiveSessionContext implemented
- [ ] P0-003: Query key factory created and integrated
- [ ] P0-004: Mobile-first responsive design (90+ components)
- [ ] P0-005: Focus trap added to all modals
- [ ] P0-006: Color contrast violations fixed (32 instances)
- [ ] P0-007: SettingsContext refactored to spec structure
- [ ] P0-008: SSE retry logic with exponential backoff
- [ ] P0-009: SubagentCard integrated in message flow
- [ ] P0-010: Missing providers added to app layout

### P1 Important Issues
- [ ] P1-001: Session search/filter implemented
- [ ] P1-002: CheckpointMarker integrated
- [ ] P1-003: Optimistic updates on all mutations
- [ ] P1-004: MessageContent memoized
- [ ] P1-005: /mcp connect command implemented
- [ ] P1-006: @mcp-server-name autocomplete implemented
- [ ] P1-007: Missing autocomplete entity types added
- [ ] P1-008: API contract violations fixed
- [ ] P1-009: Missing Zod schemas created

### P2 Test Coverage
- [ ] P2-001: E2E tests for all 12 user stories
- [ ] P2-002: Mobile viewport tests (320px, 375px, 414px)
- [ ] P2-003: Accessibility tests with @axe-core/playwright
- [ ] P2-004: Performance tests (LCP, FID, CLS)

---

## Appendix D: Risk Assessment

### High Risk Areas

#### 1. PlateJS Implementation (if chosen)
**Risk:** 2-3 weeks of work, potential scope creep
**Mitigation:**
- Clear scope definition upfront
- Incremental implementation (agents → skills → MCP)
- Weekly progress reviews
- Fallback: basic textarea with validation

#### 2. Mobile-First Refactor
**Risk:** Breaking existing desktop functionality
**Mitigation:**
- Component-by-component approach
- Desktop regression testing after each change
- Feature flags for gradual rollout
- Visual regression testing

#### 3. E2E Test Coverage
**Risk:** Time-consuming, requires maintenance
**Mitigation:**
- Prioritize happy path tests first
- Use Page Object Model pattern
- Automate in CI from day one
- Budget 20% time for test maintenance

### Medium Risk Areas

#### 1. Query Key Factory Refactor
**Risk:** Breaking existing cache behavior
**Mitigation:**
- Comprehensive testing before/after
- Gradual rollout (one hook at a time)
- Monitor cache hit rates

#### 2. SSE Retry Logic
**Risk:** Connection storms, resource exhaustion
**Mitigation:**
- Conservative backoff times
- Max retry limit
- Circuit breaker pattern
- Load testing

### Low Risk Areas

#### 1. Context Implementations
**Risk:** Minimal - well-defined scope
**Mitigation:** Standard React patterns, good test coverage

#### 2. Color Contrast Fixes
**Risk:** Minimal - straightforward CSS changes
**Mitigation:** Automated testing with axe-core

---

## Document Metadata

**Created:** January 11, 2026
**Author:** Code Review Team (19 Specialized Agents)
**Version:** 1.0
**Total Review Time:** ~8 hours (parallelized)
**Total Issues Found:** 211 (97 critical, 69 important, 45 suggestions)
**Document Length:** ~15,000 words
**Last Updated:** January 11, 2026

---

## Conclusion

The Claude Agent Web Interface implementation demonstrates strong technical foundations with excellent type safety, component architecture, and backend integration. However, critical gaps in mobile responsiveness (5% compliance), PlateJS implementation (0%), and E2E test coverage (8%) require immediate attention before production deployment.

**Recommended Next Steps:**

1. **Week 1:** Make PlateJS decision, fix critical context issues, address WCAG violations
2. **Weeks 2-4:** Mobile-first responsive design refactor
3. **Weeks 5-8:** Complete P1 features and expand E2E test coverage
4. **Weeks 9+:** Polish, performance optimization, and remaining enhancements

**Estimated Time to Production-Ready:** 10-13 weeks with current team velocity

This comprehensive review provides a clear roadmap for bringing the implementation to production quality while maintaining the strong foundations already in place.
