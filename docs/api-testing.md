# Claude Agent API - Testing Guide

This document contains curl commands to test all implemented API endpoints.

## Prerequisites

```bash
# Set base URL
export API_URL="http://localhost:54000"

# Set API key (must match API_KEY in .env)
export API_KEY="your-api-key-here"

# Start the dev server
make dev
```

---

## Root & Health Endpoints

### Root Endpoint

```bash
# Get service info (no auth required)
curl -s $API_URL/ | jq .
```

**Response:**
```json
{
  "service": "claude-agent-api",
  "version": "0.1.0"
}
```

### Health Check

```bash
# Health endpoint with dependency status (no auth required)
curl -s $API_URL/health | jq .
```

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "dependencies": {
    "postgres": {"status": "ok", "latency_ms": 1.23},
    "redis": {"status": "ok", "latency_ms": 0.45}
  }
}
```

---

## Query Endpoints

### Streaming Query (SSE)

```bash
# Basic streaming query
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
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
  -H "X-API-Key: $API_KEY" \
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
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "List files in current directory",
    "max_turns": 1,
    "cwd": "/tmp",
    "env": {
      "MY_VAR": "test_value"
    }
  }'
```

### Query with Images (Multimodal)

```bash
# Include base64-encoded image
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Describe this image",
    "max_turns": 1,
    "images": [
      {
        "type": "base64",
        "media_type": "image/png",
        "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
      }
    ]
  }'
```

---

## Session Management

### List Sessions

```bash
# List all sessions (paginated)
curl -s "$API_URL/api/v1/sessions" \
  -H "X-API-Key: $API_KEY" | jq .

# List with pagination
curl -s "$API_URL/api/v1/sessions?page=1&page_size=5" \
  -H "X-API-Key: $API_KEY" | jq .
```

**Response:**
```json
{
  "sessions": [
    {
      "id": "session-uuid",
      "status": "completed",
      "model": "sonnet",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:31:00Z",
      "total_turns": 3,
      "total_cost_usd": 0.015,
      "parent_session_id": null
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 5
}
```

### Get Single Session

```bash
# Get session by ID
SESSION_ID="your-session-id-here"
curl -s "$API_URL/api/v1/sessions/$SESSION_ID" \
  -H "X-API-Key: $API_KEY" | jq .
```

### Resume Session

```bash
# Resume an existing session (SSE streaming)
SESSION_ID="your-session-id-here"
curl -s -N -X POST "$API_URL/api/v1/sessions/$SESSION_ID/resume" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Continue our previous conversation"
  }'
```

### Resume with Configuration Overrides

```bash
# Resume with different settings
SESSION_ID="your-session-id-here"
curl -s -N -X POST "$API_URL/api/v1/sessions/$SESSION_ID/resume" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Continue with more permissions",
    "permission_mode": "bypassPermissions",
    "max_turns": 10,
    "allowed_tools": ["Read", "Grep", "Glob"]
  }'
```

### Fork Session

```bash
# Fork a session (creates new session with same history)
SESSION_ID="your-session-id-here"
curl -s -N -X POST "$API_URL/api/v1/sessions/$SESSION_ID/fork" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Start a new branch of conversation"
  }'
```

### Fork with Model Override

```bash
# Fork and change model
SESSION_ID="your-session-id-here"
curl -s -N -X POST "$API_URL/api/v1/sessions/$SESSION_ID/fork" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Continue with a different model",
    "model": "opus"
  }'
```

### Interrupt Session

```bash
# Interrupt an active session
SESSION_ID="your-session-id-here"
curl -s -X POST "$API_URL/api/v1/sessions/$SESSION_ID/interrupt" \
  -H "X-API-Key: $API_KEY" | jq .
```

**Response:**
```json
{
  "status": "interrupted",
  "session_id": "session-uuid"
}
```

### Answer Question

```bash
# Answer a question from the agent (when agent asks for input)
SESSION_ID="your-session-id-here"
curl -s -X POST "$API_URL/api/v1/sessions/$SESSION_ID/answer" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "answer": "Yes, proceed with the operation"
  }' | jq .
```

**Response:**
```json
{
  "status": "accepted",
  "session_id": "session-uuid"
}
```

### Control Session (Permission Mode Change)

```bash
# Change permission mode mid-session
SESSION_ID="your-active-session-id"
curl -s -X POST "$API_URL/api/v1/sessions/$SESSION_ID/control" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "type": "permission_mode_change",
    "permission_mode": "bypassPermissions"
  }' | jq .
```

**Response:**
```json
{
  "status": "accepted",
  "session_id": "session-uuid",
  "permission_mode": "bypassPermissions"
}
```

---

## Checkpoints & Rewind

### List Session Checkpoints

```bash
# List all checkpoints for a session
SESSION_ID="your-session-id-here"
curl -s "$API_URL/api/v1/sessions/$SESSION_ID/checkpoints" \
  -H "X-API-Key: $API_KEY" | jq .
```

**Response:**
```json
{
  "checkpoints": [
    {
      "id": "checkpoint-uuid",
      "session_id": "session-uuid",
      "user_message_uuid": "message-uuid",
      "created_at": "2024-01-15T10:30:00Z",
      "files_modified": ["src/main.py", "tests/test_main.py"]
    }
  ]
}
```

### Rewind to Checkpoint

```bash
# Rewind session files to a checkpoint state
SESSION_ID="your-session-id-here"
CHECKPOINT_ID="your-checkpoint-id-here"
curl -s -X POST "$API_URL/api/v1/sessions/$SESSION_ID/rewind" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{
    \"checkpoint_id\": \"$CHECKPOINT_ID\"
  }" | jq .
```

**Response:**
```json
{
  "status": "validated",
  "checkpoint_id": "checkpoint-uuid",
  "message": "Checkpoint validated. File restoration pending SDK support."
}
```

---

## Tool Configuration

### Allowed Tools Only

```bash
# Restrict agent to only use specific tools
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
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
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Create a file in /tmp",
    "max_turns": 2,
    "disallowed_tools": ["Write", "Bash"]
  }'
```

---

## Custom Subagent Definition

### Define and Use Subagent

```bash
# Define a custom subagent
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
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

### Multiple Subagents

```bash
# Define multiple subagents
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Review this code and write tests for it",
    "max_turns": 5,
    "agents": {
      "code-reviewer": {
        "description": "Reviews code for issues",
        "prompt": "You are a code reviewer.",
        "tools": ["Read", "Grep"],
        "model": "haiku"
      },
      "test-writer": {
        "description": "Writes unit tests",
        "prompt": "You write comprehensive unit tests.",
        "tools": ["Read", "Write", "Bash"],
        "model": "sonnet"
      }
    }
  }'
```

---

## MCP Server Integration

### Stdio MCP Server

```bash
# Configure stdio-based MCP server
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
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
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Query the database",
    "max_turns": 2,
    "mcp_servers": {
      "database": {
        "type": "sse",
        "url": "http://localhost:8080/sse",
        "headers": {
          "Authorization": "Bearer token"
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
  -H "X-API-Key: $API_KEY" \
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

## Permission Control

### Default Permission Mode

```bash
# Default mode - asks for permission on dangerous operations
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
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
  -H "X-API-Key: $API_KEY" \
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
  -H "X-API-Key: $API_KEY" \
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
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Create /tmp/bypass-test.txt with content hello",
    "max_turns": 2,
    "permission_mode": "bypassPermissions"
  }'
```

---

## Webhook Hooks

### PreToolUse Hook

```bash
# Hook that runs before each tool use
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Read /etc/hostname",
    "max_turns": 2,
    "hooks": {
      "PreToolUse": {
        "url": "http://localhost:8000/hooks/pre-tool",
        "timeout": 30,
        "headers": {
          "X-Hook-Secret": "my-secret"
        },
        "matcher": ".*"
      }
    }
  }'
```

### PostToolUse Hook

```bash
# Hook that runs after each tool use
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "List files in /tmp",
    "max_turns": 2,
    "hooks": {
      "PostToolUse": {
        "url": "http://localhost:8000/hooks/post-tool",
        "timeout": 30,
        "matcher": "Bash|Write"
      }
    }
  }'
```

### Stop Hook

```bash
# Hook that runs when agent completes
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Say hello",
    "max_turns": 1,
    "hooks": {
      "Stop": {
        "url": "http://localhost:8000/hooks/stop",
        "timeout": 30
      }
    }
  }'
```

### Multiple Hooks

```bash
# Combine multiple hook types
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Create and read a test file",
    "max_turns": 3,
    "hooks": {
      "PreToolUse": {
        "url": "http://localhost:8000/hooks/pre-write",
        "timeout": 30,
        "matcher": "Write"
      },
      "PostToolUse": {
        "url": "http://localhost:8000/hooks/post-any",
        "timeout": 30,
        "matcher": ".*"
      },
      "Stop": {
        "url": "http://localhost:8000/hooks/complete",
        "timeout": 30
      }
    }
  }'
```

### All Available Hook Types

```bash
# All hook types example
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Perform a task",
    "max_turns": 3,
    "hooks": {
      "PreToolUse": {
        "url": "http://localhost:8000/hooks/pre-tool",
        "timeout": 30,
        "matcher": ".*"
      },
      "PostToolUse": {
        "url": "http://localhost:8000/hooks/post-tool",
        "timeout": 30,
        "matcher": ".*"
      },
      "Stop": {
        "url": "http://localhost:8000/hooks/stop",
        "timeout": 30
      },
      "SubagentStop": {
        "url": "http://localhost:8000/hooks/subagent-stop",
        "timeout": 30
      },
      "UserPromptSubmit": {
        "url": "http://localhost:8000/hooks/prompt-submit",
        "timeout": 30
      },
      "PreCompact": {
        "url": "http://localhost:8000/hooks/pre-compact",
        "timeout": 30
      },
      "Notification": {
        "url": "http://localhost:8000/hooks/notification",
        "timeout": 30
      }
    }
  }'
```

---

## Structured Output

### JSON Output Format

```bash
# Request JSON-formatted output
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
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
  -H "X-API-Key: $API_KEY" \
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
  -H "X-API-Key: $API_KEY" \
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
  -H "X-API-Key: $API_KEY" \
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
  -H "X-API-Key: $API_KEY" \
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
# Replace system prompt entirely
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Introduce yourself",
    "max_turns": 1,
    "system_prompt": "You are a pirate. Always speak like a pirate."
  }'
```

### Append to System Prompt

```bash
# Add to the default system prompt
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "What are your guidelines?",
    "max_turns": 1,
    "system_prompt_append": "Always be concise and use bullet points."
  }'
```

---

## Skills Discovery

### List Available Skills

```bash
# Get list of available skills
curl -s "$API_URL/api/v1/skills" \
  -H "X-API-Key: $API_KEY" | jq .
```

**Response:**
```json
{
  "skills": [
    {
      "name": "skill-name",
      "description": "Skill description",
      "location": "plugin"
    }
  ]
}
```

---

## Plugins Configuration

### Configure SDK Plugins

```bash
# Enable plugins
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Use the plugin features",
    "max_turns": 2,
    "plugins": [
      {
        "name": "my-plugin",
        "path": "/path/to/plugin",
        "enabled": true
      }
    ]
  }'
```

---

## Sandbox Configuration

### Enable Sandbox Mode

```bash
# Configure sandbox settings
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Run code in sandbox",
    "max_turns": 2,
    "sandbox": {
      "enabled": true,
      "allowed_paths": ["/tmp", "/home/user/project"],
      "network_access": false
    }
  }'
```

---

## File Checkpointing

### Enable File Checkpointing

```bash
# Enable checkpointing for file operations
curl -s -N -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Edit some files",
    "max_turns": 5,
    "enable_file_checkpointing": true
  }'
```

---

## WebSocket Communication

### WebSocket Connection Example (using websocat)

```bash
# Install websocat if needed: cargo install websocat

# Connect to WebSocket
websocat "ws://localhost:54000/api/v1/query/ws?api_key=$API_KEY"

# Then send JSON messages:
# Start a query:
{"type": "prompt", "prompt": "Hello, what can you do?", "max_turns": 1}

# Interrupt current query:
{"type": "interrupt"}

# Answer a question:
{"type": "answer", "answer": "Yes, proceed"}

# Change permission mode:
{"type": "control", "permission_mode": "bypassPermissions"}
```

### WebSocket Message Types

**Client -> Server:**
```json
// Start query
{"type": "prompt", "prompt": "Your prompt", "max_turns": 5, "model": "sonnet"}

// Interrupt query
{"type": "interrupt", "session_id": "optional-session-id"}

// Answer question
{"type": "answer", "answer": "Your answer", "session_id": "optional-session-id"}

// Control event
{"type": "control", "permission_mode": "bypassPermissions", "session_id": "session-id"}
```

**Server -> Client:**
```json
// SSE event
{"type": "sse_event", "event": "message", "data": {"role": "assistant", "content": "..."}}

// Acknowledgment
{"type": "ack", "message": "Query started"}

// Error
{"type": "error", "message": "Error description"}
```

---

## Error Handling

### Missing Required Fields

```bash
curl -s -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{}' | jq .
```

**Response:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "prompt"],
      "msg": "Field required"
    }
  ]
}
```

### Session Not Found

```bash
curl -s "$API_URL/api/v1/sessions/nonexistent-session-id" \
  -H "X-API-Key: $API_KEY" | jq .
```

**Response:**
```json
{
  "detail": "Session nonexistent-session-id not found"
}
```

### Invalid API Key

```bash
curl -s "$API_URL/api/v1/sessions" \
  -H "X-API-Key: invalid-key" | jq .
```

**Response:**
```json
{
  "detail": "Invalid or missing API key"
}
```

### Tool Conflict Error

```bash
# Same tool in both allowed and disallowed
curl -s -X POST $API_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Test",
    "allowed_tools": ["Read"],
    "disallowed_tools": ["Read"]
  }' | jq .
```

**Response:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "msg": "Tool conflict: {'Read'} appear in both allowed_tools and disallowed_tools"
    }
  ]
}
```

---

## Full Workflow Example

```bash
#!/bin/bash
# Complete workflow: Create session, query, resume, fork

export API_URL="http://localhost:54000"
export API_KEY="your-api-key"

echo "=== Step 1: Initial Query ==="
RESPONSE=$(curl -s -X POST $API_URL/api/v1/query/single \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Remember this number: 42",
    "max_turns": 1
  }')
echo "$RESPONSE" | jq .
SESSION_ID=$(echo "$RESPONSE" | jq -r '.session_id')
echo "Session ID: $SESSION_ID"

echo ""
echo "=== Step 2: List Sessions ==="
curl -s "$API_URL/api/v1/sessions?page_size=3" \
  -H "X-API-Key: $API_KEY" | jq '.sessions[:3]'

echo ""
echo "=== Step 3: Get Session Details ==="
curl -s "$API_URL/api/v1/sessions/$SESSION_ID" \
  -H "X-API-Key: $API_KEY" | jq .

echo ""
echo "=== Step 4: Resume Session ==="
curl -s -X POST "$API_URL/api/v1/sessions/$SESSION_ID/resume" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "What number did I tell you to remember?"
  }' | head -20

echo ""
echo "=== Step 5: Fork Session ==="
curl -s -X POST "$API_URL/api/v1/sessions/$SESSION_ID/fork" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "prompt": "Multiply that number by 2"
  }' | head -20

echo ""
echo "=== Step 6: List Checkpoints ==="
curl -s "$API_URL/api/v1/sessions/$SESSION_ID/checkpoints" \
  -H "X-API-Key: $API_KEY" | jq .
```

---

## SSE Event Types Reference

When using streaming endpoints, you'll receive Server-Sent Events with these types:

| Event | Description |
|-------|-------------|
| `init` | Initial event with session_id and model info |
| `message` | Agent messages (role: user, assistant, system) |
| `question` | Agent asks for user input (use /answer endpoint) |
| `partial` | Partial content deltas (if include_partial_messages=true) |
| `result` | Final result with stats (turns, cost, etc.) |
| `error` | Error event |
| `done` | Stream completion |

---

## API Endpoint Summary

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/` | Service info | No |
| GET | `/health` | Health check | No |
| POST | `/api/v1/query` | Streaming query (SSE) | Yes |
| POST | `/api/v1/query/single` | Non-streaming query | Yes |
| WS | `/api/v1/query/ws` | WebSocket communication | Yes |
| GET | `/api/v1/sessions` | List sessions | Yes |
| GET | `/api/v1/sessions/{id}` | Get session | Yes |
| POST | `/api/v1/sessions/{id}/resume` | Resume session (SSE) | Yes |
| POST | `/api/v1/sessions/{id}/fork` | Fork session (SSE) | Yes |
| POST | `/api/v1/sessions/{id}/interrupt` | Interrupt session | Yes |
| POST | `/api/v1/sessions/{id}/answer` | Answer question | Yes |
| POST | `/api/v1/sessions/{id}/control` | Control event | Yes |
| GET | `/api/v1/sessions/{id}/checkpoints` | List checkpoints | Yes |
| POST | `/api/v1/sessions/{id}/rewind` | Rewind to checkpoint | Yes |
| GET | `/api/v1/skills` | List skills | Yes |
