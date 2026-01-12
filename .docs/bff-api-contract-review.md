# BFF API Contract Compliance Review

**Date**: 2026-01-11
**Reviewer**: Senior Code Reviewer
**Scope**: Next.js BFF API routes in `apps/web/app/api/` against OpenAPI spec in `specs/002-claude-agent-web/contracts/openapi-extensions.yaml`

---

## Executive Summary

**Overall Compliance**: **CRITICAL VIOLATIONS FOUND**

The BFF API implementation has **multiple critical contract violations** that must be addressed before deployment. While some endpoints align with the spec, there are significant gaps in:

1. **Response Schema Compliance** - Missing required wrapper objects
2. **HTTP Status Codes** - Incorrect status codes for DELETE operations
3. **Error Response Format** - Inconsistent error structures
4. **Authentication Enforcement** - Missing security middleware
5. **Query Parameter Support** - Missing filtering/pagination on list endpoints
6. **Missing Endpoints** - Several spec-defined endpoints not implemented

---

## Critical Issues (Must Fix)

### 1. Projects API - Response Schema Violations

**File**: `/mnt/cache/workspace/claude-agent-api/apps/web/app/api/projects/route.ts`

**Issue**: GET response returns bare array instead of wrapped object

**Spec Requirement**:
```yaml
responses:
  '200':
    content:
      application/json:
        schema:
          type: object
          properties:
            projects:
              type: array
            total:
              type: integer
```

**Current Implementation**:
```typescript
return NextResponse.json(mockProjects); // Returns bare array
```

**Required Fix**:
```typescript
return NextResponse.json({
  projects: mockProjects,
  total: mockProjects.length
});
```

---

**Issue**: POST request body doesn't validate all required fields

**Spec Requirement**:
```yaml
required:
  - name
properties:
  name:
    type: string
    minLength: 1
    maxLength: 100
  path:
    type: string
    description: Optional custom path
  metadata:
    type: object
```

**Current Implementation**:
```typescript
const { name, path } = body as { name: string; path: string };
if (!name || !path) { // Incorrectly requires path
  return NextResponse.json(
    { error: "Name and path are required" },
    { status: 400 }
  );
}
```

**Required Fix**:
- `path` is OPTIONAL per spec
- `name` must be validated for minLength/maxLength
- Missing `metadata` support

---

**Issue**: POST returns 201 with project object but spec expects wrapped object

**Current Implementation**:
```typescript
return NextResponse.json(newProject, { status: 201 });
```

**Spec Requirement**: Should return the Project schema directly (this one is actually correct per spec)

---

**Issue**: Missing query parameter support

**Spec Requirement**:
```yaml
parameters:
  - name: sort
    schema:
      type: string
      enum: [name, created_at, last_accessed_at]
      default: last_accessed_at
  - name: order
    schema:
      type: string
      enum: [asc, desc]
      default: desc
```

**Current Implementation**: No query parameter handling

**Required Fix**: Implement sorting logic

---

### 2. Projects Detail API - DELETE Status Code Violation

**File**: `/mnt/cache/workspace/claude-agent-api/apps/web/app/api/projects/[id]/route.ts`

**Issue**: DELETE returns 200 with body instead of 204 No Content

**Spec Requirement**:
```yaml
responses:
  '204':
    description: Project deleted successfully
```

**Current Implementation**:
```typescript
return NextResponse.json({ success: true }); // Returns 200 with body
```

**Required Fix**:
```typescript
return new NextResponse(null, { status: 204 });
```

---

### 3. Agents API - Response Schema Violations

**File**: `/mnt/cache/workspace/claude-agent-api/apps/web/app/api/agents/route.ts`

**Issue**: POST response wraps in `{ agent: ... }` but spec expects bare object

**Spec Requirement**:
```yaml
responses:
  '201':
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/AgentDefinition'
```

**Current Implementation**:
```typescript
return NextResponse.json({
  agent: data.agent as AgentDefinition, // Extra wrapper
}, { status: 201 });
```

**Required Fix**:
```typescript
return NextResponse.json(data.agent as AgentDefinition, { status: 201 });
```

**Note**: This pattern is repeated across all agent/skill/slash-command endpoints.

---

### 4. Agents Detail API - DELETE Status Code Violation

**File**: `/mnt/cache/workspace/claude-agent-api/apps/web/app/api/agents/[id]/route.ts`

**Issue**: DELETE returns 200 with message body instead of 204 No Content

**Spec Requirement**:
```yaml
responses:
  '204':
    description: Agent deleted
```

**Current Implementation**:
```typescript
return NextResponse.json(
  { message: 'Agent deleted successfully' },
  { status: 200 }
);
```

**Required Fix**:
```typescript
return new NextResponse(null, { status: 204 });
```

**Scope**: Same issue in skills, slash-commands DELETE endpoints

---

### 5. Agent Share API - Response Schema Violation

**File**: `/mnt/cache/workspace/claude-agent-api/apps/web/app/api/agents/[id]/share/route.ts`

**Issue**: Response includes `agent_id` field not in spec

**Spec Requirement**:
```yaml
schema:
  type: object
  properties:
    share_url:
      type: string
      format: uri
    share_token:
      type: string
```

**Current Implementation**:
```typescript
return NextResponse.json({
  share_url: data.share_url,
  agent_id: id, // Not in spec
});
```

**Required Fix**:
```typescript
return NextResponse.json({
  share_url: data.share_url,
  share_token: data.share_token // Add missing field
});
```

---

### 6. Tool Presets API - Schema Field Mismatches

**File**: `/mnt/cache/workspace/claude-agent-api/apps/web/app/api/tool-presets/route.ts`

**Issue**: Response maps `allowed_tools` to `tools` but spec uses `allowed_tools`

**Spec Schema**:
```yaml
properties:
  allowed_tools:
    type: array
    items:
      type: string
  disallowed_tools:
    type: array
    items:
      type: string
    default: []
  is_system:
    type: boolean
    default: false
```

**Current Implementation**:
```typescript
function mapPreset(preset: Record<string, unknown>) {
  const tools = Array.isArray(preset.allowed_tools)
    ? preset.allowed_tools
    : Array.isArray(preset.tools)
      ? preset.tools
      : [];
  return {
    // ...
    tools, // Should be allowed_tools
    is_default: preset.is_system ?? preset.is_default, // Should be is_system
  };
}
```

**Required Fix**: Return fields exactly as specified in OpenAPI schema

---

### 7. MCP Servers API - Missing Schema Field

**File**: `/mnt/cache/workspace/claude-agent-api/apps/web/app/api/mcp-servers/route.ts`

**Issue**: POST request validation expects `type` but spec uses `transport_type`

**Spec Request Body**:
```yaml
required:
  - name
  - type
  - config
properties:
  name:
    type: string
  type:
    type: string
    enum: [stdio, sse, http]
  config:
    type: object
```

**Spec Response Schema**:
```yaml
McpServerConfig:
  properties:
    transport_type:
      type: string
      enum: [stdio, sse, http]
```

**Analysis**: The spec is internally inconsistent. The request body uses `type` but the response schema uses `transport_type`. The implementation follows the request spec but may cause confusion.

**Recommendation**: Clarify with backend team which field name is canonical.

---

### 8. Sessions API - Missing Query Parameters

**File**: `/mnt/cache/workspace/claude-agent-api/apps/web/app/api/sessions/route.ts`

**Issue**: GET endpoint doesn't support filtering/pagination

**Spec Requirements**:
```yaml
parameters:
  - name: mode
    schema:
      enum: [brainstorm, code]
  - name: project_id
    schema:
      type: string
      format: uuid
  - name: tags
    schema:
      type: array
      items:
        type: string
  - name: search
    schema:
      type: string
  - name: page
    schema:
      type: integer
      default: 1
  - name: page_size
    schema:
      type: integer
      default: 50
      maximum: 100
```

**Current Implementation**: No query parameter handling

**Required Fix**: Extract and forward query parameters to backend

---

### 9. Sessions Response Schema - Missing Pagination Metadata

**Issue**: GET response doesn't include pagination metadata

**Spec Requirement**:
```yaml
schema:
  type: object
  properties:
    sessions:
      type: array
    total:
      type: integer
    page:
      type: integer
    page_size:
      type: integer
```

**Current Implementation**:
```typescript
return NextResponse.json({
  sessions: data.sessions || [],
  // Missing: total, page, page_size
});
```

---

### 10. Error Response Format Inconsistency

**Issue**: Error responses use different structures across endpoints

**Spec Requirement**:
```yaml
Error:
  type: object
  required:
    - code
    - message
  properties:
    code:
      type: string
    message:
      type: string
    details:
      type: object
```

**Examples of Inconsistency**:

```typescript
// agents/route.ts
return NextResponse.json(
  { error: error.message || 'Failed to fetch agents' }, // Bare string
  { status: response.status }
);

// mcp-servers/route.ts
return NextResponse.json(
  {
    error: {
      code: 'INVALID_API_KEY',
      message: 'API key is required'
    }
  }, // Correct structure
  { status: 401 }
);
```

**Required Fix**: Standardize all error responses to use `{ code, message, details? }` structure

---

## Important Issues (Should Fix)

### 11. Missing Authentication Enforcement

**Issue**: Security scheme defined in spec but not enforced in BFF layer

**Spec Requirement**:
```yaml
security:
  - ApiKeyAuth: []

securitySchemes:
  ApiKeyAuth:
    type: apiKey
    in: header
    name: X-API-Key
```

**Current Implementation**: Some routes check for API key, others don't

**Examples**:
- `mcp-servers/route.ts`: Checks API key ✓
- `agents/route.ts`: Relies on backend auth (forwards Authorization header)
- `projects/route.ts`: No auth checks at all ✗

**Recommendation**: Implement consistent auth middleware for all routes

---

### 12. TypeScript Type Mismatches

**File**: `/mnt/cache/workspace/claude-agent-api/apps/web/types/index.ts`

**Issue 1**: `McpServerConfig.type` vs `transport_type`

```typescript
export interface McpServerConfig {
  id: string;
  name: string;
  type: McpTransportType; // Should be transport_type per spec
  // ...
}
```

**Issue 2**: `ToolPreset.tools` vs `allowed_tools`

```typescript
export interface ToolPreset {
  tools: string[]; // Should be allowed_tools per spec
  // Missing: disallowed_tools, is_system
}
```

**Required Fix**: Align TypeScript interfaces with OpenAPI schema field names

---

### 13. Missing Route Parameter Validation

**Issue**: Dynamic route parameters not validated before use

**Example** (`agents/[id]/route.ts`):
```typescript
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params; // No UUID validation
    // ...
  }
}
```

**Recommendation**: Add UUID format validation for all `id` path parameters

---

## Suggestions (Nice to Have)

### 14. Inconsistent API Base URL Patterns

**Issue**: Different URL construction approaches

```typescript
// Some files
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:54000';
fetch(`${API_BASE_URL}/agents`, ...);

// Other files
const BACKEND_API_URL = process.env.API_BASE_URL || 'http://localhost:54000/api/v1';
fetch(`${BACKEND_API_URL}/mcp-servers`, ...);
```

**Recommendation**: Standardize on one pattern with `/api/v1` prefix

---

### 15. Missing Request/Response Logging

**Issue**: No structured logging for debugging

**Recommendation**: Add request/response logging with correlation IDs

---

### 16. No Request Timeout Handling

**Issue**: Backend proxy calls have no timeout

**Recommendation**: Add timeout to all `fetch()` calls

```typescript
const response = await fetch(url, {
  ...options,
  signal: AbortSignal.timeout(30000) // 30s timeout
});
```

---

## Missing Endpoints

The following endpoints are defined in the spec but **NOT IMPLEMENTED**:

1. **Skills Share** - `POST /api/skills/{id}/share` (endpoint exists but not reviewed in detail)
2. **Tools List** - Implementation exists at `/api/tools/route.ts` but not in spec (out of scope for this review)

---

## Route-by-Route Compliance Matrix

| Route | Method | Status Code | Request Schema | Response Schema | Auth | Query Params | Notes |
|-------|--------|-------------|----------------|-----------------|------|--------------|-------|
| `/projects` | GET | ✓ | N/A | ✗ Missing wrapper | ✗ | ✗ Missing sort/order | Critical |
| `/projects` | POST | ✓ | ✗ Path required incorrectly | ✓ | ✗ | N/A | Critical |
| `/projects/{id}` | GET | ✓ | N/A | ✓ | ✗ | N/A | Auth missing |
| `/projects/{id}` | PATCH | ✓ | ✓ | ✓ | ✗ | N/A | Auth missing |
| `/projects/{id}` | DELETE | ✗ Returns 200 | N/A | ✗ Should be 204 | ✗ | N/A | Critical |
| `/agents` | GET | ✓ | N/A | ✓ | ✗ | N/A | Auth inconsistent |
| `/agents` | POST | ✓ | ✓ | ✗ Extra wrapper | ✗ | N/A | Critical |
| `/agents/{id}` | GET | ✓ | N/A | ✗ Extra wrapper | ✗ | N/A | Important |
| `/agents/{id}` | PUT | ✓ | ✓ | ✗ Extra wrapper | ✗ | N/A | Important |
| `/agents/{id}` | DELETE | ✗ Returns 200 | N/A | ✗ Should be 204 | ✗ | N/A | Critical |
| `/agents/{id}/share` | POST | ✓ | N/A | ✗ Wrong fields | ✗ | N/A | Critical |
| `/skills` | GET | ✓ | N/A | ✓ | ✗ | N/A | Auth inconsistent |
| `/skills` | POST | ✓ | ✓ | ✗ Extra wrapper | ✗ | N/A | Critical |
| `/skills/{id}` | GET | ✓ | N/A | ✗ Extra wrapper | ✗ | N/A | Important |
| `/skills/{id}` | PUT | ✓ | ✓ | ✗ Extra wrapper | ✗ | N/A | Important |
| `/skills/{id}` | DELETE | ✗ Returns 200 | N/A | ✗ Should be 204 | ✗ | N/A | Critical |
| `/slash-commands` | GET | ✓ | N/A | ✓ | ✗ | N/A | Auth inconsistent |
| `/slash-commands` | POST | ✓ | ✓ | ✗ Extra wrapper | ✗ | N/A | Critical |
| `/slash-commands/{id}` | GET | ✓ | N/A | ✗ Extra wrapper | ✗ | N/A | Important |
| `/slash-commands/{id}` | PUT | ✓ | ✓ | ✗ Extra wrapper | ✗ | N/A | Important |
| `/slash-commands/{id}` | DELETE | ✗ Returns 200 | N/A | ✗ Should be 204 | ✗ | N/A | Critical |
| `/tool-presets` | GET | ✓ | N/A | ✗ Wrong field names | ✓ | N/A | Critical |
| `/tool-presets` | POST | ✓ | ✓ | ✗ Wrong field names | ✓ | N/A | Critical |
| `/tool-presets/{id}` | GET | ✓ | N/A | ✗ Wrong field names | ✓ | N/A | Critical |
| `/tool-presets/{id}` | PUT | ✓ | ✓ | ✗ Wrong field names | ✓ | N/A | Critical |
| `/tool-presets/{id}` | DELETE | ✓ | N/A | ✓ | ✓ | N/A | OK |
| `/mcp-servers` | GET | ✓ | N/A | ✓ | ✓ | N/A | OK |
| `/mcp-servers` | POST | ✓ | ✓ | ✓ | ✓ | N/A | OK |
| `/mcp-servers/{name}` | GET | ✓ | N/A | ✓ | ✓ | N/A | OK |
| `/mcp-servers/{name}` | PUT | ✓ | ✓ | ✓ | ✓ | N/A | OK |
| `/mcp-servers/{name}` | DELETE | ✓ | N/A | ✓ | ✓ | N/A | OK |
| `/mcp-servers/{name}/resources` | GET | ✓ | N/A | ✓ | ✓ | N/A | OK |
| `/mcp-servers/{name}/resources/{uri}` | GET | ✓ | N/A | ✓ | ✓ | N/A | OK |
| `/sessions` | GET | ✓ | N/A | ✗ Missing pagination | ✗ | ✗ Missing filters | Critical |
| `/sessions` | POST | ✓ | ✓ | ✗ Extra wrapper | ✗ | N/A | Critical |
| `/sessions/{id}/tags` | PATCH | ✓ | ✓ | ✗ Extra wrapper | ✗ | N/A | Important |
| `/sessions/{id}/promote` | POST | ✓ | ✓ | ✗ Extra wrapper | ✗ | N/A | Important |

**Legend**:
- ✓ = Compliant
- ✗ = Non-compliant
- N/A = Not applicable

---

## Recommendations

### Immediate Actions (Before Deployment)

1. **Fix DELETE endpoints** - Return 204 No Content across all resource deletion endpoints
2. **Fix response wrappers** - Remove extra object wrappers from single-resource responses
3. **Fix error format** - Standardize on `{ code, message, details? }` structure
4. **Fix tool preset fields** - Use `allowed_tools`, `disallowed_tools`, `is_system`
5. **Fix agent share response** - Include `share_token`, remove `agent_id`
6. **Fix projects GET** - Wrap array in `{ projects, total }` object
7. **Fix projects POST** - Make `path` optional, add `metadata` support

### Short-term (Next Sprint)

8. **Add query parameter support** - Implement filtering, sorting, pagination
9. **Add auth middleware** - Consistent API key validation across all routes
10. **Add request validation** - UUID format checks, required field validation
11. **Update TypeScript types** - Align field names with OpenAPI spec

### Medium-term

12. **Add request timeouts** - Prevent hanging requests to backend
13. **Add structured logging** - Request/response logging with correlation IDs
14. **Add integration tests** - Contract testing against OpenAPI spec
15. **Resolve spec ambiguities** - Clarify `type` vs `transport_type` with backend team

---

## Testing Recommendations

### Contract Testing

Use tools like Prism or Spectral to validate:

```bash
# Install Prism
npm install -g @stoplight/prism-cli

# Validate BFF responses against spec
prism mock specs/002-claude-agent-web/contracts/openapi-extensions.yaml

# Run BFF tests against mock
npm test -- --api-mock
```

### Integration Testing

Create test suite covering:

1. All HTTP methods for each endpoint
2. Success and error paths
3. Request validation (missing fields, invalid types)
4. Response schema validation
5. Status code compliance
6. Authentication/authorization

### Type Safety Testing

```bash
# Generate TypeScript types from OpenAPI spec
npx openapi-typescript specs/002-claude-agent-web/contracts/openapi-extensions.yaml -o apps/web/types/api.generated.ts

# Compare with manually written types
```

---

## Conclusion

The BFF API implementation has **significant contract violations** that must be addressed before production deployment. The most critical issues are:

1. Incorrect HTTP status codes (DELETE endpoints)
2. Response schema mismatches (extra wrappers, wrong field names)
3. Missing query parameter support (filtering, pagination)
4. Inconsistent error formatting

**Estimated Effort**: 2-3 days to fix all critical and important issues.

**Recommended Approach**:
1. Create shared utility functions for error responses, auth checks
2. Fix all DELETE endpoints in one pass
3. Standardize response wrapping logic
4. Add contract tests to prevent regressions

**Risk Assessment**: **HIGH** - These violations will cause frontend integration failures and potential data inconsistencies.

---

**Reviewed By**: Senior Code Reviewer
**Review Date**: 2026-01-11
**Next Review**: After fixes are implemented
