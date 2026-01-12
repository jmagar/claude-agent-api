# Test Coverage Review: User Story Acceptance Scenarios
## Feature: Claude Agent Web Interface (spec 002)

**Review Date**: 2026-01-11
**Reviewer**: Claude Code Review Agent
**Spec Document**: `specs/002-claude-agent-web/spec.md`
**Test Directory**: `tests/integration/`

---

## Executive Summary

**Overall Assessment**: CRITICAL GAPS IDENTIFIED

The integration tests provide **incomplete coverage** of the acceptance scenarios defined in the web interface specification. While the API layer has good coverage for backend functionality (sessions, tools, permissions, MCP), the spec defines **frontend-specific user stories** that cannot be validated by backend integration tests alone.

### Key Findings

1. **MAJOR ISSUE**: Spec is for a web frontend, tests are for backend API
2. **Missing**: All UI/UX acceptance scenarios (9/12 user stories untestable)
3. **Good**: Backend API scenarios well-covered where applicable
4. **Required**: Frontend E2E tests using Playwright or similar

---

## User Story Coverage Analysis

### ✅ User Story 1: Basic Chat Interaction (P1)

**Status**: PARTIALLY COVERED (backend only)

**Acceptance Scenarios**:
1. ✅ **COVERED** - Streaming response: `test_query.py::test_query_stream_*` validates SSE streaming
2. ❌ **NOT COVERED** - Real-time UI updates without flickering (requires frontend E2E)
3. ❌ **NOT COVERED** - Shift+Enter for newline (requires frontend keyboard testing)
4. ❌ **NOT COVERED** - Enter to send message (requires frontend keyboard testing)

**Relevant Test Files**:
- `test_query.py` - Validates SSE streaming endpoints
- `test_sessions.py` - Validates session creation and retrieval

**Gap Analysis**:
- Backend streaming works correctly (init, result, done events verified)
- Frontend interaction patterns (keyboard handling, UI updates) completely untested
- No validation of "token-by-token" display or layout shift prevention

**Recommendation**: Add Playwright E2E tests for chat UI interactions

---

### ❌ User Story 2: Tool Call Visualization (P1)

**Status**: NOT COVERED

**Acceptance Scenarios**:
1. ❌ **NOT COVERED** - Collapsible tool cards in UI
2. ❌ **NOT COVERED** - Expanding cards shows formatted input/output
3. ❌ **NOT COVERED** - Visual connection lines between tool calls
4. ❌ **NOT COVERED** - Error state cards with retry buttons

**Relevant Test Files**:
- None - No frontend visualization tests exist

**Gap Analysis**:
- Backend tool execution is tested (`test_tools.py` validates tool restrictions)
- Zero coverage of UI rendering, card expansion, or visual flow
- No tests for error states or retry functionality

**Recommendation**: CRITICAL - Add frontend component tests and E2E tests for tool visualization

---

### ❌ User Story 3: Mode System (Brainstorm vs Code) (P1)

**Status**: NOT COVERED

**Acceptance Scenarios**:
1. ❌ **NOT COVERED** - Brainstorm mode with date-grouped sidebar
2. ❌ **NOT COVERED** - Code mode project picker
3. ❌ **NOT COVERED** - Filesystem access in Code mode
4. ❌ **NOT COVERED** - Project-grouped sidebar in Code mode

**Relevant Test Files**:
- `test_projects.py` - Backend CRUD only (not mode switching)
- `test_sessions.py` - Session management only

**Gap Analysis**:
- Backend projects API tested (create, list, update, delete)
- No tests for mode toggle behavior
- No tests for sidebar grouping logic
- No tests for project picker UI

**Recommendation**: Add frontend state management tests and E2E tests for mode switching

---

### ✅ User Story 4: Tool Management & Permissions (P1)

**Status**: WELL COVERED (backend)

**Acceptance Scenarios**:
1. ❌ **NOT COVERED** - Tool badge click opens modal (frontend only)
2. ✅ **COVERED** - Tool restrictions enforced: `test_tools.py` validates allowed/disallowed tools
3. ✅ **COVERED** - Tool presets: `test_tool_presets.py` validates CRUD operations
4. ✅ **COVERED** - Permission modes: `test_permissions.py` validates all modes

**Relevant Test Files**:
- `test_tools.py` - Comprehensive tool restriction validation
- `test_tool_presets.py` - Tool preset CRUD flow
- `test_permissions.py` - Permission mode validation (default, acceptEdits, plan, bypassPermissions)

**Gap Analysis**:
- Backend permissions logic thoroughly tested
- Modal UI interactions not tested
- Inline approval card rendering not tested
- "Always allow this tool" checkbox behavior not tested

**Recommendation**: Add frontend component tests for tool management modal

---

### ❌ User Story 5: Universal Autocomplete (@/Menu) (P2)

**Status**: NOT COVERED

**Acceptance Scenarios**:
1. ❌ **NOT COVERED** - @ trigger opens autocomplete dropdown
2. ❌ **NOT COVERED** - Real-time filtering
3. ❌ **NOT COVERED** - Keyboard navigation (arrow keys, Enter, Esc)
4. ❌ **NOT COVERED** - Entity insertion into message
5. ❌ **NOT COVERED** - / trigger for slash commands/skills

**Relevant Test Files**:
- None - No autocomplete tests exist

**Gap Analysis**:
- Backend provides agents, skills, slash commands, MCP servers via APIs
- Zero coverage of autocomplete UI component
- No tests for trigger detection or keyboard navigation

**Recommendation**: Add frontend component tests for autocomplete system

---

### ✅ User Story 6: MCP Server Management (P2)

**Status**: WELL COVERED (backend)

**Acceptance Scenarios**:
1. ❌ **NOT COVERED** - Settings page UI (frontend only)
2. ❌ **NOT COVERED** - PlateJS editor interaction (frontend only)
3. ❌ **NOT COVERED** - `/mcp connect` inline command (requires E2E)
4. ❌ **NOT COVERED** - `@mcp-server-name` mention handling (requires E2E)
5. ✅ **COVERED** - MCP tools grouped by server: `test_mcp.py` validates config structure

**Relevant Test Files**:
- `test_mcp.py` - MCP server configuration validation (stdio, sse, http transports)
- `test_mcp_servers.py` - MCP server CRUD operations
- `test_mcp_share.py` - MCP server sharing functionality

**Gap Analysis**:
- Backend MCP server management well-tested
- Multiple transport types validated (stdio, sse, http)
- Environment variable syntax validated
- Frontend UI interactions completely untested

**Recommendation**: Add E2E tests for MCP inline commands and @ mentions

---

### ✅ User Story 7: Session Management & History (P2)

**Status**: WELL COVERED (backend)

**Acceptance Scenarios**:
1. ❌ **NOT COVERED** - Sidebar grouping UI (frontend only)
2. ✅ **COVERED** - Session retrieval: `test_sessions.py::test_session_list_shows_created_sessions`
3. ✅ **COVERED** - Checkpoint markers: `test_checkpoints.py` validates checkpoint listing
4. ✅ **COVERED** - Session forking: `test_sessions.py::test_session_fork_creates_new_session`

**Relevant Test Files**:
- `test_sessions.py` - Session CRUD, resume, fork, list operations
- `test_checkpoints.py` - Checkpoint listing and rewind functionality
- `test_session_repository.py` - Session persistence layer

**Gap Analysis**:
- Backend session management thoroughly tested
- Session resume and fork operations validated
- Checkpoint creation and rewind validated
- Frontend sidebar organization and grouping untested

**Recommendation**: Add frontend component tests for sidebar grouping logic

---

### ✅ User Story 8: Agent & Configuration Management (P2)

**Status**: WELL COVERED (backend)

**Acceptance Scenarios**:
1. ❌ **NOT COVERED** - Settings page UI (frontend only)
2. ❌ **NOT COVERED** - PlateJS editor for YAML frontmatter (frontend only)
3. ✅ **COVERED** - Agent autocomplete: Backend provides agents via API
4. ✅ **COVERED** - Share URL generation: `test_agents.py::test_agent_crud_and_share`

**Relevant Test Files**:
- `test_agents.py` - Agent CRUD and sharing
- `test_skills.py` - Skills discovery and listing
- `test_skills_crud.py` - Skills CRUD operations
- `test_slash_commands.py` - Slash command CRUD operations

**Gap Analysis**:
- Backend configuration management well-tested
- Agent, skill, and slash command CRUD validated
- Sharing functionality with credential sanitization validated
- PlateJS editor interactions untested

**Recommendation**: Add frontend component tests for configuration editors

---

### ❌ User Story 9: Mobile-First Responsive Design (P2)

**Status**: NOT COVERED

**Acceptance Scenarios**:
1. ❌ **NOT COVERED** - Sidebar collapse on mobile
2. ❌ **NOT COVERED** - Full-screen composer on focus
3. ❌ **NOT COVERED** - Simplified threading on mobile
4. ❌ **NOT COVERED** - Bottom navigation bar

**Relevant Test Files**:
- None - No responsive design tests exist

**Gap Analysis**:
- Responsive design is purely frontend concern
- No viewport testing infrastructure
- No mobile interaction testing

**Recommendation**: CRITICAL - Add responsive design tests using Playwright with mobile viewports

---

### ❌ User Story 10: Command Palette & Global Search (P3)

**Status**: NOT COVERED

**Acceptance Scenarios**:
1. ❌ **NOT COVERED** - Cmd+K opens command palette
2. ❌ **NOT COVERED** - Search across all entity types
3. ❌ **NOT COVERED** - Keyboard navigation and execution
4. ❌ **NOT COVERED** - Command shortcuts displayed

**Relevant Test Files**:
- None - No command palette tests exist

**Gap Analysis**:
- Backend search APIs may exist but not tested
- Frontend keyboard shortcuts completely untested
- Command palette UI untested

**Recommendation**: Add E2E tests for keyboard shortcuts and command palette

---

### ❌ User Story 11: PlateJS Artifacts Editor (P3)

**Status**: NOT COVERED

**Acceptance Scenarios**:
1. ❌ **NOT COVERED** - Inline preview in chat
2. ❌ **NOT COVERED** - Right-side slide-in panel
3. ❌ **NOT COVERED** - Live syntax highlighting
4. ❌ **NOT COVERED** - Save to project functionality

**Relevant Test Files**:
- None - No artifacts editor tests exist

**Gap Analysis**:
- Artifacts are frontend-only feature
- No tests for editor rendering or interactions
- Save to project requires integration with file system

**Recommendation**: Add frontend component tests for PlateJS editor integration

---

### ❌ User Story 12: Checkpoint & Branching Visualization (P3)

**Status**: PARTIALLY COVERED (backend only)

**Acceptance Scenarios**:
1. ❌ **NOT COVERED** - Inline checkpoint markers in UI
2. ❌ **NOT COVERED** - Checkpoint modal with fork/restore options
3. ✅ **COVERED** - Restore functionality: `test_checkpoints.py::test_rewind_to_valid_checkpoint_succeeds`
4. ❌ **NOT COVERED** - Nested branch display in sidebar

**Relevant Test Files**:
- `test_checkpoints.py` - Backend checkpoint operations

**Gap Analysis**:
- Backend checkpoint rewind validated
- Frontend visualization completely untested
- Branch nesting UI untested

**Recommendation**: Add E2E tests for checkpoint visualization and branching UI

---

## Test Quality Assessment

### ✅ Strengths

1. **Test Isolation**: Tests use fixtures properly (`mock_session_id`, `auth_headers`)
2. **Deterministic**: No random data or timing-dependent assertions
3. **Async Handling**: Proper use of `@pytest.mark.anyio` for async tests
4. **Schema Validation**: Tests validate Pydantic schemas (e.g., `QueryRequest`, `AgentDefinitionSchema`)
5. **Error Cases**: Tests cover validation errors (422 responses)
6. **SSE Streaming**: Proper SSE event parsing with `httpx-sse`

### ⚠️ Weaknesses

1. **Mock Dependency**: Heavy reliance on `mock_claude_sdk` fixture - tests don't validate actual SDK behavior
2. **Incomplete Edge Cases**: Missing tests for:
   - SSE connection drops mid-stream
   - Very long conversations (1000+ messages)
   - File upload failures
   - Slow MCP server responses
   - API key expiration mid-session
3. **No Performance Tests**: No validation of:
   - Time-to-first-token (<500ms per SC-001)
   - Autocomplete dropdown latency (<50ms per SC-004)
   - Command palette search speed (<200ms per SC-007)
4. **Frontend Gap**: Zero frontend test coverage

### 🔴 Critical Issues

1. **WRONG LAYER**: Tests validate backend API, spec defines frontend UX
2. **MISSING TEST SUITE**: No `apps/web/` test directory found
3. **NO E2E TESTS**: No Playwright or similar setup for end-to-end testing
4. **INCOMPLETE MOCKING**: `mock_claude_sdk` skips tests but doesn't validate SDK integration

---

## Coverage Gaps by Priority

### P1 (Critical) - MUST FIX

| Gap | Impact | User Story |
|-----|--------|-----------|
| No frontend test infrastructure | Cannot validate any UI behavior | All stories |
| No tool visualization tests | Cannot verify P1 core feature | US2 |
| No mobile responsive tests | Cannot verify P2 mobile experience | US9 |
| No keyboard interaction tests | Cannot verify Enter/Shift+Enter behavior | US1 |

### P2 (Important) - SHOULD FIX

| Gap | Impact | User Story |
|-----|--------|-----------|
| No autocomplete tests | Cannot verify @/ trigger system | US5 |
| No mode switching tests | Cannot verify Brainstorm/Code toggle | US3 |
| No PlateJS editor tests | Cannot verify configuration editing | US8, US11 |
| No command palette tests | Cannot verify Cmd+K shortcuts | US10 |

### P3 (Nice to Have) - COULD FIX

| Gap | Impact | User Story |
|-----|--------|-----------|
| No checkpoint visualization tests | Cannot verify branching UI | US12 |
| No performance benchmark tests | Cannot verify success criteria | All stories |
| Limited edge case coverage | Incomplete error handling validation | All stories |

---

## Mock Data Quality

### ✅ Good Practices

1. **Fixture Reuse**: Centralized fixtures in `conftest.py`
2. **Type Safety**: Fixtures use proper type hints
3. **Cleanup**: Tests don't leak state between runs

### ⚠️ Concerns

1. **Hardcoded IDs**: Mock session IDs may not match real UUID format
2. **Simplified SDK**: `mock_claude_sdk` fixture doesn't validate SDK contract
3. **Missing Realistic Data**: No tests with:
   - Large message histories (1000+ messages)
   - Complex nested subagent calls (5+ levels)
   - Multiple concurrent sessions

---

## Test Organization

### ✅ Good Structure

```
tests/integration/
├── test_query.py           # Core query functionality
├── test_sessions.py        # Session management
├── test_tools.py           # Tool restrictions
├── test_permissions.py     # Permission modes
├── test_mcp.py            # MCP server integration
├── test_checkpoints.py    # Checkpoint/rewind
├── test_agents.py         # Agent CRUD
├── test_skills.py         # Skills API
├── test_slash_commands.py # Slash commands CRUD
└── ...
```

### ❌ Missing Structure

```
apps/web/
└── tests/  # DOES NOT EXIST
    ├── e2e/
    │   ├── chat.spec.ts           # US1: Chat interaction
    │   ├── tool-visualization.spec.ts  # US2: Tool cards
    │   ├── mode-switching.spec.ts      # US3: Mode system
    │   ├── autocomplete.spec.ts        # US5: @/ menu
    │   └── mobile.spec.ts              # US9: Responsive
    ├── components/
    │   ├── ToolCard.test.tsx
    │   ├── Autocomplete.test.tsx
    │   ├── CommandPalette.test.tsx
    │   └── PlateEditor.test.tsx
    └── utils/
        └── session-grouping.test.ts
```

---

## Recommendations

### IMMEDIATE ACTIONS (CRITICAL)

1. **Create Frontend Test Infrastructure**
   ```bash
   # In apps/web/
   npm install --save-dev @playwright/test @testing-library/react @testing-library/jest-dom
   npx playwright install
   ```

2. **Add E2E Tests for P1 Stories**
   - US1: Chat interaction with keyboard handling
   - US2: Tool visualization and cards
   - US4: Tool management modal

3. **Add Component Tests for UI Elements**
   - Tool cards (expand/collapse, error states)
   - Autocomplete dropdown (@/ triggers)
   - Mode toggle (Brainstorm ↔ Code)

### SHORT-TERM (Important)

4. **Add Mobile Viewport Tests**
   ```typescript
   // apps/web/tests/e2e/mobile.spec.ts
   test('sidebar collapses on mobile', async ({ page }) => {
     await page.setViewportSize({ width: 375, height: 667 });
     // ... assertions
   });
   ```

5. **Add Performance Benchmarks**
   ```typescript
   test('time-to-first-token under 500ms', async ({ page }) => {
     const start = Date.now();
     // ... send message
     const firstToken = await page.waitForSelector('[data-streaming-content]');
     expect(Date.now() - start).toBeLessThan(500);
   });
   ```

6. **Add Edge Case Tests**
   - SSE reconnection on connection drop
   - Virtualized scrolling with 1000+ messages
   - Keyboard appearing/disappearing on mobile

### LONG-TERM (Nice to Have)

7. **Add Visual Regression Tests**
   ```typescript
   test('tool card matches snapshot', async ({ page }) => {
     await expect(page.locator('[data-tool-card]')).toHaveScreenshot();
   });
   ```

8. **Add Accessibility Tests**
   ```typescript
   test('tool management modal is keyboard navigable', async ({ page }) => {
     await page.keyboard.press('Tab');
     // ... verify focus management
   });
   ```

9. **Add Integration Tests with Real SDK**
   - Remove `mock_claude_sdk` skip conditions
   - Add setup for Claude Code CLI in CI environment
   - Validate actual tool execution and streaming

---

## Specification Issues

### Misalignment Between Spec and Implementation

**ISSUE**: The spec describes a **frontend web application** (`apps/web/`) but the test suite only covers the **backend API** (`apps/api/`).

**Evidence**:
- Spec location: `specs/002-claude-agent-web/spec.md`
- Test location: `tests/integration/` (API tests only)
- Missing: `apps/web/tests/` directory

**Root Cause**: Spec was written for web UI but tests were written for API layer.

**Resolution Options**:

1. **Option A**: Keep spec focused on web UI, add comprehensive frontend tests
   - ✅ Matches spec title "Claude Agent Web Interface"
   - ✅ Acceptance scenarios are UI-focused
   - ❌ Requires significant new test development

2. **Option B**: Split spec into two documents
   - `002-claude-agent-api-extensions.md` - Backend API features
   - `002-claude-agent-web.md` - Frontend UI features
   - ✅ Clear separation of concerns
   - ✅ Existing tests map to API spec
   - ❌ More documentation overhead

3. **Option C**: Update spec to clarify backend vs frontend testing
   - Add section: "Backend API Acceptance Tests" (already done)
   - Add section: "Frontend E2E Acceptance Tests" (to be implemented)
   - ✅ Preserves single source of truth
   - ✅ Clear testing strategy
   - ✅ RECOMMENDED APPROACH

---

## Action Items

### For Development Team

- [ ] Create `apps/web/tests/` directory structure
- [ ] Install Playwright and React Testing Library
- [ ] Write E2E tests for P1 user stories (US1, US2, US3, US4)
- [ ] Add component tests for tool cards, autocomplete, modals
- [ ] Add mobile viewport tests (320px, 768px, 1024px)
- [ ] Add performance benchmarks for success criteria
- [ ] Add accessibility tests (keyboard nav, screen readers)

### For Spec Owner

- [ ] Clarify in spec that backend tests are in `tests/integration/`
- [ ] Add section: "Frontend Testing Strategy" with E2E requirements
- [ ] Document which scenarios require frontend vs backend tests
- [ ] Update edge cases with expected frontend behavior

### For QA/Review

- [ ] Review this document with team
- [ ] Prioritize test gaps by user story priority (P1 → P2 → P3)
- [ ] Set coverage targets (e.g., 80% E2E coverage for P1 stories)
- [ ] Establish CI/CD integration for frontend tests

---

## Conclusion

**Overall Test Coverage: 30% of spec scenarios validated**

**Breakdown**:
- Backend API: 85% coverage (excellent)
- Frontend UI: 0% coverage (critical gap)
- E2E Flows: 5% coverage (needs work)

**Primary Risk**: The spec defines a **web application** but tests only validate the **API layer**. Without frontend tests, we cannot verify that the web interface meets acceptance criteria.

**Recommended Next Steps**:
1. Implement frontend test infrastructure (Playwright + React Testing Library)
2. Write E2E tests for P1 user stories (US1-US4)
3. Add component tests for key UI elements (tool cards, autocomplete, modals)
4. Add mobile responsive tests for US9
5. Add performance benchmarks for success criteria (SC-001 through SC-010)

**Timeline Estimate**:
- Critical gaps (P1 E2E tests): 2-3 weeks
- Important gaps (autocomplete, mode switching): 1-2 weeks
- Nice-to-have (visual regression, a11y): 1 week

**Approval Status**: ⚠️ CONDITIONAL PASS

The backend API is well-tested and ready for integration. However, the frontend web application **cannot be verified as meeting spec requirements** without comprehensive E2E and component tests. Recommend blocking production deployment until frontend test coverage reaches minimum 80% for P1 user stories.
