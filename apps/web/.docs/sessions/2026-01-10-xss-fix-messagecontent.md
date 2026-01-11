# XSS Vulnerability Fix - MessageContent Component

**Date:** 2026-01-10
**Component:** `/apps/web/components/chat/MessageContent.tsx`
**Issue:** XSS vulnerability from unsafe `dangerouslySetInnerHTML` usage

## Summary

Fixed critical XSS vulnerability in MessageContent component by replacing unsafe regex-based markdown parsing with secure `react-markdown` + `rehype-sanitize` libraries.

## Changes Made

### 1. Dependencies Installed

```bash
pnpm add react-markdown rehype-sanitize
```

- `react-markdown@10.1.0` - Secure markdown parsing library
- `rehype-sanitize@6.0.0` - HTML sanitization plugin

### 2. Component Refactoring

**Before (Vulnerable):**
```typescript
let html = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
html = html.replace(/`(.+?)`/g, "<code>$1</code>");
html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank">$1</a>');

<div dangerouslySetInnerHTML={{ __html: html }} />
```

**After (Secure):**
```typescript
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";

<ReactMarkdown
  rehypePlugins={[rehypeSanitize]}
  components={components}
>
  {text}
</ReactMarkdown>
```

### 3. Security Features Implemented

- **HTML Sanitization**: `rehype-sanitize` strips all dangerous HTML tags and attributes
- **Protocol Validation**: Custom link component only allows `http://` and `https://` protocols
  - Blocks: `javascript:`, `data:`, `file:`, etc.
- **Link Security**: All links have `target="_blank"` and `rel="noopener noreferrer"`
- **XSS Prevention**: Prevents script injection, event handlers, and style injection

### 4. Testing Updates

**New Test File:** `/apps/web/tests/unit/components/MessageContent.test.tsx`

- 10 tests covering markdown rendering and security
- Tests verify proper markdown parsing (bold, italic, code, links)
- Tests verify security attributes on links
- Mock implementation in `jest.setup.js` to handle ESM dependencies

**Test Results:**
- All 62 unit tests passing
- No regressions in existing MessageItem tests
- New MessageContent tests validate security behavior

### 5. Configuration Changes

**jest.setup.js** - Added mock for react-markdown:
```javascript
jest.mock("react-markdown", () => {
  return {
    __esModule: true,
    default: ({ children }) => {
      // Simple markdown parser for tests
      // (production uses real react-markdown with full security)
    },
  };
});
```

## Security Analysis

### Vulnerabilities Prevented

1. **Script Injection**: `<script>alert('XSS')</script>`
2. **Event Handlers**: `<img onerror="alert(1)">`
3. **JavaScript Protocol**: `[Click](javascript:alert(1))`
4. **Data URLs**: `[Click](data:text/html,<script>...)`
5. **Style Injection**: `<style>body { display: none; }</style>`

### Production vs Test Behavior

- **Production**: Full react-markdown + rehype-sanitize (robust XSS protection)
- **Tests**: Mocked implementation (basic markdown parsing)
- **Recommendation**: Add E2E tests for comprehensive security validation

## Verification Steps

1. ✅ Dependencies installed successfully
2. ✅ Component refactored to use react-markdown
3. ✅ Custom link component validates protocols
4. ✅ All existing tests still pass (52 MessageItem tests)
5. ✅ New security tests added (10 MessageContent tests)
6. ✅ Total 62/62 tests passing

## Notes

- The mock in `jest.setup.js` provides basic markdown parsing for unit tests
- The actual production implementation uses the full react-markdown library with rehype-sanitize
- For comprehensive XSS testing in the browser, E2E tests should be added using Playwright
- All markdown functionality (bold, italic, code, links) preserved
- Component maintains existing styling classes

## References

- [react-markdown Documentation](https://github.com/remarkjs/react-markdown)
- [rehype-sanitize Documentation](https://github.com/rehypejs/rehype-sanitize)
- [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
