# Personal AI Assistant Specification

## Vision

A simplified, Claude-only personal AI assistant inspired by OpenClaw's capabilities but with dramatically reduced complexity. We achieve ~90% of OpenClaw's functionality with ~10% of the architectural complexity by:

1. **Claude-only**: No multi-model support. Claude MAX subscription or API key only.
2. **Web-first**: Mobile-first PWA instead of WhatsApp/Telegram/Discord/Slack/iMessage integrations.
3. **Unified codebase**: FastAPI + Next.js instead of Gateway/Control UI/Daemon/Node architecture.
4. **Skills-compatible**: Full AgentSkills spec support for ecosystem compatibility.
5. **SSH-based device access**: Simple key-based SSH instead of complex multi-node orchestration.

## Existing Infrastructure

### What Already Exists

#### claude-agent-api (This Repository)
✅ **Full Skills System** - Filesystem + database skill discovery, CRUD API, auto-injection into queries
✅ **FastAPI Backend** - Async routes, SSE streaming, OpenAI compatibility layer
✅ **Three-Tier MCP Config** - Application → API-Key → Request level MCP server injection
✅ **Session Storage** - Redis cache + PostgreSQL durability
✅ **Type-Safe Schemas** - Pydantic models with zero `Any` types
✅ **Claude Code SDK** - Full tool access (bash, filesystem, git, etc.)

#### cli-firecrawl (`../cli-firecrawl`)
✅ **Firecrawl Integration** - Web scraping CLI with 13 commands (scrape, crawl, map, search, extract, etc.)
✅ **TEI Integration** - Text Embeddings Inference at `http://localhost:52000` for vector generation
✅ **Qdrant Integration** - Vector database at `http://localhost:53333` with semantic search
✅ **Embedding Pipeline** - Automatic chunking → embedding → storage workflow
✅ **Semantic Search** - `firecrawl query <text>` for vector similarity search

#### homelab (`../homelab`)
✅ **13+ Domain Skills** - tailscale, unifi, unraid, radarr, sonarr, prowlarr, sabnzbd, qbittorrent, plex, overseerr, gotify, glances, linkding
✅ **SSH Inventory Discovery** - Parses `~/.ssh/config` to build device inventory
✅ **Remote Execution** - Timeout-protected SSH with parallel support
✅ **Memory Bank Integration** - Writes to `~/memory/bank/` with temporal JSON snapshots
✅ **Gotify Notifications** - Push notifications via self-hosted Gotify server
✅ **Infrastructure Monitoring** - Dashboard scripts for Unraid, Linux, UniFi

#### Memory Bank (`~/memory/bank/`)
✅ **Temporal Data Storage** - Timestamped JSON snapshots per topic
✅ **Human-Readable Dashboards** - `latest.md` markdown summaries
✅ **12 Topic Directories** - docker, linux, unraid, unifi, tailscale, ssh, swag, overseerr, weekly
✅ **Device Inventory** - 9 SSH hosts, 144 Docker containers, 2 Unraid servers, 33 network clients

#### synapse-mcp (`../synapse-mcp`)
✅ **Infrastructure MCP Server** - Unified multi-host Docker + SSH management via MCP protocol
✅ **Flux Tool (40 operations)** - Container lifecycle, Compose management, system operations, host resources
✅ **Scout Tool (16 operations)** - SSH commands, file transfer, ZFS pools, log retrieval (syslog, journal, dmesg)
✅ **Auto-Discovery** - Reads `~/.ssh/config`, auto-discovers Compose projects across hosts
✅ **Connection Pooling** - 50× performance improvement for repeated SSH operations
✅ **Security Hardened** - Command allowlists, path traversal prevention, SSH injection protection
✅ **Multi-Host Transparent** - Seamless operations across all configured SSH hosts

#### Chrome Integration (Claude Code Built-in)
✅ **Browser Automation** - Navigate, click, type, fill forms, scroll via Claude in Chrome extension
✅ **Live Debugging** - Read console errors/logs, DOM state directly from browser
✅ **Authenticated Apps** - Access Google Docs, Gmail, Notion without API setup (uses existing login)
✅ **Data Extraction** - Pull structured info from web pages, save locally
✅ **Task Automation** - Form filling, multi-site workflows, data entry
✅ **Session Recording** - Record browser interactions as GIFs
✅ **Web App Testing** - Test forms, verify user flows, check visual regressions

**Setup**: `claude --chrome` or `/chrome` command in session

**Key Use Cases**:
- Test our web app during development
- Browse ClawHub to discover/evaluate skills
- Interact with authenticated services (Google, Notion, etc.) without API connectors
- Extract data from web pages
- Automate repetitive browser tasks

#### LLM Gateway (Multi-Provider Support)
✅ **Environment Variable Config** - Switch providers via `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`
✅ **Model Aliases** - `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`
✅ **Subagent Models** - `CLAUDE_CODE_SUBAGENT_MODEL` for fast agent tasks
✅ **Multiple Providers** - DeepSeek, z.ai/GLM, Kimi/Moonshot, OpenRouter (via y-router)

**Supported Providers**:
| Provider | Base URL | Notes |
|----------|----------|-------|
| Anthropic | (default) | Claude models, MAX subscription |
| DeepSeek | `https://api.deepseek.com` | Cost-effective coding |
| Kimi/Moonshot | `https://api.moonshot.ai/anthropic` | 128K+ context |
| OpenRouter | `http://localhost:8787` (via y-router) | 100+ models |

**Our Strategy**:
- **Default**: Claude (MAX subscription) - primary
- **Cost Optimization**: DeepSeek/Haiku for bulk operations, background tasks
- **Subagents**: Haiku model for fast, cheap parallel agent execution

## Core Features (from OpenClaw)

### 1. Persistent Memory & Persona

**What OpenClaw does:**
- Learns user patterns over time
- Maintains context across sessions
- Customizable personality ("soul")
- Remembers relationships, preferences, workflows

**Our implementation:**
- **Leverage existing infrastructure:**
  - TEI (cli-firecrawl) for embedding generation
  - Qdrant (cli-firecrawl) for vector storage and semantic search
  - Memory bank (`~/memory/bank/`) for structured data
- PostgreSQL for additional memory metadata
- Redis for active session cache
- Memory types: facts, preferences, relationships, workflows
- Persona configuration via YAML/JSON

```python
class Memory:
    id: str
    content: str
    memory_type: Literal["fact", "preference", "relationship", "workflow"]
    embedding: list[float]  # Generated via TEI
    created_at: datetime
    last_accessed: datetime
    access_count: int
    source: Literal["user", "inferred", "imported"]
```

### 2. AgentSkills-Compatible Skills System

**Current State: ✅ ALREADY IMPLEMENTED**

The claude-agent-api already has a complete skill system:

- **Routes**: `/api/v1/skills` with full CRUD operations
- **Sources**: Filesystem (`~/.claude/skills/*.md`) + Database (Redis)
- **Discovery**: `SkillsService` discovers skills from global and project paths
- **Persistence**: `SkillCrudService` stores API-created skills in Redis
- **Injection**: `QueryEnrichmentService` auto-injects skills into queries
- **Built-in Tools**: "Skill" is in `BUILT_IN_TOOLS` constant

**What we add:**
- Hot-reload via file watcher
- Skill gating enforcement (check env vars, binaries, config)
- Integration with homelab skills

### 3. Heartbeat (Proactive Awareness)

**What OpenClaw does:**
- Periodic agent runs (default 30 min)
- Batches multiple checks in one turn (inbox, calendar, notifications)
- Context-aware prioritization
- Smart suppression (HEARTBEAT_OK if nothing important)
- Active hours configuration
- HEARTBEAT.md checklist

**Our implementation:**
- Background scheduler (APScheduler)
- Configurable heartbeat interval
- HEARTBEAT.md in user workspace
- Active hours support
- **Gotify push notifications** (existing homelab integration)
- Heartbeat history logging
- **gog skill** for Gmail/Calendar checks (clawhub.com)

**Heartbeat Checks via gog (Google):**
```bash
# Check urgent emails
gog gmail search 'newer_than:30m is:unread' --max 5 --json

# Upcoming calendar events
gog calendar events primary --from now --to +2h --json

# Drive activity
gog drive search 'modifiedTime > 1d' --max 10 --json
```

**Heartbeat Checks via caldav (iCloud/Fastmail/Nextcloud):**
```bash
# Sync first
vdirsyncer sync

# Upcoming events
khal list today 7d --format "{start-date} {start-time} {title}"

# Search events
khal search "meeting"
```

```python
class HeartbeatConfig:
    enabled: bool = True
    interval_minutes: int = 30
    active_hours: tuple[str, str] = ("08:00", "22:00")
    timezone: str = "America/New_York"
    checklist_path: str = "~/.config/assistant/HEARTBEAT.md"
    notification_method: Literal["gotify", "none"] = "gotify"
```

### 4. Cron Jobs (Scheduled Tasks)

**What OpenClaw does:**
- Precise timing with cron expressions
- One-shot reminders with `--at`
- Main session (shared context) vs isolated session (fresh)
- Delivery to channels
- Model overrides per job
- Job persistence and history

**Our implementation:**
- APScheduler with cron triggers
- PostgreSQL job storage
- Main vs isolated session modes
- **Gotify notifications** for delivery (existing homelab integration)
- Job CRUD API endpoints
- Execution history with status

```python
class CronJob:
    id: str
    name: str
    schedule: CronSchedule | AtSchedule | EverySchedule
    session_mode: Literal["main", "isolated"]
    payload: SystemEvent | AgentTurn
    enabled: bool = True
    created_at: datetime
    last_run: datetime | None
    next_run: datetime | None
```

### 5. Full System Access

**What OpenClaw does:**
- Runs on dedicated computer
- Can write code, execute scripts, modify files
- Access to all local tools and APIs

**Our implementation:**
- Claude Code SDK provides full tool access
- Bash, filesystem, git, etc. via SDK
- Configurable tool permissions
- Audit logging for all tool calls

### 6. Device Management (SSH)

**Current State: ✅ ALREADY IMPLEMENTED (via homelab)**

The homelab project already provides:

- **SSH Inventory Discovery** (`inventory/ssh.sh`):
  - Parses `~/.ssh/config` to extract hosts
  - Detects OS type (Linux, Darwin, Unraid)
  - Tracks capabilities (docker, systemd, etc.)
  - Stores in `~/memory/bank/ssh/latest.json`

- **Remote Execution** (`lib/remote-exec.sh`):
  - Timeout protection (connect: 10s, command: 60s)
  - Parallel SSH support (max 3 concurrent)
  - Script deployment with hash-based updates

**What we add:**
- API endpoints to query device inventory
- Integration with skill system for device control
- Real-time device status via existing monitoring

**Current inventory:**
- 9 SSH hosts (6 reachable, 3 unreachable)
- Hosts: clawd, shart, squirts, steamy-wsl, tootie, vivobook-wsl
- Capabilities tracked per host

### 7. MCP Server Integration

**Current State: ✅ ALREADY IMPLEMENTED**

- Three-tier MCP config (Application → API-Key → Request)
- Skills can reference MCP tools
- Security validation (command injection, SSRF prevention)

**synapse-mcp Integration:**

The synapse-mcp server provides unified infrastructure management:

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

**Available Operations:**

| Tool | Action | Subactions |
|------|--------|------------|
| Flux | container | list, start, stop, restart, logs, stats, inspect, exec, pull, recreate |
| Flux | compose | list, status, up, down, restart, logs, build, pull |
| Flux | system | info, df, prune, images, networks, volumes |
| Flux | host | status, resources, info, uptime, services, network, mounts |
| Scout | - | nodes, peek, exec, find, delta, emit, beam, ps, df |
| Scout | zfs | pools, datasets, snapshots |
| Scout | logs | syslog, journal, dmesg, auth |

**Use Cases:**
- Check container status across all hosts
- View logs from any service
- Transfer files between hosts
- Query ZFS pool health
- Monitor system resources
- Execute commands with allowlist protection

### 8. Semantic Search (QMD - Query Markup Documents)

**New Feature**

On-device semantic search for markdown files:
- Leverages existing TEI + Qdrant infrastructure
- Index markdown files from configurable directories
- Semantic search across documentation, notes, project files

**Implementation:**
- **Skill**: QMD skill for searching markdown files
- **Hook**: Auto-index new/modified markdown files
- **Integration**: Use cli-firecrawl's embed pipeline

```python
class QMDConfig:
    watch_directories: list[str] = [
        "~/Documents",
        "~/workspace",
        "~/notes",
    ]
    exclude_patterns: list[str] = [
        "**/node_modules/**",
        "**/.git/**",
        "**/dist/**",
    ]
    collection_name: str = "qmd_documents"
```

### 9. Session Search & Retrieval

**New Feature**

Semantic search across Claude session logs:
- Index sessions from `~/.claude/projects/*/`
- Search past conversations by topic
- Retrieve relevant context from historical sessions

**Implementation:**
- Parse JSONL session files
- Extract user prompts and assistant responses
- Generate embeddings via TEI
- Store in Qdrant with session metadata

```python
class SessionSearchConfig:
    session_root: str = "~/.claude/projects"
    collection_name: str = "claude_sessions"
    include_tool_calls: bool = False
    max_sessions: int | None = None  # None = all
```

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
│  │  • MCP server integration (existing)          │             │
│  │  • Session management (existing)              │             │
│  └──────────────────────────────────────────────┘             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    Data Layer                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ PostgreSQL  │  │   Redis     │  │ TEI + Qdrant│             │
│  │ • Sessions  │  │ • Cache     │  │ (existing)  │             │
│  │ • Cron jobs │  │ • Pub/Sub   │  │ :52000/:53333│            │
│  │ • Heartbeat │  │ • Skills DB │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Memory Bank │  │  Homelab    │  │   Gotify    │             │
│  │ ~/memory/   │  │  Skills     │  │ (existing)  │             │
│  │ bank/       │  │  (existing) │  │             │             │
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

## OpenClaw Feature Parity

We've achieved near-complete OpenClaw feature coverage through skills and configuration:

| OpenClaw Feature | Our Solution | Status |
|------------------|--------------|--------|
| WhatsApp, Telegram, Discord, Slack, iMessage | **claw-me-maybe** (Beeper unified messaging) | ✅ |
| Multi-model support (GPT, Gemini, Ollama) | **LLM Gateway** env vars + **gemini** skill | ✅ |
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

## Ecosystem Compatibility

Because we follow the AgentSkills spec, we can use:
- Any skill from clawhub.com
- Claude Code's built-in skills
- OpenClaw community skills
- Custom skills following the spec
- **Existing homelab skills** (tailscale, unifi, unraid, media stack, etc.)

### Skillbox - Skill Management Layer

**[skillbox](https://github.com/christiananagnostou/skillbox/)** is a local-first, agent-agnostic skills manager.

**What it provides:**
- Central skill repository at `~/.config/skillbox/skills/`
- Install skills from GitHub/ClawHub: `skillbox add owner/repo`
- Auto-sync to multiple agents (Claude Code, Cursor, our API)
- Version management and updates: `skillbox status`, `skillbox update`

**Why we use it:**
- No need to build our own skill installer
- Handles multi-agent sync automatically
- Community-maintained, agent-agnostic
- JSON output for automation

**Integration with our API:**
```python
# Read skills from skillbox's canonical location
SKILLBOX_PATH = Path.home() / ".config" / "skillbox" / "skills"

# Existing QueryEnrichmentService already handles injection
# Just need to add skillbox path to skill discovery
```

### Planned Community Skills (from ClawHub)

| Skill | Downloads | Purpose |
|-------|-----------|---------|
| **gog** | - | Google Workspace (Gmail, Calendar, Drive, Contacts, Sheets, Docs) |
| **caldav** | - | CalDAV calendars (iCloud, Fastmail, Nextcloud) via vdirsyncer + khal |
| **weather** | 4,186 | Weather + forecasts (no API key required) - heartbeat awareness |
| **hackernews** | 18 | Browse/search Hacker News, job postings, tech news awareness |
| **morning-email-rollup** | 609 | Daily email + calendar digest pattern for heartbeat |
| **daily-recap** | 269 | Weather-aware daily summaries, cron-driven |
| **adhd-assistant** | 63 | Task breakdown, prioritization, time management |
| **zero-trust** | 12 | Security-first behavioral guidelines for cautious agent operation |
| **windows-control** | - | Full Windows desktop control (mouse, keyboard, screenshots, interact with any Windows app) |
| **computer-use** | - | Headless Linux desktop control via Xvfb+XFCE (17 actions, VNC remote viewing) |
| **clawflows** | - | Multi-skill automation orchestration (109+ automations, skill-agnostic) |
| **yt-video-downloader** | - | Download YouTube videos/playlists, extract audio, multiple formats/qualities |
| **clawdhub** | - | ClawdHub CLI (steipete) - search, install, update, publish skills |
| **twitter** | - | Twitter/X - post tweets, read timeline, manage followers, engagement metrics |
| **browsh** | - | Text-based browser using headless Firefox - web browsing in terminal/headless environments |
| **bitwarden** | - | Bitwarden/Vaultwarden password management via rbw CLI |
| **agent-browser** | - | Rust headless browser automation CLI (navigate, click, type, snapshot) for AI agents |
| **adguard** | - | AdGuard Home DNS filtering - manage blocklists/allowlists, stats, toggle protection |
| **reddit-scraper** | - | Read/search Reddit posts via old.reddit.com scraping (read-only research) |
| **youtube-transcript** | - | Fetch/summarize YouTube video transcripts (bypasses cloud IP blocks) |
| **skill-creator** | - | Guide for creating new skills - templates, best practices, tool integrations |
| **mcporter** | - | MCP server management (steipete) - list, configure, auth, call HTTP/stdio servers |
| **gemini** | - | Gemini CLI (steipete) - one-shot Q&A, summaries, text generation |
| **notebooklm-cli** | - | Google NotebookLM CLI - manage notebooks, sources, audio overviews |
| **tldr** | - | Simplified man pages from tldr-pages - quick CLI tool reference |
| **create-cli** | - | CLI design guide (steipete) - args, flags, subcommands, help, error handling |
| **openai-docs** | - | Query OpenAI developer docs via MCP - APIs, SDKs, Codex, rate limits |
| **codexmonitor** | - | Monitor/inspect local OpenAI Codex sessions (CLI + VS Code) |
| **google-home-control** | - | Smart home control via Google Assistant SDK (lights, TV, etc.) |
| **local-places** | - | Google Places search (steipete) - restaurants, cafes, nearby venues |
| **claw-me-maybe** | - | Beeper multi-platform messaging (WhatsApp, Telegram, Signal, Discord, Slack, iMessage, LinkedIn, FB, etc.) |

### ClawFlows - Automation Orchestration Layer

**[ClawFlows](https://clawflows.com)** is a registry of 109+ capability-based automations for AI agents.

**Core Philosophy**: Skill-agnostic automations using abstract interfaces (capabilities) that map to concrete skill implementations. "Write once, run anywhere" - automations don't break when you switch underlying skills.

**Capability → Skill Mapping:**
```
Capability (abstract)       →    Skill (concrete implementation)
───────────────────────────────────────────────────────────────
calendar.list_events        →    gog, caldav, google-calendar
email.send                  →    gog, email, gmail, agentmail
database.query              →    sqlite, postgres, supabase
social.search               →    twitter, x-search
```

**Standard Capabilities (Building Blocks):**
- Prediction markets (Polymarket, Kalshi)
- Database operations (SQLite, storage)
- Chart generation
- Social media search (X/Twitter)
- Calendar/scheduling
- Text-to-speech

**Integration with our system:**
- Pre-built automations for heartbeat/cron patterns (morning briefings, daily recaps)
- Abstracts away which email/calendar skill is installed
- Community-maintained automation library (109+ and growing)
- Agent-driven automation creation (AI writes YAML, docs, opens PR)

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

Full desktop automation across all platforms: Chrome (web), windows-control (Windows), computer-use (Linux headless), synapse-mcp (infrastructure).

**Top ClawHub Skills by Downloads (reference):**

| Skill | Downloads | Description |
|-------|-----------|-------------|
| github | 4,500 | `gh` CLI for issues, PRs, CI runs |
| weather | 4,186 | Weather + forecasts (no API key) |
| homeassistant | 3,608 | Smart home control |
| slack | 1,897 | Slack messaging |
| email | 1,615 | Multi-provider email management |
| trello | 1,517 | Board/card management |
| agentmail | 907 | API-first email for AI agents |
| github-pr | 616 | Test PRs locally before merge |
| docker-essentials | 565 | Container management |
| deepwiki | 443 | GitHub repo documentation |

**Note:** Many ClawHub skills duplicate functionality we already have:
- `synapse-mcp` provides Docker/SSH operations (skip docker-essentials, portainer)
- `gog` provides Gmail/Calendar (skip email, gmail skills)
- Existing homelab skills cover infrastructure monitoring

Skills/MCP servers are plug-and-play across:
- Our personal assistant
- Claude Code
- OpenClaw
- Any AgentSkills-compatible agent

## API Surface

### Agent Endpoints (Existing)
```
POST   /api/v1/query                     # Single query
POST   /api/v1/stream                    # SSE streaming
GET    /api/v1/sessions                  # List sessions
POST   /api/v1/sessions                  # Create session
GET    /api/v1/sessions/{id}             # Get session
DELETE /api/v1/sessions/{id}             # Delete session
```

### Skills Endpoints (Existing)
```
GET    /api/v1/skills                    # List available skills
POST   /api/v1/skills                    # Create skill (database)
GET    /api/v1/skills/{id}               # Get skill details
PUT    /api/v1/skills/{id}               # Update skill (database)
DELETE /api/v1/skills/{id}               # Delete skill (database)
```

### Memory Endpoints (New)
```
GET    /api/v1/memory                    # List memories
POST   /api/v1/memory                    # Create memory
GET    /api/v1/memory/search             # Search memories (semantic)
DELETE /api/v1/memory/{id}               # Delete memory
```

### Heartbeat Endpoints (New)
```
GET    /api/v1/heartbeat/config          # Get heartbeat config
PUT    /api/v1/heartbeat/config          # Update heartbeat config
POST   /api/v1/heartbeat/trigger         # Trigger immediate heartbeat
GET    /api/v1/heartbeat/history         # Get heartbeat history
```

### Cron Endpoints (New)
```
GET    /api/v1/cron                      # List cron jobs
POST   /api/v1/cron                      # Create cron job
GET    /api/v1/cron/{id}                 # Get cron job
PUT    /api/v1/cron/{id}                 # Update cron job
DELETE /api/v1/cron/{id}                 # Delete cron job
POST   /api/v1/cron/{id}/run             # Trigger immediate run
GET    /api/v1/cron/{id}/history         # Get run history
```

### QMD Endpoints (New)
```
POST   /api/v1/qmd/index                 # Index markdown directory
GET    /api/v1/qmd/search                # Semantic search markdown files
GET    /api/v1/qmd/status                # Indexing status
```

### Session Search Endpoints (New)
```
POST   /api/v1/session-search/index      # Index Claude sessions
GET    /api/v1/session-search/search     # Search past sessions
GET    /api/v1/session-search/status     # Indexing status
```

### Device Endpoints (New)
```
GET    /api/v1/devices                   # List devices (from memory bank)
GET    /api/v1/devices/{name}            # Get device details
POST   /api/v1/devices/{name}/exec       # Execute command on device
GET    /api/v1/devices/inventory/refresh # Refresh SSH inventory
```

### Infrastructure Endpoints (New - via synapse-mcp)
```
GET    /api/v1/infrastructure/containers                  # List containers (all hosts)
GET    /api/v1/infrastructure/containers/{name}/logs      # Container logs with grep
GET    /api/v1/infrastructure/compose                     # List Compose projects
GET    /api/v1/infrastructure/compose/{project}/status    # Compose project status
GET    /api/v1/infrastructure/hosts/{host}/resources      # CPU/memory/disk usage
GET    /api/v1/infrastructure/hosts/{host}/zfs/pools      # ZFS pool health
GET    /api/v1/infrastructure/hosts/{host}/logs/journal   # systemd journal logs
```

### Persona Endpoints (New)
```
GET    /api/v1/persona                   # Get persona config
PUT    /api/v1/persona                   # Update persona config
```

## Implementation Phases

### Phase 1: Memory System Integration
- Integrate with existing TEI + Qdrant (cli-firecrawl)
- Memory service using existing embedding pipeline
- Memory injection into prompts
- Memory CRUD API endpoints

### Phase 2: Heartbeat System
- Background scheduler (APScheduler)
- HEARTBEAT.md loading and parsing
- Active hours support
- **Gotify integration** (use existing homelab skill)
- Heartbeat history logging

### Phase 3: Cron Jobs
- Cron job storage (PostgreSQL)
- APScheduler with cron triggers
- Main vs isolated session modes
- Job CRUD API endpoints
- **Gotify notifications** for delivery

### Phase 4: QMD (Query Markup Documents)
- Skill for markdown semantic search
- Hook for auto-indexing new files
- Integration with existing Qdrant collection
- Search API endpoints

### Phase 5: Session Search
- JSONL session parser
- Incremental indexing
- Search API endpoints
- Context retrieval for queries

### Phase 6: Device Management API
- Read device inventory from `~/memory/bank/ssh/`
- API endpoints for device queries
- Command execution endpoint (with confirmation)
- Integration with homelab SSH execution

### Phase 7: Web App
- Next.js 15 PWA
- Mobile-first responsive design
- Chat interface with streaming
- Settings/config UI
- Heartbeat/cron dashboard

## Success Metrics

- **Simplicity**: Single `docker compose up` deployment
- **Compatibility**: 100% AgentSkills spec compliance
- **Performance**: Memory search < 200ms (via existing Qdrant)
- **Reliability**: 99.9% heartbeat execution success rate
- **Coverage**: 90% of OpenClaw use cases supported
- **Code Reuse**: Leverage 100% of existing cli-firecrawl and homelab infrastructure
