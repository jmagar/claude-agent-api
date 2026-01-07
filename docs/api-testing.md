# Claude Agent API - Testing Guide

This document contains curl commands to test all implemented API endpoints.

## Prerequisites

```bash
# Set base URL
export API_URL="http://localhost:54000"

# Start the dev server
make dev
```

---

## Health Check

```bash
# Health endpoint (no auth required)
curl -s $API_URL/health | jq .
```

---

## US1: Basic Agent Query

### Streaming Query (SSE)

```bash
# Basic streaming query
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is 2+2? Answer briefly.",
    "max_turns": 1
  }'
```

### Single Query (Non-streaming)

```bash
# Non-streaming query - returns complete JSON response
curl -s -X POST $API_URL/api/v1/query/single \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the capital of France? Answer in one word.",
    "max_turns": 1
  }' | jq .
```

### Query with Working Directory and Environment

```bash
# Set working directory and environment variables
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "List files in current directory",
    "max_turns": 1,
    "cwd": "/tmp",
    "env": {
      "MY_VAR": "test_value"
    }
  }'
```

---

## US2: Session Management

### List Sessions

```bash
# List all sessions (paginated)
curl -s "$API_URL/api/v1/sessions" | jq .

# List with pagination
curl -s "$API_URL/api/v1/sessions?page=1&page_size=5" | jq .
```

### Get Single Session

```bash
# Get session by ID (replace SESSION_ID)
SESSION_ID="your-session-id-here"
curl -s "$API_URL/api/v1/sessions/$SESSION_ID" | jq .
```

### Resume Session

```bash
# Resume an existing session
SESSION_ID="your-session-id-here"
curl -s -N -X POST "$API_URL/api/v1/sessions/$SESSION_ID/resume" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Continue our previous conversation"
  }'
```

### Fork Session

```bash
# Fork a session (creates new session with same history)
SESSION_ID="your-session-id-here"
curl -s -N -X POST "$API_URL/api/v1/sessions/$SESSION_ID/fork" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Start a new branch of conversation"
  }'
```

### Interrupt Session

```bash
# Interrupt an active session
SESSION_ID="your-session-id-here"
curl -s -X POST "$API_URL/api/v1/sessions/$SESSION_ID/interrupt" | jq .
```

### Answer Question

```bash
# Answer a question from the agent (when agent asks for input)
SESSION_ID="your-session-id-here"
curl -s -X POST "$API_URL/api/v1/sessions/$SESSION_ID/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "answer": "Yes, proceed with the operation"
  }' | jq .
```

---

## US3: Tool Configuration

### Allowed Tools Only

```bash
# Restrict agent to only use specific tools
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Read the contents of /tmp/test.txt",
    "max_turns": 2,
    "allowed_tools": ["Read", "Glob"]
  }'
```

### Disallowed Tools

```bash
# Block specific tools
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a file in /tmp",
    "max_turns": 2,
    "disallowed_tools": ["Write", "Bash"]
  }'
```

---

## US4: Custom Subagent Definition

### Define and Use Subagent

```bash
# Define a custom subagent
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Use the code-reviewer agent to review this code: def add(a,b): return a+b",
    "max_turns": 3,
    "agents": {
      "code-reviewer": {
        "description": "Reviews code for quality and best practices",
        "prompt": "You are a code reviewer. Analyze code for bugs, style issues, and improvements.",
        "tools": ["Read", "Grep", "Glob"],
        "model": "haiku"
      }
    }
  }'
```

---

## US5: MCP Server Integration

### Stdio MCP Server

```bash
# Configure stdio-based MCP server
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Use the filesystem tools to list /tmp",
    "max_turns": 2,
    "mcp_servers": {
      "filesystem": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        "env": {}
      }
    }
  }'
```

### SSE MCP Server

```bash
# Configure SSE-based MCP server
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Query the database",
    "max_turns": 2,
    "mcp_servers": {
      "database": {
        "type": "sse",
        "url": "http://localhost:8080/sse",
        "headers": {
          "Authorization": "Bearer ${DB_TOKEN:-default-token}"
        }
      }
    }
  }'
```

### HTTP MCP Server

```bash
# Configure HTTP-based MCP server
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Search the web",
    "max_turns": 2,
    "mcp_servers": {
      "search": {
        "type": "http",
        "url": "http://localhost:9000/mcp",
        "headers": {}
      }
    }
  }'
```

---

## US6: Permission Control

### Default Permission Mode

```bash
# Default mode - asks for permission on dangerous operations
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a file called /tmp/test-default.txt",
    "max_turns": 2,
    "permission_mode": "default"
  }'
```

### Accept Edits Mode

```bash
# Auto-accept file edits
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Edit /tmp/test.txt and add a new line",
    "max_turns": 2,
    "permission_mode": "acceptEdits"
  }'
```

### Plan Mode

```bash
# Plan mode - agent plans but doesn't execute
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Plan how to refactor this codebase",
    "max_turns": 2,
    "permission_mode": "plan"
  }'
```

### Bypass Permissions Mode

```bash
# Bypass all permission prompts (use with caution!)
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create /tmp/bypass-test.txt with content hello",
    "max_turns": 2,
    "permission_mode": "bypassPermissions"
  }'
```

### Dynamic Permission Mode Change

```bash
# Change permission mode mid-session
SESSION_ID="your-active-session-id"
curl -s -X POST "$API_URL/api/v1/sessions/$SESSION_ID/control" \
  -H "Content-Type: application/json" \
  -d '{
    "permission_mode": "bypassPermissions"
  }' | jq .
```

---

## US7: Hooks for Agent Lifecycle

### PreToolUse Hook

```bash
# Hook that runs before each tool use
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Read /etc/hostname",
    "max_turns": 2,
    "hooks": {
      "PreToolUse": [
        {
          "matcher": ".*",
          "webhook": {
            "url": "http://localhost:8000/hooks/pre-tool",
            "timeout": 5000,
            "headers": {
              "X-Hook-Secret": "my-secret"
            }
          }
        }
      ]
    }
  }'
```

### PostToolUse Hook

```bash
# Hook that runs after each tool use
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "List files in /tmp",
    "max_turns": 2,
    "hooks": {
      "PostToolUse": [
        {
          "matcher": "Bash|Write",
          "webhook": {
            "url": "http://localhost:8000/hooks/post-tool",
            "timeout": 5000
          }
        }
      ]
    }
  }'
```

### Stop Hook

```bash
# Hook that runs when agent completes
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Say hello",
    "max_turns": 1,
    "hooks": {
      "Stop": [
        {
          "webhook": {
            "url": "http://localhost:8000/hooks/stop",
            "timeout": 5000
          }
        }
      ]
    }
  }'
```

### Multiple Hooks

```bash
# Combine multiple hook types
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create and read a test file",
    "max_turns": 3,
    "hooks": {
      "PreToolUse": [
        {
          "matcher": "Write",
          "webhook": {
            "url": "http://localhost:8000/hooks/pre-write",
            "timeout": 5000
          }
        }
      ],
      "PostToolUse": [
        {
          "matcher": ".*",
          "webhook": {
            "url": "http://localhost:8000/hooks/post-any",
            "timeout": 5000
          }
        }
      ],
      "Stop": [
        {
          "webhook": {
            "url": "http://localhost:8000/hooks/complete",
            "timeout": 5000
          }
        }
      ]
    }
  }'
```

---

## US8: Structured Output

### JSON Output Format

```bash
# Request JSON-formatted output
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Return a JSON object with name, age, and city fields using made-up values",
    "max_turns": 1,
    "output_format": {
      "type": "json"
    }
  }'
```

### JSON Schema Output Format

```bash
# Request output matching a specific JSON schema
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Generate a person record",
    "max_turns": 1,
    "output_format": {
      "type": "json_schema",
      "schema": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "age": {"type": "integer"},
          "email": {"type": "string"}
        },
        "required": ["name", "age"]
      }
    }
  }'
```

---

## Model Selection

### Use Haiku (Fast/Cheap)

```bash
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What model are you?",
    "max_turns": 1,
    "model": "haiku"
  }'
```

### Use Sonnet (Balanced)

```bash
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What model are you?",
    "max_turns": 1,
    "model": "sonnet"
  }'
```

### Use Opus (Most Capable)

```bash
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What model are you?",
    "max_turns": 1,
    "model": "opus"
  }'
```

---

## System Prompt Customization

### Custom System Prompt

```bash
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Introduce yourself",
    "max_turns": 1,
    "system_prompt": "You are a pirate. Always speak like a pirate."
  }'
```

---

## Error Handling

### Missing Required Fields

```bash
curl -s -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{}' | jq .
```

### Session Not Found

```bash
curl -s "$API_URL/api/v1/sessions/nonexistent-session-id" | jq .
```

---

## Full Workflow Example

```bash
#!/bin/bash
# Complete workflow: Create session, query, resume, fork

export API_URL="http://localhost:54000"

echo "=== Step 1: Initial Query ==="
RESPONSE=$(curl -s -X POST $API_URL/api/v1/query/single \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Remember this number: 42",
    "max_turns": 1
  }')
echo "$RESPONSE" | jq .
SESSION_ID=$(echo "$RESPONSE" | jq -r '.session_id')
echo "Session ID: $SESSION_ID"

echo ""
echo "=== Step 2: List Sessions ==="
curl -s "$API_URL/api/v1/sessions?page_size=3" | jq '.sessions[:3]'

echo ""
echo "=== Step 3: Get Session Details ==="
curl -s "$API_URL/api/v1/sessions/$SESSION_ID" | jq .

echo ""
echo "=== Step 4: Fork Session ==="
curl -s -X POST "$API_URL/api/v1/sessions/$SESSION_ID/fork" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What number did I tell you to remember?"
  }' | head -20
```
