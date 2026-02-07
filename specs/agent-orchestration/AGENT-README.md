# Personal AI Assistant System

A Claude-only personal AI assistant with ~90% of OpenClaw's capabilities at ~10% of the complexity.

## Vision

Build a unified, self-hosted personal AI assistant that combines:
- **Persistent memory** with semantic search
- **Proactive awareness** via heartbeat checks
- **Scheduled automation** via cron jobs
- **Full infrastructure control** across distributed homelab
- **Semantic document search** for markdown and session logs
- **Mobile-first web interface** with push notifications

All powered by **Claude only** (MAX subscription or API key) - no multi-model complexity.

---

## Existing Infrastructure

We're building on top of four mature projects:

### 1. claude-agent-api (This Repository)

**Location**: `/home/jmagar/workspace/claude-agent-api`

The FastAPI backend wrapping the Claude Agent SDK with full feature parity.

| Feature | Status | Details |
|---------|--------|---------|
| Skills System | ✅ Done | Filesystem + database discovery, CRUD API, auto-injection |
| MCP Integration | ✅ Done | Three-tier config (App → API-Key → Request) |
| Session Storage | ✅ Done | Redis cache + PostgreSQL durability |
| SSE Streaming | ✅ Done | Bounded queues, real-time delivery |
| OpenAI Compatibility | ✅ Done | `/v1/chat/completions` drop-in replacement |
| Type Safety | ✅ Done | Zero `Any` types, strict ty checking |

**Key Files**:
- `apps/api/routes/skills.py` - Skills CRUD endpoints
- `apps/api/services/mcp/` - MCP configuration management
- `apps/api/routes/stream.py` - SSE streaming endpoint

### 2. cli-firecrawl

**Location**: `/home/jmagar/workspace/cli-firecrawl`

Web scraping CLI with a complete embedding pipeline.

| Component | URL | Purpose |
|-----------|-----|---------|
| Firecrawl | CLI | Web scraping (13 commands: scrape, crawl, map, search, extract, etc.) |
| TEI | `http://localhost:52000` | Text Embeddings Inference - vector generation |
| Qdrant | `http://localhost:53333` | Vector database - semantic search |

**Embedding Pipeline**:
```
Content → Chunking → TEI (embed) → Qdrant (store)
                                         ↓
                            Query → TEI → Qdrant (search) → Results
```

**Key Commands**:
```bash
firecrawl scrape <url>           # Scrape single page
firecrawl crawl <url>            # Crawl entire site
firecrawl embed <file>           # Generate embeddings
firecrawl query <text>           # Semantic search
```

### 3. homelab

**Location**: `/home/jmagar/workspace/homelab`

Infrastructure monitoring and automation with 13+ domain-specific skills.

#### Skills Available

| Skill | Purpose | API/Integration |
|-------|---------|-----------------|
| tailscale | VPN network management | CLI + Tailscale API |
| unifi | UniFi network monitoring | Cloud Gateway Max API |
| unraid | Server monitoring | GraphQL API |
| radarr | Movie management | Radarr API v3 |
| sonarr | TV show management | Sonarr API v3 |
| prowlarr | Indexer aggregation | Prowlarr API |
| sabnzbd | Usenet downloads | SABnzbd API |
| qbittorrent | Torrent management | WebUI API |
| plex | Media server browsing | Plex API |
| overseerr | Media requests | Overseerr API |
| gotify | Push notifications | Gotify API |
| glances | System monitoring | Glances REST API |
| linkding | Bookmark management | Linkding API |

#### SSH Infrastructure

**Inventory Discovery** (`inventory/ssh.sh`):
- Parses `~/.ssh/config` automatically
- Detects OS type (Linux, Darwin, Unraid)
- Tracks capabilities (docker, systemd, etc.)
- Stores in `~/memory/bank/ssh/latest.json`

**Remote Execution** (`lib/remote-exec.sh`):
- Timeout protection (connect: 10s, command: 60s)
- Parallel SSH support (max 3 concurrent)
- Script deployment with hash-based updates

**Current Inventory**:
- 9 SSH hosts (6 reachable, 3 unreachable)
- Hosts: clawd, shart, squirts, steamy-wsl, tootie, vivobook-wsl

#### Memory Bank

**Location**: `~/memory/bank/`

Temporal data storage for infrastructure monitoring:

```
~/memory/bank/
├── docker/              # Container inventory (144 containers)
├── linux/               # Linux system dashboards
├── unraid/              # Unraid fleet monitoring (2 servers)
├── unifi/               # Network clients (33 devices)
├── tailscale/           # VPN device status
├── ssh/                 # SSH host inventory
├── swag/                # Reverse proxy configs
├── overseerr/           # Media request status
├── weekly/              # Weekly summary reports
└── orchestrator/        # Multi-script coordination
```

Each directory contains:
- `latest.json` - Symlink to most recent snapshot
- `TIMESTAMP.json` - Timestamped JSON snapshots
- `latest.md` - Human-readable markdown dashboard

#### Notification System

**Gotify Integration** (`skills/gotify/`):
- Push notifications via self-hosted Gotify server
- Priority levels (0-10)
- Markdown support
- File logging fallback

**Configuration**: `~/workspace/homelab/credentials/gotify/config.json`

### 4. synapse-mcp

**Location**: `/home/jmagar/workspace/synapse-mcp`

Unified MCP server for multi-host infrastructure management.

#### Tools

**Flux (Docker Operations)** - 40 subactions:

| Action | Subactions |
|--------|------------|
| container | list, start, stop, restart, pause, resume, logs, stats, inspect, search, pull, recreate, exec, top |
| compose | list, status, up, down, restart, logs, build, pull, recreate |
| system | info, df, prune, images, pull, build, rmi, networks, volumes |
| host | status, resources, info, uptime, services, network, mounts |

**Scout (SSH Operations)** - 16 subactions:

| Action | Subactions |
|--------|------------|
| (simple) | nodes, peek, exec, find, delta, emit, beam, ps, df |
| zfs | pools, datasets, snapshots |
| logs | syslog, journal, dmesg, auth |

#### Key Features

- **Auto-Discovery**: Reads `~/.ssh/config`, discovers Compose projects
- **Connection Pooling**: 50× performance improvement for SSH
- **Security Hardened**: Command allowlists, path traversal prevention
- **Multi-Host**: Seamless operations across all configured hosts

#### Usage

```bash
# Start in stdio mode (for Claude Code)
node dist/index.js

# Start in HTTP mode (for API integration)
SYNAPSE_PORT=3000 node dist/index.js --http
```

### 5. Chrome Integration (Claude Code)

**Source**: [Claude Code Chrome Extension](https://code.claude.com/docs/en/chrome) (beta)

Browser automation directly from Claude Code via the Claude in Chrome extension.

#### Capabilities

| Feature | Description |
|---------|-------------|
| **Live Debugging** | Read console errors and DOM state, fix code that caused them |
| **Design Verification** | Build UI, then verify it matches Figma mock in browser |
| **Web App Testing** | Test forms, check visual regressions, verify user flows |
| **Authenticated Apps** | Interact with Google Docs, Gmail, Notion (already logged in) |
| **Data Extraction** | Pull structured info from web pages, save locally |
| **Task Automation** | Form filling, multi-site workflows, data entry |
| **Session Recording** | Record browser interactions as GIFs |

#### Setup

```bash
# Prerequisites
# 1. Google Chrome browser
# 2. Claude in Chrome extension (v1.0.36+)
# 3. Claude Code CLI (v2.0.73+)
# 4. Claude Pro/Team/Enterprise plan

# Start Claude Code with Chrome enabled
claude --chrome

# Or enable from within a session
/chrome

# Enable by default (increases context usage)
/chrome → "Enabled by default"
```

#### Example Workflows

```bash
# Test local web app
"Open localhost:3000, try submitting the form with invalid data,
 check if error messages appear correctly"

# Debug with console logs
"Open the dashboard page and check the console for any errors"

# Interact with authenticated apps
"Draft a project update based on recent commits and add it to my
 Google Doc at docs.google.com/document/d/abc123"

# Extract data
"Go to the product listings page and extract name, price, availability
 for each item. Save as CSV"

# Multi-site workflow
"Check my calendar for meetings tomorrow, then for each meeting
 with an external attendee, look up their company on LinkedIn"

# Record demo
"Record a GIF showing how to complete the checkout flow"
```

#### Key Points

- Opens new tabs (doesn't take over existing ones)
- Shares browser login state (no re-authentication)
- Requires visible browser window (no headless mode)
- Pauses for login pages/CAPTCHAs (you handle, then say "continue")
- Site permissions managed in Chrome extension settings

### 6. LLM Gateway (Multi-Provider Support)

**Source**: [Claude Code Model Configuration](https://code.claude.com/docs/en/model-config)

While we're "Claude-only" by default, Claude Code supports multiple LLM providers via environment variables.

#### Supported Providers

| Provider | Base URL | Use Case |
|----------|----------|----------|
| **Anthropic** | (default) | Primary - Claude models |
| **DeepSeek** | `https://api.deepseek.com` | Cost-effective coding |
| **z.ai/GLM** | `https://open.bigmodel.cn/api/paas/v4` | Chinese language support |
| **Kimi/Moonshot** | `https://api.moonshot.ai/anthropic` | Long context (128K+) |
| **OpenRouter** | via y-router proxy | Access to 100+ models |

#### Environment Variables

```bash
# Model aliases (what sonnet/opus/haiku resolve to)
ANTHROPIC_DEFAULT_OPUS_MODEL="claude-opus-4-5-20251101"
ANTHROPIC_DEFAULT_SONNET_MODEL="claude-sonnet-4-5-20250929"
ANTHROPIC_DEFAULT_HAIKU_MODEL="claude-haiku-3-5-20241022"
CLAUDE_CODE_SUBAGENT_MODEL="claude-haiku-3-5-20241022"

# Alternative provider (overrides Anthropic)
ANTHROPIC_BASE_URL="https://api.deepseek.com"
ANTHROPIC_AUTH_TOKEN="your-api-key"
# or
ANTHROPIC_API_KEY="your-api-key"

# Custom headers (for some providers)
ANTHROPIC_CUSTOM_HEADERS="x-api-key: your-key"
```

#### Shell Functions for Quick Switching

```bash
# Add to ~/.bashrc or ~/.zshrc
deepseek() {
    export ANTHROPIC_BASE_URL="https://api.deepseek.com"
    export ANTHROPIC_AUTH_TOKEN="${DEEPSEEK_API_KEY}"
    claude "$@"
}

kimi() {
    export ANTHROPIC_BASE_URL="https://api.moonshot.ai/anthropic"
    export ANTHROPIC_AUTH_TOKEN="${KIMI_API_KEY}"
    claude "$@"
}

# Usage: deepseek, kimi, etc.
```

#### OpenRouter Setup (100+ Models)

```bash
# 1. Clone and run y-router (Anthropic→OpenAI translation)
git clone https://github.com/luohy15/y-router
cd y-router && docker-compose up -d

# 2. Configure Claude Code
export ANTHROPIC_BASE_URL="http://localhost:8787"
export ANTHROPIC_API_KEY="${OPENROUTER_API_KEY}"
claude
```

#### Our Approach

- **Default**: Claude (MAX subscription) - no config needed
- **Fallback**: Can switch to DeepSeek/OpenRouter for cost savings on bulk operations
- **Subagents**: Use Haiku for fast, cheap agent tasks

---

## What We're Building

### Phase 1: Memory System Integration

**Goal**: Persistent memory with semantic search using existing TEI + Qdrant.

| Component | Purpose |
|-----------|---------|
| `TeiEmbeddingService` | Generate embeddings via existing TEI server |
| `QdrantVectorService` | Store/search vectors in existing Qdrant |
| `MemoryService` | CRUD + semantic search for memories |
| `QueryEnrichmentService` | Inject relevant memories into prompts |

**Memory Types**:
- `fact` - Objective information about the user
- `preference` - User preferences and settings
- `relationship` - People, places, things the user knows
- `workflow` - How the user does things
- `context` - Ongoing project context

**API Endpoints**:
```
GET    /api/v1/memory                    # List memories
POST   /api/v1/memory                    # Create memory
GET    /api/v1/memory/search             # Semantic search
DELETE /api/v1/memory/{id}               # Delete memory
```

### Phase 2: Heartbeat System

**Goal**: Proactive awareness with periodic checks and Gotify notifications.

| Component | Purpose |
|-----------|---------|
| `HeartbeatScheduler` | APScheduler-based periodic execution |
| `GotifyService` | Push notifications (uses homelab config) |
| `HEARTBEAT.md` | User-defined checklist for heartbeat checks |

**Features**:
- Configurable interval (default: 30 minutes)
- Active hours support (e.g., 08:00-22:00)
- Smart suppression (`HEARTBEAT_OK` = no notification)
- Execution history logging

**API Endpoints**:
```
GET    /api/v1/heartbeat/config          # Get config
PUT    /api/v1/heartbeat/config          # Update config
POST   /api/v1/heartbeat/trigger         # Manual trigger
GET    /api/v1/heartbeat/history         # Execution history
```

### Phase 3: Cron Jobs

**Goal**: Scheduled tasks with PostgreSQL persistence and session modes.

| Component | Purpose |
|-----------|---------|
| `CronExecutor` | APScheduler with cron/at/every triggers |
| `CronJobModel` | PostgreSQL storage for job definitions |
| `CronRunModel` | Execution history storage |

**Schedule Types**:
- `cron` - Standard cron expressions (`0 7 * * *`)
- `at` - One-shot at specific datetime
- `every` - Interval-based (`30m`, `2h`, `1d`)

**Session Modes**:
- `main` - Shared context with main session
- `isolated` - Fresh session per execution

**API Endpoints**:
```
GET    /api/v1/cron                      # List jobs
POST   /api/v1/cron                      # Create job
GET    /api/v1/cron/{id}                 # Get job
PUT    /api/v1/cron/{id}                 # Update job
DELETE /api/v1/cron/{id}                 # Delete job
POST   /api/v1/cron/{id}/run             # Manual trigger
GET    /api/v1/cron/{id}/history         # Execution history
```

### Phase 4: QMD (Query Markup Documents)

**Goal**: Semantic search for markdown files using existing embedding pipeline.

| Component | Purpose |
|-----------|---------|
| `QMDService` | Index and search markdown files |
| `QMDConfig` | Watch directories, exclude patterns |

**Features**:
- Watches configurable directories (`~/Documents`, `~/workspace`, `~/notes`)
- Excludes patterns (`node_modules`, `.git`, `dist`)
- Chunks by headers with size limits
- Content-hash deduplication

**API Endpoints**:
```
POST   /api/v1/qmd/index                 # Index directory
GET    /api/v1/qmd/search                # Semantic search
GET    /api/v1/qmd/status                # Indexing status
```

### Phase 5: Session Search

**Goal**: Semantic search across Claude session logs.

| Component | Purpose |
|-----------|---------|
| `SessionSearchService` | Index and search JSONL session files |
| `SessionSearchConfig` | Session root, collection settings |

**Features**:
- Parses JSONL files from `~/.claude/projects/*/`
- Extracts user/assistant turns
- Chunks conversations into overlapping windows
- Filter by project

**API Endpoints**:
```
POST   /api/v1/session-search/index      # Index sessions
GET    /api/v1/session-search/search     # Semantic search
GET    /api/v1/session-search/status     # Indexing status
```

### Phase 6: Device Management API

**Goal**: API access to device inventory and infrastructure operations.

#### Static Inventory (Memory Bank)

| Component | Purpose |
|-----------|---------|
| `DeviceService` | Read inventory from `~/memory/bank/ssh/` |

**API Endpoints**:
```
GET    /api/v1/devices                   # List devices
GET    /api/v1/devices/{name}            # Get device details
POST   /api/v1/devices/{name}/exec       # Execute command
POST   /api/v1/devices/inventory/refresh # Refresh inventory
```

#### Real-Time Infrastructure (synapse-mcp)

| Component | Purpose |
|-----------|---------|
| `SynapseClient` | HTTP client for synapse-mcp |

**API Endpoints**:
```
GET    /api/v1/infrastructure/containers                  # List containers
GET    /api/v1/infrastructure/containers/{name}/logs      # Container logs
GET    /api/v1/infrastructure/compose                     # Compose projects
GET    /api/v1/infrastructure/compose/{project}/status    # Project status
GET    /api/v1/infrastructure/hosts/{host}/resources      # CPU/memory/disk
GET    /api/v1/infrastructure/hosts/{host}/zfs/pools      # ZFS health
GET    /api/v1/infrastructure/hosts/{host}/logs/journal   # systemd logs
```

### Phase 7: Web App

**Goal**: Mobile-first PWA for chat and configuration.

**Tech Stack**:
- Next.js 15 with App Router
- Tailwind CSS v4
- shadcn/ui components
- PWA with service worker
- Gotify for push notifications

**Screens**:
```
/                    # Chat interface
/settings            # Persona, heartbeat, general config
/settings/skills     # Skill management
/settings/devices    # Device inventory
/cron                # Cron job dashboard
/memory              # Memory browser
/history             # Conversation history
/search              # QMD and session search
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Mobile-First Web App                         │
│                    (Next.js 15 PWA)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Chat UI   │  │  Settings   │  │  Heartbeat/Cron Dashboard│ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ WebSocket + REST
┌──────────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Query API  │  │  Skill API  │  │  Cron API   │             │
│  │  (existing) │  │  (existing) │  │  (new)      │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│  ┌──────▼────────────────▼────────────────▼──────┐             │
│  │           Agent Orchestration Service          │             │
│  │  • Memory injection (TEI + Qdrant)             │             │
│  │  • Heartbeat scheduler                         │             │
│  │  • Cron job executor                           │             │
│  │  • Gotify notifications                        │             │
│  └──────────────────────┬───────────────────────┘             │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────┐             │
│  │            Claude Code SDK                    │             │
│  │  • Full tool access (bash, fs, git, etc.)     │             │
│  │  • MCP server integration                     │             │
│  │  • Session management                         │             │
│  └──────────────────────────────────────────────┘             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    Data Layer                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ PostgreSQL  │  │   Redis     │  │ TEI + Qdrant│             │
│  │ :54432      │  │ :54379      │  │ :52000/:53333│            │
│  │ • Sessions  │  │ • Cache     │  │ • Embeddings│             │
│  │ • Cron jobs │  │ • Pub/Sub   │  │ • Vectors   │             │
│  │ • Heartbeat │  │ • Skills DB │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Memory Bank │  │  Homelab    │  │   Gotify    │             │
│  │ ~/memory/   │  │  Skills     │  │ (push)      │             │
│  │ bank/       │  │  (13+)      │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌───────────────────────────────────────────────┐             │
│  │              synapse-mcp                       │             │
│  │  • Flux: Docker/Compose (40 operations)       │             │
│  │  • Scout: SSH/Files/ZFS (16 operations)       │             │
│  │  • Multi-host with auto-discovery             │             │
│  │  • Connection pooling + caching               │             │
│  └───────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:54432/claude_agent

# Redis
REDIS_URL=redis://localhost:54379

# Embedding Infrastructure (cli-firecrawl)
TEI_URL=http://localhost:52000
QDRANT_URL=http://localhost:53333

# Gotify (from homelab)
GOTIFY_URL=https://gotify.example.com
GOTIFY_TOKEN=your-token

# synapse-mcp (optional HTTP mode)
SYNAPSE_URL=http://localhost:3000
```

### MCP Configuration

```json
// .mcp-server-config.json
{
  "mcpServers": {
    "synapse": {
      "type": "stdio",
      "command": "node",
      "args": ["../synapse-mcp/dist/index.js"],
      "env": {
        "SYNAPSE_CONFIG_FILE": "../synapse-mcp/synapse.config.json"
      }
    }
  }
}
```

### Heartbeat Configuration

```markdown
# ~/.config/assistant/HEARTBEAT.md
# Heartbeat Checklist

## Quick Checks (every heartbeat)
- [ ] Check for urgent emails: `gog gmail search 'newer_than:30m is:unread' --max 5 --json`
- [ ] Review upcoming events (Google): `gog calendar events primary --from now --to +2h --json`
- [ ] Review upcoming events (CalDAV): `vdirsyncer sync && khal list today 2d`
- [ ] Check infrastructure alerts via synapse-mcp (container health, ZFS pools)

## Periodic Checks (if idle > 4 hours)
- [ ] Summarize unread emails from today: `gog gmail search 'newer_than:1d is:unread'`
- [ ] Review today's completed calendar events
- [ ] Check memory bank for any anomalies (unraid, unifi)

## Weekly Checks (Monday morning)
- [ ] Summarize last week's calendar
- [ ] Review Drive activity: `gog drive search 'modifiedTime > 7d'`
```

### Persona Configuration

**Storage Options:**

- **Multi-User Deployments**: PostgreSQL database with API key scoping (primary)
- **Single-User Deployments**: `~/.config/assistant/persona.json` (fallback when `DATABASE_URL` not set)

**Configuration Structure:**

```json
{
  "name": "Jarvis",
  "personality": "helpful, concise, proactive",
  "communication_style": "professional but warm",
  "expertise_areas": ["homelab", "automation", "development"],
  "proactivity": "medium",
  "verbosity": "balanced",
  "formality": "balanced",
  "use_emoji": false,
  "custom_instructions": "Always prioritize security and modularity"
}
```

**API Endpoints:**

```http
GET /api/v1/persona    # Get current persona config
PUT /api/v1/persona    # Update persona config
```

See [spec.md Persona Endpoints section](spec.md#persona-endpoints-new) for complete database schema and implementation details.

---

## Port Assignments

| Service | Port | Description |
|---------|------|-------------|
| API | 54000 | FastAPI server |
| PostgreSQL | 54432 | Database |
| Redis | 54379 | Cache/pub-sub |
| TEI | 52000 | Text Embeddings Inference |
| Qdrant | 53333 | Vector database |
| synapse-mcp | 3000 | Infrastructure MCP (HTTP mode) |
| Web App | 53000 | Next.js frontend |

---

## Getting Started

### Prerequisites

1. **Claude MAX subscription** or **Anthropic API key**
2. **Docker + Docker Compose** for infrastructure services
3. **Node.js 20+** for synapse-mcp
4. **Python 3.11+** with **uv** for API

### Start Infrastructure

```bash
# Start databases and embedding services
docker compose up -d postgres redis

# TEI + Qdrant (from cli-firecrawl)
cd ../cli-firecrawl
docker compose up -d

# synapse-mcp (optional HTTP mode)
cd ../synapse-mcp
pnpm install && pnpm build
SYNAPSE_PORT=3000 node dist/index.js --http &
```

### Start API

```bash
cd /home/jmagar/workspace/claude-agent-api

# Install dependencies
uv sync

# Run migrations
uv run alembic upgrade head

# Start server
uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 54000 --reload
```

### Verify Installation

```bash
# Health check
curl http://localhost:54000/health

# List skills
curl http://localhost:54000/api/v1/skills

# Test embedding
curl -X POST http://localhost:52000/embed \
  -H "Content-Type: application/json" \
  -d '{"inputs": ["Hello world"]}'

# Test Qdrant
curl http://localhost:53333/collections
```

---

## OpenClaw Feature Parity

We've achieved near-complete OpenClaw feature coverage through skills and configuration:

| OpenClaw Feature | Our Solution | Status |
|------------------|--------------|--------|
| WhatsApp, Telegram, Discord, Slack, iMessage | **claw-me-maybe** (Beeper unified messaging) | ✅ |
| Multi-model support | **LLM Gateway** env vars + **gemini** skill | ✅ |
| Gateway/Control UI/Daemon architecture | Single FastAPI + Next.js (simpler) | ✅ |
| Multi-node remote execution | **synapse-mcp** (56 ops) + SSH skills | ✅ |
| Docker management | **synapse-mcp** Flux tool (40 ops) | ✅ |
| Skills/Plugin system | AgentSkills spec + **clawdhub** + **skillbox** | ✅ |
| Vector embeddings | TEI + Qdrant (already running) | ✅ |
| Push notifications | Gotify (existing homelab) | ✅ |
| Browser automation | Chrome + **agent-browser** + **browsh** | ✅ |
| Desktop control | **windows-control** + **computer-use** | ✅ |
| Smart home | **google-home-control** + homeassistant | ✅ |
| Social media | **twitter** + **reddit-scraper** | ✅ |
| Password management | **bitwarden** | ✅ |
| Automation orchestration | **clawflows** (109+ automations) | ✅ |

**What we're choosing NOT to build** (simplicity over complexity):
- Kubernetes/Swarm orchestration → Docker Compose is sufficient
- Multi-daemon architecture → Only needed for HA; personal assistant restarts fine

Everything else OpenClaw does? We can do it too.

---

## Ecosystem Compatibility

Because we follow the **AgentSkills spec**, we can use:
- Skills from clawhub.com
- Claude Code's built-in skills
- OpenClaw community skills
- Existing homelab skills (13+)
- Custom skills following the spec

### Skillbox - Skill Management Layer

**[skillbox](https://github.com/christiananagnostou/skillbox/)** is a local-first, agent-agnostic skills manager that handles skill installation, updates, and multi-agent sync.

**Why skillbox?**
- Eliminates need to build our own skill installer
- Central repository at `~/.config/skillbox/skills/`
- Auto-syncs skills to Claude Code, Cursor, and our API
- Handles versioning and updates from GitHub/ClawHub

**Installation:**
```bash
npm install -g skillbox
```

**Usage:**
```bash
# Install skills from GitHub/ClawHub
skillbox add anthropics/weather
skillbox add anthropics/hackernews
skillbox add anthropics/morning-email-rollup
skillbox add anthropics/gog
skillbox add anthropics/caldav

# List installed skills
skillbox list

# Check for updates
skillbox status

# Update all skills
skillbox update

# Update specific skill
skillbox update weather
```

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                      skillbox                            │
│            ~/.config/skillbox/skills/                    │
│  (canonical repository - single source of truth)        │
└─────────────────┬───────────────────────────────────────┘
                  │ auto-syncs to
        ┌─────────┼─────────┬─────────┐
        ▼         ▼         ▼         ▼
   Claude Code  Our API   Cursor   OpenClaw
   ~/.claude/   (reads    ~/.cursor/
   skills/      from      skills/
                skillbox)
```

**Our API Integration:**
- Read skills from skillbox's canonical location (`~/.config/skillbox/skills/`)
- Inject into queries via existing `QueryEnrichmentService`
- Web UI provides browse/install interface that calls `skillbox` CLI

### Planned Community Skills (from ClawHub)

| Skill | Downloads | Purpose |
|-------|-----------|---------|
| **gog** | - | Google Workspace CLI (Gmail, Calendar, Drive, Contacts, Sheets, Docs) |
| **caldav** | - | CalDAV calendars (iCloud, Fastmail, Nextcloud) via vdirsyncer + khal |
| **weather** | 4,186 | Weather + forecasts (no API key) - heartbeat/daily briefings |
| **hackernews** | 18 | Browse/search Hacker News for tech news awareness |
| **morning-email-rollup** | 609 | Daily email + calendar digest at 8am |
| **daily-recap** | 269 | Weather-aware daily summaries, cron-driven |
| **adhd-assistant** | 63 | Task breakdown, prioritization, time management |
| **zero-trust** | 12 | Security-first behavioral guidelines |
| **windows-control** | - | Full Windows desktop control (mouse, keyboard, screenshots) |
| **computer-use** | - | Headless Linux desktop control via Xvfb+XFCE (17 actions, VNC) |
| **clawflows** | - | Multi-skill automation orchestration (109+ automations, skill-agnostic) |
| **yt-video-downloader** | - | Download YouTube videos/playlists, extract audio, multiple formats |
| **clawdhub** | - | ClawdHub CLI (steipete) - search, install, update, publish skills |
| **twitter** | - | Twitter/X - post tweets, read timeline, manage followers, engagement metrics |
| **browsh** | - | Text-based browser using headless Firefox - web browsing in terminal/headless |
| **bitwarden** | - | Bitwarden/Vaultwarden password management via rbw CLI |
| **agent-browser** | - | Rust headless browser automation CLI (navigate, click, type, snapshot) |
| **adguard** | - | AdGuard Home DNS filtering - blocklists, allowlists, stats, toggle protection |
| **reddit-scraper** | - | Read/search Reddit posts via old.reddit.com scraping (read-only) |
| **youtube-transcript** | - | Fetch/summarize YouTube video transcripts (bypasses cloud IP blocks) |
| **skill-creator** | - | Guide for creating new skills - templates, best practices, tool integrations |
| **mcporter** | - | MCP server management (steipete) - list, configure, auth, call servers/tools |
| **gemini** | - | Gemini CLI (steipete) - one-shot Q&A, summaries, text generation |
| **notebooklm-cli** | - | Google NotebookLM CLI - notebooks, sources, audio overviews |
| **tldr** | - | Simplified man pages from tldr-pages - quick CLI tool reference |
| **create-cli** | - | CLI design guide (steipete) - args, flags, subcommands, help, error handling |
| **openai-docs** | - | Query OpenAI developer docs via MCP - APIs, SDKs, Codex, rate limits |
| **codexmonitor** | - | Monitor/inspect local OpenAI Codex sessions (CLI + VS Code) |
| **google-home-control** | - | Smart home control via Google Assistant SDK (lights, TV, etc.) |
| **local-places** | - | Google Places search (steipete) - restaurants, cafes, nearby venues |
| **claw-me-maybe** | - | Beeper multi-platform messaging (WhatsApp, Telegram, Signal, Discord, Slack, iMessage, etc.) |

### ClawFlows - Automation Orchestration

**[ClawFlows](https://clawflows.com)** is a registry of 109+ capability-based automations for AI agents.

**Key Concept**: Skill-agnostic automations using abstract interfaces. "Write once, run anywhere" - automations don't break when you switch underlying skills.

**How it works:**
```
Capabilities (abstract)     →    Skills (concrete)
───────────────────────────────────────────────────
calendar.list_events        →    gog, caldav, google-calendar
email.send                  →    gog, email, gmail, agentmail
database.query              →    sqlite, postgres, supabase
social.search               →    twitter, x-search
```

**Available Building Blocks:**
- Prediction markets (Polymarket, Kalshi)
- Database operations (SQLite, storage)
- Chart generation
- Social media search (X/Twitter)
- Calendar/scheduling
- Text-to-speech

**Usage:**
```bash
# Install clawflows skill
skillbox add cluka-399/clawflows

# Browse and install automations
# (via Claude) "Search clawflows for email automation"
# (via Claude) "Install the morning-briefing automation"
```

**Why this matters for us:**
- Pre-built automations for heartbeat/cron use cases
- Abstracts away skill dependencies
- Community-maintained automation library
- Compatible with our existing skills

**Control Surface:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Control Surface                                   │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│ Chrome          │ windows-control │ computer-use    │ synapse-mcp           │
│ (Web/Browser)   │ (Windows Apps)  │ (Linux Desktop) │ (Infrastructure)      │
│ • Navigate      │ • Mouse control │ • Xvfb virtual  │ • Docker/Compose      │
│ • Click/fill    │ • Keyboard      │   display       │ • SSH/Files/ZFS       │
│ • Extract data  │ • Screenshots   │ • Mouse/keyboard│ • Multi-host          │
│ • Auth'd apps   │ • Any Windows   │ • Screenshots   │ • 56 operations       │
│                 │   application   │ • VNC remote    │                       │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
```

**Top ClawHub Skills (reference only - many duplicate our existing capabilities):**
- `github` (4,500 downloads) - `gh` CLI - we already have this via Claude Code
- `homeassistant` (3,608 downloads) - Smart home control
- `slack` (1,897 downloads) - Slack messaging
- `email` (1,615 downloads) - Multi-provider email - `gog` covers Gmail
- `trello` (1,517 downloads) - Board management
- `docker-essentials` (565 downloads) - We have `synapse-mcp` with 40 Docker operations

**gog** is particularly important for heartbeat checks (Google accounts):
- `gog gmail search 'newer_than:1h is:unread'` - Check for urgent emails
- `gog calendar events <id> --from <now> --to <+2h>` - Upcoming events
- `gog drive search "query"` - Find documents

**gog Setup:**
```bash
# One-time OAuth setup
gog auth credentials /path/to/client_secret.json
gog auth add you@gmail.com --services gmail,calendar,drive,contacts,sheets,docs

# Set default account
export GOG_ACCOUNT=you@gmail.com
```

**caldav** is important for non-Google calendars:
- `vdirsyncer sync` - Sync calendars to local .ics files
- `khal list today 7d` - Upcoming events
- `khal new 2026-01-15 10:00 11:00 "Meeting"` - Create events
- `khal search "meeting"` - Search events

**caldav Setup:**
```bash
# Configure vdirsyncer (~/.config/vdirsyncer/config) for your provider:
# - iCloud: https://caldav.icloud.com/
# - Fastmail: https://caldav.fastmail.com/dav/calendars/user/EMAIL/
# - Nextcloud: https://YOUR.CLOUD/remote.php/dav/calendars/USERNAME/

# Initial sync
vdirsyncer discover
vdirsyncer sync
```

Skills/MCP servers are plug-and-play across:
- Our personal assistant
- Claude Code
- OpenClaw
- Any AgentSkills-compatible agent

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Deployment complexity | Single `docker compose up` |
| TEI + Qdrant integration | Zero additional setup |
| Memory search latency | < 200ms |
| Heartbeat success rate | 99.9% |
| Skill compatibility | 100% AgentSkills spec |
| Code reuse | 100% of existing infrastructure |
| OpenClaw feature coverage | ~90% |

---

## Related Documentation

- [Feature Specification](specs/agent-orchestration/spec.md)
- [Implementation Plan](specs/agent-orchestration/plan.md)
- [API Contract](specs/001-claude-agent-api/contracts/openapi.yaml)
- [Server-Side MCP Spec](specs/server-side-mcp/spec.md)

---

## License

MIT
