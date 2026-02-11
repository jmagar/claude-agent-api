# Claude Agent API - cURL Examples

**Base URL:** `http://localhost:54000`
**API Key:** Replace `YOUR_API_KEY` with your actual API key

---

## Table of Contents

- [Authentication](#authentication)
- [Root Endpoints](#root-endpoints)
- [Native API (`/api/v1/*`)](#native-api-apiv1)
  - [Projects](#projects)
  - [Agents](#agents)
  - [Query & Interaction](#query--interaction)
  - [Sessions](#sessions)
  - [Session Control](#session-control)
  - [Checkpoints](#checkpoints)
  - [Skills](#skills)
  - [Slash Commands](#slash-commands)
  - [MCP Servers](#mcp-servers)
  - [Memories](#memories-mem0)
  - [Tool Presets](#tool-presets)
- [OpenAI-Compatible API (`/v1/*`)](#openai-compatible-api-v1)
  - [Chat Completions](#chat-completions)
  - [Models](#models)
  - [Assistants (Beta)](#assistants-beta)
  - [Threads (Beta)](#threads-beta)
  - [Messages (Beta)](#messages-beta)
  - [Runs (Beta)](#runs-beta)

---

## Authentication

### Native API Headers

```bash
-H "X-API-Key: YOUR_API_KEY"
```

### OpenAI API Headers

```bash
-H "Authorization: Bearer YOUR_API_KEY"
```

---

## Root Endpoints

### Get Service Info

```bash
curl http://localhost:54000/
```

### Health Check

```bash
curl http://localhost:54000/health
```

Or:

```bash
curl http://localhost:54000/api/v1/health
```

---

## Native API (`/api/v1/*`)

### Projects

#### List Projects

```bash
curl -X GET http://localhost:54000/api/v1/projects \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Create Project

```bash
curl -X POST http://localhost:54000/api/v1/projects \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "path": "/home/user/projects/my-project",
    "metadata": {
      "description": "A sample project"
    }
  }'
```

#### Get Project

```bash
curl -X GET http://localhost:54000/api/v1/projects/PROJECT_ID \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Update Project

```bash
curl -X PATCH http://localhost:54000/api/v1/projects/PROJECT_ID \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Project Name",
    "metadata": {
      "description": "Updated description"
    }
  }'
```

#### Delete Project

```bash
curl -X DELETE http://localhost:54000/api/v1/projects/PROJECT_ID \
  -H "X-API-Key: YOUR_API_KEY"
```

---

### Agents

#### List Agents

```bash
curl -X GET http://localhost:54000/api/v1/agents \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Create Agent

```bash
curl -X POST http://localhost:54000/api/v1/agents \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Code Assistant",
    "description": "Helps with coding tasks",
    "prompt": "You are a helpful coding assistant that follows best practices.",
    "tools": ["Bash", "Edit", "Read", "Write"],
    "model": "sonnet"
  }'
```

#### Get Agent

```bash
curl -X GET http://localhost:54000/api/v1/agents/AGENT_ID \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Update Agent

```bash
curl -X PUT http://localhost:54000/api/v1/agents/AGENT_ID \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Code Assistant",
    "description": "Enhanced coding assistant",
    "prompt": "You are an expert coding assistant.",
    "tools": ["Bash", "Edit", "Read"],
    "model": "opus"
  }'
```

#### Delete Agent

```bash
curl -X DELETE http://localhost:54000/api/v1/agents/AGENT_ID \
  -H "X-API-Key: YOUR_API_KEY"
```

#### Share Agent

```bash
curl -X POST http://localhost:54000/api/v1/agents/AGENT_ID/share \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

---

### Query & Interaction

#### Streaming Query (SSE)

```bash
curl -N -X POST http://localhost:54000/api/v1/query \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, Claude! Please help me understand async/await in Python.",
    "model": "sonnet",
    "max_turns": 10,
    "permission_mode": "bypassPermissions",
    "include_partial_messages": true
  }'
```

**Note:** The `-N` flag disables buffering for SSE streams.

#### Non-Streaming Query

```bash
curl -X POST http://localhost:54000/api/v1/query/single \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the capital of France?",
    "model": "sonnet"
  }'
```

#### Resume Existing Session

```bash
curl -X POST http://localhost:54000/api/v1/query/single \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Can you explain more about that?",
    "session_id": "SESSION_ID",
    "model": "sonnet"
  }'
```

#### Query with MCP Servers

```bash
curl -X POST http://localhost:54000/api/v1/query/single \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Use the GitHub MCP server to fetch repository info",
    "model": "sonnet",
    "mcp_servers": {
      "github": {
        "type": "stdio",
        "command": "mcp-github",
        "args": ["--repo", "myorg/myrepo"],
        "env": {
          "GITHUB_TOKEN": "ghp_token_here"
        }
      }
    }
  }'
```

#### WebSocket Connection (using websocat)

```bash
# Install websocat first: cargo install websocat
websocat -H="X-API-Key: YOUR_API_KEY" ws://localhost:54000/api/v1/query/ws
```

**Send prompt:**
```json
{"type": "prompt", "prompt": "Hello!", "model": "sonnet"}
```

**Interrupt session:**
```json
{"type": "interrupt", "session_id": "SESSION_ID"}
```

**Answer question:**
```json
{"type": "answer", "session_id": "SESSION_ID", "answer": "Yes, proceed"}
```

**Change permission mode:**
```json
{"type": "control", "session_id": "SESSION_ID", "permission_mode": "default"}
```

---

### Sessions

#### List Sessions

```bash
curl -X GET "http://localhost:54000/api/v1/sessions?page=1&page_size=50" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### List Sessions with Filters

```bash
curl -X GET "http://localhost:54000/api/v1/sessions?mode=code&project_id=PROJECT_ID&tags=feature,bugfix&search=authentication&page=1&page_size=20" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Get Session

```bash
curl -X GET http://localhost:54000/api/v1/sessions/SESSION_ID \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Promote Session

```bash
curl -X POST http://localhost:54000/api/v1/sessions/SESSION_ID/promote \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "PROJECT_ID"
  }'
```

#### Update Session Tags

```bash
curl -X PATCH http://localhost:54000/api/v1/sessions/SESSION_ID/tags \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["feature", "authentication", "urgent"]
  }'
```

---

### Session Control

#### Resume Session

```bash
curl -N -X POST http://localhost:54000/api/v1/sessions/SESSION_ID/resume \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Continue where we left off",
    "permission_mode": "bypassPermissions",
    "max_turns": 10
  }'
```

#### Fork Session

```bash
curl -N -X POST http://localhost:54000/api/v1/sessions/SESSION_ID/fork \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Try a different approach using TypeScript instead",
    "model": "sonnet",
    "permission_mode": "bypassPermissions"
  }'
```

#### Interrupt Session

```bash
curl -X POST http://localhost:54000/api/v1/sessions/SESSION_ID/interrupt \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Send Control Event

```bash
curl -X POST http://localhost:54000/api/v1/sessions/SESSION_ID/control \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "permission_mode_change",
    "permission_mode": "default"
  }'
```

#### Answer Question

```bash
curl -X POST http://localhost:54000/api/v1/sessions/SESSION_ID/answer \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "answer": "Yes, proceed with the changes to the database schema"
  }'
```

---

### Checkpoints

#### List Checkpoints

```bash
curl -X GET http://localhost:54000/api/v1/sessions/SESSION_ID/checkpoints \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Rewind to Checkpoint

```bash
curl -X POST http://localhost:54000/api/v1/sessions/SESSION_ID/rewind \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "checkpoint_id": "CHECKPOINT_ID"
  }'
```

---

### Skills

#### List All Skills

```bash
curl -X GET http://localhost:54000/api/v1/skills \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### List Filesystem Skills Only

```bash
curl -X GET "http://localhost:54000/api/v1/skills?source=filesystem" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### List Database Skills Only

```bash
curl -X GET "http://localhost:54000/api/v1/skills?source=database" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Create Skill

```bash
curl -X POST http://localhost:54000/api/v1/skills \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "python-debugger",
    "description": "Advanced Python debugging techniques",
    "content": "# Python Debugging\n\nUse pdb for interactive debugging...",
    "enabled": true
  }'
```

#### Get Skill (Filesystem)

```bash
curl -X GET http://localhost:54000/api/v1/skills/fs:my-skill \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Get Skill (Database)

```bash
curl -X GET http://localhost:54000/api/v1/skills/SKILL_ID \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Update Skill

```bash
curl -X PUT http://localhost:54000/api/v1/skills/SKILL_ID \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "python-debugger-advanced",
    "description": "Updated description",
    "content": "# Updated content...",
    "enabled": false
  }'
```

#### Delete Skill

```bash
curl -X DELETE http://localhost:54000/api/v1/skills/SKILL_ID \
  -H "X-API-Key: YOUR_API_KEY"
```

---

### Slash Commands

#### List Slash Commands

```bash
curl -X GET http://localhost:54000/api/v1/slash-commands \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Create Slash Command

```bash
curl -X POST http://localhost:54000/api/v1/slash-commands \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "review-pr",
    "description": "Review a pull request for code quality",
    "content": "Review the following pull request for code quality, security issues, and best practices...",
    "enabled": true
  }'
```

#### Get Slash Command

```bash
curl -X GET http://localhost:54000/api/v1/slash-commands/COMMAND_ID \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Update Slash Command

```bash
curl -X PUT http://localhost:54000/api/v1/slash-commands/COMMAND_ID \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "review-pr-thorough",
    "description": "Thorough PR review with security focus",
    "content": "Updated prompt content...",
    "enabled": true
  }'
```

#### Delete Slash Command

```bash
curl -X DELETE http://localhost:54000/api/v1/slash-commands/COMMAND_ID \
  -H "X-API-Key: YOUR_API_KEY"
```

---

### MCP Servers

#### List All MCP Servers

```bash
curl -X GET http://localhost:54000/api/v1/mcp-servers \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### List Filesystem MCP Servers Only

```bash
curl -X GET "http://localhost:54000/api/v1/mcp-servers?source=filesystem" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### List Database MCP Servers Only

```bash
curl -X GET "http://localhost:54000/api/v1/mcp-servers?source=database" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Create MCP Server (stdio)

```bash
curl -X POST http://localhost:54000/api/v1/mcp-servers \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "github-mcp",
    "type": "stdio",
    "config": {
      "command": "mcp-github",
      "args": ["--repo", "myorg/myrepo"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }'
```

#### Create MCP Server (SSE)

```bash
curl -X POST http://localhost:54000/api/v1/mcp-servers \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "slack-mcp",
    "type": "sse",
    "config": {
      "url": "https://api.slack.com/mcp",
      "headers": {
        "Authorization": "Bearer xoxb-your-token"
      }
    }
  }'
```

#### Get MCP Server (Filesystem)

```bash
curl -X GET http://localhost:54000/api/v1/mcp-servers/fs:github \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Get MCP Server (Database)

```bash
curl -X GET http://localhost:54000/api/v1/mcp-servers/github-mcp \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Update MCP Server

```bash
curl -X PUT http://localhost:54000/api/v1/mcp-servers/github-mcp \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "stdio",
    "config": {
      "command": "mcp-github",
      "args": ["--repo", "myorg/different-repo"],
      "env": {
        "GITHUB_TOKEN": "ghp_updated_token"
      },
      "enabled": true
    }
  }'
```

#### Delete MCP Server

```bash
curl -X DELETE http://localhost:54000/api/v1/mcp-servers/github-mcp \
  -H "X-API-Key: YOUR_API_KEY"
```

#### List MCP Resources

```bash
curl -X GET http://localhost:54000/api/v1/mcp-servers/github-mcp/resources \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Get MCP Resource

```bash
curl -X GET "http://localhost:54000/api/v1/mcp-servers/github-mcp/resources/repo://myorg/myrepo/README.md" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Create MCP Share

```bash
curl -X POST http://localhost:54000/api/v1/mcp-servers/github-mcp/share \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "type": "stdio",
      "command": "mcp-github",
      "args": ["--repo", "myorg/myrepo"],
      "env": {
        "GITHUB_TOKEN": "ghp_token"
      }
    }
  }'
```

#### Resolve MCP Share

```bash
curl -X GET http://localhost:54000/api/v1/mcp-servers/share/SHARE_TOKEN \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

---

### Memories (Mem0)

#### Search Memories

```bash
curl -X POST http://localhost:54000/api/v1/memories/search \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are my coding preferences?",
    "limit": 10,
    "enable_graph": true
  }'
```

#### Add Memory

```bash
curl -X POST http://localhost:54000/api/v1/memories \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "User prefers TypeScript over JavaScript and uses functional programming patterns",
    "metadata": {
      "category": "preferences",
      "topic": "coding-style"
    },
    "enable_graph": true
  }'
```

#### Add Memory (Conversation Format)

```bash
curl -X POST http://localhost:54000/api/v1/memories \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "I prefer using async/await over promises"},
      {"role": "assistant", "content": "Noted. I will use async/await syntax in code examples."}
    ],
    "metadata": {
      "category": "preferences"
    },
    "enable_graph": true
  }'
```

#### List All Memories

```bash
curl -X GET http://localhost:54000/api/v1/memories \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Delete Specific Memory

```bash
curl -X DELETE http://localhost:54000/api/v1/memories/MEMORY_ID \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Delete All Memories

```bash
curl -X DELETE http://localhost:54000/api/v1/memories \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

---

### Tool Presets

#### List Tool Presets

```bash
curl -X GET http://localhost:54000/api/v1/tool-presets \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Create Tool Preset

```bash
curl -X POST http://localhost:54000/api/v1/tool-presets \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Read Only",
    "description": "Only read operations allowed",
    "allowed_tools": ["Read", "Glob", "Grep"],
    "disallowed_tools": ["Edit", "Write", "Bash"]
  }'
```

#### Get Tool Preset

```bash
curl -X GET http://localhost:54000/api/v1/tool-presets/PRESET_ID \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### Update Tool Preset

```bash
curl -X PUT http://localhost:54000/api/v1/tool-presets/PRESET_ID \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Read Only Extended",
    "description": "Read operations with LSP support",
    "allowed_tools": ["Read", "Glob", "Grep", "LSP"],
    "disallowed_tools": ["Edit", "Write", "Bash", "Task"]
  }'
```

#### Delete Tool Preset

```bash
curl -X DELETE http://localhost:54000/api/v1/tool-presets/PRESET_ID \
  -H "X-API-Key: YOUR_API_KEY"
```

---

## OpenAI-Compatible API (`/v1/*`)

### Chat Completions

#### Non-Streaming Chat Completion

```bash
curl -X POST http://localhost:54000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "What is the capital of France?"
      }
    ],
    "stream": false
  }'
```

#### Streaming Chat Completion

```bash
curl -N -X POST http://localhost:54000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {
        "role": "user",
        "content": "Write a short poem about coding"
      }
    ],
    "stream": true
  }'
```

#### Chat Completion with Custom Permission Mode

```bash
curl -X POST http://localhost:54000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Permission-Mode: default" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {
        "role": "user",
        "content": "Help me refactor this Python function"
      }
    ]
  }'
```

#### Chat Completion with All Parameters

```bash
curl -X POST http://localhost:54000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {
        "role": "system",
        "content": "You are an expert Python developer."
      },
      {
        "role": "user",
        "content": "Explain decorators in Python"
      }
    ],
    "temperature": 0.7,
    "top_p": 1.0,
    "max_tokens": 1000,
    "stream": false
  }'
```

**Note:** `temperature`, `top_p`, `max_tokens`, and `stop` are accepted but ignored by the Claude Agent SDK.

---

### Models

#### List Models

```bash
curl -X GET http://localhost:54000/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Get Model

```bash
curl -X GET http://localhost:54000/v1/models/gpt-4 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Get Model (Alternative)

```bash
curl -X GET http://localhost:54000/v1/models/gpt-3.5-turbo \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

### Assistants (Beta)

#### Create Assistant

```bash
curl -X POST http://localhost:54000/v1/assistants \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "name": "Math Tutor",
    "description": "Expert in mathematics and problem solving",
    "instructions": "You are a patient math tutor who explains concepts clearly.",
    "tools": [
      {"type": "code_interpreter"}
    ],
    "metadata": {
      "subject": "mathematics"
    }
  }'
```

#### List Assistants

```bash
curl -X GET "http://localhost:54000/v1/assistants?limit=20&order=desc" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### List Assistants with Pagination

```bash
curl -X GET "http://localhost:54000/v1/assistants?limit=10&order=asc&after=asst_abc123" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Get Assistant

```bash
curl -X GET http://localhost:54000/v1/assistants/asst_ASSISTANT_ID \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Modify Assistant

```bash
curl -X POST http://localhost:54000/v1/assistants/asst_ASSISTANT_ID \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Advanced Math Tutor",
    "instructions": "You are an expert math tutor specializing in calculus and linear algebra.",
    "metadata": {
      "subject": "advanced-mathematics"
    }
  }'
```

#### Delete Assistant

```bash
curl -X DELETE http://localhost:54000/v1/assistants/asst_ASSISTANT_ID \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

### Threads (Beta)

#### Create Thread

```bash
curl -X POST http://localhost:54000/v1/threads \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "topic": "python-help"
    }
  }'
```

#### Create Thread with Initial Messages

```bash
curl -X POST http://localhost:54000/v1/threads \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "I need help with Python async programming",
        "metadata": {}
      }
    ],
    "metadata": {
      "topic": "python-async"
    }
  }'
```

#### Get Thread

```bash
curl -X GET http://localhost:54000/v1/threads/thread_THREAD_ID \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Modify Thread

```bash
curl -X POST http://localhost:54000/v1/threads/thread_THREAD_ID \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "topic": "python-async-advanced",
      "status": "active"
    }
  }'
```

#### Delete Thread

```bash
curl -X DELETE http://localhost:54000/v1/threads/thread_THREAD_ID \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

### Messages (Beta)

#### Create Message

```bash
curl -X POST http://localhost:54000/v1/threads/thread_THREAD_ID/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "content": "Can you explain asyncio.gather() with an example?",
    "metadata": {
      "topic": "asyncio"
    }
  }'
```

#### List Messages

```bash
curl -X GET "http://localhost:54000/v1/threads/thread_THREAD_ID/messages?limit=20&order=desc" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### List Messages with Pagination

```bash
curl -X GET "http://localhost:54000/v1/threads/thread_THREAD_ID/messages?limit=10&order=asc&after=msg_abc123" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Get Message

```bash
curl -X GET http://localhost:54000/v1/threads/thread_THREAD_ID/messages/msg_MESSAGE_ID \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Modify Message

```bash
curl -X POST http://localhost:54000/v1/threads/thread_THREAD_ID/messages/msg_MESSAGE_ID \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "priority": "high",
      "reviewed": "true"
    }
  }'
```

---

### Runs (Beta)

#### Create Run

```bash
curl -X POST http://localhost:54000/v1/threads/thread_THREAD_ID/runs \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "asst_ASSISTANT_ID",
    "model": "gpt-4",
    "instructions": "Please help the user with their Python questions.",
    "metadata": {
      "session": "tutoring"
    }
  }'
```

#### Create Run (Minimal)

```bash
curl -X POST http://localhost:54000/v1/threads/thread_THREAD_ID/runs \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "asst_ASSISTANT_ID"
  }'
```

#### List Runs

```bash
curl -X GET "http://localhost:54000/v1/threads/thread_THREAD_ID/runs?limit=20&order=desc" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Get Run

```bash
curl -X GET http://localhost:54000/v1/threads/thread_THREAD_ID/runs/run_RUN_ID \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Cancel Run

```bash
curl -X POST http://localhost:54000/v1/threads/thread_THREAD_ID/runs/run_RUN_ID/cancel \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## Advanced Examples

### Complete Workflow: Create Agent, Query, Resume

```bash
# 1. Create an agent
AGENT_RESPONSE=$(curl -s -X POST http://localhost:54000/api/v1/agents \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Code Helper",
    "description": "Helps with coding",
    "prompt": "You are a helpful coding assistant.",
    "tools": ["Bash", "Edit", "Read"],
    "model": "sonnet"
  }')

AGENT_ID=$(echo $AGENT_RESPONSE | jq -r '.id')
echo "Created agent: $AGENT_ID"

# 2. Send initial query
QUERY_RESPONSE=$(curl -s -X POST http://localhost:54000/api/v1/query/single \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are Python decorators?",
    "model": "sonnet"
  }')

SESSION_ID=$(echo $QUERY_RESPONSE | jq -r '.session_id')
echo "Created session: $SESSION_ID"

# 3. Resume session with follow-up
curl -X POST http://localhost:54000/api/v1/query/single \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"prompt\": \"Can you show me an example?\",
    \"session_id\": \"$SESSION_ID\",
    \"model\": \"sonnet\"
  }"
```

### Complete Workflow: OpenAI Assistant + Thread + Run

```bash
# 1. Create an assistant
ASSISTANT_RESPONSE=$(curl -s -X POST http://localhost:54000/v1/assistants \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "name": "Code Reviewer",
    "instructions": "You review code for best practices."
  }')

ASSISTANT_ID=$(echo $ASSISTANT_RESPONSE | jq -r '.id')
echo "Created assistant: $ASSISTANT_ID"

# 2. Create a thread
THREAD_RESPONSE=$(curl -s -X POST http://localhost:54000/v1/threads \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}')

THREAD_ID=$(echo $THREAD_RESPONSE | jq -r '.id')
echo "Created thread: $THREAD_ID"

# 3. Add a message
curl -s -X POST http://localhost:54000/v1/threads/$THREAD_ID/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "content": "Please review this Python function for improvements."
  }'

# 4. Create a run
RUN_RESPONSE=$(curl -s -X POST http://localhost:54000/v1/threads/$THREAD_ID/runs \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"assistant_id\": \"$ASSISTANT_ID\"
  }")

RUN_ID=$(echo $RUN_RESPONSE | jq -r '.id')
echo "Created run: $RUN_ID"

# 5. Get run status
curl -s -X GET http://localhost:54000/v1/threads/$THREAD_ID/runs/$RUN_ID \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### MCP Server Configuration in Query

```bash
curl -X POST http://localhost:54000/api/v1/query/single \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Use the PostgreSQL MCP to query the users table",
    "model": "sonnet",
    "mcp_servers": {
      "postgres": {
        "type": "stdio",
        "command": "mcp-postgres",
        "env": {
          "DATABASE_URL": "postgresql://user:pass@localhost:5432/mydb"
        }
      }
    }
  }'
```

### Memory-Enhanced Query

```bash
# 1. Add memory
curl -X POST http://localhost:54000/api/v1/memories \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "User prefers TypeScript and uses React with hooks",
    "metadata": {"category": "preferences"},
    "enable_graph": true
  }'

# 2. Query (memories automatically injected)
curl -X POST http://localhost:54000/api/v1/query/single \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Help me build a form component",
    "model": "sonnet"
  }'
```

---

## Tips & Tricks

### Save Response to File

```bash
curl -X GET http://localhost:54000/api/v1/sessions \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -o sessions.json
```

### Pretty Print JSON Response (using jq)

```bash
curl -s -X GET http://localhost:54000/api/v1/agents \
  -H "X-API-Key: YOUR_API_KEY" | jq
```

### Extract Specific Field (using jq)

```bash
curl -s -X POST http://localhost:54000/api/v1/query/single \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "model": "sonnet"}' | jq -r '.session_id'
```

### Include Verbose Output

```bash
curl -v -X GET http://localhost:54000/health
```

### Set Timeout

```bash
curl --max-time 30 -X POST http://localhost:54000/api/v1/query/single \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "model": "sonnet"}'
```

### Follow Redirects

```bash
curl -L -X GET http://localhost:54000/api/v1/agents \
  -H "X-API-Key: YOUR_API_KEY"
```

### Send File as Request Body

```bash
curl -X POST http://localhost:54000/api/v1/skills \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d @skill.json
```

---

## Environment Variables

Create a `.env.curl` file for reusable values:

```bash
# .env.curl
export API_KEY="your-api-key-here"
export BASE_URL="http://localhost:54000"
```

Source it before running curl commands:

```bash
source .env.curl

curl -X GET $BASE_URL/api/v1/agents \
  -H "X-API-Key: $API_KEY"
```

---

## Troubleshooting

### Check API is Running

```bash
curl http://localhost:54000/health
```

### Test Authentication

```bash
curl -X GET http://localhost:54000/api/v1/projects \
  -H "X-API-Key: test-key" \
  -w "\nHTTP Status: %{http_code}\n"
```

### Debug SSL Issues

```bash
curl -k -X GET https://localhost:54000/health
```

### Show Response Headers

```bash
curl -i -X GET http://localhost:54000/health
```

### Test with Invalid JSON

```bash
curl -X POST http://localhost:54000/api/v1/query/single \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{invalid json}'
```

Expected: `400 Bad Request`

---

**For complete API documentation, see:** [API_ENDPOINTS.md](./API_ENDPOINTS.md)
