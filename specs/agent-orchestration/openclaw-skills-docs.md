Skills - OpenClaw
  URL: https://docs.openclaw.ai/tools/skills
  Tools & Skills Skills OpenClaw uses AgentSkills -compatible skill folders to teach the agent how to use tools. Each skill is a directory containing a SKILL.md with YAML frontmatter and instructions. OpenClaw loads bundled skills plus optional local overrides, and filters them at load time based on environment, config, and binary presence.

  --- Content ---
  [Skip to main content](https://docs.openclaw.ai/tools/skills#content-area)
  
  [OpenClaw home page![light logo](https://mintcdn.com/clawdhub/4rYvG-uuZrMK_URE/assets/pixel-lobster.svg?fit=max&auto=format&n=4rYvG-uuZrMK_URE&q=85&s=da2032e9eac3b5d9bfe7eb96ca6a8a26)![dark logo](https://mintcdn.com/clawdhub/4rYvG-uuZrMK_URE/assets/pixel-lobster.svg?fit=max&auto=format&n=4rYvG-uuZrMK_URE&q=85&s=da2032e9eac3b5d9bfe7eb96ca6a8a26)](https://docs.openclaw.ai/)
  
  ![US](https://d3gk2c5xim1je2.cloudfront.net/flags/US.svg)
  
  English
  
  Search...
  
  Ctrl K
  
  Search...
  
  Navigation
  
  Tools & Skills
  
  Skills
  
  On this page
  
  *   [Skills (OpenClaw)](https://docs.openclaw.ai/tools/skills#skills-openclaw)
      
  *   [Locations and precedence](https://docs.openclaw.ai/tools/skills#locations-and-precedence)
      
  *   [Per-agent vs shared skills](https://docs.openclaw.ai/tools/skills#per-agent-vs-shared-skills)
      
  *   [Plugins + skills](https://docs.openclaw.ai/tools/skills#plugins-%2B-skills)
      
  *   [ClawHub (install + sync)](https://docs.openclaw.ai/tools/skills#clawhub-install-%2B-sync)
      
  *   [Security notes](https://docs.openclaw.ai/tools/skills#security-notes)
      
  *   [Format (AgentSkills + Pi-compatible)](https://docs.openclaw.ai/tools/skills#format-agentskills-%2B-pi-compatible)
      
  *   [Gating (load-time filters)](https://docs.openclaw.ai/tools/skills#gating-load-time-filters)
      
  *   [Config overrides (~/.openclaw/openclaw.json)](https://docs.openclaw.ai/tools/skills#config-overrides-%2F-openclaw%2Fopenclaw-json)
      
  *   [Environment injection (per agent run)](https://docs.openclaw.ai/tools/skills#environment-injection-per-agent-run)
      
  *   [Session snapshot (performance)](https://docs.openclaw.ai/tools/skills#session-snapshot-performance)
      
  *   [Remote macOS nodes (Linux gateway)](https://docs.openclaw.ai/tools/skills#remote-macos-nodes-linux-gateway)
      
  *   [Skills watcher (auto-refresh)](https://docs.openclaw.ai/tools/skills#skills-watcher-auto-refresh)
      
  *   [Token impact (skills list)](https://docs.openclaw.ai/tools/skills#token-impact-skills-list)
      
  *   [Managed skills lifecycle](https://docs.openclaw.ai/tools/skills#managed-skills-lifecycle)
      
  *   [Config reference](https://docs.openclaw.ai/tools/skills#config-reference)
      
  *   [Looking for more skills?](https://docs.openclaw.ai/tools/skills#looking-for-more-skills)
      
  
  [​](https://docs.openclaw.ai/tools/skills#skills-openclaw)
  
  Skills (OpenClaw)
  ===============================================================================
  
  OpenClaw uses **[AgentSkills](https://agentskills.io/)
  \-compatible** skill folders to teach the agent how to use tools. Each skill is a directory containing a `SKILL.md` with YAML frontmatter and instructions. OpenClaw loads **bundled skills** plus optional local overrides, and filters them at load time based on environment, config, and binary presence.
  
  [​](https://docs.openclaw.ai/tools/skills#locations-and-precedence)
  
  Locations and precedence
  -----------------------------------------------------------------------------------------------
  
  Skills are loaded from **three** places:
  
  1.  **Bundled skills**: shipped with the install (npm package or OpenClaw.app)
  2.  **Managed/local skills**: `~/.openclaw/skills`
  3.  **Workspace skills**: `<workspace>/skills`
  
  If a skill name conflicts, precedence is: `<workspace>/skills` (highest) → `~/.openclaw/skills` → bundled skills (lowest) Additionally, you can configure extra skill folders (lowest precedence) via `skills.load.extraDirs` in `~/.openclaw/openclaw.json`.
  
  [​](https://docs.openclaw.ai/tools/skills#per-agent-vs-shared-skills)
  
  Per-agent vs shared skills
  ---------------------------------------------------------------------------------------------------
  
  In **multi-agent** setups, each agent has its own workspace. That means:
  
  *   **Per-agent skills** live in `<workspace>/skills` for that agent only.
  *   **Shared skills** live in `~/.openclaw/skills` (managed/local) and are visible to **all agents** on the same machine.
  *   **Shared folders** can also be added via `skills.load.extraDirs` (lowest precedence) if you want a common skills pack used by multiple agents.
  
  If the same skill name exists in more than one place, the usual precedence applies: workspace wins, then managed/local, then bundled.
  
  [​](https://docs.openclaw.ai/tools/skills#plugins-+-skills)
  
  Plugins + skills
  -------------------------------------------------------------------------------
  
  Plugins can ship their own skills by listing `skills` directories in `openclaw.plugin.json` (paths relative to the plugin root). Plugin skills load when the plugin is enabled and participate in the normal skill precedence rules. You can gate them via `metadata.openclaw.requires.config` on the plugin’s config entry. See [Plugins](https://docs.openclaw.ai/plugin)
   for discovery/config and [Tools](https://docs.openclaw.ai/tools)
   for the tool surface those skills teach.
  
  [​](https://docs.openclaw.ai/tools/skills#clawhub-install-+-sync)
  
  ClawHub (install + sync)
  ---------------------------------------------------------------------------------------------
  
  ClawHub is the public skills registry for OpenClaw. Browse at [https://clawhub.com](https://clawhub.com/)
  . Use it to discover, install, update, and back up skills. Full guide: [ClawHub](https://docs.openclaw.ai/tools/clawhub)
  . Common flows:
  
  *   Install a skill into your workspace:
      *   `clawhub install <skill-slug>`
  *   Update all installed skills:
      *   `clawhub update --all`
  *   Sync (scan + publish updates):
      *   `clawhub sync --all`
  
  By default, `clawhub` installs into `./skills` under your current working directory (or falls back to the configured OpenClaw workspace). OpenClaw picks that up as `<workspace>/skills` on the next session.
  
  [​](https://docs.openclaw.ai/tools/skills#security-notes)
  
  Security notes
  ---------------------------------------------------------------------------
  
  *   Treat third-party skills as **untrusted code**. Read them before enabling.
  *   Prefer sandboxed runs for untrusted inputs and risky tools. See [Sandboxing](https://docs.openclaw.ai/gateway/sandboxing)
      .
  *   `skills.entries.*.env` and `skills.entries.*.apiKey` inject secrets into the **host** process for that agent turn (not the sandbox). Keep secrets out of prompts and logs.
  *   For a broader threat model and checklists, see [Security](https://docs.openclaw.ai/gateway/security)
      .
  
  [​](https://docs.openclaw.ai/tools/skills#format-agentskills-+-pi-compatible)
  
  Format (AgentSkills + Pi-compatible)
  ---------------------------------------------------------------------------------------------------------------------
  
  `SKILL.md` must include at least:
  
  Copy
  
      ---
      name: nano-banana-pro
      description: Generate or edit images via Gemini 3 Pro Image
      ---
      
  
  Notes:
  
  *   We follow the AgentSkills spec for layout/intent.
  *   The parser used by the embedded agent supports **single-line** frontmatter keys only.
  *   `metadata` should be a **single-line JSON object**.
  *   Use `{baseDir}` in instructions to reference the skill folder path.
  *   Optional frontmatter keys:
      *   `homepage` — URL surfaced as “Website” in the macOS Skills UI (also supported via `metadata.openclaw.homepage`).
      *   `user-invocable` — `true|false` (default: `true`). When `true`, the skill is exposed as a user slash command.
      *   `disable-model-invocation` — `true|false` (default: `false`). When `true`, the skill is excluded from the model prompt (still available via user invocation).
      *   `command-dispatch` — `tool` (optional). When set to `tool`, the slash command bypasses the model and dispatches directly to a tool.
      *   `command-tool` — tool name to invoke when `command-dispatch: tool` is set.
      *   `command-arg-mode` — `raw` (default). For tool dispatch, forwards the raw args string to the tool (no core parsing). The tool is invoked with params: `{ command: "<raw args>", commandName: "<slash command>", skillName: "<skill name>" }`.
  
  [​](https://docs.openclaw.ai/tools/skills#gating-load-time-filters)
  
  Gating (load-time filters)
  -------------------------------------------------------------------------------------------------
  
  OpenClaw **filters skills at load time** using `metadata` (single-line JSON):
  
  Copy
  
      ---
      name: nano-banana-pro
      description: Generate or edit images via Gemini 3 Pro Image
      metadata:
        {
          "openclaw":
            {
              "requires": { "bins": ["uv"], "env": ["GEMINI_API_KEY"], "config": ["browser.enabled"] },
              "primaryEnv": "GEMINI_API_KEY",
            },
        }
      ---
      
  
  Fields under `metadata.openclaw`:
  
  *   `always: true` — always include the skill (skip other gates).
  *   `emoji` — optional emoji used by the macOS Skills UI.
  *   `homepage` — optional URL shown as “Website” in the macOS Skills UI.
  *   `os` — optional list of platforms (`darwin`, `linux`, `win32`). If set, the skill is only eligible on those OSes.
  *   `requires.bins` — list; each must exist on `PATH`.
  *   `requires.anyBins` — list; at least one must exist on `PATH`.
  *   `requires.env` — list; env var must exist **or** be provided in config.
  *   `requires.config` — list of `openclaw.json` paths that must be truthy.
  *   `primaryEnv` — env var name associated with `skills.entries.<name>.apiKey`.
  *   `install` — optional array of installer specs used by the macOS Skills UI (brew/node/go/uv/download).
  
  Note on sandboxing:
  
  *   `requires.bins` is checked on the **host** at skill load time.
  *   If an agent is sandboxed, the binary must also exist **inside the container**. Install it via `agents.defaults.sandbox.docker.setupCommand` (or a custom image). `setupCommand` runs once after the container is created. Package installs also require network egress, a writable root FS, and a root user in the sandbox. Example: the `summarize` skill (`skills/summarize/SKILL.md`) needs the `summarize` CLI in the sandbox container to run there.
  
  Installer example:
  
  Copy
  
      ---
      name: gemini
      description: Use Gemini CLI for coding assistance and Google search lookups.
      metadata:
        {
          "openclaw":
            {
              "emoji": "♊️",
              "requires": { "bins": ["gemini"] },
              "install":
                [\
                  {\
                    "id": "brew",\
                    "kind": "brew",\
                    "formula": "gemini-cli",\
                    "bins": ["gemini"],\
                    "label": "Install Gemini CLI (brew)",\
                  },\
                ],
            },
        }
      ---
      
  
  Notes:
  
  *   If multiple installers are listed, the gateway picks a **single** preferred option (brew when available, otherwise node).
  *   If all installers are `download`, OpenClaw lists each entry so you can see the available artifacts.
  *   Installer specs can include `os: ["darwin"|"linux"|"win32"]` to filter options by platform.
  *   Node installs honor `skills.install.nodeManager` in `openclaw.json` (default: npm; options: npm/pnpm/yarn/bun). This only affects **skill installs**; the Gateway runtime should still be Node (Bun is not recommended for WhatsApp/Telegram).
  *   Go installs: if `go` is missing and `brew` is available, the gateway installs Go via Homebrew first and sets `GOBIN` to Homebrew’s `bin` when possible.
  *   Download installs: `url` (required), `archive` (`tar.gz` | `tar.bz2` | `zip`), `extract` (default: auto when archive detected), `stripComponents`, `targetDir` (default: `~/.openclaw/tools/<skillKey>`).
  
  If no `metadata.openclaw` is present, the skill is always eligible (unless disabled in config or blocked by `skills.allowBundled` for bundled skills).
  
  [​](https://docs.openclaw.ai/tools/skills#config-overrides-/-openclaw/openclaw-json)
  
  Config overrides (`~/.openclaw/openclaw.json`)
  --------------------------------------------------------------------------------------------------------------------------------------
  
  Bundled/managed skills can be toggled and supplied with env values:
  
  Copy
  
      {
        skills: {
          entries: {
            "nano-banana-pro": {
              enabled: true,
              apiKey: "GEMINI_KEY_HERE",
              env: {
                GEMINI_API_KEY: "GEMINI_KEY_HERE",
              },
              config: {
                endpoint: "https://example.invalid",
                model: "nano-pro",
              },
            },
            peekaboo: { enabled: true },
            sag: { enabled: false },
          },
        },
      }
      
  
  Note: if the skill name contains hyphens, quote the key (JSON5 allows quoted keys). Config keys match the **skill name** by default. If a skill defines `metadata.openclaw.skillKey`, use that key under `skills.entries`. Rules:
  
  *   `enabled: false` disables the skill even if it’s bundled/installed.
  *   `env`: injected **only if** the variable isn’t already set in the process.
  *   `apiKey`: convenience for skills that declare `metadata.openclaw.primaryEnv`.
  *   `config`: optional bag for custom per-skill fields; custom keys must live here.
  *   `allowBundled`: optional allowlist for **bundled** skills only. If set, only bundled skills in the list are eligible (managed/workspace skills unaffected).
  
  [​](https://docs.openclaw.ai/tools/skills#environment-injection-per-agent-run)
  
  Environment injection (per agent run)
  -----------------------------------------------------------------------------------------------------------------------
  
  When an agent run starts, OpenClaw:
  
  1.  Reads skill metadata.
  2.  Applies any `skills.entries.<key>.env` or `skills.entries.<key>.apiKey` to `process.env`.
  3.  Builds the system prompt with **eligible** skills.
  4.  Restores the original environment after the run ends.
  
  This is **scoped to the agent run**, not a global shell environment.
  
  [​](https://docs.openclaw.ai/tools/skills#session-snapshot-performance)
  
  Session snapshot (performance)
  ---------------------------------------------------------------------------------------------------------
  
  OpenClaw snapshots the eligible skills **when a session starts** and reuses that list for subsequent turns in the same session. Changes to skills or config take effect on the next new session. Skills can also refresh mid-session when the skills watcher is enabled or when a new eligible remote node appears (see below). Think of this as a **hot reload**: the refreshed list is picked up on the next agent turn.
  
  [​](https://docs.openclaw.ai/tools/skills#remote-macos-nodes-linux-gateway)
  
  Remote macOS nodes (Linux gateway)
  -----------------------------------------------------------------------------------------------------------------
  
  If the Gateway is running on Linux but a **macOS node** is connected **with `system.run` allowed** (Exec approvals security not set to `deny`), OpenClaw can treat macOS-only skills as eligible when the required binaries are present on that node. The agent should execute those skills via the `nodes` tool (typically `nodes.run`). This relies on the node reporting its command support and on a bin probe via `system.run`. If the macOS node goes offline later, the skills remain visible; invocations may fail until the node reconnects.
  
  [​](https://docs.openclaw.ai/tools/skills#skills-watcher-auto-refresh)
  
  Skills watcher (auto-refresh)
  -------------------------------------------------------------------------------------------------------
  
  By default, OpenClaw watches skill folders and bumps the skills snapshot when `SKILL.md` files change. Configure this under `skills.load`:
  
  Copy
  
      {
        skills: {
          load: {
            watch: true,
            watchDebounceMs: 250,
          },
        },
      }
      
  
  [​](https://docs.openclaw.ai/tools/skills#token-impact-skills-list)
  
  Token impact (skills list)
  -------------------------------------------------------------------------------------------------
  
  When skills are eligible, OpenClaw injects a compact XML list of available skills into the system prompt (via `formatSkillsForPrompt` in `pi-coding-agent`). The cost is deterministic:
  
  *   **Base overhead (only when ≥1 skill):** 195 characters.
  *   **Per skill:** 97 characters + the length of the XML-escaped `<name>`, `<description>`, and `<location>` values.
  
  Formula (characters):
  
  Copy
  
      total = 195 + Σ (97 + len(name_escaped) + len(description_escaped) + len(location_escaped))
      
  
  Notes:
  
  *   XML escaping expands `& < > " '` into entities (`&amp;`, `&lt;`, etc.), increasing length.
  *   Token counts vary by model tokenizer. A rough OpenAI-style estimate is ~4 chars/token, so **97 chars ≈ 24 tokens** per skill plus your actual field lengths.
  
  [​](https://docs.openclaw.ai/tools/skills#managed-skills-lifecycle)
  
  Managed skills lifecycle
  -----------------------------------------------------------------------------------------------
  
  OpenClaw ships a baseline set of skills as **bundled skills** as part of the install (npm package or OpenClaw.app). `~/.openclaw/skills` exists for local overrides (for example, pinning/patching a skill without changing the bundled copy). Workspace skills are user-owned and override both on name conflicts.
  
  [​](https://docs.openclaw.ai/tools/skills#config-reference)
  
  Config reference
  -------------------------------------------------------------------------------
  
  See [Skills config](https://docs.openclaw.ai/tools/skills-config)
   for the full configuration schema.
  
  [​](https://docs.openclaw.ai/tools/skills#looking-for-more-skills)
  
  Looking for more skills?
  ----------------------------------------------------------------------------------------------
  
  Browse [https://clawhub.com](https://clawhub.com/)
  .
  
  * * *
  
  [Reactions](https://docs.openclaw.ai/tools/reactions)
  [Skills Config](https://docs.openclaw.ai/tools/skills-config)
  
  Ctrl+I
  
  Assistant
  
  Responses are generated using AI and may contain mistakes.
  --- End Content ---

How to Run OpenClaw with DigitalOcean's One-Click Deploy
  URL: https://www.digitalocean.com/community/tutorials/how-to-run-openclaw
  Step 3 — Installing Skills ... OpenClaw comes with over 50 skills automatically loaded in the skill registry. You can install skills in the GUI by ...

  --- Content ---
  Report this
  -----------
  
  What is the reason for this report?
  
  This undefined is spam
  
  This undefined is offensive
  
  This undefined is off-topic
  
  This undefined is other
  
  Submit
  
  [Tutorial](https://www.digitalocean.com/community/tutorials?subtype=tutorial)
  
  How to Run OpenClaw with DigitalOcean's One-Click Deploy
  ========================================================
  
  Published on January 29, 2026
  
  [](https://twitter.com/intent/tweet?url=https%3A%2F%2Fwww.digitalocean.com%2Fcommunity%2Ftutorials%2Fhow-to-run-openclaw%3Futm_medium%3Dcommunity%26utm_source%3Dtwshare%26utm_content%3Dhow-to-run-openclaw&text=&via=digitalocean "Share to X (Twitter)")
  [](https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Fwww.digitalocean.com%2Fcommunity%2Ftutorials%2Fhow-to-run-openclaw%3Futm_medium%3Dcommunity%26utm_source%3Dtwshare%26utm_content%3Dhow-to-run-openclaw&t= "Share to Facebook")
  [](https://www.linkedin.com/shareArticle?mini=true&url=https%3A%2F%2Fwww.digitalocean.com%2Fcommunity%2Ftutorials%2Fhow-to-run-openclaw%3Futm_medium%3Dcommunity%26utm_source%3Dtwshare%26utm_content%3Dhow-to-run-openclaw&title= "Share to LinkedIn")
  [](https://news.ycombinator.com/submitlink?u=https%3A%2F%2Fwww.digitalocean.com%2Fcommunity%2Ftutorials%2Fhow-to-run-openclaw%3Futm_medium%3Dcommunity%26utm_source%3Dtwshare%26utm_content%3Dhow-to-run-openclaw&t= "Share to YCombinator")
  
  [AI/ML](https://www.digitalocean.com/community/tags/ai-ml)
  
  ![Andrew Dugan](https://www.gravatar.com/avatar/b0ff6a610e46fa2ae4d77c43b13c4bfd20cf902be9f00a869e302651b6700aaa?default=retro&size=256)
  
  By [Andrew Dugan](https://www.digitalocean.com/community/users/andrewdugan)
  
  Senior AI Technical Content Creator II
  
  ![How to Run OpenClaw with DigitalOcean's One-Click Deploy](https://www.digitalocean.com/api/static-content/v1/images?src=https%3A%2F%2Fdoimages.nyc3.cdn.digitaloceanspaces.com%2F007BlogBanners2024%2Freport-2%28spraytan%29.png&width=1920 "How to Run OpenClaw with DigitalOcean's One-Click Deploy")
  
  Table of contents
  
  Popular topics
  
  ### [Introduction](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#introduction)
  [](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#introduction)
  
  [OpenClaw](https://openclaw.ai/)
   (formerly known as Moltbot and Clawdbot) is an open-source, self-hosted personal AI assistant that can run directly on your computer. It can execute a variety of tasks, such as managing your calendar, browsing the web, organizing files, managing your email, and running terminal commands. It supports any Large Language Model (LLM), and you can communicate with it through standard chat apps that you already use like WhatsApp, iMessage, Telegram, Discord, or Slack.
  
  While it is technically possible to run OpenClaw on your local machine, security concerns arise when giving an AI agent open access to your computer with all of your personal data on it. A better approach is to deploy it on a separate machine specifically for OpenClaw or to deploy it on a cloud server.
  
  In this tutorial, you will deploy a OpenClaw instance onto DigitalOcean’s 1 Click Deploy OpenClaw. Then you will access the Graphical User Interface (GUI) via a secure connection through your web browser. The DigitalOcean 1 Click Deploy OpenClaw will handle many of the security best-practices for you automatically. These security enhancements include:
  
  *   **Authenticated communication:** Droplets generate a OpenClaw gateway token, so communication to your OpenClaw is authenticated, essentially protecting your instance from unauthorized users.
  *   **Hardened firewall rules:** Droplets harden your server with default firewall rules that rate-limit OpenClaw ports to prevent inappropriate traffic from interfering with your OpenClaw use and to help prevent denial-of-service attacks.
  *   **Non-root user execution:** Droplets run OpenClaw as a non-root user on the server, limiting the attack surface if an inappropriate command is executed by OpenClaw.
  *   **Docker container isolation:** Droplets run OpenClaw inside Docker containers on your server, setting up an [isolated sandbox](https://docs.openclaw.ai/gateway/sandboxing)
       and further preventing unintended commands from impacting your server.
  *   **Private DM pairing:** Droplets configure [Direct Message (DM) pairing](https://docs.openclaw.ai/start/pairing)
       by default, which prevents unauthorized individuals from being able to talk to your OpenClaw.
  
  While deploying this way on a cloud server offers security benefits, OpenClaw is still quite new. Like many new tools, it might have architectural characteristics that have not been designed to work with additional security features yet. Therefore, with added security features, some of OpenClaw’s functionality may not function as perfectly as it was intended. For example, some skills might not work out-of-the-box and can require some additional manual setup.
  
  [Key Takeaways](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#key-takeaways)
  [](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#key-takeaways)
  
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  *   OpenClaw is a powerful, self-hosted AI assistant that can execute tasks like managing calendars, browsing the web, and running terminal commands. It should not be run on your personal machine due to significant security risks associated with giving an AI agent high-level system access.
      
  *   Deploying OpenClaw on a cloud server provides a safer environment through security features like authenticated communication, hardened firewall rules, non-root user execution, Docker container isolation, and private Direct Message (DM) pairing.
      
  *   OpenClaw is model-agnostic and supports various LLMs via Application Programming Interface (API) keys or local deployment, making it flexible for different use cases and preferences.
      
  
  [Step 1 — Creating a OpenClaw Droplet](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#step-1-creating-a-openclaw-droplet)
  [](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#step-1-creating-a-openclaw-droplet)
  
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  First, sign in to your DigitalOcean account and [create a Droplet](https://cloud.digitalocean.com/droplets/new)
  . On the Create Droplets page, under `Region`, select the region that best applies to you. Under `Choose an Image`, select the `Marketplace` tab.
  
  In the search bar, type `Moltbot` and select the Moltbot image from the search results.
  
  Next, choose a Droplet plan. The Basic plan with at least 4GB of RAM (such as the `s-2vcpu-4gb` size) is recommended for running OpenClaw effectively.
  
  Under **Authentication**, select **SSH Key** and add your SSH key if you haven’t already. If you need to create an SSH key, follow the instructions in [How to Add SSH Keys to New or Existing Droplets](https://docs.digitalocean.com/products/droplets/how-to/add-ssh-keys/)
  .
  
  Finally, give your Droplet a hostname (such as `OpenClaw-server`), and click **Create Droplet**.
  
  Alternatively, you can create a OpenClaw Droplet using the DigitalOcean API. To create a 4GB OpenClaw Droplet in the NYC3 region, use the following curl command. You’ll need to either save your [API access token](https://docs.digitalocean.com/reference/api/create-personal-access-token/)
   to an environment variable or substitute it into the command:
  
      curl -X POST -H 'Content-Type: application/json' \
           -H 'Authorization: Bearer '$TOKEN'' -d \
          '{"name":"choose_a_name","region":"nyc3","size":"s-2vcpu-4gb","image":"Moltbot"}' \
          "https://api.digitalocean.com/v2/droplets"
      
  
  Copy
  
  Once your Droplet is created, it will take a few minutes to fully initialize. After initialization, you can SSH into your Droplet using the ipv4 address shown in your DigitalOcean dashboard:
  
      ssh root@your_droplet_ip
      
  
  Copy
  
  Replace `your_droplet_ip` with your Droplet’s actual IP address.
  
  Once logged in, the OpenClaw installation will be ready to configure. The 1 Click Deploy OpenClaw includes OpenClaw version 2026.1.24-1 pre-installed with all necessary dependencies.
  
  You will see a welcome message from OpenClaw. Under the `Control UI & Gateway Access` section, you will see a `Dashboard URL`. Note the Dashboard URL value. You will use it later to access the GUI in your browser.
  
  ![Dashboard URL](https://doimages.nyc3.cdn.digitaloceanspaces.com/010AI-ML/2025/Andrew/9_Moltbot/Dashboard_URL.png)
  
  Within the terminal, choose `Anthropic` as your AI Provider. If you have access to Gradient AI, you can select that option. OpenAI models will be available soon. Once you select your provider, provide the respective API/Secret key.
  
  This will set you up to start using OpenClaw with your LLM.
  
  [Step 2 — Using OpenClaw](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#step-2-using-openclaw)
  [](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#step-2-using-openclaw)
  
  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  There are two ways to use OpenClaw: you can either use the Graphical User Interface (GUI) through your browser, or you can use the Text User Interface (TUI) through your terminal. To use the TUI, run the following command.
  
      /opt/clawdbot-tui.sh
      
  
  Copy
  
  To use the GUI, open a browser and in the URL bar, paste the dashboard URL from earlier. This will open a standard OpenClaw GUI directly in your browser that uses the Gateway token to authenticate you for additional security. This will direct you to the default Chat page.
  
  ![OpenClaw GUI](https://doimages.nyc3.cdn.digitaloceanspaces.com/010AI-ML/2025/Andrew/9_Moltbot/Moltbot%20Chat%20Page.png)
  
  Here you can type a message and send, and OpenClaw will respond. For example, if you ask about what files it can see, it will tell you.
  
      InputWhat files can you currently see on my computer?
      
  
      OutputHere’s a list of the files and directories currently visible in the sandbox workspace:
      .
      ├── AGENTS.md
      ├── BOOTSTRAP.md
      ├── HEARTBEAT.md
      ├── USER.md
      └── skills
          ├── 1password
          │   ├── SKILL.md
          │   └── references
      ...
      
  
  From the GUI, you can review the bot’s usage, add communication channels, schedule cron jobs, add skills, and manage all aspects of OpenClaw. You’ve now successfully deployed OpenClaw on DigitalOcean and accessed it through a web browser. From here, you can explore additional OpenClaw capabilities, such as browsing the web, managing files, or executing terminal commands on your Droplet.
  
  [Step 3 — Installing Skills](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#step-3-installing-skills)
  [](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#step-3-installing-skills)
  
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  OpenClaw comes with over 50 skills automatically loaded in the skill registry. You can install skills in the GUI by navigating to the `Skills` section in the browser dashboard. For example, to integrate with Google Calendar, search for calendar, and click on \`Install gog (brew).
  
  ![Install a skilll on OpenClaw](https://doimages.nyc3.cdn.digitaloceanspaces.com/010AI-ML/2025/Andrew/9_Moltbot/Install%20a%20Skill.png)
  
  A large number of skills are available to perform a wide range of tasks including managing your files, automating web browsing, monitoring health and smart home technologies, and managing social media communication. Read through [What is OpenClaw?](https://www.digitalocean.com/resources/articles/what-is-moltbot)
   for an overview of how OpenClaw works and what OpenClaw’s capabilities are.
  
  [FAQ](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#faq)
  [](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#faq)
  
  -------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  **Can I use a model other than Claude?**
  
  Yes, OpenClaw is designed to be model-agnostic, so it does support models other than Anthropic’s Claude. It allows users to use various Large Language Models (LLMs) via API keys or locally. However, note that using the 1 Click Deploy OpenClaw as outlined above, most users will only be able to use Anthropic (support for OpenAI coming soon!).
  
  **Can I deploy it on other operating systems that are not Linux?**
  
  Yes, you can deploy OpenClaw on [Windows](https://docs.openclaw.ai/platforms/windows)
  , [macOS](https://docs.openclaw.ai/platforms/macos)
  , and [Linux](https://docs.openclaw.ai/platforms/linux)
  , and [other platforms](https://docs.openclaw.ai/platforms)
  .
  
  **What are the main security concerns?**
  
  The main security concerns are its high-level system access, potential for misconfiguration, and its ability to execute arbitrary code that might be harmful to your system. It’s important to be aware of the environment in which it’s deployed and the access it has.
  
  **How do I give API Key access to my Agents?**
  
  It is possible to selectively give agents more control over the world around you. The default OpenClaw application will keep these keys together in an environment that is available to all agents. This configuration gives you control to inject the keys you want to the agents that should have those powers. On the “Agents” Menu bar, select the Agent you’d like to grant access (or “Defaults” for all), then under Sandbox > Docker > Env, add the select API Keys that should be used.
  
  **How does pricing work with OpenClaw?**
  
  OpenClaw is free and open-source to download and use, but you are paying for the LLM tokens. Therefore, the price depends on your usage. You should be careful with this because with scheduled jobs or other functionality, the costs can increase quickly and unexpectedly.
  
  [Conclusion](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#conclusion)
  [](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#conclusion)
  
  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  In this tutorial, you deployed DigitalOcean’s 1 Click Deploy OpenClaw, creating a secure environment for your personal AI assistant. By running OpenClaw on a cloud server instead of your local machine, you’ve significantly reduced security risks while maintaining the full functionality of this powerful tool.
  
  The DigitalOcean 1 Click Deploy OpenClaw provides critical security features out of the box—including authenticated communication, hardened firewall rules, Docker container isolation, and non-root user execution—that make it safer to experiment with AI agent capabilities. You accessed it through a web browser and can now execute various tasks through your preferred messaging apps. Next, try adding new skills to your OpenClaw instance and customize the app to best suit your agentic needs.
  
  [Related Links](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#related-links)
  [](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#related-links)
  
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  *   [OpenClaw Quickstart Guide](https://www.digitalocean.com/community/tutorials/moltbot-quickstart-guide)
      
  *   [How to Build Parallel Agentic Workflows with Python](https://www.digitalocean.com/community/tutorials/how-to-build-parallel-agentic-workflows-with-python)
      
  *   [Mistral 3 Models on DigitalOcean](https://www.digitalocean.com/community/tutorials/mistral-3-models)
      
  
  Thanks for learning with the DigitalOcean Community. Check out our offerings for compute, storage, networking, and managed databases.
  
  [Learn more about our products](https://www.digitalocean.com/products "Learn more about our products")
  
  ### About the author
  
  ![Andrew Dugan](https://www.gravatar.com/avatar/b0ff6a610e46fa2ae4d77c43b13c4bfd20cf902be9f00a869e302651b6700aaa?default=retro&size=256)
  
  Andrew Dugan
  
  Author
  
  Senior AI Technical Content Creator II
  
  [See author profile](https://www.digitalocean.com/community/users/andrewdugan)
  
  Andrew is an NLP Scientist with 8 years of experience designing and deploying enterprise AI applications and language processing systems.
  
  [See author profile](https://www.digitalocean.com/community/users/andrewdugan)
  
  Category:
  
  [Tutorial](https://www.digitalocean.com/community/tutorials?subtype=tutorial)
  
  Tags:
  
  [AI/ML](https://www.digitalocean.com/community/tags/ai-ml)
  
  [](https://twitter.com/intent/tweet?url=https%3A%2F%2Fwww.digitalocean.com%2Fcommunity%2Ftutorials%2Fhow-to-run-openclaw%3Futm_medium%3Dcommunity%26utm_source%3Dtwshare%26utm_content%3Dhow-to-run-openclaw&text=&via=digitalocean "Share to X (Twitter)")
  [](https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Fwww.digitalocean.com%2Fcommunity%2Ftutorials%2Fhow-to-run-openclaw%3Futm_medium%3Dcommunity%26utm_source%3Dtwshare%26utm_content%3Dhow-to-run-openclaw&t= "Share to Facebook")
  [](https://www.linkedin.com/shareArticle?mini=true&url=https%3A%2F%2Fwww.digitalocean.com%2Fcommunity%2Ftutorials%2Fhow-to-run-openclaw%3Futm_medium%3Dcommunity%26utm_source%3Dtwshare%26utm_content%3Dhow-to-run-openclaw&title= "Share to LinkedIn")
  [](https://news.ycombinator.com/submitlink?u=https%3A%2F%2Fwww.digitalocean.com%2Fcommunity%2Ftutorials%2Fhow-to-run-openclaw%3Futm_medium%3Dcommunity%26utm_source%3Dtwshare%26utm_content%3Dhow-to-run-openclaw&t= "Share to YCombinator")
  
  #### Still looking for an answer?
  
  [Ask a question](https://www.digitalocean.com/community/questions)
  [Search for more help](https://www.digitalocean.com/community)
  
  Was this helpful?
  
  YesNo
  
  Comments(2)Follow-up questions(0)
  
  [](https://www.digitalocean.com/community/markdown "Help")
  
  Leave a comment...﻿
  
  This textbox defaults to using Markdown to format your answer.
  
  You can type !ref in this text area to quickly search our full set of tutorials, documentation & marketplace offerings and insert the link!
  
  [Sign in/up to comment](https://www.digitalocean.com/api/dynamic-content/v1/login?success_redirect=https%3A%2F%2Fwww.digitalocean.com%2Fcommunity%2Ftutorials%2Fhow-to-run-openclaw&error_redirect=https%3A%2F%2Fwww.digitalocean.com%2Fauth-error&type=register)
  
  ![Romain Bernardeau](https://www.gravatar.com/avatar/6beb02ed26b9f9b5a0fb7ee5feba24976d9504e03e25814851ac5366c69436af?default=retro)
  
  [Romain Bernardeau](https://www.digitalocean.com/community/users/romainbernardeau)
  
  [January 29, 2026](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw?comment=213389)
  
  Show less
  
  Thank you for this useful guide and the Molt integration!
  
  Could you share more detail regarding Gradient AI integration, does it work only whith anthropic ?
  
  Reply
  
  ![Joel DeTeves](https://www.gravatar.com/avatar/00697febf3bc64ec41617cbc72a17dc8543747d1de9094604e2eaccced9f8aa8?default=retro)
  
  [Joel DeTeves](https://www.digitalocean.com/community/users/joeldeteves)
  
  [February 1, 2026](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw?comment=213428)
  
  Show less
  
  A couple of suggestions:
  
  1.  Please include brew out of the box. This would allow for more plugins to be installed.
  2.  DO should support any model openclaw supports using BYOK. Being limited to Gradient, OpenAI and Anthropic is a bummber. You can manually finagle it using the CLI but no idea how this works with the docker setup, or if it’s fragile / breaks something.
  
  Reply
  
  [![Creative Commons](https://www.digitalocean.com/api/static-content/v1/images?src=%2F_next%2Fstatic%2Fmedia%2Fcreativecommons.c0a877f1.png&width=384)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
  This work is licensed under a Creative Commons Attribution-NonCommercial- ShareAlike 4.0 International License.
  
  ##### Join the Tech Talk
  
  **Success!** Thank you! Please check your email for further details.
  
  Please complete your information!
  
  *   Table of contents
  
  *   [Key Takeaways](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#key-takeaways)
      
  *   [Step 1 — Creating a OpenClaw Droplet](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#step-1-creating-a-openclaw-droplet)
      
  *   [Step 2 — Using OpenClaw](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#step-2-using-openclaw)
      
  *   [Step 3 — Installing Skills](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#step-3-installing-skills)
      
  *   [FAQ](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#faq)
      
  *   [Conclusion](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#conclusion)
      
  *   [Related Links](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw#related-links)
      
  
  *   Deploy on DigitalOcean
      ----------------------
      
      Click below to sign up for DigitalOcean's virtual machines, Databases, and AIML products.
      
      [Sign up](https://cloud.digitalocean.com/registrations/new?refcode=f6fcd01aaffb)
      
  
  ![](https://www.digitalocean.com/api/static-content/v1/images?src=%2F_next%2Fstatic%2Fmedia%2Ftutorials-2-tulip.764b9f59.svg&width=1920)
  
  Become a contributor for community
  ----------------------------------
  
  Get paid to write technical tutorials and select a tech-focused charity to receive a matching donation.
  
  [Sign Up](https://www.digitalocean.com/community/pages/write-for-digitalocean)
  
  ![](https://www.digitalocean.com/api/static-content/v1/images?src=%2F_next%2Fstatic%2Fmedia%2Fdocs-2-kiwi.239a03ef.svg&width=1920)
  
  DigitalOcean Documentation
  --------------------------
  
  Full documentation for every DigitalOcean product.
  
  [Learn more](https://docs.digitalocean.com/)
  
  ![](https://www.digitalocean.com/api/static-content/v1/images?src=%2F_next%2Fstatic%2Fmedia%2Fblogs-1-lavender.495d1f00.svg&width=1920)
  
  Resources for startups and SMBs
  -------------------------------
  
  The Wave has everything you need to know about building a business, from raising funding to marketing your product.
  
  [Learn more](https://www.digitalocean.com/resources)
  
  Get our newsletter
  ------------------
  
  Stay up to date by signing up for DigitalOcean’s Infrastructure as a Newsletter.
  
  Submit
  
  Submit
  
  New accounts only. By submitting your email you agree to our [Privacy Policy](https://www.digitalocean.com/legal/privacy-policy)
  
  The developer cloud
  -------------------
  
  Scale up as you grow — whether you're running one virtual machine or ten thousand.
  
  [View all products](https://www.digitalocean.com/products)
  
  ![](https://www.digitalocean.com/api/static-content/v1/images?src=%2F_next%2Fstatic%2Fmedia%2Fclouds-mobile.5d14bead.svg&width=3840)
  
  Get started for free
  --------------------
  
  Sign up and get $200 in credit for your first 60 days with DigitalOcean.\*
  
  [Get started](https://cloud.digitalocean.com/registrations/new?refcode=f6fcd01aaffb)
  
  ![](https://www.digitalocean.com/api/static-content/v1/images?src=%2F_next%2Fstatic%2Fmedia%2Fwaves-mobile.a054c63e.svg&width=3840)
  
  \*This promotional offer applies to new accounts only.
  --- End Content ---

OpenClaw Custom Skill Creation - Step by Step
  URL: https://zenvanriel.nl/ai-engineer-blog/openclaw-custom-skill-creation-guide/
  Learn how to create custom skills for OpenClaw that make your AI assistant do exactly what you need. From SKILL.md anatomy to community sharing.

Exploring the OpenClaw Extension Ecosystem: 50+ Official Integrations ...
  URL: https://help.apiyi.com/en/openclaw-extensions-ecosystem-guide-en.html
  OpenClaw's Skills system uses the AgentSkills standard format—an open standard developed by Anthropic and adopted by several AI coding assistants. This means skills developed for OpenClaw can theoretically be used on other compatible platforms, and vice versa. Architectural Advantage: OpenClaw's modular design makes extending it a breeze.

  --- Content ---
  [Skip to content](https://help.apiyi.com/en/openclaw-extensions-ecosystem-guide-en.html#main)
    
  
  Author's Note: A deep dive into the OpenClaw extension ecosystem, covering the 700+ Skills library, 12 major messaging platform integrations, and a guide to using the ClawHub skill store to help developers quickly build personalized AI assistants.
  
  Want your AI assistant to connect to WhatsApp, control your smart home, or automate GitHub workflows? OpenClaw's extension ecosystem is the perfect solution for these needs. This article will systematically introduce OpenClaw's 700+ Skills library and 12 major messaging platform integrations, helping you quickly build a powerful personalized AI assistant.
  
  **Core Value**: By the end of this article, you'll master how to install and configure OpenClaw extensions, understand the use cases for various extensions, and be able to choose the best skill combination for your needs.
  
  ![openclaw-extensions-ecosystem-guide-en 图示](https://help.apiyi.com/wp-content/uploads/2026/02/openclaw-extensions-ecosystem-guide-en-image-0.png)
  
  * * *
  
  OpenClaw Extension Ecosystem Key Points
  ---------------------------------------
  
  OpenClaw (formerly Clawdbot/Moltbot) is the hottest open-source AI assistant project of 2026, with over 135,000 GitHub stars. Its powerful extension ecosystem is one of its core competitive advantages.
  
  | Key Point | Description | Value |
  | --- | --- | --- |
  | **700+ Skills** | ClawHub skill store offers a massive library of community skills | Plug-and-play, rapid capability expansion |
  | **12 Messaging Platforms** | Supports WhatsApp, Telegram, Discord, and other major platforms | Unified entry point, cross-platform interaction |
  | **Local-First Architecture** | All data is stored locally, ensuring privacy and security | Enterprise-grade security, data sovereignty |
  | **Model-Agnostic Design** | Supports Claude, GPT, Gemini, and more | Flexible switching, cost control |
  
  ### OpenClaw Extension Architecture Deep Dive
  
  OpenClaw's extension ecosystem is built on four core components: **Gateway**, **Agent**, **Skills**, and **Memory**. The Gateway acts as the backend service managing all messaging platform connections; the Agent is the reasoning engine responsible for understanding user intent; Skills are modular capability extensions that implement specific functions; and Memory is the persistent storage layer that keeps context and preferences.
  
  This architectural design gives OpenClaw incredible scalability. Each Skill is an independent directory containing a SKILL.md config file and related scripts, with metadata and dependencies defined via YAML frontmatter. The system automatically filters available skills based on the environment, configuration, and dependencies during loading, ensuring only the functions the user needs are loaded.
  
  ### OpenClaw Extension Core Component Comparison
  
  | Component | Responsibility | Technical Implementation | Extension Method |
  | --- | --- | --- | --- |
  | **Gateway** | Messaging platform connection management | Node.js long-connection service | Add new Channel plugins |
  | **Agent** | Intent understanding and reasoning | Large Language Model API calls | Switch between different AI models |
  | **Skills** | Specific functional implementation | SKILL.md + scripts | Install/develop new skills |
  | **Memory** | Contextual persistence | Markdown file storage | Configure storage strategies |
  
  OpenClaw's Skills system uses the AgentSkills standard format—an open standard developed by Anthropic and adopted by several AI coding assistants. This means skills developed for OpenClaw can theoretically be used on other compatible platforms, and vice versa.
  
  > **Architectural Advantage**: OpenClaw's modular design makes extending it a breeze. If you need to connect a specific messaging platform or add a new feature, you just need to develop the corresponding Channel or Skill module without touching the core code. This design philosophy aligns perfectly with APIYI's (apiyi.com) unified interface approach—reducing integration costs through standardization.
  
  ![openclaw-extensions-ecosystem-guide-en 图示](https://help.apiyi.com/wp-content/uploads/2026/02/openclaw-extensions-ecosystem-guide-en-image-1.png)
  
  * * *
  
  OpenClaw Message Platform Integration Guide
  -------------------------------------------
  
  OpenClaw supports 12 major message platforms, allowing you to interact with your AI assistant on any device. Here's the full list of supported platforms and key configuration points.
  
  ### Message Platform Support at a Glance
  
  | Platform | Integration Method | Difficulty | Core Features |
  | --- | --- | --- | --- |
  | **WhatsApp** | Baileys (Web Protocol) | ⭐⭐  | Scan to log in, most common |
  | **Telegram** | grammY (Bot API) | ⭐   | Create a Bot, simplest |
  | **Discord** | discord.js | ⭐⭐  | Server integration |
  | **Slack** | Bolt SDK | ⭐⭐  | Top choice for enterprise collab |
  | **iMessage** | imsg CLI | ⭐⭐⭐ | macOS only |
  | **Signal** | signal-cli | ⭐⭐⭐ | Privacy first |
  | **Google Chat** | Chat API | ⭐⭐  | Workspace integration |
  | **Microsoft Teams** | Extension | ⭐⭐⭐ | Enterprise office |
  | **Matrix** | Extension | ⭐⭐  | Open-source protocol |
  | **BlueBubbles** | Extension | ⭐⭐  | iOS message bridging |
  | **Zalo** | Extension | ⭐⭐  | Vietnam market |
  | **WebChat** | Built-in | ⭐   | Browser interface |
  
  ### Telegram Bot Quick Setup
  
  Telegram is the easiest integration method. Here are the steps:
  
      # 1. Install OpenClaw
      npm install -g openclaw@latest
      
      # 2. Run the interactive configuration wizard
      openclaw onboard --inst
      
      # 3. Select Telegram in the wizard and enter your Bot Token
      # Get your Token from @BotFather
      
  
  Search for @BotFather in Telegram, send `/newbot` to create a new bot, follow the prompts to set a name, and grab your Token. Just enter that Token into the config wizard to finish the integration.
  
  **View Full Telegram Bot Config Code**
  
      // telegram-config.js
      // Advanced OpenClaw Telegram integration example
      
      const config = {
        // Base Config
        telegram: {
          token: process.env.TELEGRAM_BOT_TOKEN,
          // Allowed User ID whitelist (Security)
          allowedUsers: [123456789, 987654321],
          // Admin IDs
          adminIds: [123456789],
        },
      
        // Message Handling Config
        messageOptions: {
          // Enable Markdown parsing
          parseMode: 'MarkdownV2',
          // Disable link previews
          disableWebPagePreview: true,
          // Message timeout (seconds)
          timeout: 60,
        },
      
        // Feature Toggles
        features: {
          // Enable voice-to-text
          voiceToText: true,
          // Enable image understanding
          imageAnalysis: true,
          // Enable file processing
          fileProcessing: true,
        }
      };
      
      module.exports = config;
  
  ### WhatsApp Integration
  
  WhatsApp integration uses the Baileys library to connect via the Web protocol:
  
      # Start the Gateway service
      openclaw gateway
      
      # Open the control panel
      # Visit http://127.0.0.1:18789/
      
      # Scan the WhatsApp Web QR code in the panel to connect
      
  
  > **Tip**: A single host can only run one Gateway instance to manage WhatsApp sessions. If you need multi-account support, you can use the cloud deployment solutions provided by [APIYI](https://apiyi.com/)
  >  for centralized management.
  
  ### Discord Server Integration
  
  Discord integration is perfect for team collaboration, allowing you to interact with the AI assistant within server channels:
  
      # 1. Create an app in the Discord Developer Portal
      # Visit discord.com/developers/applications
      
      # 2. Create a Bot in the app and get your Token
      
      # 3. Configure OpenClaw
      openclaw config set discord.token YOUR_BOT_TOKEN
      openclaw config set discord.guildId YOUR_SERVER_ID
      
      # 4. Invite the Bot to your server
      # Use the OAuth2 URL Generator to create an invite link
      
  
  Discord integration supports features like slash commands, message replies, file uploads/downloads, and voice channels (via extensions). It's especially great for dev teams looking to bake an AI assistant into their daily workflow.
  
  ### Multi-Platform Message Sync
  
  OpenClaw supports cross-platform message synchronization. You can start a conversation on WhatsApp and pick it up on Telegram; the AI assistant will maintain the full conversation context:
  
  | Sync Feature | Description | Use Case |
  | --- | --- | --- |
  | **Context Retention** | Cross-platform chat history sync | Switching from mobile to desktop |
  | **Preference Sync** | User preferences apply everywhere | Unified personalized experience |
  | **Task Status Sync** | To-dos display across platforms | Multi-device task management |
  | **File Sharing** | Uploaded files accessible everywhere | Access resources anytime |
  
  * * *
  
  OpenClaw Skills: Category Breakdown
  -----------------------------------
  
  ClawHub is the official skill store for OpenClaw, located at [clawhub.ai](https://clawhub.ai/)
  , featuring over 700 community skills. Here's a look at the core skills by category.
  
  ### Productivity & Office Skills
  
  | Skill Name | Description | Best For |
  | --- | --- | --- |
  | **apple-notes** | Manage Apple Notes | macOS/iOS users |
  | **apple-reminders** | Handle Apple Reminders | Schedule management |
  | **notion-integration** | Notion DB and page operations | Knowledge management |
  | **obsidian-vault** | Manage Obsidian vaults | Markdown notes |
  | **trello-boards** | Trello board and card management | Project management |
  | **asana-tasks** | Asana task and project operations | Team collaboration |
  | **microsoft-365** | Email, Calendar, OneDrive | Office suites |
  | **hubspot-crm** | Contacts, deals, company management | Sales management |
  
  Productivity skills let you manage your daily grind using natural language:
  
      User: "Help me create a new page in Notion titled 'Weekly Project Report' with a list of tasks completed this week."
      OpenClaw: "Created the 'Weekly Project Report' page with a task list template. Should I add specific task details?"
      
      User: "Add my meeting tomorrow at 3 PM to my calendar and remind me 30 minutes early."
      OpenClaw: "Added the meeting to Apple Calendar with a reminder at 14:30. Want me to add any attendees?"
      
  
  ### Developer & DevOps Skills
  
  OpenClaw offers extensive skill support for developers, including GitHub integration, code search, and automated deployment:
  
  *   **github-integration**: Manage Issues, PRs, and repos; supports Webhook triggers.
  *   **claude-code-usage**: Check your Claude Code OAuth usage limits.
  *   **coolify**: Self-hosted PaaS management integrated with the Coolify platform.
  *   **news-aggregator**: Aggregates 8 sources including Hacker News, GitHub Trending, and Product Hunt.
  *   **agent-browser**: Headless browser automation with Playwright and accessibility tree snapshots.
  
  Developers can use Webhooks and Cron Jobs to build automated workflows:
  
      # cron-job config example
      # Check GitHub Issues every morning at 9 AM
      schedule: "0 9 * * *"
      action: check-github-issues
      params:
        repo: "your-org/your-repo"
        notify: telegram
      
  
  #### DevOps Skills Feature Table
  
  | Skill Name | Core Functionality | Automation Scenario | Trigger |
  | --- | --- | --- | --- |
  | **github-integration** | Issue/PR/Repo management | Auto-assign, label, close | Webhook/Cron |
  | **gitlab-integration** | MR/Pipeline management | CI/CD status monitoring | Webhook |
  | **jenkins-skill** | Build job management | Trigger builds, view logs | API Call |
  | **docker-skill** | Container management | Start/stop, view logs | CLI |
  | **k8s-skill** | Kubernetes operations | Pod status, scaling | kubectl |
  | **aws-skill** | AWS resource management | EC2, S3, Lambda ops | AWS CLI |
  
  ### Smart Home Control Skills
  
  | Skill Name | Supported Devices | Control Capabilities |
  | --- | --- | --- |
  | **philips-hue** | Philips Hue lights | On/off, brightness, color temp, scenes |
  | **elgato-devices** | Elgato Key Light, etc. | Brightness, color temp adjustment |
  | **home-assistant** | Home Assistant Hub | Full-home smart control |
  | **health-wearables** | Various fitness trackers | Read health data |
  
  Control your smart home with simple commands:
  
      User: "Set the living room light to 50% brightness and warm white."
      OpenClaw: "Living room light set to 50% brightness, color temp 3000K."
      
      User: "Turn off all lights automatically at 11 PM."
      OpenClaw: "Automation rule created: Turn off all lights daily at 23:00. Any exceptions?"
      
      User: "Check my steps and sleep data for today."
      OpenClaw: "Steps: 8,432 (84% of goal). 
      Sleep: 7h 23m, Deep sleep 1.5h. 
      Heart rate: 58-112 bpm."
      
  
  Smart home skills support scene linking, allowing for complex automation rules:
  
  *   **Away Mode**: Detects when your phone leaves the home WiFi, then turns off lights and arms security.
  *   **Home Mode**: Automatically turns on lights and adjusts the AC when you're near the door.
  *   **Sleep Mode**: Adjusts the bedroom environment based on your sleep data.
  
  ### AI Model Integration Skills
  
  OpenClaw supports various AI models, allowing you to switch flexibly via skills:
  
  | Skill Name | Model Provider | Core Functionality |
  | --- | --- | --- |
  | **gemini-cli** | Google | One-off Q&A, summary generation |
  | **gemini-computer-use** | Google | Browser control Agent |
  | **gemini-deep-research** | Google | Deep research tasks |
  | **replicate-api** | Replicate | AI image and media generation |
  | **openrouter** | OpenRouter | Multi-model aggregation |
  
  > **Model Selection Tip**: Different models have different strengths—Claude excels at code and reasoning, GPT is great for creative writing, and Gemini shines in multimodal understanding. We recommend using the [APIYI](https://apiyi.com/)
  >  platform to manage your Large Language Model calls centrally for better pricing and stability.
  
  ### Browser Automation & Data Collection Skills
  
  | Skill Name | Description | Tech Stack | Typical Use Case |
  | --- | --- | --- | --- |
  | **agent-browser** | Headless browser automation | Playwright | Web scraping, form filling |
  | **web-scraper** | Structured data collection | Cheerio | Price monitoring, content aggregation |
  | **screenshot-skill** | Webpage screenshots | Puppeteer | Page archiving, change monitoring |
  | **pdf-extractor** | PDF content extraction | pdf-parse | Document analysis, data import |
  
  Browser automation skills are incredibly powerful, supporting full web interaction flows:
  
      User: "Check the price of AirPods Pro on Amazon for me."
      OpenClaw: "Searching... 
      Current Amazon Price: $249.00. 
      All-time low: $189.00 (Black Friday 2025). 
      Trend: Stable over the last 30 days. 
      Want me to set a price alert?"
      
  
  ![openclaw-extensions-ecosystem-guide-en 图示](https://help.apiyi.com/wp-content/uploads/2026/02/openclaw-extensions-ecosystem-guide-en-image-2.png)
  
  OpenClaw Skill Installation and Management
  ------------------------------------------
  
  ### ClawHub Skill Installation Methods
  
  ClawHub offers three ways to install skills: via the GUI, the CLI, or manual installation.
  
  **Method 1: GUI Installation**
  
  1.  Start the Gateway: `openclaw gateway`
  2.  Open the control panel: `http://127.0.0.1:18789/`
  3.  Go to the Skills page and search for the skill you need.
  4.  Click the **Install** button to finish.
  
  **Method 2: CLI Installation**
  
      # Search for a skill
      openclaw skill search "calendar"
      
      # Install a skill
      openclaw skill install google-calendar
      
      # List installed skills
      openclaw skill list
      
      # Update all skills
      openclaw skill update --all
      
  
  **Method 3: Manual Installation**
  
  Just copy the skill directory to `~/.openclaw/skills/`. Skill priority follows this order: Workspace Skills > User Skills > Built-in Skills.
  
  ### SKILL.md Configuration Format
  
  Every skill requires a `SKILL.md` file, using YAML frontmatter to define its metadata:
  
      ---
      name: my-custom-skill
      description: Custom skill example
      metadata:
        openclaw:
          emoji: "🔧"
          bins:
            - node
          install:
            brew: some-package
          os:
            - darwin
            - linux
      ---
      
      
      ## Skill Description
      
      This is the documentation for skill usage and instructions...
      
  
  Key configuration fields:
  
  | Field | Description | Example |
  | --- | --- | --- |
  | **name** | Unique skill identifier | `google-calendar` |
  | **description** | Skill description | "Manage Google Calendar" |
  | **bins** | Required binary dependencies | `["node", "python"]` |
  | **install.brew** | Homebrew package | `"google-cloud-sdk"` |
  | **os** | Supported operating systems | `["darwin", "linux"]` |
  
  ### Automation Configuration & Cron Jobs
  
  OpenClaw supports scheduled task automation via Cron Jobs:
  
      # Configuration file location
      ~/.openclaw/cron/jobs.json
      
      # Example configuration
      {
        "jobs": [\
          {\
            "name": "daily-news",\
            "schedule": "0 8 * * *",\
            "skill": "news-aggregator",\
            "action": "fetch-and-summarize",\
            "notify": "telegram"\
          }\
        ]
      }
      
  
  Webhook triggers are also supported, allowing you to connect external services like GitHub or Stripe for event-driven automation.
  
  > **Automation Tips**: When configuring automation workflows, security is paramount. OpenClaw provides signature verification, whitelisting, deduplication, and loop protection mechanisms. However, we still recommend thoroughly testing in a staging environment before deploying to production. For enterprise-grade security solutions, feel free to consult the technical support team at APIYI (apiyi.com).
  
  ### Custom Skill Development Guide
  
  If existing skills don't quite meet your needs, you can develop your own. Here's the complete development workflow:
  
  **Step 1: Create the skill directory structure**
  
      mkdir -p ~/.openclaw/skills/my-custom-skill
      cd ~/.openclaw/skills/my-custom-skill
      
  
  **Step 2: Write the SKILL.md configuration file**
  
      ---
      name: my-custom-skill
      description: Custom skill example - Fetch weather info
      version: 1.0.0
      author: your-name
      metadata:
        openclaw:
          emoji: "🌤️"
          bins: []
          env:
            - WEATHER_API_KEY
      ---
      
  
  Skill Description
  -----------------
  
  This is a weather query skill that supports the following features:
  
  *   Check current weather for a specific city
  *   Get a 7-day weather forecast
  *   Set weather change alerts
  
  Usage Examples
  --------------
  
  Users can call it in the following ways:
  
  *   "Check today's weather in Beijing"
  *   "Will it rain in Shanghai tomorrow?"
  *   "Set a rain alert"
  
  **Step 3: Add Execution Script (Optional)**
  
      # weather.py
      import os
      import requests
      
      def get_weather(city: str) -> dict:
          api_key = os.environ.get('WEATHER_API_KEY')
          url = f"https://api.weather.com/v1/current?city={city}&key={api_key}"
          response = requests.get(url)
          return response.json()
      
  
  Once development is complete, restart the Gateway service to load the new skill.
  
  * * *
  
  OpenClaw Extension Ecosystem vs. Claude Code
  --------------------------------------------
  
  As two of the hottest tools in the AI assistant space, OpenClaw and Claude Code each bring something unique to the table.
  
  | Comparison Dimension | OpenClaw | Claude Code |
  | --- | --- | --- |
  | **Positioning** | All-in-one Personal Assistant | Specialized Coding Assistant |
  | **Extension Method** | Skills + Channels | MCP Servers |
  | **Messaging Platforms** | 12+ Platforms supported | Primarily Terminal/IDE |
  | **Number of Skills** | 700+ Skills | 50+ MCP Servers |
  | **Model Support** | Multi-model switching | Claude Series |
  | **Deployment** | Self-hosted / Cloud-hosted | Local execution |
  | **Core Strengths** | Unified cross-platform entry point | Powerful coding capabilities |
  
  **Usage Recommendations**:
  
  *   If you need cross-platform messaging integration or smart home control: Go with OpenClaw.
  *   If you're focused on coding and need deep IDE integration: Choose Claude Code.
  *   You can even use them together: let OpenClaw handle your daily assistant tasks while Claude Code tackles the heavy coding.
  
  > **Model API Tip**: Whether you're using OpenClaw or Claude Code, you'll need to call AI model APIs under the hood. You can get better pricing and more stable service through [APIYI](https://apiyi.com/)
  > , which supports unified API calls for major models like Claude, GPT, and Gemini.
  
  ### Detailed Skill Ecosystem Comparison
  
  | Comparison Dimension | OpenClaw Skills | Claude Code MCP |
  | --- | --- | --- |
  | **Skill Format** | SKILL.md + Scripts | MCP Server (JSON-RPC) |
  | **Community Size** | 700+ Skills | 50+ MCP Servers |
  | **Installation Method** | ClawHub GUI/CLI | CLI Configuration |
  | **Dev Difficulty** | Low (primarily Markdown) | Medium (requires MCP protocol implementation) |
  | **Interoperability** | Compatible with AgentSkills standard | MCP protocol ecosystem |
  | **Update Mechanism** | ClawHub auto-updates | Manual configuration updates |
  
  The skill ecosystems for both platforms are evolving rapidly. Some community developers have already started creating dual-compatible skill packages, allowing the same functionality to be used in both OpenClaw and Claude Code.
  
  * * *
  
  Optimizing OpenClaw Extension Performance
  -----------------------------------------
  
  To keep OpenClaw running smoothly, here are some performance optimization tips:
  
  ### Skill Loading Optimization
  
  | Optimization Method | Description | Result |
  | --- | --- | --- |
  | **Load on Demand** | Only install the skills you actually need | Reduce memory usage by 50%+ |
  | **Disable Idle Skills** | Set unused skills to disabled | Faster startup |
  | **Regular Cleanup** | Delete skills you haven't used in a long time | Save disk space |
  | **Use an SSD** | Keep the skill directory on an SSD | 3-5x faster loading |
  
  ### Messaging Platform Optimization
  
      # Check Gateway resource usage
      openclaw gateway status
      
      # View connection status for all platforms
      openclaw channel list
      
      # Restart a specific platform connection
      openclaw channel restart whatsapp
      
  
  We recommend configuring a process manager (like PM2 or systemd) for the Gateway service to ensure it stays stable and automatically restarts if it crashes.
  
  * * *
  
  OpenClaw Extension FAQ
  ----------------------
  
  **Q1: How do I fix frequent WhatsApp connection drops?**
  
  The WhatsApp Web protocol has session limits. We recommend:
  
  1.  Ensuring the Gateway service is running stably and avoiding frequent restarts.
  2.  Using a dedicated phone number to register your WhatsApp account.
  3.  Avoiding logging into WhatsApp Web on other devices at the same time.
  4.  Regularly checking Gateway logs to troubleshoot connection issues.
  
  **Q2: What should I do if a skill won’t load after installation?**
  
  Skill loading failures are usually due to dependency issues. Try these troubleshooting steps:
  
  1.  Check if the binaries defined in the `bins` section of `SKILL.md` are installed.
  2.  Confirm that the `os` configuration matches your current operating system.
  3.  Run `openclaw skill check <skill-name>` to check the dependency status.
  4.  Review the Gateway logs for detailed error messages.
  
  **Q3: How do I choose the right AI model?**
  
  OpenClaw supports various models. Here are our suggestions:
  
  *   **Daily Conversations**: Claude Haiku or GPT-4o-mini—they're fast and cost-effective.
  *   **Complex Reasoning**: Claude Opus or GPT-4o for high-level capabilities.
  *   **Code Generation**: Claude Sonnet 3.5 (or 4) for excellent programming performance.
  *   **Multimodal Tasks**: Gemini Pro for great image and text understanding.
  
  We recommend testing different models via APIYI (apiyi.com). The platform offers free credits and a unified interface, making it easy to compare and choose quickly.
  
  **Q4: How does OpenClaw ensure data security?**
  
  OpenClaw uses a local-first architecture. Key security features include:
  
  1.  All data is stored locally and isn't uploaded to the cloud.
  2.  Sensitive information like API Keys is stored with encryption.
  3.  Support for private deployment, giving you full control over your data sovereignty.
  4.  Open-source code that's auditable, with ongoing security checks from the community.
  
  Enterprise users can also consider OpenClaw's official managed services for extra security hardening and compliance support.
  
  * * *
  
  OpenClaw Extension Ecosystem Summary
  ------------------------------------
  
  Key highlights of the OpenClaw extension ecosystem:
  
  1.  **Rich Skill Library**: Over 700+ Skills covering productivity, development, smart homes, and AI models, all available via one-click installation through ClawHub.
  2.  **Comprehensive Platform Support**: Integration with 12 major messaging platforms, including full coverage for mainstream apps like WhatsApp, Telegram, and Discord.
  3.  **Flexible Extension Architecture**: Uses the `SKILL.md` standard format, supporting custom skill development and community sharing.
  4.  **Powerful Automation**: Cron Jobs + Webhooks enable event-driven workflows and scheduled task automation.
  
  The OpenClaw extension ecosystem is growing fast, with new skills released every week. We suggest keeping an eye on ClawHub for the latest updates so you can gradually build your personalized AI assistant based on your specific needs.
  
  If you want to use multiple Large Language Models within OpenClaw, we recommend getting your API Keys through APIYI (apiyi.com). The platform provides free test credits and a unified interface for multiple models, making model switching much more convenient.
  
  * * *
  
  References
  ----------
  
  > The following links use a colon-separated format for easy copying while preventing direct clicks to preserve SEO link equity.
  
  1.  **OpenClaw Official Documentation**: Comprehensive installation, configuration, and usage guides
      
      *   Link: `docs.openclaw.ai`
      *   Description: Official authoritative documentation containing detailed explanations of all features.
  2.  **OpenClaw GitHub Repository**: Source code and issue discussions
      
      *   Link: `github.com/openclaw/openclaw`
      *   Description: Check out the latest code, submit issues, or contribute to the project.
  3.  **ClawHub Skill Store**: Browse and install 700+ community skills
      
      *   Link: `clawhub.ai`
      *   Description: The official platform for searching, installing, and managing OpenClaw skills.
  4.  **awesome-openclaw-skills**: A curated collection of community skills
      
      *   Link: `github.com/VoltAgent/awesome-openclaw-skills`
      *   Description: A recommended list of high-quality skills organized by category.
  5.  **DigitalOcean OpenClaw Guide**: Cloud deployment tutorial
      
      *   Link: `digitalocean.com/resources/articles/what-is-openclaw`
      *   Description: A detailed tutorial on how to deploy OpenClaw on DigitalOcean with just one click.
  
  * * *
  
  > **Author**: Technical Team  
  > **Tech Talk**: Feel free to discuss OpenClaw tips in the comments. For more AI model resources, visit the APIYI (apiyi.com) tech community.
  
  ![](https://secure.gravatar.com/avatar/7c3ee8cfcb5072ffbe34588f38bde67985c25ee2f943825b105f3234045bf43b?s=160&d=mm&r=g)
  
  **[APIYI - Stable and affordable AI API](https://help.apiyi.com/en/author/apiyi "Posts by APIYI - Stable and affordable AI API")
  **
  
  Try AI Large Model https://api.apiyi.com for free  
  Stable and reliable AI LM API aggregation service, Get 300 Millions Tokens for Free~
  
   
  
  Similar Posts
  -------------
  
  *   [![clawdbot renamed moltbot complete guide en image 0 图示](https://help.apiyi.com/wp-content/uploads/2026/01/clawdbot-renamed-moltbot-complete-guide-en-image-0.png)](https://help.apiyi.com/en/clawdbot-renamed-moltbot-complete-guide-en.html)
      
      ClawdBot is officially Moltbot now! As the fastest-growing AI assistant project on GitHub, it was forced to undergo a rebranding because its name was too similar to Anthropic's Claude trademark. This article will break down the full story behind the name change and how newcomers can quickly get started with Moltbot. Core Value: A 3-minute…
      
  *   [![sora 2 ecommerce video templates guide en image 0 图示](https://help.apiyi.com/wp-content/uploads/2026/01/sora-2-ecommerce-video-templates-guide-en-image-0.png)](https://help.apiyi.com/en/sora-2-ecommerce-video-templates-guide-en.html)
      
      Author's Note: Detailed explanation of Sora 2 e-commerce video generation templates, including 7 presets like unboxing videos, product displays, and luxury ads, to help e-commerce sellers quickly create professional-grade product videos. High production costs and long turnaround times are common headaches for e-commerce sellers. This article will walk you through the full usage of Sora…
      
  *   [![glm 4 7 text structuring guide en image 0 图示](https://help.apiyi.com/wp-content/uploads/2026/01/glm-4-7-text-structuring-guide-en-image-0.png)](https://help.apiyi.com/en/glm-4-7-text-structuring-guide-en.html)
      
      Author's Note: Deep dive into the text structuring capabilities of the GLM-4.7 Large Language Model, and master practical tips for extracting key information in JSON format from complex documents like contracts and reports. Quickly extracting key info from vast amounts of unstructured text is a major hurdle in enterprise data processing. Released by Zhipu AI…
      
  *   [![nano banana pro batch template advertising guide en image 0 图示](https://help.apiyi.com/wp-content/uploads/2026/01/nano-banana-pro-batch-template-advertising-guide-en-image-0.png)](https://help.apiyi.com/en/nano-banana-pro-batch-template-advertising-guide-en.html)
      
      E-commerce ad placement faces the double challenge of "high-frequency updates" and "multi-platform adaptation." Traditional design workflows struggle to meet the daily demand for hundreds of assets. Nano Banana Pro API provides e-commerce teams with a solution for batch-generating high-quality ad assets through templating and automation. Core Value: After reading this article, you'll master the full…
      
  *   [![google ai studio deploy app export code guide en image 0 图示](https://help.apiyi.com/wp-content/uploads/2026/01/google-ai-studio-deploy-app-export-code-guide-en-image-0.png)](https://help.apiyi.com/en/google-ai-studio-deploy-app-export-code-guide-en.html)
      
      Author's Note: This is a detailed guide on the complete workflow for deploying apps using Google AI Studio's Build mode. I'll show you how to export code to your local IDE and connect to low-cost API proxies like APIYI, significantly cutting your development costs. Deploying apps from Google AI Studio is a hot topic for…
      
  *   [![google flow access restricted veo 3 1 api alternative solution en image 0 图示](https://help.apiyi.com/wp-content/uploads/2026/01/google-flow-access-restricted-veo-3-1-api-alternative-solution-en-image-0.png)](https://help.apiyi.com/en/google-flow-access-restricted-veo-3-1-api-alternative-solution-en.html)
      
      Encountering the error message "It looks like you don't have access to Flow. Click here to see our rollout areas" when visiting Google Flow (labs.google/fx/zh/tools/flow) is a common issue for users in mainland China and some overseas regions. In this article, we'll introduce 3 effective solutions, including calling the Veo 3.1 API directly to generate…
      
  *   [![clawdbot renamed moltbot complete guide en image 0 图示](https://help.apiyi.com/wp-content/uploads/2026/01/clawdbot-renamed-moltbot-complete-guide-en-image-0.png)](https://help.apiyi.com/en/clawdbot-renamed-moltbot-complete-guide-en.html)
      
      ClawdBot is officially Moltbot now! As the fastest-growing AI assistant project on GitHub, it was forced to undergo a rebranding because its name was too similar to Anthropic's Claude trademark. This article will break down the full story behind the name change and how newcomers can quickly get started with Moltbot. Core Value: A 3-minute…
      
  *   [![sora 2 ecommerce video templates guide en image 0 图示](https://help.apiyi.com/wp-content/uploads/2026/01/sora-2-ecommerce-video-templates-guide-en-image-0.png)](https://help.apiyi.com/en/sora-2-ecommerce-video-templates-guide-en.html)
      
      Author's Note: Detailed explanation of Sora 2 e-commerce video generation templates, including 7 presets like unboxing videos, product displays, and luxury ads, to help e-commerce sellers quickly create professional-grade product videos. High production costs and long turnaround times are common headaches for e-commerce sellers. This article will walk you through the full usage of Sora…
      
  *   [![glm 4 7 text structuring guide en image 0 图示](https://help.apiyi.com/wp-content/uploads/2026/01/glm-4-7-text-structuring-guide-en-image-0.png)](https://help.apiyi.com/en/glm-4-7-text-structuring-guide-en.html)
      
      Author's Note: Deep dive into the text structuring capabilities of the GLM-4.7 Large Language Model, and master practical tips for extracting key information in JSON format from complex documents like contracts and reports. Quickly extracting key info from vast amounts of unstructured text is a major hurdle in enterprise data processing. Released by Zhipu AI…
      
  *   [![nano banana pro batch template advertising guide en image 0 图示](https://help.apiyi.com/wp-content/uploads/2026/01/nano-banana-pro-batch-template-advertising-guide-en-image-0.png)](https://help.apiyi.com/en/nano-banana-pro-batch-template-advertising-guide-en.html)
      
      E-commerce ad placement faces the double challenge of "high-frequency updates" and "multi-platform adaptation." Traditional design workflows struggle to meet the daily demand for hundreds of assets. Nano Banana Pro API provides e-commerce teams with a solution for batch-generating high-quality ad assets through templating and automation. Core Value: After reading this article, you'll master the full…
      
  *   [![google ai studio deploy app export code guide en image 0 图示](https://help.apiyi.com/wp-content/uploads/2026/01/google-ai-studio-deploy-app-export-code-guide-en-image-0.png)](https://help.apiyi.com/en/google-ai-studio-deploy-app-export-code-guide-en.html)
      
      Author's Note: This is a detailed guide on the complete workflow for deploying apps using Google AI Studio's Build mode. I'll show you how to export code to your local IDE and connect to low-cost API proxies like APIYI, significantly cutting your development costs. Deploying apps from Google AI Studio is a hot topic for…
      
  *   [![google flow access restricted veo 3 1 api alternative solution en image 0 图示](https://help.apiyi.com/wp-content/uploads/2026/01/google-flow-access-restricted-veo-3-1-api-alternative-solution-en-image-0.png)](https://help.apiyi.com/en/google-flow-access-restricted-veo-3-1-api-alternative-solution-en.html)
      
      Encountering the error message "It looks like you don't have access to Flow. Click here to see our rollout areas" when visiting Google Flow (labs.google/fx/zh/tools/flow) is a common issue for users in mainland China and some overseas regions. In this article, we'll introduce 3 effective solutions, including calling the Veo 3.1 API directly to generate…
      
  *   [![clawdbot renamed moltbot complete guide en image 0 图示](https://help.apiyi.com/wp-content/uploads/2026/01/clawdbot-renamed-moltbot-complete-guide-en-image-0.png)](https://help.apiyi.com/en/clawdbot-renamed-moltbot-complete-guide-en.html)
      
      ClawdBot is officially Moltbot now! As the fastest-growing AI assistant project on GitHub, it was forced to undergo a rebranding because its name was too similar to Anthropic's Claude trademark. This article will break down the full story behind the name change and how newcomers can quickly get started with Moltbot. Core Value: A 3-minute…
      
  *   [![sora 2 ecommerce video templates guide en image 0 图示](https://help.apiyi.com/wp-content/uploads/2026/01/sora-2-ecommerce-video-templates-guide-en-image-0.png)](https://help.apiyi.com/en/sora-2-ecommerce-video-templates-guide-en.html)
      
      Author's Note: Detailed explanation of Sora 2 e-commerce video generation templates, including 7 presets like unboxing videos, product displays, and luxury ads, to help e-commerce sellers quickly create professional-grade product videos. High production costs and long turnaround times are common headaches for e-commerce sellers. This article will walk you through the full usage of Sora…
      
  
   
  
   
  
  [Scroll to top](https://help.apiyi.com/en/openclaw-extensions-ecosystem-guide-en.html#wrapper)
   Scroll to top
  
  *   [![](https://help.apiyi.com/wp-content/plugins/sitepress-multilingual-cms/res/flags/zh-hans.svg)简体中文 (Chinese (Simplified))](https://help.apiyi.com/openclaw-extensions-ecosystem-guide.html "Switch to Chinese (Simplified)(简体中文)")
      
  *   [![](https://help.apiyi.com/wp-content/plugins/sitepress-multilingual-cms/res/flags/zh-hant.svg)繁體中文 (Chinese (Traditional))](https://help.apiyi.com/zh-hant/openclaw-extensions-ecosystem-guide-zh-hant.html "Switch to Chinese (Traditional)(繁體中文)")
      
  *   [![](https://help.apiyi.com/wp-content/plugins/sitepress-multilingual-cms/res/flags/en.svg)English](https://help.apiyi.com/en/openclaw-extensions-ecosystem-guide-en.html)
      
  *   [![](https://help.apiyi.com/wp-content/plugins/sitepress-multilingual-cms/res/flags/ru.svg)Русский (Russian)](https://help.apiyi.com/ru/openclaw-extensions-ecosystem-guide-ru.html "Switch to Russian(Русский)")
      
  *   [![](https://help.apiyi.com/wp-content/plugins/sitepress-multilingual-cms/res/flags/ja.svg)日本語 (Japanese)](https://help.apiyi.com/ja/openclaw-extensions-ecosystem-guide-ja.html "Switch to Japanese(日本語)")
      
  *   [![](https://help.apiyi.com/wp-content/plugins/sitepress-multilingual-cms/res/flags/ko.svg)한국어 (Korean)](https://help.apiyi.com/ko/openclaw-extensions-ecosystem-guide-ko.html "Switch to Korean(한국어)")
      
  *   [![](https://help.apiyi.com/wp-content/plugins/sitepress-multilingual-cms/res/flags/ar.svg)العربية (Arabic)](https://help.apiyi.com/ar/openclaw-extensions-ecosystem-guide-ar.html "Switch to Arabic(العربية)")
      
  *   [![](https://help.apiyi.com/wp-content/plugins/sitepress-multilingual-cms/res/flags/fr.svg)Français (French)](https://help.apiyi.com/fr/openclaw-extensions-ecosystem-guide-fr.html "Switch to French(Français)")
      
  *   [![](https://help.apiyi.com/wp-content/plugins/sitepress-multilingual-cms/res/flags/de.svg)Deutsch (German)](https://help.apiyi.com/de/openclaw-extensions-ecosystem-guide-de.html "Switch to German(Deutsch)")
      
  *   [![](https://help.apiyi.com/wp-content/plugins/sitepress-multilingual-cms/res/flags/id.svg)Indonesia (Indonesian)](https://help.apiyi.com/id/openclaw-extensions-ecosystem-guide-id.html "Switch to Indonesian(Indonesia)")
      
  *   [![](https://help.apiyi.com/wp-content/plugins/sitepress-multilingual-cms/res/flags/pt-pt.svg)Português (Portuguese (Portugal))](https://help.apiyi.com/pt-pt/openclaw-extensions-ecosystem-guide-pt-pt.html "Switch to Portuguese (Portugal)(Português)")
      
  *   [![](https://help.apiyi.com/wp-content/plugins/sitepress-multilingual-cms/res/flags/es.svg)Español (Spanish)](https://help.apiyi.com/es/openclaw-extensions-ecosystem-guide-es.html "Switch to Spanish(Español)")
  --- End Content ---

Markdown formatting - OpenClaw
  URL: https://docs.openclaw.ai/concepts/markdown-formatting
  Markdown formatting OpenClaw formats outbound Markdown by converting it into a shared intermediate representation (IR) before rendering channel-specific output. The IR keeps the source text intact while carrying style/link spans so chunking and rendering can stay consistent across channels.

  --- Content ---
  [Skip to main content](https://docs.openclaw.ai/concepts/markdown-formatting#content-area)
  
  [OpenClaw home page![light logo](https://mintcdn.com/clawdhub/4rYvG-uuZrMK_URE/assets/pixel-lobster.svg?fit=max&auto=format&n=4rYvG-uuZrMK_URE&q=85&s=da2032e9eac3b5d9bfe7eb96ca6a8a26)![dark logo](https://mintcdn.com/clawdhub/4rYvG-uuZrMK_URE/assets/pixel-lobster.svg?fit=max&auto=format&n=4rYvG-uuZrMK_URE&q=85&s=da2032e9eac3b5d9bfe7eb96ca6a8a26)](https://docs.openclaw.ai/)
  
  ![US](https://d3gk2c5xim1je2.cloudfront.net/flags/US.svg)
  
  English
  
  Search...
  
  Ctrl K
  
  Search...
  
  Navigation
  
  Core Concepts
  
  Markdown Formatting
  
  On this page
  
  *   [Markdown formatting](https://docs.openclaw.ai/concepts/markdown-formatting#markdown-formatting)
      
  *   [Goals](https://docs.openclaw.ai/concepts/markdown-formatting#goals)
      
  *   [Pipeline](https://docs.openclaw.ai/concepts/markdown-formatting#pipeline)
      
  *   [IR example](https://docs.openclaw.ai/concepts/markdown-formatting#ir-example)
      
  *   [Where it is used](https://docs.openclaw.ai/concepts/markdown-formatting#where-it-is-used)
      
  *   [Table handling](https://docs.openclaw.ai/concepts/markdown-formatting#table-handling)
      
  *   [Chunking rules](https://docs.openclaw.ai/concepts/markdown-formatting#chunking-rules)
      
  *   [Link policy](https://docs.openclaw.ai/concepts/markdown-formatting#link-policy)
      
  *   [Spoilers](https://docs.openclaw.ai/concepts/markdown-formatting#spoilers)
      
  *   [How to add or update a channel formatter](https://docs.openclaw.ai/concepts/markdown-formatting#how-to-add-or-update-a-channel-formatter)
      
  *   [Common gotchas](https://docs.openclaw.ai/concepts/markdown-formatting#common-gotchas)
      
  
  [​](https://docs.openclaw.ai/concepts/markdown-formatting#markdown-formatting)
  
  Markdown formatting
  =====================================================================================================
  
  OpenClaw formats outbound Markdown by converting it into a shared intermediate representation (IR) before rendering channel-specific output. The IR keeps the source text intact while carrying style/link spans so chunking and rendering can stay consistent across channels.
  
  [​](https://docs.openclaw.ai/concepts/markdown-formatting#goals)
  
  Goals
  -------------------------------------------------------------------------
  
  *   **Consistency:** one parse step, multiple renderers.
  *   **Safe chunking:** split text before rendering so inline formatting never breaks across chunks.
  *   **Channel fit:** map the same IR to Slack mrkdwn, Telegram HTML, and Signal style ranges without re-parsing Markdown.
  
  [​](https://docs.openclaw.ai/concepts/markdown-formatting#pipeline)
  
  Pipeline
  -------------------------------------------------------------------------------
  
  1.  **Parse Markdown -> IR**
      *   IR is plain text plus style spans (bold/italic/strike/code/spoiler) and link spans.
      *   Offsets are UTF-16 code units so Signal style ranges align with its API.
      *   Tables are parsed only when a channel opts into table conversion.
  2.  **Chunk IR (format-first)**
      *   Chunking happens on the IR text before rendering.
      *   Inline formatting does not split across chunks; spans are sliced per chunk.
  3.  **Render per channel**
      *   **Slack:** mrkdwn tokens (bold/italic/strike/code), links as `<url|label>`.
      *   **Telegram:** HTML tags (`<b>`, `<i>`, `<s>`, `<code>`, `<pre><code>`, `<a href>`).
      *   **Signal:** plain text + `text-style` ranges; links become `label (url)` when label differs.
  
  [​](https://docs.openclaw.ai/concepts/markdown-formatting#ir-example)
  
  IR example
  -----------------------------------------------------------------------------------
  
  Input Markdown:
  
  Copy
  
      Hello **world** — see [docs](https://docs.openclaw.ai).
      
  
  IR (schematic):
  
  Copy
  
      {
        "text": "Hello world — see docs.",
        "styles": [{ "start": 6, "end": 11, "style": "bold" }],
        "links": [{ "start": 19, "end": 23, "href": "https://docs.openclaw.ai" }]
      }
      
  
  [​](https://docs.openclaw.ai/concepts/markdown-formatting#where-it-is-used)
  
  Where it is used
  -----------------------------------------------------------------------------------------------
  
  *   Slack, Telegram, and Signal outbound adapters render from the IR.
  *   Other channels (WhatsApp, iMessage, MS Teams, Discord) still use plain text or their own formatting rules, with Markdown table conversion applied before chunking when enabled.
  
  [​](https://docs.openclaw.ai/concepts/markdown-formatting#table-handling)
  
  Table handling
  -------------------------------------------------------------------------------------------
  
  Markdown tables are not consistently supported across chat clients. Use `markdown.tables` to control conversion per channel (and per account).
  
  *   `code`: render tables as code blocks (default for most channels).
  *   `bullets`: convert each row into bullet points (default for Signal + WhatsApp).
  *   `off`: disable table parsing and conversion; raw table text passes through.
  
  Config keys:
  
  Copy
  
      channels:
        discord:
          markdown:
            tables: code
          accounts:
            work:
              markdown:
                tables: off
      
  
  [​](https://docs.openclaw.ai/concepts/markdown-formatting#chunking-rules)
  
  Chunking rules
  -------------------------------------------------------------------------------------------
  
  *   Chunk limits come from channel adapters/config and are applied to the IR text.
  *   Code fences are preserved as a single block with a trailing newline so channels render them correctly.
  *   List prefixes and blockquote prefixes are part of the IR text, so chunking does not split mid-prefix.
  *   Inline styles (bold/italic/strike/inline-code/spoiler) are never split across chunks; the renderer reopens styles inside each chunk.
  
  If you need more on chunking behavior across channels, see [Streaming + chunking](https://docs.openclaw.ai/concepts/streaming)
  .
  
  [​](https://docs.openclaw.ai/concepts/markdown-formatting#link-policy)
  
  Link policy
  -------------------------------------------------------------------------------------
  
  *   **Slack:** `[label](url)` -> `<url|label>`; bare URLs remain bare. Autolink is disabled during parse to avoid double-linking.
  *   **Telegram:** `[label](url)` -> `<a href="url">label</a>` (HTML parse mode).
  *   **Signal:** `[label](url)` -> `label (url)` unless label matches the URL.
  
  [​](https://docs.openclaw.ai/concepts/markdown-formatting#spoilers)
  
  Spoilers
  -------------------------------------------------------------------------------
  
  Spoiler markers (`||spoiler||`) are parsed only for Signal, where they map to SPOILER style ranges. Other channels treat them as plain text.
  
  [​](https://docs.openclaw.ai/concepts/markdown-formatting#how-to-add-or-update-a-channel-formatter)
  
  How to add or update a channel formatter
  -----------------------------------------------------------------------------------------------------------------------------------------------
  
  1.  **Parse once:** use the shared `markdownToIR(...)` helper with channel-appropriate options (autolink, heading style, blockquote prefix).
  2.  **Render:** implement a renderer with `renderMarkdownWithMarkers(...)` and a style marker map (or Signal style ranges).
  3.  **Chunk:** call `chunkMarkdownIR(...)` before rendering; render each chunk.
  4.  **Wire adapter:** update the channel outbound adapter to use the new chunker and renderer.
  5.  **Test:** add or update format tests and an outbound delivery test if the channel uses chunking.
  
  [​](https://docs.openclaw.ai/concepts/markdown-formatting#common-gotchas)
  
  Common gotchas
  -------------------------------------------------------------------------------------------
  
  *   Slack angle-bracket tokens (`<@U123>`, `<#C123>`, `<https://...>`) must be preserved; escape raw HTML safely.
  *   Telegram HTML requires escaping text outside tags to avoid broken markup.
  *   Signal style ranges depend on UTF-16 offsets; do not use code point offsets.
  *   Preserve trailing newlines for fenced code blocks so closing markers land on their own line.
  
  [Streaming and Chunking](https://docs.openclaw.ai/concepts/streaming)
  [Groups](https://docs.openclaw.ai/concepts/groups)
  
  Ctrl+I
  
  Assistant
  
  Responses are generated using AI and may contain mistakes.
  --- End Content ---

Skills System | openclaw/openclaw | DeepWiki
  URL: https://deepwiki.com/openclaw/openclaw/6.3-skills-system
  Overview Skills in OpenClaw are discovered, indexed, and presented to the agent as a compact list in the system prompt. When the agent identifies a task that matches a skill, it uses the read tool to load the corresponding SKILL.md file and follow its instructions. Key Characteristics:

  --- Content ---
  Index your code with Devin
  
  [DeepWiki](https://deepwiki.com/)
  
  [DeepWiki](https://deepwiki.com/)
  
  [openclaw/openclaw](https://github.com/openclaw/openclaw "Open repository")
  
  Index your code with
  
  Devin
  
  Edit WikiShare
  
  Last indexed: 30 January 2026 ([bf6ec6](https://github.com/openclaw/openclaw/commits/bf6ec64f)
  )
  
  *   [Overview](https://deepwiki.com/openclaw/openclaw/1-overview)
      
  *   [Key Concepts](https://deepwiki.com/openclaw/openclaw/1.1-key-concepts)
      
  *   [Quick Start](https://deepwiki.com/openclaw/openclaw/1.2-quick-start)
      
  *   [Installation](https://deepwiki.com/openclaw/openclaw/2-installation)
      
  *   [System Requirements](https://deepwiki.com/openclaw/openclaw/2.1-system-requirements)
      
  *   [Installation Methods](https://deepwiki.com/openclaw/openclaw/2.2-installation-methods)
      
  *   [Onboarding Wizard](https://deepwiki.com/openclaw/openclaw/2.3-onboarding-wizard)
      
  *   [Gateway](https://deepwiki.com/openclaw/openclaw/3-gateway)
      
  *   [Gateway Configuration](https://deepwiki.com/openclaw/openclaw/3.1-gateway-configuration)
      
  *   [Gateway Protocol](https://deepwiki.com/openclaw/openclaw/3.2-gateway-protocol)
      
  *   [Gateway Service Management](https://deepwiki.com/openclaw/openclaw/3.3-gateway-service-management)
      
  *   [Remote Access](https://deepwiki.com/openclaw/openclaw/3.4-remote-access)
      
  *   [Configuration System](https://deepwiki.com/openclaw/openclaw/4-configuration-system)
      
  *   [Configuration File Structure](https://deepwiki.com/openclaw/openclaw/4.1-configuration-file-structure)
      
  *   [Configuration Management](https://deepwiki.com/openclaw/openclaw/4.2-configuration-management)
      
  *   [Multi-Agent Configuration](https://deepwiki.com/openclaw/openclaw/4.3-multi-agent-configuration)
      
  *   [Agent System](https://deepwiki.com/openclaw/openclaw/5-agent-system)
      
  *   [Agent Execution Flow](https://deepwiki.com/openclaw/openclaw/5.1-agent-execution-flow)
      
  *   [System Prompt](https://deepwiki.com/openclaw/openclaw/5.2-system-prompt)
      
  *   [Session Management](https://deepwiki.com/openclaw/openclaw/5.3-session-management)
      
  *   [Model Selection and Failover](https://deepwiki.com/openclaw/openclaw/5.4-model-selection-and-failover)
      
  *   [Tools and Skills](https://deepwiki.com/openclaw/openclaw/6-tools-and-skills)
      
  *   [Built-in Tools](https://deepwiki.com/openclaw/openclaw/6.1-built-in-tools)
      
  *   [Tool Security and Sandboxing](https://deepwiki.com/openclaw/openclaw/6.2-tool-security-and-sandboxing)
      
  *   [Skills System](https://deepwiki.com/openclaw/openclaw/6.3-skills-system)
      
  *   [Memory System](https://deepwiki.com/openclaw/openclaw/7-memory-system)
      
  *   [Memory Configuration](https://deepwiki.com/openclaw/openclaw/7.1-memory-configuration)
      
  *   [Memory Indexing](https://deepwiki.com/openclaw/openclaw/7.2-memory-indexing)
      
  *   [Memory Search](https://deepwiki.com/openclaw/openclaw/7.3-memory-search)
      
  *   [Channels](https://deepwiki.com/openclaw/openclaw/8-channels)
      
  *   [Channel Routing and Access Control](https://deepwiki.com/openclaw/openclaw/8.1-channel-routing-and-access-control)
      
  *   [WhatsApp Integration](https://deepwiki.com/openclaw/openclaw/8.2-whatsapp-integration)
      
  *   [Telegram Integration](https://deepwiki.com/openclaw/openclaw/8.3-telegram-integration)
      
  *   [Discord Integration](https://deepwiki.com/openclaw/openclaw/8.4-discord-integration)
      
  *   [Signal Integration](https://deepwiki.com/openclaw/openclaw/8.5-signal-integration)
      
  *   [Other Channels](https://deepwiki.com/openclaw/openclaw/8.6-other-channels)
      
  *   [Commands and Directives](https://deepwiki.com/openclaw/openclaw/9-commands-and-directives)
      
  *   [Command Reference](https://deepwiki.com/openclaw/openclaw/9.1-command-reference)
      
  *   [Platform-Specific Commands](https://deepwiki.com/openclaw/openclaw/9.2-platform-specific-commands)
      
  *   [Directives](https://deepwiki.com/openclaw/openclaw/9.3-directives)
      
  *   [Extensions and Plugins](https://deepwiki.com/openclaw/openclaw/10-extensions-and-plugins)
      
  *   [Plugin System Overview](https://deepwiki.com/openclaw/openclaw/10.1-plugin-system-overview)
      
  *   [Built-in Extensions](https://deepwiki.com/openclaw/openclaw/10.2-built-in-extensions)
      
  *   [Creating Custom Plugins](https://deepwiki.com/openclaw/openclaw/10.3-creating-custom-plugins)
      
  *   [Device Nodes](https://deepwiki.com/openclaw/openclaw/11-device-nodes)
      
  *   [Node Pairing and Discovery](https://deepwiki.com/openclaw/openclaw/11.1-node-pairing-and-discovery)
      
  *   [Node Capabilities](https://deepwiki.com/openclaw/openclaw/11.2-node-capabilities)
      
  *   [CLI Reference](https://deepwiki.com/openclaw/openclaw/12-cli-reference)
      
  *   [Gateway Commands](https://deepwiki.com/openclaw/openclaw/12.1-gateway-commands)
      
  *   [Agent Commands](https://deepwiki.com/openclaw/openclaw/12.2-agent-commands)
      
  *   [Channel Commands](https://deepwiki.com/openclaw/openclaw/12.3-channel-commands)
      
  *   [Model Commands](https://deepwiki.com/openclaw/openclaw/12.4-model-commands)
      
  *   [Configuration Commands](https://deepwiki.com/openclaw/openclaw/12.5-configuration-commands)
      
  *   [Diagnostic Commands](https://deepwiki.com/openclaw/openclaw/12.6-diagnostic-commands)
      
  *   [Deployment](https://deepwiki.com/openclaw/openclaw/13-deployment)
      
  *   [Local Deployment](https://deepwiki.com/openclaw/openclaw/13.1-local-deployment)
      
  *   [VPS Deployment](https://deepwiki.com/openclaw/openclaw/13.2-vps-deployment)
      
  *   [Cloud Deployment](https://deepwiki.com/openclaw/openclaw/13.3-cloud-deployment)
      
  *   [Network Configuration](https://deepwiki.com/openclaw/openclaw/13.4-network-configuration)
      
  *   [Operations and Troubleshooting](https://deepwiki.com/openclaw/openclaw/14-operations-and-troubleshooting)
      
  *   [Health Monitoring](https://deepwiki.com/openclaw/openclaw/14.1-health-monitoring)
      
  *   [Doctor Command Guide](https://deepwiki.com/openclaw/openclaw/14.2-doctor-command-guide)
      
  *   [Common Issues](https://deepwiki.com/openclaw/openclaw/14.3-common-issues)
      
  *   [Migration and Backup](https://deepwiki.com/openclaw/openclaw/14.4-migration-and-backup)
      
  *   [Development](https://deepwiki.com/openclaw/openclaw/15-development)
      
  *   [Architecture Deep Dive](https://deepwiki.com/openclaw/openclaw/15.1-architecture-deep-dive)
      
  *   [Protocol Specification](https://deepwiki.com/openclaw/openclaw/15.2-protocol-specification)
      
  *   [Building from Source](https://deepwiki.com/openclaw/openclaw/15.3-building-from-source)
      
  *   [Release Process](https://deepwiki.com/openclaw/openclaw/15.4-release-process)
      
  
  Menu
  
  Skills System
  =============
  
  Relevant source files
  
  *   [.npmrc](https://github.com/openclaw/openclaw/blob/bf6ec64f/.npmrc)
      
  *   [CHANGELOG.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/CHANGELOG.md)
      
  *   [README.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/README.md)
      
  *   [assets/avatar-placeholder.svg](https://github.com/openclaw/openclaw/blob/bf6ec64f/assets/avatar-placeholder.svg)
      
  *   [docs/concepts/system-prompt.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/concepts/system-prompt.md)
      
  *   [extensions/memory-core/package.json](https://github.com/openclaw/openclaw/blob/bf6ec64f/extensions/memory-core/package.json)
      
  *   [package.json](https://github.com/openclaw/openclaw/blob/bf6ec64f/package.json)
      
  *   [pnpm-lock.yaml](https://github.com/openclaw/openclaw/blob/bf6ec64f/pnpm-lock.yaml)
      
  *   [pnpm-workspace.yaml](https://github.com/openclaw/openclaw/blob/bf6ec64f/pnpm-workspace.yaml)
      
  *   [scripts/clawtributors-map.json](https://github.com/openclaw/openclaw/blob/bf6ec64f/scripts/clawtributors-map.json)
      
  *   [scripts/update-clawtributors.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/scripts/update-clawtributors.ts)
      
  *   [scripts/update-clawtributors.types.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/scripts/update-clawtributors.types.ts)
      
  *   [src/agents/channel-tools.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/channel-tools.ts)
      
  *   [src/agents/cli-runner.test.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/cli-runner.test.ts)
      
  *   [src/agents/cli-runner/helpers.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/cli-runner/helpers.ts)
      
  *   [src/agents/pi-embedded-runner-extraparams.live.test.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner-extraparams.live.test.ts)
      
  *   [src/agents/pi-embedded-runner-extraparams.test.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner-extraparams.test.ts)
      
  *   [src/agents/pi-embedded-runner.test.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner.test.ts)
      
  *   [src/agents/pi-embedded-runner/compact.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner/compact.ts)
      
  *   [src/agents/pi-embedded-runner/run.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner/run.ts)
      
  *   [src/agents/pi-embedded-runner/run/attempt.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner/run/attempt.ts)
      
  *   [src/agents/pi-embedded-runner/run/params.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner/run/params.ts)
      
  *   [src/agents/pi-embedded-runner/run/types.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner/run/types.ts)
      
  *   [src/agents/pi-embedded-runner/system-prompt.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner/system-prompt.ts)
      
  *   [src/agents/system-prompt-params.test.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/system-prompt-params.test.ts)
      
  *   [src/agents/system-prompt-params.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/system-prompt-params.ts)
      
  *   [src/agents/system-prompt-report.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/system-prompt-report.ts)
      
  *   [src/agents/system-prompt.test.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/system-prompt.test.ts)
      
  *   [src/agents/system-prompt.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/system-prompt.ts)
      
  *   [src/auto-reply/reply/commands-context-report.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/auto-reply/reply/commands-context-report.ts)
      
  *   [src/commands/agent/run-context.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/commands/agent/run-context.ts)
      
  *   [src/commands/agent/types.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/commands/agent/types.ts)
      
  *   [src/gateway/protocol/schema/agent.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/gateway/protocol/schema/agent.ts)
      
  *   [src/index.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/index.ts)
      
  *   [src/telegram/group-migration.test.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/telegram/group-migration.test.ts)
      
  *   [src/telegram/group-migration.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/telegram/group-migration.ts)
      
  *   [ui/package.json](https://github.com/openclaw/openclaw/blob/bf6ec64f/ui/package.json)
      
  *   [ui/src/styles.css](https://github.com/openclaw/openclaw/blob/bf6ec64f/ui/src/styles.css)
      
  *   [ui/src/styles/layout.mobile.css](https://github.com/openclaw/openclaw/blob/bf6ec64f/ui/src/styles/layout.mobile.css)
      
  
  The Skills System provides a modular way to extend agent capabilities through self-contained instruction sets. Each skill is a directory containing a `SKILL.md` file with specialized guidance that the agent reads on demand when a task matches the skill's purpose.
  
  For information about how skills are injected into the system prompt, see [System Prompt](https://deepwiki.com/openclaw/openclaw/5.2-system-prompt)
  . For workspace organization and bootstrap files, see [Agent Execution Flow](https://deepwiki.com/openclaw/openclaw/5.1-agent-execution-flow)
  . For tool configuration and security policies, see [Tool Security and Sandboxing](https://deepwiki.com/openclaw/openclaw/6.2-tool-security-and-sandboxing)
  .
  
  * * *
  
  Overview
  --------
  
  Skills in OpenClaw are discovered, indexed, and presented to the agent as a compact list in the system prompt. When the agent identifies a task that matches a skill, it uses the `read` tool to load the corresponding `SKILL.md` file and follow its instructions.
  
  **Key Characteristics:**
  
  | Aspect | Description |
  | --- | --- |
  | **Storage** | `~/.openclaw/workspace/skills/<skill-name>/` |
  | **Entry Point** | `SKILL.md` per skill directory |
  | **Discovery** | Automatic scan at agent startup and on workspace changes |
  | **Activation** | Agent-driven (model decides when to load) |
  | **Scope** | Session-independent (all sessions see same skills) |
  | **Types** | Workspace (user), Managed (installed), Bundled (shipped) |
  
  Skills are **not** tools. They are instruction documents that guide the agent's behavior for specific scenarios. The agent remains in control of when and whether to load a skill.
  
  Sources: [src/agents/system-prompt.ts15-32](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/system-prompt.ts#L15-L32)
   [docs/concepts/system-prompt.md83-95](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/concepts/system-prompt.md#L83-L95)
  
  * * *
  
  Skills Architecture
  -------------------
  
  **Skills Architecture**
  
  The system scans the workspace skills directory at startup and builds a snapshot containing eligible skills. This snapshot is formatted into a compact XML structure and injected into the system prompt. The agent sees the available skills list and can choose to load any skill by reading its `SKILL.md` file.
  
  Sources: [src/agents/system-prompt.ts15-32](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/system-prompt.ts#L15-L32)
   [src/agents/skills.ts (referenced)](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/skills.ts%20(referenced))
   [src/agents/pi-embedded-runner/run/attempt.ts162-181](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner/run/attempt.ts#L162-L181)
  
  * * *
  
  Skill Discovery and Loading
  ---------------------------
  
  **Skill Discovery Flow**
  
  Discovery happens in three phases:
  
  1.  **Entry Loading**: `loadWorkspaceSkillEntries` scans the `skills/` directory and identifies valid skill directories (those containing `SKILL.md`).
  2.  **Snapshot Building**: `buildWorkspaceSkillSnapshot` filters skills by eligibility (remote skill settings, config overrides) and creates a cached snapshot.
  3.  **Prompt Formatting**: The snapshot is formatted into XML with `<available_skills>` containing `<skill>` entries, each with `<name>`, `<description>`, and `<location>`.
  
  The resulting prompt is injected into the **Skills** section of the system prompt, instructing the agent to read the `SKILL.md` file at the listed location when a task matches.
  
  Sources: [src/agents/pi-embedded-runner/run/attempt.ts162-181](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner/run/attempt.ts#L162-L181)
   [src/agents/system-prompt.ts15-32](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/system-prompt.ts#L15-L32)
   [src/auto-reply/reply/commands-context-report.ts64-72](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/auto-reply/reply/commands-context-report.ts#L64-L72)
  
  * * *
  
  Skill Directory Structure
  -------------------------
  
  Each skill lives in its own directory under `~/.openclaw/workspace/skills/<skill-name>/`:
  
      skills/
      ├── my-skill/
      │   ├── SKILL.md              # Required: Instructions for the agent
      │   ├── skill.json            # Optional: Metadata (dependencies, env vars)
      │   ├── bins/                 # Optional: Executables (auto-added to PATH)
      │   │   └── my-tool
      │   └── README.md             # Optional: Human documentation
      
  
  ### SKILL.md Format
  
  The `SKILL.md` file contains natural language instructions for the agent. It should:
  
  *   **Describe** when to use the skill
  *   **Provide** step-by-step guidance
  *   **Reference** tools and commands as needed
  *   **Include** examples and edge cases
  
  Example structure:
  
      # Skill Name
      
      When to use: <scenario description>
      
      Steps:
      1. Check prerequisites with `<tool>`
      2. Execute `<command>`
      3. Verify output matches <pattern>
      
      Constraints:
      - Do not proceed if <condition>
      - Always confirm with user before <action>
  
  ### skill.json Metadata
  
  Optional JSON file for skill configuration:
  
  | Field | Type | Purpose |
  | --- | --- | --- |
  | `name` | string | Skill identifier |
  | `description` | string | Short summary (used in prompt) |
  | `dependencies` | string\[\] | Required npm packages or binaries |
  | `env` | object | Environment variable overrides |
  | `install` | object | Installation instructions (OS-specific) |
  
  Sources: [src/agents/skills.ts (referenced)](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/skills.ts%20(referenced))
   [CHANGELOG.md30](https://github.com/openclaw/openclaw/blob/bf6ec64f/CHANGELOG.md#L30-L30)
  
  * * *
  
  Skills in the System Prompt
  ---------------------------
  
  **Skills Section in System Prompt**
  
  The skills section is injected by `buildSkillsSection` in [src/agents/system-prompt.ts15-32](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/system-prompt.ts#L15-L32)
   It contains:
  
  1.  **Guidance Block**: Instructs the agent how to select and load skills:
      
      *   "Before replying: scan `<available_skills>` `<description>` entries."
      *   "If exactly one skill clearly applies: read its SKILL.md at `<location>` with `read`, then follow it."
      *   "If multiple could apply: choose the most specific one, then read/follow it."
      *   "If none clearly apply: do not read any SKILL.md."
      *   "Constraints: never read more than one skill up front; only read after selecting."
  2.  **Skills XML**: The formatted skills list from `formatSkillsForPrompt`, containing:
      
          <available_skills>
            <skill>
              <name>skill-name</name>
              <description>Brief description</description>
              <location>~/.openclaw/workspace/skills/skill-name/SKILL.md</location>
            </skill>
            ...
          </available_skills>
      
  
  The skills section is **omitted** when:
  
  *   `promptMode` is `"minimal"` or `"none"` (e.g., for subagents)
  *   No eligible skills exist
  *   `skillsPrompt` is empty after formatting
  
  Sources: [src/agents/system-prompt.ts15-32](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/system-prompt.ts#L15-L32)
   [docs/concepts/system-prompt.md83-95](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/concepts/system-prompt.md#L83-L95)
  
  * * *
  
  Skill Environment Overrides
  ---------------------------
  
  Skills can inject environment variables into the agent runtime, allowing them to configure tools, set API keys, or adjust paths without modifying the global environment.
  
  **Skill Environment Workflow**
  
  When an agent run begins:
  
  1.  **Load Skills**: `loadWorkspaceSkillEntries` discovers skill directories
  2.  **Apply Overrides**: `applySkillEnvOverrides` or `applySkillEnvOverridesFromSnapshot` merges skill environment variables into `process.env`
  3.  **Run Agent**: The agent executes with the enhanced environment
  4.  **Restore**: The returned cleanup function restores the original environment after the run completes
  
  Environment variables from skills are applied **after** config.env but **before** the agent run, giving skills the ability to configure tools dynamically.
  
  **Example skill.json with env:**
  
      {
        "name": "my-skill",
        "description": "Custom skill",
        "env": {
          "MY_TOOL_API_KEY": "sk-...",
          "MY_TOOL_ENDPOINT": "https://api.example.com"
        }
      }
  
  Sources: [src/agents/pi-embedded-runner/run/attempt.ts159-174](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner/run/attempt.ts#L159-L174)
   [src/agents/pi-embedded-runner/compact.ts164](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner/compact.ts#L164-L164)
  
  * * *
  
  Skills Snapshot and Caching
  ---------------------------
  
  To avoid redundant filesystem scans, OpenClaw maintains a **skill snapshot** that caches discovered skills and their formatted prompts.
  
  **Snapshot Structure**
  
  The snapshot ([src/agents/skills.ts (SkillSnapshot type)](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/skills.ts%20(SkillSnapshot%20type))
  ) contains:
  
  | Field | Type | Description |
  | --- | --- | --- |
  | `prompt` | string | Formatted XML for system prompt |
  | `skills` | string\[\] | List of skill names |
  | `resolvedSkills` | ResolvedSkill\[\] | Full skill metadata (location, description, env) |
  | `snapshotVersion` | string | Workspace version hash (for invalidation) |
  
  **Snapshot Lifecycle:**
  
  1.  **Creation**: `buildWorkspaceSkillSnapshot` scans the workspace and builds the snapshot
  2.  **Versioning**: `getSkillsSnapshotVersion` computes a hash of the workspace state (file mtimes, directory structure)
  3.  **Reuse**: If the snapshot version matches the current workspace version, the cached snapshot is used
  4.  **Refresh**: If stale, a new snapshot is built and cached
  5.  **Application**: `applySkillEnvOverridesFromSnapshot` uses the cached `resolvedSkills` to apply environment overrides without re-scanning
  
  This optimization is especially important for rapid-fire agent runs (e.g., during conversations) where filesystem scans would add latency.
  
  Sources: [src/agents/pi-embedded-runner/run/attempt.ts162-181](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner/run/attempt.ts#L162-L181)
   [src/agents/skills.ts (referenced)](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/skills.ts%20(referenced))
   [src/auto-reply/reply/commands-context-report.ts64-72](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/auto-reply/reply/commands-context-report.ts#L64-L72)
  
  * * *
  
  Skill Types and Locations
  -------------------------
  
  OpenClaw supports three skill locations, prioritized in this order:
  
  **Skill Priority and Resolution**
  
  When multiple skills have the same name, the one from the higher-priority location wins:
  
  1.  **Workspace Skills**: User-created or user-edited skills in `~/.openclaw/workspace/skills/`
      
      *   Highest priority
      *   Fully user-controlled
      *   Can override managed or bundled skills
  2.  **Managed Skills**: Installed via `openclaw skills install` or package managers
      
      *   Medium priority
      *   Versioned and updateable
      *   Stored in `~/.openclaw/managed-skills/` or similar
  3.  **Bundled Skills**: Shipped with OpenClaw in `node_modules/openclaw/skills/` or the npm package
      
      *   Lowest priority
      *   Updated with OpenClaw releases
      *   Provide baseline capabilities
  
  **Remote Skills Eligibility:**
  
  Remote (managed and bundled) skills can be gated by configuration:
  
  *   `getRemoteSkillEligibility()` checks if remote skills are enabled
  *   Workspace skills are always eligible
  *   Config can enable/disable individual skills via overrides
  
  Sources: [src/auto-reply/reply/commands-context-report.ts66](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/auto-reply/reply/commands-context-report.ts#L66-L66)
   [CHANGELOG.md17](https://github.com/openclaw/openclaw/blob/bf6ec64f/CHANGELOG.md#L17-L17)
  
  * * *
  
  Skill Bins and PATH Injection
  -----------------------------
  
  Skills can provide executable binaries in a `bins/` subdirectory. These are automatically added to the agent's PATH during runs that load the skill's environment.
  
  **PATH Injection Workflow**
  
  1.  **Discovery**: When `applySkillEnvOverrides` processes a skill, it checks for a `bins/` directory
  2.  **PATH Update**: If `bins/` exists, its absolute path is prepended to `process.env.PATH`
  3.  **Tool Availability**: Any executables in `bins/` become available to the `exec` tool without specifying full paths
  4.  **Cleanup**: The restore function resets PATH to its original value after the run
  
  This allows skills to bundle custom CLIs, scripts, or compiled binaries without requiring global installation or manual PATH configuration.
  
  **Security Note**: Skills with binaries should be reviewed before use, especially if sourced from untrusted origins. The `tools.exec.safeBins` config can allowlist specific binaries for approval-free execution.
  
  Sources: [src/agents/skills.ts (referenced)](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/skills.ts%20(referenced))
   [CHANGELOG.md18](https://github.com/openclaw/openclaw/blob/bf6ec64f/CHANGELOG.md#L18-L18)
  
  * * *
  
  Skill Dependencies and Installation
  -----------------------------------
  
  Skills can declare dependencies (npm packages, system binaries) and provide installation instructions for different platforms.
  
  **skill.json with dependencies:**
  
      {
        "name": "my-skill",
        "description": "Example skill with deps",
        "dependencies": [\
          "github-cli",\
          "jq"\
        ],
        "install": {
          "darwin": {
            "command": "brew install gh jq",
            "download": [\
              {\
                "url": "https://example.com/tool-macos.tar.gz",\
                "dest": "bins/tool"\
              }\
            ]
          },
          "linux": {
            "command": "apt-get install -y gh jq"
          }
        }
      }
  
  **Installation Workflow:**
  
  1.  **Detection**: When a skill is loaded, OpenClaw checks for `install` metadata
  2.  **OS Matching**: The appropriate install instructions for the current OS are selected
  3.  **Execution** (manual or automated):
      *   `command`: Shell command to install dependencies
      *   `download`: URLs to fetch and unpack into the skill directory
  4.  **Validation**: After installation, dependencies should be available in PATH or the skill's `bins/`
  
  Skills with missing dependencies will still appear in the skills list, but the agent may encounter errors when attempting to use them. Consider adding dependency checks in the `SKILL.md` instructions.
  
  Sources: [CHANGELOG.md30](https://github.com/openclaw/openclaw/blob/bf6ec64f/CHANGELOG.md#L30-L30)
  
  * * *
  
  Creating Custom Skills
  ----------------------
  
  To create a new skill:
  
  1.  **Create the directory:**
      
          mkdir -p ~/.openclaw/workspace/skills/my-skill
      
  2.  **Write SKILL.md:**
      
          # My Skill
          
          When to use: [describe scenario]
          
          Steps:
          1. [instruction]
          2. [instruction]
          
          Constraints:
          - [constraint]
      
  3.  **Add metadata (optional):**
      
          {
            "name": "my-skill",
            "description": "Brief description for prompt",
            "env": {
              "MY_VAR": "value"
            }
          }
      
  4.  **Refresh skills:** The agent will discover the skill on its next run. To force immediate discovery, restart the gateway or trigger a workspace refresh (editing a file in the workspace typically triggers a refresh).
      
  5.  **Test the skill:** Send a message that should trigger the skill's scenario. Check the agent's reasoning (via `/think high` or `/reasoning on`) to see if it loads and follows the SKILL.md.
      
  
  **Best Practices:**
  
  *   **Keep SKILL.md focused**: One skill per scenario
  *   **Use examples**: Show expected input/output patterns
  *   **Test incrementally**: Start with simple instructions, refine based on agent behavior
  *   **Version control**: Track your workspace skills in git for reproducibility
  *   **Document dependencies**: If the skill requires external tools, document them clearly
  
  Sources: [docs/concepts/system-prompt.md83-95](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/concepts/system-prompt.md#L83-L95)
   [src/agents/system-prompt.ts15-32](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/system-prompt.ts#L15-L32)
  
  * * *
  
  Skills CLI Commands
  -------------------
  
  OpenClaw provides CLI commands for managing skills:
  
  | Command | Purpose |
  | --- | --- |
  | `openclaw skills list` | List all discovered skills (workspace, managed, bundled) |
  | `openclaw skills install <name>` | Install a managed skill from a registry or URL |
  | `openclaw skills refresh` | Force rebuild of the skills snapshot |
  | `openclaw skills bins` | List all skill binaries available in PATH |
  
  (Note: Exact command availability depends on OpenClaw version. Use `openclaw help` to verify.)
  
  The skills system integrates with the broader workspace and configuration management. For more on workspace structure, see [Agent Execution Flow](https://deepwiki.com/openclaw/openclaw/5.1-agent-execution-flow)
  .
  
  Sources: [src/agents/system-prompt.ts15-32](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/system-prompt.ts#L15-L32)
   [CHANGELOG.md17-30](https://github.com/openclaw/openclaw/blob/bf6ec64f/CHANGELOG.md#L17-L30)
  
  Dismiss
  
  Refresh this wiki
  
  This wiki was recently refreshed. Please wait 4 days to refresh again.
  
  ### On this page
  
  *   [Skills System](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#skills-system)
      
  *   [Overview](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#overview)
      
  *   [Skills Architecture](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#skills-architecture)
      
  *   [Skill Discovery and Loading](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#skill-discovery-and-loading)
      
  *   [Skill Directory Structure](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#skill-directory-structure)
      
  *   [SKILL.md Format](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#skillmd-format)
      
  *   [skill.json Metadata](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#skilljson-metadata)
      
  *   [Skills in the System Prompt](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#skills-in-the-system-prompt)
      
  *   [Skill Environment Overrides](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#skill-environment-overrides)
      
  *   [Skills Snapshot and Caching](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#skills-snapshot-and-caching)
      
  *   [Skill Types and Locations](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#skill-types-and-locations)
      
  *   [Skill Bins and PATH Injection](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#skill-bins-and-path-injection)
      
  *   [Skill Dependencies and Installation](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#skill-dependencies-and-installation)
      
  *   [Creating Custom Skills](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#creating-custom-skills)
      
  *   [Skills CLI Commands](https://deepwiki.com/openclaw/openclaw/6.3-skills-system#skills-cli-commands)
      
  
  Ask Devin about openclaw/openclaw
  
  Fast
  --- End Content ---

OpenClaw: The Revolutionary AI Assistant That Actually Does Your ...
  URL: https://ai.plainenglish.io/openclaw-the-revolutionary-ai-assistant-that-actually-does-your-computer-work-667cd4449883
  22 hours ago ... Skills are modular components that teach the AI how to use specific tools and capabilities. Each skill consists of a markdown file containing ...

  --- Content ---
  [Sitemap](https://ai.plainenglish.io/sitemap/sitemap.xml)
  
  [Open in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3DmobileNavBar&source=post_page---top_nav_layout_nav-----------------------------------------)
  
  Sign up
  
  [Sign in](https://medium.com/m/signin?operation=login&redirect=https%3A%2F%2Fai.plainenglish.io%2Fopenclaw-the-revolutionary-ai-assistant-that-actually-does-your-computer-work-667cd4449883&source=post_page---top_nav_layout_nav-----------------------global_nav------------------)
  
  [Medium Logo](https://medium.com/?source=post_page---top_nav_layout_nav-----------------------------------------)
  
  [Write](https://medium.com/m/signin?operation=register&redirect=https%3A%2F%2Fmedium.com%2Fnew-story&source=---top_nav_layout_nav-----------------------new_post_topnav------------------)
  
  [Search](https://medium.com/search?source=post_page---top_nav_layout_nav-----------------------------------------)
  
  Sign up
  
  [Sign in](https://medium.com/m/signin?operation=login&redirect=https%3A%2F%2Fai.plainenglish.io%2Fopenclaw-the-revolutionary-ai-assistant-that-actually-does-your-computer-work-667cd4449883&source=post_page---top_nav_layout_nav-----------------------global_nav------------------)
  
  ![](https://miro.medium.com/v2/resize:fill:64:64/1*dmbNkD5D-u45r44go_cf0g.png)
  
  [Artificial Intelligence in Plain English\
  \
  \
  --------------------------------------------](https://ai.plainenglish.io/?source=post_page---publication_nav-78d064101951-667cd4449883---------------------------------------)
  
  ·
  
  Follow publication
  
  [![Artificial Intelligence in Plain English](https://miro.medium.com/v2/resize:fill:76:76/1*9zAmnK08gUCmZX7q0McVKw@2x.png)](https://ai.plainenglish.io/?source=post_page---post_publication_sidebar-78d064101951-667cd4449883---------------------------------------)
  
  New AI, ML and Data Science articles every day. Follow to join our 3.5M+ monthly readers.
  
  Follow publication
  
  Member-only story
  
  **OpenClaw: The Revolutionary AI Assistant That Actually Does Your Computer Work**
  ==================================================================================
  
  [![0xJiuJitsuJerry](https://miro.medium.com/v2/resize:fill:64:64/1*HFX3J8ywccvL408M-FzEig.jpeg)](https://medium.com/@0xJiuJitsuJerry?source=post_page---byline--667cd4449883---------------------------------------)
  
  [0xJiuJitsuJerry](https://medium.com/@0xJiuJitsuJerry?source=post_page---byline--667cd4449883---------------------------------------)
  
  Follow
  
  7 min read
  
  ·
  
  22 hours ago
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fvote%2Fai-in-plain-english%2F667cd4449883&operation=register&redirect=https%3A%2F%2Fai.plainenglish.io%2Fopenclaw-the-revolutionary-ai-assistant-that-actually-does-your-computer-work-667cd4449883&user=0xJiuJitsuJerry&userId=a2ef077f226d&source=---header_actions--667cd4449883---------------------clap_footer------------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F667cd4449883&operation=register&redirect=https%3A%2F%2Fai.plainenglish.io%2Fopenclaw-the-revolutionary-ai-assistant-that-actually-does-your-computer-work-667cd4449883&source=---header_actions--667cd4449883---------------------bookmark_footer------------------)
  
  [Listen](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2Fplans%3Fdimension%3Dpost_audio_button%26postId%3D667cd4449883&operation=register&redirect=https%3A%2F%2Fai.plainenglish.io%2Fopenclaw-the-revolutionary-ai-assistant-that-actually-does-your-computer-work-667cd4449883&source=---header_actions--667cd4449883---------------------post_audio_button------------------)
  
  Share
  
  Press enter or click to view image in full size
  
  ![](https://miro.medium.com/v2/resize:fit:700/1*RA5mZ7k8gXSy_tleXLdPDg.jpeg)
  
  **Meet the AI That Doesn’t Just Chat — It Takes Action**
  
  Imagine having an AI assistant that doesn’t just respond with text suggestions but actually operates your computer for you. Picture an AI that can read your files, run your applications, manage your communications, and execute complex tasks on your behalf. This isn’t science fiction — it’s OpenClaw, an open-source, locally-running AI assistant that transforms how we think about artificial intelligence and personal productivity.
  
  OpenClaw (formerly known as Clawdbot, then Moltbot) represents a fundamental shift from traditional AI assistants that merely provide information to intelligent agents that can actively manipulate your digital environment. Unlike cloud-based chatbots that are limited to conversation, OpenClaw runs locally on your hardware and integrates deeply with your operating system, giving it the ability to perform real-world tasks on your computer.
  
  **Understanding OpenClaw: What Makes It Different?**
  
  Traditional AI assistants like ChatGPT, Claude, or Gemini excel at generating text and providing information, but they operate in isolation from your computer’s systems. They can’t access your files, run your applications, or perform actions on your behalf. OpenClaw breaks down…
  
  Create an account to read the full story.
  
  
  ---------------------------------------------
  
  The author made this story available to Medium members only.  
  If you’re new to Medium, create a new account to read this story on us.
  
  [Continue in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3Dregwall&source=-----667cd4449883---------------------post_regwall------------------)
  
  Or, continue in mobile web
  
  [Sign up with Google](https://medium.com/m/connect/google?state=google-%7Chttps%3A%2F%2Fai.plainenglish.io%2Fopenclaw-the-revolutionary-ai-assistant-that-actually-does-your-computer-work-667cd4449883%3Fsource%3D-----667cd4449883---------------------post_regwall------------------%26skipOnboarding%3D1%7Cregister&source=-----667cd4449883---------------------post_regwall------------------)
  
  [Sign up with Facebook](https://medium.com/m/connect/facebook?state=facebook-%7Chttps%3A%2F%2Fai.plainenglish.io%2Fopenclaw-the-revolutionary-ai-assistant-that-actually-does-your-computer-work-667cd4449883%3Fsource%3D-----667cd4449883---------------------post_regwall------------------%26skipOnboarding%3D1%7Cregister&source=-----667cd4449883---------------------post_regwall------------------)
  
  Sign up with email
  
  Already have an account? [Sign in](https://medium.com/m/signin?operation=login&redirect=https%3A%2F%2Fai.plainenglish.io%2Fopenclaw-the-revolutionary-ai-assistant-that-actually-does-your-computer-work-667cd4449883&source=-----667cd4449883---------------------post_regwall------------------)
  
  [![Artificial Intelligence in Plain English](https://miro.medium.com/v2/resize:fill:96:96/1*9zAmnK08gUCmZX7q0McVKw@2x.png)](https://ai.plainenglish.io/?source=post_page---post_publication_info--667cd4449883---------------------------------------)
  
  [![Artificial Intelligence in Plain English](https://miro.medium.com/v2/resize:fill:128:128/1*9zAmnK08gUCmZX7q0McVKw@2x.png)](https://ai.plainenglish.io/?source=post_page---post_publication_info--667cd4449883---------------------------------------)
  
  Follow
  
  [Published in Artificial Intelligence in Plain English\
  -----------------------------------------------------](https://ai.plainenglish.io/?source=post_page---post_publication_info--667cd4449883---------------------------------------)
  
  [38K followers](https://ai.plainenglish.io/followers?source=post_page---post_publication_info--667cd4449883---------------------------------------)
  
  ·[Last published 12 hours ago](https://ai.plainenglish.io/ai-in-dubais-real-estate-market-automation-analytics-roi-cce2a7592b8b?source=post_page---post_publication_info--667cd4449883---------------------------------------)
  
  New AI, ML and Data Science articles every day. Follow to join our 3.5M+ monthly readers.
  
  Follow
  
  [![0xJiuJitsuJerry](https://miro.medium.com/v2/resize:fill:96:96/1*HFX3J8ywccvL408M-FzEig.jpeg)](https://medium.com/@0xJiuJitsuJerry?source=post_page---post_author_info--667cd4449883---------------------------------------)
  
  [![0xJiuJitsuJerry](https://miro.medium.com/v2/resize:fill:128:128/1*HFX3J8ywccvL408M-FzEig.jpeg)](https://medium.com/@0xJiuJitsuJerry?source=post_page---post_author_info--667cd4449883---------------------------------------)
  
  Follow
  
  [Written by 0xJiuJitsuJerry\
  --------------------------](https://medium.com/@0xJiuJitsuJerry?source=post_page---post_author_info--667cd4449883---------------------------------------)
  
  [165 followers](https://medium.com/@0xJiuJitsuJerry/followers?source=post_page---post_author_info--667cd4449883---------------------------------------)
  
  ·[415 following](https://medium.com/@0xJiuJitsuJerry/following?source=post_page---post_author_info--667cd4449883---------------------------------------)
  
  BJJ Instructor - AI & Web3 builder - @Wharton Economics Blockchain & Digital Assets - Dev @FreshMintsCoin on Solana - $Jerry for NFTs AI & crypto alpha.
  
  Follow
  
  No responses yet
  ----------------
  
  [](https://policy.medium.com/medium-rules-30e5502c4eb4?source=post_page---post_responses--667cd4449883---------------------------------------)
  
  ![](https://miro.medium.com/v2/resize:fill:32:32/1*dmbNkD5D-u45r44go_cf0g.png)
  
  Write a response
  
  [What are your thoughts?](https://medium.com/m/signin?operation=register&redirect=https%3A%2F%2Fai.plainenglish.io%2Fopenclaw-the-revolutionary-ai-assistant-that-actually-does-your-computer-work-667cd4449883&source=---post_responses--667cd4449883---------------------respond_sidebar------------------)
  
  Cancel
  
  Respond
  
  More from 0xJiuJitsuJerry and Artificial Intelligence in Plain English
  ----------------------------------------------------------------------
  
  ![COMET STRIKES: How Perplexity AI’s New Browser Is Revolutionizing the Web — and Threatening…](https://miro.medium.com/v2/resize:fit:679/format:webp/1*8ucFx5tmHeO0XmUMRRi8Iw.jpeg)
  
  [![Artificial Intelligence in Plain English](https://miro.medium.com/v2/resize:fill:20:20/1*9zAmnK08gUCmZX7q0McVKw@2x.png)](https://ai.plainenglish.io/?source=post_page---author_recirc--667cd4449883----0---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  In
  
  [Artificial Intelligence in Plain English](https://ai.plainenglish.io/?source=post_page---author_recirc--667cd4449883----0---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  by
  
  [0xJiuJitsuJerry](https://medium.com/@0xJiuJitsuJerry?source=post_page---author_recirc--667cd4449883----0---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  [COMET STRIKES: How Perplexity AI’s New Browser Is Revolutionizing the Web — and Threatening…\
  --------------------------------------------------------------------------------------------\
  \
  ### A new star just streaked across the digital sky, and it’s called Comet — the AI-native web browser from Perplexity AI. With the web…](https://ai.plainenglish.io/comet-strikes-how-perplexity-ais-new-browser-is-revolutionizing-the-web-and-threatening-f273bd36741d?source=post_page---author_recirc--667cd4449883----0---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  Jul 10, 2025
  
  [](https://ai.plainenglish.io/comet-strikes-how-perplexity-ais-new-browser-is-revolutionizing-the-web-and-threatening-f273bd36741d?source=post_page---author_recirc--667cd4449883----0---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2Ff273bd36741d&operation=register&redirect=https%3A%2F%2Fai.plainenglish.io%2Fcomet-strikes-how-perplexity-ais-new-browser-is-revolutionizing-the-web-and-threatening-f273bd36741d&source=---author_recirc--667cd4449883----0-----------------bookmark_preview----8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  ![How Fortran Outsmarted Our Billion-Dollar AI Chip](https://miro.medium.com/v2/resize:fit:679/format:webp/0*DdvF6nV7hVB1TGeh)
  
  [![Artificial Intelligence in Plain English](https://miro.medium.com/v2/resize:fill:20:20/1*9zAmnK08gUCmZX7q0McVKw@2x.png)](https://ai.plainenglish.io/?source=post_page---author_recirc--667cd4449883----1---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  In
  
  [Artificial Intelligence in Plain English](https://ai.plainenglish.io/?source=post_page---author_recirc--667cd4449883----1---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  by
  
  [Prem Chandak](https://medium.com/@premchandak_11?source=post_page---author_recirc--667cd4449883----1---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  [How Fortran Outsmarted Our Billion-Dollar AI Chip\
  -------------------------------------------------\
  \
  ### A 70-year-old programming language just humbled cutting-edge AI hardware — and revealed a truth we forgot about computing efficiency.](https://ai.plainenglish.io/how-fortran-outsmarted-our-billion-dollar-ai-chip-98fabbefd01b?source=post_page---author_recirc--667cd4449883----1---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  Nov 6, 2025
  
  [A response icon37](https://ai.plainenglish.io/how-fortran-outsmarted-our-billion-dollar-ai-chip-98fabbefd01b?source=post_page---author_recirc--667cd4449883----1---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F98fabbefd01b&operation=register&redirect=https%3A%2F%2Fai.plainenglish.io%2Fhow-fortran-outsmarted-our-billion-dollar-ai-chip-98fabbefd01b&source=---author_recirc--667cd4449883----1-----------------bookmark_preview----8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  ![GPT-5 Spent One Night in a Wet Lab — The Next Morning the Experiment Ran 79× Faster](https://miro.medium.com/v2/resize:fit:679/format:webp/1*ymq8gy81w_t-SQeDNG1l2g.png)
  
  [![Artificial Intelligence in Plain English](https://miro.medium.com/v2/resize:fill:20:20/1*9zAmnK08gUCmZX7q0McVKw@2x.png)](https://ai.plainenglish.io/?source=post_page---author_recirc--667cd4449883----2---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  In
  
  [Artificial Intelligence in Plain English](https://ai.plainenglish.io/?source=post_page---author_recirc--667cd4449883----2---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  by
  
  [Faisal haque](https://medium.com/@faisalhaque226?source=post_page---author_recirc--667cd4449883----2---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  [GPT-5 Spent One Night in a Wet Lab — The Next Morning the Experiment Ran 79× Faster\
  -----------------------------------------------------------------------------------\
  \
  ### Bench scientists who tried the AI protocol saw 6-month projects finish in a week. Here’s the step-by-step (and why post-docs are nervous)](https://ai.plainenglish.io/gpt-5-spent-one-night-in-a-wet-lab-the-next-morning-the-experiment-ran-79-faster-496d397142b6?source=post_page---author_recirc--667cd4449883----2---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  Dec 30, 2025
  
  [A response icon10](https://ai.plainenglish.io/gpt-5-spent-one-night-in-a-wet-lab-the-next-morning-the-experiment-ran-79-faster-496d397142b6?source=post_page---author_recirc--667cd4449883----2---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F496d397142b6&operation=register&redirect=https%3A%2F%2Fai.plainenglish.io%2Fgpt-5-spent-one-night-in-a-wet-lab-the-next-morning-the-experiment-ran-79-faster-496d397142b6&source=---author_recirc--667cd4449883----2-----------------bookmark_preview----8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  ![The “USB Moment” for AI: Why the Model Context Protocol (MCP) Changes Everything](https://miro.medium.com/v2/resize:fit:679/format:webp/1*RA_m95ml_HRuz6oxkcMrSA.jpeg)
  
  [![Artificial Intelligence in Plain English](https://miro.medium.com/v2/resize:fill:20:20/1*9zAmnK08gUCmZX7q0McVKw@2x.png)](https://ai.plainenglish.io/?source=post_page---author_recirc--667cd4449883----3---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  In
  
  [Artificial Intelligence in Plain English](https://ai.plainenglish.io/?source=post_page---author_recirc--667cd4449883----3---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  by
  
  [0xJiuJitsuJerry](https://medium.com/@0xJiuJitsuJerry?source=post_page---author_recirc--667cd4449883----3---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  [The “USB Moment” for AI: Why the Model Context Protocol (MCP) Changes Everything\
  --------------------------------------------------------------------------------\
  \
  ### When Connecting Everything to Everything Else Finally Makes Sense](https://ai.plainenglish.io/the-usb-moment-for-ai-why-the-model-context-protocol-mcp-changes-everything-6a584c388960?source=post_page---author_recirc--667cd4449883----3---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  Jan 8
  
  [](https://ai.plainenglish.io/the-usb-moment-for-ai-why-the-model-context-protocol-mcp-changes-everything-6a584c388960?source=post_page---author_recirc--667cd4449883----3---------------------8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F6a584c388960&operation=register&redirect=https%3A%2F%2Fai.plainenglish.io%2Fthe-usb-moment-for-ai-why-the-model-context-protocol-mcp-changes-everything-6a584c388960&source=---author_recirc--667cd4449883----3-----------------bookmark_preview----8341ce3f_f4b9_4c13_989c_7204e5b9f33f--------------)
  
  [See all from 0xJiuJitsuJerry](https://medium.com/@0xJiuJitsuJerry?source=post_page---author_recirc--667cd4449883---------------------------------------)
  
  Recommended from Medium
  -----------------------
  
  ![Moltbot (Clawdbot) The most hyped AI Assistant Full Guide](https://miro.medium.com/v2/resize:fit:679/format:webp/1*MIwggS9uYbDt-nB19-hW8A.png)
  
  [![Reza Rezvani](https://miro.medium.com/v2/resize:fill:20:20/1*jDxVaEgUePd76Bw8xJrr2g.png)](https://alirezarezvani.medium.com/?source=post_page---read_next_recirc--667cd4449883----0---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [Reza Rezvani](https://alirezarezvani.medium.com/?source=post_page---read_next_recirc--667cd4449883----0---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [Everyone’s Installing Moltbot (Clawdbot). Here’s Why I’m Not Running It in Production (Yet).\
  --------------------------------------------------------------------------------------------\
  \
  ### What actually works, what doesn’t, and whether you should set this AI Assistant up](https://alirezarezvani.medium.com/everyones-installing-moltbot-clawdbot-here-s-why-i-m-not-running-it-in-production-yet-04f9ec596ef5?source=post_page---read_next_recirc--667cd4449883----0---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  5d ago
  
  [A response icon8](https://alirezarezvani.medium.com/everyones-installing-moltbot-clawdbot-here-s-why-i-m-not-running-it-in-production-yet-04f9ec596ef5?source=post_page---read_next_recirc--667cd4449883----0---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F04f9ec596ef5&operation=register&redirect=https%3A%2F%2Falirezarezvani.medium.com%2Feveryones-installing-moltbot-clawdbot-here-s-why-i-m-not-running-it-in-production-yet-04f9ec596ef5&source=---read_next_recirc--667cd4449883----0-----------------bookmark_preview----6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  ![How Agent Skills Became AI’s Most Important Standard in 90 Days](https://miro.medium.com/v2/resize:fit:679/format:webp/1*VqPChBhF5Apow495dgruIQ.png)
  
  [![AI Advances](https://miro.medium.com/v2/resize:fill:20:20/1*R8zEd59FDf0l8Re94ImV0Q.png)](https://ai.gopubby.com/?source=post_page---read_next_recirc--667cd4449883----1---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  In
  
  [AI Advances](https://ai.gopubby.com/?source=post_page---read_next_recirc--667cd4449883----1---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  by
  
  [Han HELOIR YAN, Ph.D. ☕️](https://medium.com/@han.heloir?source=post_page---read_next_recirc--667cd4449883----1---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [How Agent Skills Became AI’s Most Important Standard in 90 Days\
  ---------------------------------------------------------------\
  \
  ### The AI infrastructure War You Missed](https://ai.gopubby.com/how-agent-skills-became-ais-most-important-standard-in-90-days-a66b6369b1b7?source=post_page---read_next_recirc--667cd4449883----1---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  Jan 25
  
  [A response icon15](https://ai.gopubby.com/how-agent-skills-became-ais-most-important-standard-in-90-days-a66b6369b1b7?source=post_page---read_next_recirc--667cd4449883----1---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2Fa66b6369b1b7&operation=register&redirect=https%3A%2F%2Fai.gopubby.com%2Fhow-agent-skills-became-ais-most-important-standard-in-90-days-a66b6369b1b7&source=---read_next_recirc--667cd4449883----1-----------------bookmark_preview----6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  ![Ollama LaunchOllama Launch](https://miro.medium.com/v2/resize:fit:679/format:webp/1*FU-zudfoF4r2b2q825bl_A.png)
  
  [![AI Software Engineer](https://miro.medium.com/v2/resize:fill:20:20/1*RZVWENvZRwVijHDlg5hw7w.png)](https://medium.com/ai-software-engineer?source=post_page---read_next_recirc--667cd4449883----0---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  In
  
  [AI Software Engineer](https://medium.com/ai-software-engineer?source=post_page---read_next_recirc--667cd4449883----0---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  by
  
  [Joe Njenga](https://medium.com/@joe.njenga?source=post_page---read_next_recirc--667cd4449883----0---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [I Tested (New) Ollama Launch For Claude Code, Codex, OpenCode (No More Configs)\
  -------------------------------------------------------------------------------\
  \
  ### Forget configuration headaches, Ollama launch is the new easy way to launch Claude Code, Codex, OpenCode, Moltbot, or any other CLI tool.](https://medium.com/ai-software-engineer/i-tested-new-ollama-launch-for-claude-code-codex-opencode-more-bfae2af3c3db?source=post_page---read_next_recirc--667cd4449883----0---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  5d ago
  
  [A response icon3](https://medium.com/ai-software-engineer/i-tested-new-ollama-launch-for-claude-code-codex-opencode-more-bfae2af3c3db?source=post_page---read_next_recirc--667cd4449883----0---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2Fbfae2af3c3db&operation=register&redirect=https%3A%2F%2Fmedium.com%2Fai-software-engineer%2Fi-tested-new-ollama-launch-for-claude-code-codex-opencode-more-bfae2af3c3db&source=---read_next_recirc--667cd4449883----0-----------------bookmark_preview----6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  ![6 brain images](https://miro.medium.com/v2/resize:fit:679/format:webp/1*Q-mzQNzJSVYkVGgsmHVjfw.png)
  
  [![Write A Catalyst](https://miro.medium.com/v2/resize:fill:20:20/1*KCHN5TM3Ga2PqZHA4hNbaw.png)](https://medium.com/write-a-catalyst?source=post_page---read_next_recirc--667cd4449883----1---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  In
  
  [Write A Catalyst](https://medium.com/write-a-catalyst?source=post_page---read_next_recirc--667cd4449883----1---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  by
  
  [Dr. Patricia Schmidt](https://medium.com/@creatorschmidt?source=post_page---read_next_recirc--667cd4449883----1---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [As a Neuroscientist, I Quit These 5 Morning Habits That Destroy Your Brain\
  --------------------------------------------------------------------------\
  \
  ### Most people do #1 within 10 minutes of waking (and it sabotages your entire day)](https://medium.com/write-a-catalyst/as-a-neuroscientist-i-quit-these-5-morning-habits-that-destroy-your-brain-3efe1f410226?source=post_page---read_next_recirc--667cd4449883----1---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  Jan 14
  
  [A response icon392](https://medium.com/write-a-catalyst/as-a-neuroscientist-i-quit-these-5-morning-habits-that-destroy-your-brain-3efe1f410226?source=post_page---read_next_recirc--667cd4449883----1---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F3efe1f410226&operation=register&redirect=https%3A%2F%2Fmedium.com%2Fwrite-a-catalyst%2Fas-a-neuroscientist-i-quit-these-5-morning-habits-that-destroy-your-brain-3efe1f410226&source=---read_next_recirc--667cd4449883----1-----------------bookmark_preview----6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  ![Building AI Agents in 2026: Chatbots to Agentic Architectures](https://miro.medium.com/v2/resize:fit:679/format:webp/1*QOF4rZaV-KHzmvnBFsiOPQ.png)
  
  [![Level Up Coding](https://miro.medium.com/v2/resize:fill:20:20/1*5D9oYBd58pyjMkV_5-zXXQ.jpeg)](https://levelup.gitconnected.com/?source=post_page---read_next_recirc--667cd4449883----2---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  In
  
  [Level Up Coding](https://levelup.gitconnected.com/?source=post_page---read_next_recirc--667cd4449883----2---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  by
  
  [Gaurav Shrivastav](https://medium.com/@gaurav21s?source=post_page---read_next_recirc--667cd4449883----2---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [Building AI Agents in 2026: Chatbots to Agentic Architectures\
  -------------------------------------------------------------\
  \
  ### This is the engineering blueprint for building production-ready agentic systems that actually work.](https://levelup.gitconnected.com/the-2026-roadmap-to-ai-agent-mastery-5e43756c0f26?source=post_page---read_next_recirc--667cd4449883----2---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  Jan 22
  
  [A response icon1](https://levelup.gitconnected.com/the-2026-roadmap-to-ai-agent-mastery-5e43756c0f26?source=post_page---read_next_recirc--667cd4449883----2---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F5e43756c0f26&operation=register&redirect=https%3A%2F%2Flevelup.gitconnected.com%2Fthe-2026-roadmap-to-ai-agent-mastery-5e43756c0f26&source=---read_next_recirc--667cd4449883----2-----------------bookmark_preview----6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  ![OpenAI Is Headed For Bankruptcy](https://miro.medium.com/v2/resize:fit:679/format:webp/0*-ZmB4i4JnceA2UJU)
  
  [![Will Lockett](https://miro.medium.com/v2/resize:fill:20:20/1*V0qWMQ8V5_NaF9yUoHAdyg.jpeg)](https://wlockett.medium.com/?source=post_page---read_next_recirc--667cd4449883----3---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [Will Lockett](https://wlockett.medium.com/?source=post_page---read_next_recirc--667cd4449883----3---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [OpenAI Is Headed For Bankruptcy\
  -------------------------------\
  \
  ### It is nearly game over for Altman.](https://wlockett.medium.com/openai-is-headed-for-bankruptcy-d8883bf20f7c?source=post_page---read_next_recirc--667cd4449883----3---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  Jan 24
  
  [A response icon133](https://wlockett.medium.com/openai-is-headed-for-bankruptcy-d8883bf20f7c?source=post_page---read_next_recirc--667cd4449883----3---------------------6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2Fd8883bf20f7c&operation=register&redirect=https%3A%2F%2Fwlockett.medium.com%2Fopenai-is-headed-for-bankruptcy-d8883bf20f7c&source=---read_next_recirc--667cd4449883----3-----------------bookmark_preview----6afcddd5_7563_404a_b577_2911806b4cba--------------)
  
  [See more recommendations](https://medium.com/?source=post_page---read_next_recirc--667cd4449883---------------------------------------)
  
  [Help](https://help.medium.com/hc/en-us?source=post_page-----667cd4449883---------------------------------------)
  
  [Status](https://status.medium.com/?source=post_page-----667cd4449883---------------------------------------)
  
  [About](https://medium.com/about?autoplay=1&source=post_page-----667cd4449883---------------------------------------)
  
  [Careers](https://medium.com/jobs-at-medium/work-at-medium-959d1a85284e?source=post_page-----667cd4449883---------------------------------------)
  
  [Press](mailto:pressinquiries@medium.com)
  
  [Blog](https://blog.medium.com/?source=post_page-----667cd4449883---------------------------------------)
  
  [Privacy](https://policy.medium.com/medium-privacy-policy-f03bf92035c9?source=post_page-----667cd4449883---------------------------------------)
  
  [Rules](https://policy.medium.com/medium-rules-30e5502c4eb4?source=post_page-----667cd4449883---------------------------------------)
  
  [Terms](https://policy.medium.com/medium-terms-of-service-9db0094a1e0f?source=post_page-----667cd4449883---------------------------------------)
  
  [Text to speech](https://speechify.com/medium?source=post_page-----667cd4449883---------------------------------------)
  --- End Content ---

Awesome OpenClaw (Moltbot (Clawdbot)) Skills - GitHub
  URL: https://github.com/VoltAgent/awesome-openclaw-skills
  This collection helps you discover and install the right skills for your needs. Skills in this list are sourced from OpenClaw (OpenClaw's public skills registry) and categorized for easier discovery. These skills follow the Agent Skill convention develop by Anthropic, an open standard for AI coding assistants.
  Category: github

  --- Content ---
  [Skip to content](https://github.com/VoltAgent/awesome-openclaw-skills#start-of-content)
    
  
  You signed in with another tab or window. [Reload](https://github.com/VoltAgent/awesome-openclaw-skills)
   to refresh your session. You signed out in another tab or window. [Reload](https://github.com/VoltAgent/awesome-openclaw-skills)
   to refresh your session. You switched accounts on another tab or window. [Reload](https://github.com/VoltAgent/awesome-openclaw-skills)
   to refresh your session. Dismiss alert
  
  [VoltAgent](https://github.com/VoltAgent) / **[awesome-openclaw-skills](https://github.com/VoltAgent/awesome-openclaw-skills)** Public
  
  *   [Notifications](https://github.com/login?return_to=%2FVoltAgent%2Fawesome-openclaw-skills)
       You must be signed in to change notification settings
  *   [Fork 582](https://github.com/login?return_to=%2FVoltAgent%2Fawesome-openclaw-skills)
      
  *   [Star 6.2k](https://github.com/login?return_to=%2FVoltAgent%2Fawesome-openclaw-skills)
      
  
  The awesome collection of OpenClaw Skills. Formerly known as Moltbot, originally Clawdbot.
  
  [github.com/VoltAgent/voltagent](https://github.com/VoltAgent/voltagent "https://github.com/VoltAgent/voltagent")
  
  ### License
  
  [MIT license](https://github.com/VoltAgent/awesome-openclaw-skills/blob/main/LICENSE)
  
  [6.2k stars](https://github.com/VoltAgent/awesome-openclaw-skills/stargazers)
   [582 forks](https://github.com/VoltAgent/awesome-openclaw-skills/forks)
   [Branches](https://github.com/VoltAgent/awesome-openclaw-skills/branches)
   [Tags](https://github.com/VoltAgent/awesome-openclaw-skills/tags)
   [Activity](https://github.com/VoltAgent/awesome-openclaw-skills/activity)
  
  [Star](https://github.com/login?return_to=%2FVoltAgent%2Fawesome-openclaw-skills)
  
  [Notifications](https://github.com/login?return_to=%2FVoltAgent%2Fawesome-openclaw-skills)
   You must be signed in to change notification settings
  
  VoltAgent/awesome-openclaw-skills
  =================================
  
    main
  
  [Branches](https://github.com/VoltAgent/awesome-openclaw-skills/branches)
  [Tags](https://github.com/VoltAgent/awesome-openclaw-skills/tags)
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills/branches)
  [](https://github.com/VoltAgent/awesome-openclaw-skills/tags)
  
  Go to file
  
  Code
  
  Open more actions menu
  
  Folders and files
  -----------------
  
  | Name |     | Name | Last commit message | Last commit date |
  | --- | --- | --- | --- |
  | Latest commit<br>-------------<br><br>History<br>-------<br><br>[51 Commits](https://github.com/VoltAgent/awesome-openclaw-skills/commits/main/)<br><br>[](https://github.com/VoltAgent/awesome-openclaw-skills/commits/main/)<br>51 Commits |     |     |
  | [CONTRIBUTING.md](https://github.com/VoltAgent/awesome-openclaw-skills/blob/main/CONTRIBUTING.md "CONTRIBUTING.md") |     | [CONTRIBUTING.md](https://github.com/VoltAgent/awesome-openclaw-skills/blob/main/CONTRIBUTING.md "CONTRIBUTING.md") |     |     |
  | [LICENSE](https://github.com/VoltAgent/awesome-openclaw-skills/blob/main/LICENSE "LICENSE") |     | [LICENSE](https://github.com/VoltAgent/awesome-openclaw-skills/blob/main/LICENSE "LICENSE") |     |     |
  | [README.md](https://github.com/VoltAgent/awesome-openclaw-skills/blob/main/README.md "README.md") |     | [README.md](https://github.com/VoltAgent/awesome-openclaw-skills/blob/main/README.md "README.md") |     |     |
  | View all files |     |     |
  
  Repository files navigation
  ---------------------------
  
  [![social](https://private-user-images.githubusercontent.com/18739364/542745161-a6f310af-8fed-4766-9649-b190575b399d.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NzAwMDk0ODQsIm5iZiI6MTc3MDAwOTE4NCwicGF0aCI6Ii8xODczOTM2NC81NDI3NDUxNjEtYTZmMzEwYWYtOGZlZC00NzY2LTk2NDktYjE5MDU3NWIzOTlkLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNjAyMDIlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjYwMjAyVDA1MTMwNFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTNkMGY0ZTg3ODIwZDhhNjQxODc3ZjU1OTY2ZGZjMTM1OWYwNzExMzc0Njk2Mjg5ZDVlM2QwZmEzZjBjYzAyY2YmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.A_moiWGQcPFgqzkTq4ASnynag5HCCYytWlumgF8npLA)](https://github.com/VoltAgent/voltagent)
    
    
  
  **Discover 700+ community-built OpenClaw skills, organized by category.**  
    
  
  [![Awesome](https://camo.githubusercontent.com/9d49598b873146ec650fb3f275e8a532c765dabb1f61d5afa25be41e79891aa7/68747470733a2f2f617765736f6d652e72652f62616467652e737667)](https://awesome.re/)
   [![VoltAgent](https://camo.githubusercontent.com/491fc4b849caed81f4c212aa05ac0c867b19f8ef60589ffb15096074c73ed36f/68747470733a2f2f63646e2e766f6c746167656e742e6465762f776562736974652f6c6f676f2f6c6f676f2d322d7376672e737667)](https://github.com/VoltAgent/voltagent)
  
  [![Skills Count](https://camo.githubusercontent.com/11e855db8f882785b5e7fe1cb0ffcb0a71aac7fb09dc2f19625910dd39a3109a/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f736b696c6c732d3730302b2d626c75653f7374796c653d666c61742d737175617265)](https://camo.githubusercontent.com/11e855db8f882785b5e7fe1cb0ffcb0a71aac7fb09dc2f19625910dd39a3109a/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f736b696c6c732d3730302b2d626c75653f7374796c653d666c61742d737175617265)
   [![Last Update](https://camo.githubusercontent.com/9aba4c0cefa700d9e04aa3d26ba818419d07f5f7bb61162306a6ee0c01c885a6/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c6173742d636f6d6d69742f566f6c744167656e742f617765736f6d652d636c617764626f742d736b696c6c733f6c6162656c3d4c617374253230757064617465267374796c653d666c61742d737175617265)](https://camo.githubusercontent.com/9aba4c0cefa700d9e04aa3d26ba818419d07f5f7bb61162306a6ee0c01c885a6/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c6173742d636f6d6d69742f566f6c744167656e742f617765736f6d652d636c617764626f742d736b696c6c733f6c6162656c3d4c617374253230757064617465267374796c653d666c61742d737175617265)
   [![Discord](https://camo.githubusercontent.com/dfb0fd11d00902fc0beda30d3112a0fbdf965f8845f4f34dccccd0fd8e29004c/68747470733a2f2f696d672e736869656c64732e696f2f646973636f72642f313336313535393135333738303139353437382e7376673f6c6162656c3d266c6f676f3d646973636f7264266c6f676f436f6c6f723d66666666666626636f6c6f723d373338394438266c6162656c436f6c6f723d364137454332)](https://s.voltagent.dev/discord)
   [![GitHub forks](https://camo.githubusercontent.com/6bde8bb9f274f547671c6359292575d7733c5515052eb05fceb0ba846fc1e872/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f666f726b732f566f6c744167656e742f617765736f6d652d636c617764626f742d736b696c6c733f7374796c653d736f6369616c)](https://github.com/VoltAgent/awesome-claude-skills/network/members)
  
  Awesome OpenClaw(Moltbot(Clawdbot)) Skills
  ==========================================
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#awesome-openclawmoltbotclawdbot-skills)
  
  OpenClaw (previously known as Moltbot, originally Clawdbot... identity crisis included, no extra charge) is a locally-running AI assistant that operates directly on your machine. Skills extend its capabilities, allowing it to interact with external services, automate workflows, and perform specialized tasks. This collection helps you discover and install the right skills for your needs.
  
  Skills in this list are sourced from [OpenClaw](https://clawdhub.com/)
   (OpenClaw's public skills registry) and categorized for easier discovery.
  
  These skills follow the Agent Skill convention develop by Anthropic, an open standard for AI coding assistants.
  
  Installation
  ------------
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#installation)
  
  ### ClawdHub CLI
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#clawdhub-cli)
  
  > **Note:** As you probably know, they keep renaming things. This reflects the current official docs. We'll update this when they rename it again.
  
  ```shell
  npx clawdhub@latest install <skill-slug>
  ```
  
  ### Manual Installation
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#manual-installation)
  
  Copy the skill folder to one of these locations:
  
  | Location | Path |
  | --- | --- |
  | Global | `~/.openclaw/skills/` |
  | Workspace | `<project>/skills/` |
  
  Priority: Workspace > Local > Bundled
  
  Table of Contents
  -----------------
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#table-of-contents)
  
  *   [Web & Frontend Development](https://github.com/VoltAgent/awesome-openclaw-skills#web--frontend-development)
       (14)
  *   [Coding Agents & IDEs](https://github.com/VoltAgent/awesome-openclaw-skills#coding-agents--ides)
       (15)
  *   [Git & GitHub](https://github.com/VoltAgent/awesome-openclaw-skills#git--github)
       (9)
  *   [DevOps & Cloud](https://github.com/VoltAgent/awesome-openclaw-skills#devops--cloud)
       (41)
  *   [Browser & Automation](https://github.com/VoltAgent/awesome-openclaw-skills#browser--automation)
       (11)
  *   [Image & Video Generation](https://github.com/VoltAgent/awesome-openclaw-skills#image--video-generation)
       (19)
  *   [Apple Apps & Services](https://github.com/VoltAgent/awesome-openclaw-skills#apple-apps--services)
       (14)
  *   [Search & Research](https://github.com/VoltAgent/awesome-openclaw-skills#search--research)
       (23)
  *   [Clawdbot Tools](https://github.com/VoltAgent/awesome-openclaw-skills#clawdbot-tools)
       (17)
  *   [CLI Utilities](https://github.com/VoltAgent/awesome-openclaw-skills#cli-utilities)
       (41)
  *   [Marketing & Sales](https://github.com/VoltAgent/awesome-openclaw-skills#marketing--sales)
       (42)
  *   [Productivity & Tasks](https://github.com/VoltAgent/awesome-openclaw-skills#productivity--tasks)
       (42)
  *   [AI & LLMs](https://github.com/VoltAgent/awesome-openclaw-skills#ai--llms)
       (38)
  *   [Finance](https://github.com/VoltAgent/awesome-openclaw-skills#finance)
       (29)
  *   [Media & Streaming](https://github.com/VoltAgent/awesome-openclaw-skills#media--streaming)
       (29)
  *   [Notes & PKM](https://github.com/VoltAgent/awesome-openclaw-skills#notes--pkm)
       (44)
  *   [iOS & macOS Development](https://github.com/VoltAgent/awesome-openclaw-skills#ios--macos-development)
       (13)
  *   [Transportation](https://github.com/VoltAgent/awesome-openclaw-skills#transportation)
       (34)
  *   [Personal Development](https://github.com/VoltAgent/awesome-openclaw-skills#personal-development)
       (27)
  *   [Health & Fitness](https://github.com/VoltAgent/awesome-openclaw-skills#health--fitness)
       (26)
  *   [Communication](https://github.com/VoltAgent/awesome-openclaw-skills#communication)
       (26)
  *   [Speech & Transcription](https://github.com/VoltAgent/awesome-openclaw-skills#speech--transcription)
       (21)
  *   [Smart Home & IoT](https://github.com/VoltAgent/awesome-openclaw-skills#smart-home--iot)
       (31)
  *   [Shopping & E-commerce](https://github.com/VoltAgent/awesome-openclaw-skills#shopping--e-commerce)
       (22)
  *   [Calendar & Scheduling](https://github.com/VoltAgent/awesome-openclaw-skills#calendar--scheduling)
       (16)
  *   [PDF & Documents](https://github.com/VoltAgent/awesome-openclaw-skills#pdf--documents)
       (12)
  *   [Self-Hosted & Automation](https://github.com/VoltAgent/awesome-openclaw-skills#self-hosted--automation)
       (11)
  *   [Security & Passwords](https://github.com/VoltAgent/awesome-openclaw-skills#security--passwords)
       (6)
  
    
  [![social](https://private-user-images.githubusercontent.com/18739364/540268501-4c40affa-8e20-443a-9ec5-1abb6679b170.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NzAwMDk0ODQsIm5iZiI6MTc3MDAwOTE4NCwicGF0aCI6Ii8xODczOTM2NC81NDAyNjg1MDEtNGM0MGFmZmEtOGUyMC00NDNhLTllYzUtMWFiYjY2NzliMTcwLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNjAyMDIlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjYwMjAyVDA1MTMwNFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWM4ZTQ1ZjdkYTMwN2U4YjRkYTc3NzQyMWQ3ZmFjNTZhMWNjNjEwM2VhMTA2MDAwZmU4M2I3ZWYwZjcxOTU1N2QmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.DQfKhKQYXjj95wiFjgmfHq_FBBq8xPjz93ieA8XCYv0)](https://github.com/VoltAgent/voltagent)
    
  
  ### Web & Frontend Development
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#web--frontend-development)
  
  *   [discord](https://github.com/openclaw/skills/tree/main/skills/steipete/discord/SKILL.md)
       - Use when you need to control Discord from Clawdbot via the discord tool: send messages, react.
  *   [frontend-design](https://github.com/openclaw/skills/tree/main/skills/steipete/frontend-design/SKILL.md)
       - Create distinctive, production-grade frontend interfaces with high design quality.
  *   [linux-service-triage](https://github.com/openclaw/skills/tree/main/skills/kowl64/linux-service-triage/SKILL.md)
       - Diagnoses common Linux service issues using logs, systemd/PM2, file permissions.
  *   [miniflux-news](https://github.com/openclaw/skills/tree/main/skills/hartlco/miniflux-news/SKILL.md)
       - Fetch and triage the latest unread RSS/news entries from a Miniflux instance.
  *   [pinak-frontend-guru](https://github.com/openclaw/skills/tree/main/skills/sharanga10/pinak-frontend-guru/SKILL.md)
       - Expert UI/UX and React performance auditor (PinakBot persona).
  *   [remotion-best-practices](https://github.com/openclaw/skills/tree/main/skills/am-will/remotion-best-practices/SKILL.md)
       - Best practices for Remotion - Video creation in React.
  *   [remotion-server](https://github.com/openclaw/skills/tree/main/skills/mvanhorn/remotion-server/SKILL.md)
       - Headless video rendering with Remotion. Works on any Linux server - no Mac or GUI needed.
  *   [slack](https://github.com/openclaw/skills/tree/main/skills/steipete/slack/SKILL.md)
       - Use when you need to control Slack from Clawdbot via the slack tool.
  *   [ui-audit](https://github.com/openclaw/skills/tree/main/skills/tommygeoco/ui-audit/SKILL.md)
       - AI skill for automated UI audits. Evaluate interfaces against proven UX principles.
  *   [ui-skills](https://github.com/openclaw/skills/tree/main/skills/correctroadh/ui-skills/SKILL.md)
       - Opinionated constraints for building better interfaces with agents.
  *   [ux-audit](https://github.com/openclaw/skills/tree/main/skills/tommygeoco/ux-audit/SKILL.md)
       - AI skill for automated design audits. Evaluate interfaces against proven UX principles.
  *   [ux-decisions](https://github.com/openclaw/skills/tree/main/skills/tommygeoco/ux-decisions/SKILL.md)
       - AI skill for the Making UX Decisions framework (uxdecisions.com) by Tommy Geoco.
  *   [vercel-react-best-practices](https://github.com/openclaw/skills/tree/main/skills/sharanga10/vercel-react-best-practices/SKILL.md)
       - React and Next.js performance optimization guidelines from Vercel Engineering.
  *   [web-design-guidelines](https://github.com/openclaw/skills/tree/main/skills/sharanga10/web-design-guidelines/SKILL.md)
       - Review UI code for Web Interface Guidelines compliance.
  
  ### Coding Agents & IDEs
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#coding-agents--ides)
  
  *   [agentlens](https://github.com/openclaw/skills/tree/main/skills/nguyenphutrong/agentlens/SKILL.md)
       - Navigate and understand codebases using agentlens hierarchical documentation.
  *   [claude-team](https://github.com/openclaw/skills/tree/main/skills/jalehman/claude-team/SKILL.md)
       - Orchestrate multiple Claude Code workers via iTerm2 using the claude-team MCP server.
  *   [codex-account-switcher](https://github.com/openclaw/skills/tree/main/skills/odrobnik/codex-account-switcher/SKILL.md)
       - Manage multiple OpenAI Codex accounts. Capture current login tokens.
  *   [codex-monitor](https://github.com/openclaw/skills/tree/main/skills/odrobnik/codex-monitor/SKILL.md)
       - Browse OpenAI Codex session logs stored in ~/.codex/sessions.
  *   [codex-orchestration](https://github.com/openclaw/skills/tree/main/skills/shanelindsay/codex-orchestration/SKILL.md)
       - General-purpose orchestration for Codex.
  *   [codex-quota](https://github.com/openclaw/skills/tree/main/skills/odrobnik/codex-quota/SKILL.md)
       - Check OpenAI Codex CLI rate limit status (daily/weekly quotas) using local session logs.
  *   [codexmonitor](https://github.com/openclaw/skills/tree/main/skills/odrobnik/codexmonitor/SKILL.md)
       - List/inspect/watch local OpenAI Codex sessions (CLI + VS Code)
  *   [coding-agent](https://github.com/openclaw/skills/tree/main/skills/steipete/coding-agent/SKILL.md)
       - Run Codex CLI, Claude Code, OpenCode, or Pi Coding Agent.
  *   [cursor-agent](https://github.com/openclaw/skills/tree/main/skills/swiftlysingh/cursor-agent/SKILL.md)
       - A comprehensive skill for using the Cursor CLI agent.
  *   [factory-ai](https://github.com/openclaw/skills/tree/main/skills/mitchellbernstein/factory-ai/SKILL.md)
       - Use Factory AI's droid CLI for software engineering tasks.
  *   [model-usage](https://github.com/openclaw/skills/tree/main/skills/steipete/model-usage/SKILL.md)
       - Use CodexBar CLI local cost usage to summarize per-model usage for Codex.
  *   [opencode-acp-control](https://github.com/openclaw/skills/tree/main/skills/bjesuiter/opencode-acp-control/SKILL.md)
       - Control OpenCode directly via the Agent Client Protocol (ACP).
  *   [perry-coding-agents](https://github.com/openclaw/skills/tree/main/skills/gricha/perry-coding-agents/SKILL.md)
       - Dispatch coding tasks to OpenCode or Claude Code on Perry workspaces.
  *   [perry-workspaces](https://github.com/openclaw/skills/tree/main/skills/gricha/perry-workspaces/SKILL.md)
       - Create and manage isolated Docker workspaces on your tailnet with Claude Code.
  *   [prompt-log](https://github.com/openclaw/skills/tree/main/skills/thesash/prompt-log/SKILL.md)
       - Extract conversation transcripts from AI coding session logs (Clawdbot, Claude Code, Codex).
  
  ### Git & GitHub
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#git--github)
  
  *   [conventional-commits](https://github.com/openclaw/skills/tree/main/skills/bastos/conventional-commits/SKILL.md)
       - Format commit messages using the Conventional Commits specification.
  *   [deepwiki](https://github.com/openclaw/skills/tree/main/skills/arun-8687/deepwiki/SKILL.md)
       - Query the DeepWiki MCP server for GitHub repository documentation, wiki structure.
  *   [deepwork-tracker](https://github.com/openclaw/skills/tree/main/skills/adunne09/deepwork-tracker/SKILL.md)
       - Track deep work sessions locally (start/stop/status)
  *   [deploy-agent](https://github.com/openclaw/skills/tree/main/skills/sherajdev/deploy-agent/SKILL.md)
       - Multi-step deployment agent for full-stack apps.
  *   [github](https://github.com/openclaw/skills/tree/main/skills/steipete/github/SKILL.md)
       - Interact with GitHub using the `gh` CLI.
  *   [github-pr](https://github.com/openclaw/skills/tree/main/skills/dbhurley/github-pr/SKILL.md)
       - Fetch, preview, merge, and test GitHub PRs locally.
  *   [gitload](https://github.com/openclaw/skills/tree/main/skills/waldekmastykarz/gitload/SKILL.md)
       - Download files or folders from GitHub without cloning the entire repo.
  *   [pr-commit-workflow](https://github.com/openclaw/skills/tree/main/skills/joshp123/pr-commit-workflow/SKILL.md)
       - This skill should be used when creating commits or pull requests.
  *   [read-github](https://github.com/openclaw/skills/tree/main/skills/am-will/read-github/SKILL.md)
       - Read GitHub repos via gitmcp.io with semantic search and LLM-optimized output.
  
  ### DevOps & Cloud
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#devops--cloud)
  
  *   [Azure CLI](https://github.com/openclaw/skills/tree/main/skills/ddevaal/azure-cli/SKILL.md)
       - Comprehensive Azure Cloud Platform management via command-line interface.
      
  *   [cloudflare](https://github.com/openclaw/skills/tree/main/skills/asleep123/wrangler/SKILL.md)
       - Manage Cloudflare Workers, KV, D1, R2, and secrets using the Wrangler CLI.
      
  *   [coolify](https://github.com/openclaw/skills/tree/main/skills/visiongeist/coolify/SKILL.md)
       - Manage Coolify deployments, applications, databases, and services via the Coolify API.
      
  *   [digital-ocean](https://github.com/openclaw/skills/tree/main/skills/dbhurley/digital-ocean/SKILL.md)
       - Manage Digital Ocean droplets, domains, and infrastructure via DO API.
      
  *   [dokploy](https://github.com/openclaw/skills/tree/main/skills/joshuarileydev/dokploy/SKILL.md)
       - Manage Dokploy deployments, projects, applications, and domains via the Dokploy API.
      
  *   [domain-dns-ops](https://github.com/openclaw/skills/tree/main/skills/steipete/domain-dns-ops/SKILL.md)
       - Domain/DNS ops across Cloudflare, DNSimple, and Namecheap.
      
  *   [domaindetails](https://github.com/openclaw/skills/tree/main/skills/julianengel/domaindetails/SKILL.md)
       - Look up domain WHOIS/RDAP info and check marketplace listings. Free API, no auth required.
      
  *   [exa-plus](https://github.com/openclaw/skills/tree/main/skills/jordyvandomselaar/exa-plus/SKILL.md)
       - Neural web search via Exa AI. Search people, companies, news, research, code.
      
  *   [exe-dev](https://github.com/openclaw/skills/tree/main/skills/bjesuiter/exe-dev/SKILL.md)
       - Manage persistent VMs on exe.dev. Create VMs, configure HTTP proxies, share access.
      
  *   [hetzner](https://github.com/openclaw/skills/tree/main/skills/thesethrose/hetzner/SKILL.md)
       - Hetzner Cloud server management using the hcloud CLI.
      
  *   [hetzner-cloud](https://github.com/openclaw/skills/tree/main/skills/pasogott/hetzner-cloud/SKILL.md)
       - Hetzner Cloud CLI for managing servers, volumes, firewalls, networks, DNS, and snapshots.
      
  *   [Joan Workflow](https://github.com/openclaw/skills/tree/main/skills/donny-son/joan-workflow/SKILL.md)
       - This skill should be used when the user asks about "joan", "pods", "workspace", "domain knowledge".
      
  *   [komodo](https://github.com/openclaw/skills/tree/main/skills/weird-aftertaste/komodo/SKILL.md)
       - Manage Komodo infrastructure - servers, Docker deployments, stacks, builds, and procedures.
      
  *   [kubectl-skill](https://github.com/openclaw/skills/tree/main/skills/ddevaal/kubectl/SKILL.md)
       - Execute and manage Kubernetes clusters via kubectl commands.
      
  *   [linearis](https://github.com/openclaw/skills/tree/main/skills/whoisnnamdi/linearis/SKILL.md)
       - Linear.app CLI for issue tracking. Use for listing, creating, updating.
      
  *   [npm-proxy](https://github.com/openclaw/skills/tree/main/skills/weird-aftertaste/npm-proxy/SKILL.md)
       - Manage Nginx Proxy Manager (NPM) hosts, certificates, and access lists.
      
  *   [portainer](https://github.com/openclaw/skills/tree/main/skills/asteinberger/portainer/SKILL.md)
       - Control Docker containers and stacks via Portainer API.
      
  *   [premium-domains](https://github.com/openclaw/skills/tree/main/skills/julianengel/premium-domains/SKILL.md)
       - Search for premium domains for sale across Afternic, Sedo, Atom, Dynadot, Namecheap, NameSilo.
      
  *   [private-connect](https://github.com/openclaw/skills/tree/main/skills/dantelex/private-connect/SKILL.md)
       - Access private services by name, from anywhere. No VPN or SSH tunnels.
      
  *   [proxmox](https://github.com/openclaw/skills/tree/main/skills/weird-aftertaste/proxmox/SKILL.md)
       - Manage Proxmox VE clusters via REST API.
      
  *   [proxmox-full](https://github.com/openclaw/skills/tree/main/skills/msarheed/proxmox-full/SKILL.md)
       - Complete Proxmox VE management - create/clone/start/stop VMs.
      
  *   [Send Me My Files - R2 upload with short lived signed urls](https://github.com/openclaw/skills/tree/main/skills/julianengel/r2-upload/SKILL.md)
       - Upload files to Cloudflare R2, AWS S3, or any S3-compatible storage.
      
  *   [servicenow-agent](https://github.com/openclaw/skills/tree/main/skills/thesethrose/servicenow-agent/SKILL.md)
       - Read-only CLI access to ServiceNow Table, Attachment, Aggregate.
      
  *   [servicenow-docs](https://github.com/openclaw/skills/tree/main/skills/thesethrose/servicenow-docs/SKILL.md)
       - Search and retrieve ServiceNow documentation, release notes.
      
  *   [supabase](https://github.com/openclaw/skills/tree/main/skills/stopmoclay/supabase/SKILL.md)
       - Connect to Supabase for database operations, vector search, and storage.
      
  *   [sysadmin-toolbox](https://github.com/openclaw/skills/tree/main/skills/jdrhyne/sysadmin-toolbox/SKILL.md)
       - Tool discovery and shell one-liner reference for sysadmin, DevOps, and security tasks.
      
  *   [tailscale](https://github.com/openclaw/skills/tree/main/skills/jmagar/tailscale/SKILL.md)
       - Manage Tailscale tailnet via CLI and API.
      
  *   [tailscale-serve](https://github.com/openclaw/skills/tree/main/skills/snopoke/tailscale-serve/SKILL.md)
       - tailscale-serve
      
  *   [tavily](https://github.com/openclaw/skills/tree/main/skills/bert-builder/tavily/SKILL.md)
       - AI-optimized web search using Tavily Search API.
      
  *   [unraid](https://github.com/openclaw/skills/tree/main/skills/jmagar/unraid/SKILL.md)
       - Query and monitor Unraid servers via the GraphQL API.
      
  *   [uptime-kuma](https://github.com/openclaw/skills/tree/main/skills/msarheed/uptime-kuma/SKILL.md)
       - Interact with Uptime Kuma monitoring server.
      
  *   [vercel](https://github.com/openclaw/skills/tree/main/skills/thesethrose/vercel/SKILL.md)
       - Deploy applications and manage projects with complete CLI reference.
      
  *   [vercel-deploy](https://github.com/openclaw/skills/tree/main/skills/sharanga10/vercel-deploy-claimable/SKILL.md)
       - Deploy applications and websites to Vercel.
      
  *   [pi-admin](https://github.com/openclaw/skills/tree/main/skills/thesethrose/pi-admin/SKILL.md)
       - Raspberry Pi system administration. Monitor resources, manage services, perform updates.
      
  *   [k8s-skills](https://github.com/openclaw/skills/tree/main/skills/rohitg00)
       - 6 Kubernetes skills: autoscaling (HPA/VPA/KEDA), backup (Velero), multi-cluster, Cluster API, cert-manager, dashboard browser.
      
  *   [kubernetes](https://github.com/openclaw/skills/tree/main/skills/kcns008/kubernetes/SKILL.md)
       - Comprehensive Kubernetes and OpenShift cluster management.
      
  *   [flyio-cli](https://github.com/openclaw/skills/tree/main/skills/justinburdett/flyio-cli/SKILL.md)
       - Fly.io deploy, logs, SSH, secrets, scaling, and Postgres management.
      
  *   [nomad](https://github.com/openclaw/skills/tree/main/skills/danfedick/nomad/SKILL.md)
       - Query HashiCorp Nomad clusters: jobs, nodes, allocations, services.
      
  *   [pm2](https://github.com/openclaw/skills/tree/main/skills/asteinberger/pm2/SKILL.md)
       - Manage Node.js apps with PM2 process manager.
      
  *   [cloudflare](https://github.com/openclaw/skills/tree/main/skills/dbhurley/cloudflare/SKILL.md)
       - Cloudflare CLI: DNS records, cache purge, Workers routes.
      
  *   [tmux-agents](https://github.com/openclaw/skills/tree/main/skills/cuba6112/tmux-agents/SKILL.md)
       - Manage background coding agents in tmux sessions.
      
  
  ### Browser & Automation
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#browser--automation)
  
  *   [Agent Browser](https://github.com/openclaw/skills/tree/main/skills/thesethrose/agent-browser/SKILL.md)
       - A fast Rust-based headless browser automation CLI with Node.js fallback that enables AI agents to.
  *   [browsh](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/browsh/SKILL.md)
       - A modern text-based browser. Renders web pages in the terminal using headless Firefox.
  *   [browser-use](https://github.com/openclaw/skills/tree/main/skills/shawnpana/browser-use/SKILL.md)
       - Cloud-based browser automation with managed sessions and autonomous task execution.
  *   [context7](https://github.com/openclaw/skills/tree/main/skills/am-will/context7-api/SKILL.md)
       - |.
  *   [guru-mcp](https://github.com/openclaw/skills/tree/main/skills/pvoo/guru-mcp/SKILL.md)
       - Access Guru knowledge base via MCP - ask AI questions, search documents, create drafts.
  *   [mcporter](https://github.com/openclaw/skills/tree/main/skills/steipete/mcporter/SKILL.md)
       - Use the mcporter CLI to list, configure, auth, and call MCP servers/tools directly (HTTP.
  *   [verify-on-browser](https://github.com/openclaw/skills/tree/main/skills/myestery/verify-on-browser/SKILL.md)
       - Control browser via Chrome DevTools Protocol - full CDP access.
  *   [playwright-cli](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/playwright-cli/SKILL.md)
       - Browser automation via Playwright CLI for testing and scraping.
  *   [tekin](https://github.com/openclaw/skills/tree/main/skills/gwqwghksvq-sketch/tekin/SKILL.md)
       - Rust-based headless browser CLI with Node.js fallback.
  *   [agent-browser](https://github.com/openclaw/skills/tree/main/skills/murphykobe/agent-browser-2/SKILL.md)
       - Web testing, form filling, screenshots, data extraction.
  *   [agent-zero](https://github.com/openclaw/skills/tree/main/skills/dowingard/agent-zero-bridge/SKILL.md)
       - Delegate tasks to Agent Zero autonomous coding framework.
  
  ### Image & Video Generation
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#image--video-generation)
  
  *   [clinkding](https://github.com/openclaw/skills/tree/main/skills/daveonkels/clinkding/SKILL.md)
       - Manage linkding bookmarks - save URLs, search, tag, organize.
  *   [coloring-page](https://github.com/openclaw/skills/tree/main/skills/borahm/coloring-page/SKILL.md)
       - Turn an uploaded photo into a printable black-and-white coloring page.
  *   [comfy-cli](https://github.com/openclaw/skills/tree/main/skills/johntheyoung/comfy-cli/SKILL.md)
       - Install, manage, and run ComfyUI instances.
  *   [Excalidraw Flowchart](https://github.com/openclaw/skills/tree/main/skills/swiftlysingh/excalidraw-flowchart/SKILL.md)
       - Create Excalidraw flowcharts from descriptions.
  *   [gamma](https://github.com/openclaw/skills/tree/main/skills/stopmoclay/gamma/SKILL.md)
       - Generate AI-powered presentations, documents, and social posts using Gamma.app API.
  *   [krea-api](https://github.com/openclaw/skills/tree/main/skills/fossilizedcarlos/krea-api/SKILL.md)
       - Generate images via Krea.ai API (Flux, Imagen, Ideogram, Seedream, etc.).
  *   [meshy-ai](https://github.com/openclaw/skills/tree/main/skills/sabatesduran/clawdbot-meshyai-skill/SKILL.md)
       - Use the Meshy.ai REST API to generate assets: (1) text-to-2d (Meshy Text to Image)
  *   [vap-media](https://clawdhub.com/skills/vap-media)
       - AI image, video, and music generation via VAP API. Flux, Veo 3.1, Suno V5 with transparent pricing.
  *   [veo](https://github.com/openclaw/skills/tree/main/skills/buddyh/veo/SKILL.md)
       - Generate video using Google Veo (Veo 3.1 / Veo 3.0).
  *   [video-frames](https://github.com/openclaw/skills/tree/main/skills/steipete/video-frames/SKILL.md)
       - Extract frames or short clips from videos using ffmpeg.
  *   [cad-agent](https://github.com/clawdbot/skills/tree/main/skills/clawd-maf/cad-agent/SKILL.md)
       - Rendering server for AI agents doing CAD work. Send build123d commands, receive rendered images.
  *   [figma](https://github.com/openclaw/skills/tree/main/skills/maddiedreese/figma/SKILL.md)
       - Figma design analysis, asset export, accessibility audit.
  *   [venice-ai](https://github.com/openclaw/skills/tree/main/skills/nhannah/venice-ai-media/SKILL.md)
       - Venice AI: image/video generation, upscaling, AI editing.
  *   [pollinations](https://github.com/openclaw/skills/tree/main/skills/isaacgounton/pollinations/SKILL.md)
       - Pollinations.ai: text, images, videos, audio with 25+ models.
  *   [reve-ai](https://github.com/openclaw/skills/tree/main/skills/dpaluy/reve-ai/SKILL.md)
       - Reve AI image generation, editing, and remixing.
  *   [vap-media](https://github.com/openclaw/skills/tree/main/skills/elestirelbilinc-sketch/vap-media/SKILL.md)
       - AI media generation: Flux, Veo 3.1, Suno V5.
  *   [gifhorse](https://github.com/openclaw/skills/tree/main/skills/coyote-git/gifhorse/SKILL.md)
       - Search video dialogue and create reaction GIFs with subtitles.
  *   [superdesign](https://github.com/openclaw/skills/tree/main/skills/mpociot/superdesign/SKILL.md)
       - Expert frontend design guidelines for modern UIs.
  *   [comfyui](https://github.com/openclaw/skills/tree/main/skills/xtopher86/comfyui-request/SKILL.md)
       - Send workflow requests to ComfyUI and get image results.
  *   [fal-ai](https://github.com/openclaw/skills/tree/main/skills/agmmnn/fal-ai/SKILL.md)
       - Generate images, videos and audio using Fal.ai's generative media API.
  
  ### Apple Apps & Services
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#apple-apps--services)
  
  *   [apple-contacts](https://github.com/openclaw/skills/tree/main/skills/tyler6204/apple-contacts/SKILL.md)
       - Look up contacts from macOS Contacts.app.
  *   [apple-music](https://github.com/openclaw/skills/tree/main/skills/tyler6204/apple-music/SKILL.md)
       - Search Apple Music, add songs to library, manage playlists, control playback and AirPlay.
  *   [apple-photos](https://github.com/openclaw/skills/tree/main/skills/tyler6204/apple-photos/SKILL.md)
       - Apple Photos.app integration for macOS. List albums, browse photos, search by date/person/content.
  *   [get-focus-mode](https://github.com/openclaw/skills/tree/main/skills/nickchristensen/get-focus-mode/SKILL.md)
       - Get the current macOS Focus mode.
  *   [healthkit-sync](https://github.com/openclaw/skills/tree/main/skills/mneves75/healthkit-sync/SKILL.md)
       - iOS HealthKit data sync CLI commands and patterns.
  *   [homebrew](https://github.com/openclaw/skills/tree/main/skills/thesethrose/homebrew/SKILL.md)
       - Homebrew package manager for macOS. Search, install, manage, and troubleshoot packages and casks.
  *   [icloud-findmy](https://github.com/openclaw/skills/tree/main/skills/liamnichols/icloud-findmy/SKILL.md)
       - Query Find My locations and battery status for family devices via iCloud.
  *   [media-backup](https://github.com/openclaw/skills/tree/main/skills/dbhurley/media-backup/SKILL.md)
       - Archive Clawdbot conversation media (photos, videos) to a local folder.
  *   [mole-mac-cleanup](https://github.com/openclaw/skills/tree/main/skills/bjesuiter/mole-mac-cleanup/SKILL.md)
       - Mac cleanup & optimization tool combining CleanMyMac, AppCleaner, DaisyDisk features.
  *   [shortcuts-generator](https://github.com/openclaw/skills/tree/main/skills/erik-agens/shortcuts-skill/SKILL.md)
       - Generate macOS/iOS Shortcuts by creating plist files.
  *   [apple-remind-me](https://github.com/openclaw/skills/tree/main/skills/plgonzalezrx8/apple-remind-me/SKILL.md)
       - Natural language reminders via Apple Reminders.app.
  *   [apple-mail-search](https://github.com/openclaw/skills/tree/main/skills/mneves75/apple-mail-search/SKILL.md)
       - Fast Apple Mail search via SQLite (~50ms vs 8+ min).
  *   [alter-actions](https://github.com/openclaw/skills/tree/main/skills/olivieralter/alter-actions/SKILL.md)
       - Trigger 84+ Alter macOS app actions via x-callback-urls.
  *   [voice-wake-say](https://github.com/openclaw/skills/tree/main/skills/xadenryan/voice-wake-say/SKILL.md)
       - Speak responses aloud on macOS via the say command.
  
  ### Search & Research
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#search--research)
  
  *   [brave-search](https://github.com/openclaw/skills/tree/main/skills/steipete/brave-search/SKILL.md)
       - Web search and content extraction via Brave Search API.
  *   [brightdata](https://github.com/openclaw/skills/tree/main/skills/meirkad/bright-data/SKILL.md)
       - Web scraping and search via Bright Data API.
  *   [clawdbot-logs](https://github.com/openclaw/skills/tree/main/skills/satriapamudji/clawdbot-logs/SKILL.md)
       - Analyze Clawdbot logs and diagnostics. Use when the user asks about bot performance.
  *   [exa](https://github.com/openclaw/skills/tree/main/skills/fardeenxyz/exa/SKILL.md)
       - Neural web search and code context via Exa AI API. Requires EXA\_API\_KEY.
  *   [kagi-search](https://github.com/openclaw/skills/tree/main/skills/silversteez/kagi-search/SKILL.md)
       - Web search using Kagi Search API. Use when you need to search the web.
  *   [literature-review](https://github.com/openclaw/skills/tree/main/skills/weird-aftertaste/literature-review/SKILL.md)
       - Assistance with writing literature reviews by searching for academic sources.
  *   [parallel](https://github.com/openclaw/skills/tree/main/skills/mvanhorn/parallel/SKILL.md)
       - High-accuracy web search and research via Parallel.ai API.
  *   [seo-audit](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/seo-audit/SKILL.md)
       - When the user wants to audit, review, or diagnose SEO issues on their site.
  *   [spots](https://github.com/openclaw/skills/tree/main/skills/foeken/spots/SKILL.md)
       - Exhaustive Google Places search using grid-based scanning.
  *   [tavily](https://github.com/openclaw/skills/tree/main/skills/arun-8687/tavily-search/SKILL.md)
       - AI-optimized web search via Tavily API. Returns concise, relevant results for AI agents.
  *   [tweet-writer](https://github.com/openclaw/skills/tree/main/skills/sanky369/tweet-writer/SKILL.md)
       - Write viral, persuasive, engaging tweets and threads.
  *   [web-search-plus](https://github.com/openclaw/skills/tree/main/skills/robbyczgw-cla/web-search-plus/SKILL.md)
       - Unified search skill with Intelligent Auto-Routing.
  *   [seo-analytics](https://github.com/openclaw/skills/tree/main/skills/adamkristopher)
       - 3 SEO/analytics skills: DataForSEO keywords, GA4 + Search Console, YouTube analytics.
  *   [last30days](https://github.com/openclaw/skills/tree/main/skills/zats/last30days/SKILL.md)
       - Research any topic from last 30 days on Reddit, X, and web.
  *   [youtube-summarizer](https://github.com/openclaw/skills/tree/main/skills/abe238/youtube-summarizer/SKILL.md)
       - Fetch YouTube transcripts and generate structured summaries.
  *   [gemini-yt-transcript](https://github.com/openclaw/skills/tree/main/skills/odrobnik/gemini-yt-video-transcript/SKILL.md)
       - YouTube transcript via Google Gemini with speaker labels.
  *   [arxiv-watcher](https://github.com/openclaw/skills/tree/main/skills/rubenfb23/arxiv-watcher/SKILL.md)
       - Search and summarize papers from ArXiv.
  *   [serpapi](https://github.com/openclaw/skills/tree/main/skills/ianpcook/serpapi/SKILL.md)
       - Unified search across Google, Amazon, Yelp, OpenTable, Walmart.
  *   [grok-search](https://github.com/openclaw/skills/tree/main/skills/notabhay/grok-search/SKILL.md)
       - Search web or X/Twitter using xAI Grok.
  *   [perplexity](https://github.com/openclaw/skills/tree/main/skills/dronnick/perplexity-bash/SKILL.md)
       - Perplexity API for web-grounded search with citations.
  *   [parallel](https://github.com/openclaw/skills/tree/main/skills/pntrivedy/parallel-1-0-1/SKILL.md)
       - Parallel.ai web search optimized for AI agents.
  *   [searxng](https://github.com/openclaw/skills/tree/main/skills/abk234/searxng/SKILL.md)
       - Privacy-respecting metasearch via local SearXNG instance.
  *   [news-aggregator](https://github.com/openclaw/skills/tree/main/skills/cclank/news-aggregator-skill/SKILL.md)
       - News from 8 sources: Hacker News, GitHub Trending, Product Hunt, and more.
  
  ### Clawdbot Tools
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#clawdbot-tools)
  
  *   [agent-browser](https://github.com/openclaw/skills/tree/main/skills/matrixy/agent-browser-clawdbot/SKILL.md)
       - Headless browser automation CLI optimized for AI agents with accessibility tree snapshots.
  *   [auto-updater](https://github.com/openclaw/skills/tree/main/skills/maximeprades/auto-updater/SKILL.md)
       - Automatically update Clawdbot and all installed skills once daily.
  *   [claude-code-usage](https://github.com/openclaw/skills/tree/main/skills/azaidi94/claude-code-usage/SKILL.md)
       - Check Claude Code OAuth usage limits (session & weekly quotas).
  *   [claude-connect](https://github.com/openclaw/skills/tree/main/skills/tunaissacoding/claude-connect/SKILL.md)
       - Connect Claude to Clawdbot instantly and keep it connected 24/7.
  *   [clawd-modifier](https://github.com/openclaw/skills/tree/main/skills/masonc15/clawd-modifier/SKILL.md)
       - Modify Clawd, the Claude Code mascot. Use this skill when users want to customize Clawd's.
  *   [clawdbot-documentation-expert](https://github.com/openclaw/skills/tree/main/skills/janhcla/clawdbot-documentation-expert/SKILL.md)
       - clawdbot-documentation-expert
  *   [clawdbot-skill-update](https://github.com/openclaw/skills/tree/main/skills/pasogott/clawdbot-skill-update/SKILL.md)
       - Comprehensive backup, update, and restore workflow with dynamic workspace detection.
  *   [clawdbot-workspace-template-review](https://github.com/openclaw/skills/tree/main/skills/xadenryan/clawdbot-skill-clawdbot-workspace-template-review/SKILL.md)
       - Compare a Clawdbot workspace against the official templates installed with Clawdbot (npm.
  *   [clawddocs](https://github.com/openclaw/skills/tree/main/skills/nicholasspisak/clawddocs/SKILL.md)
       - Clawdbot documentation expert with decision tree navigation, search scripts, doc fetching.
  *   [clawdhub](https://github.com/openclaw/skills/tree/main/skills/steipete/clawdhub/SKILL.md)
       - Use the ClawdHub CLI to search, install, update, and publish agent skills from clawdhub.com.
  *   [clawdlink](https://github.com/openclaw/skills/tree/main/skills/davemorin/clawdlink/SKILL.md)
       - Encrypted Clawdbot-to-Clawdbot messaging.
  *   [skills-audit](https://github.com/openclaw/skills/tree/main/skills/morozred/skill-audit/SKILL.md)
       - Audit locally installed agent skills for security/policy issues.
  *   [skills-search](https://github.com/openclaw/skills/tree/main/skills/thesethrose/skills-search/SKILL.md)
       - Search skills.sh registry from CLI. Find and discover agent skills from the skills.sh ecosystem.
  *   [git-notes-memory](https://github.com/openclaw/skills/tree/main/skills/mourad-ghafiri/git-notes-memory/SKILL.md)
       - Git-notes based persistent memory across sessions.
  *   [triple-memory](https://github.com/openclaw/skills/tree/main/skills/ktpriyatham/triple-memory/SKILL.md)
       - LanceDB + Git-Notes + file-based memory system.
  *   [self-reflect](https://github.com/openclaw/skills/tree/main/skills/stevengonsalvez/self-reflect/SKILL.md)
       - Self-improvement through conversation analysis and learning.
  *   [mcporter-skill](https://github.com/openclaw/skills/tree/main/skills/livvux/mcporter-skill/SKILL.md)
       - List, configure, auth, and call MCP servers/tools via mcporter CLI.
  
  ### CLI Utilities
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#cli-utilities)
  
  *   [bible](https://github.com/openclaw/skills/tree/main/skills/dbhurley/bible-votd/SKILL.md)
       - Get the Bible.com Verse of the Day with shareable image.
  *   [camsnap](https://github.com/openclaw/skills/tree/main/skills/steipete/camsnap/SKILL.md)
       - Capture frames or clips from RTSP/ONVIF cameras.
  *   [canvas-lms](https://github.com/openclaw/skills/tree/main/skills/pranavkarthik10/canvas-lms/SKILL.md)
       - Access Canvas LMS (Instructure) for course data, assignments, grades, and submissions.
  *   [Cat Fact](https://github.com/openclaw/skills/tree/main/skills/thesethrose/catfact/SKILL.md)
       - Random cat facts and breed information from catfact.ninja (free, no API key).
  *   [content-advisory](https://github.com/openclaw/skills/tree/main/skills/dbhurley/content-advisory/SKILL.md)
       - Lookup detailed content ratings for movies and TV shows (sex/nudity, violence/gore.
  *   [create-cli](https://github.com/openclaw/skills/tree/main/skills/steipete/create-cli/SKILL.md)
       - Design CLI arguments, flags, subcommands, and help text.
  *   [data-reconciliation-exceptions](https://github.com/openclaw/skills/tree/main/skills/kowl64/data-reconciliation-exceptions/SKILL.md)
       - Reconciles data sources using stable identifiers (Pay Number, driving licence, driver card.
  *   [dilbert](https://github.com/openclaw/skills/tree/main/skills/hjanuschka/dilbert/SKILL.md)
       - dilbert
  *   [dropbox](https://github.com/openclaw/skills/tree/main/skills/ryanlisse/dropbox/SKILL.md)
       - dropbox
  *   [duckdb-en](https://github.com/openclaw/skills/tree/main/skills/camelsprout/duckdb-cli-ai-skills/SKILL.md)
       - DuckDB CLI specialist for SQL analysis, data processing and file conversion.
  *   [entr](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/entr/SKILL.md)
       - Run arbitrary commands when files change. Useful for watching files and triggering builds or tests.
  *   [gifgrep](https://github.com/openclaw/skills/tree/main/skills/steipete/gifgrep/SKILL.md)
       - Search GIF providers with CLI/TUI, download results, and extract stills/sheets.
  *   [goplaces](https://github.com/openclaw/skills/tree/main/skills/steipete/goplaces/SKILL.md)
       - Query Google Places API (New) via the goplaces CLI for text search, place details, resolve.
  *   [journal-to-post](https://github.com/openclaw/skills/tree/main/skills/itsflow/journal-to-post/SKILL.md)
       - Convert personal journal entries into shareable social media posts.
  *   [jq](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/jq/SKILL.md)
       - Command-line JSON processor. Extract, filter, transform JSON.
  *   [local-places](https://github.com/openclaw/skills/tree/main/skills/steipete/local-places/SKILL.md)
       - Search for places (restaurants, cafes, etc.) via Google Places API proxy on localhost.
  *   [native-app-performance](https://github.com/openclaw/skills/tree/main/skills/steipete/native-app-performance/SKILL.md)
       - Native macOS/iOS app performance profiling via xctrace/Time Profiler.
  *   [office-quotes](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/office-quotes/SKILL.md)
       - Generate random quotes from The Office (US).
  *   [parcel-package-tracking](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/parcel-package-tracking/SKILL.md)
       - Track and add deliveries via Parcel API.
  *   [peekaboo](https://github.com/openclaw/skills/tree/main/skills/steipete/peekaboo/SKILL.md)
       - Capture and automate macOS UI with the Peekaboo CLI.
  *   [portable-tools](https://github.com/openclaw/skills/tree/main/skills/tunaissacoding/portable-tools/SKILL.md)
       - Build cross-device tools without hardcoding paths or account names.
  *   [post-at](https://github.com/openclaw/skills/tree/main/skills/krausefx/post-at/SKILL.md)
       - Manage Austrian Post (post.at) deliveries - list packages, check delivery status.
  *   [process-watch](https://github.com/openclaw/skills/tree/main/skills/dbhurley/process-watch/SKILL.md)
       - Monitor system processes - CPU, memory, disk I/O, network, open files, ports.
  *   [sag](https://github.com/openclaw/skills/tree/main/skills/steipete/sag/SKILL.md)
       - ElevenLabs text-to-speech with mac-style say UX.
  *   [shorten](https://github.com/openclaw/skills/tree/main/skills/kesslerio/shorten/SKILL.md)
       - Shorten URLs using is.gd (no auth required). Returns a permanent short link.
  *   [simple-backup](https://github.com/openclaw/skills/tree/main/skills/vacinc/simple-backup/SKILL.md)
       - Backup agent brain (workspace) and body (state) to local folder.
  *   [smalltalk](https://github.com/openclaw/skills/tree/main/skills/johnmci/smalltalk/SKILL.md)
       - Interact with live Smalltalk image (Cuis or Squeak).
  *   [songsee](https://github.com/openclaw/skills/tree/main/skills/steipete/songsee/SKILL.md)
       - Generate spectrograms and feature-panel visualizations from audio with the songsee CLI.
  *   [steam](https://github.com/openclaw/skills/tree/main/skills/mjrussell/steam/SKILL.md)
       - Browse, filter, and discover games in a Steam library.
  *   [sudoku](https://github.com/openclaw/skills/tree/main/skills/odrobnik/sudoku/SKILL.md)
       - Fetch Sudoku puzzles and store them as JSON in the workspace; render images on demand; reveal.
  *   [tldr](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/tldr/SKILL.md)
       - Simplified man pages from tldr-pages. Use this to quickly understand CLI tools.
  *   [tmdb](https://github.com/openclaw/skills/tree/main/skills/dbhurley/tmdb/SKILL.md)
       - Search movies/TV, get cast, ratings, streaming info, and personalized recommendations via TMDb API.
  *   [tmux](https://github.com/openclaw/skills/tree/main/skills/steipete/tmux/SKILL.md)
       - Remote-control tmux sessions for interactive CLIs by sending keystrokes and scraping pane output.
  *   [track17](https://github.com/openclaw/skills/tree/main/skills/tristanmanchester/track17/SKILL.md)
       - Track parcels via the 17TRACK API (local SQLite DB, polling + optional webhook ingestion).
  *   [units](https://github.com/openclaw/skills/tree/main/skills/asleep123/units/SKILL.md)
       - Perform unit conversions and calculations using GNU Units.
  *   [voicenotes](https://github.com/openclaw/skills/tree/main/skills/shawnhansen/voicenotes/SKILL.md)
       - Sync and access voice notes from Voicenotes.com.
  *   [xkcd](https://github.com/openclaw/skills/tree/main/skills/dbhurley/xkcd/SKILL.md)
       - Fetch xkcd comics - latest, random, by number, or search by keyword.
  *   [ecto](https://github.com/openclaw/skills/tree/main/skills/visionik/ecto/SKILL.md)
       - Ghost.io blog management via Admin API.
  *   [domain](https://github.com/openclaw/skills/tree/main/skills/abtdomain/domain/SKILL.md)
       - Domain intelligence: NRDS keyword search and NS reverse lookup.
  *   [george](https://github.com/openclaw/skills/tree/main/skills/odrobnik/george/SKILL.md)
       - George online banking automation (Erste Bank / Sparkasse Austria).
  *   [emredoganer-fizzy](https://github.com/openclaw/skills/tree/main/skills/emredoganer/emredoganer-fizzy-cli/SKILL.md)
       - Manage Fizzy Kanban boards and cards via CLI.
  
  ### iOS & macOS Development
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#ios--macos-development)
  
  *   [apple-docs](https://github.com/openclaw/skills/tree/main/skills/thesethrose/apple-docs/SKILL.md)
       - Query Apple Developer Documentation, APIs, and WWDC videos (2014-2025).
  *   [apple-docs-mcp](https://github.com/openclaw/skills/tree/main/skills/janhcla/apple-docs-mcp/SKILL.md)
       - apple-docs-mcp
  *   [instruments-profiling](https://github.com/openclaw/skills/tree/main/skills/steipete/instruments-profiling/SKILL.md)
       - Use when profiling native macOS or iOS apps with Instruments/xctrace.
  *   [ios-simulator](https://github.com/openclaw/skills/tree/main/skills/tristanmanchester/ios-simulator/SKILL.md)
       - Automate iOS Simulator workflows (simctl + idb): create/boot/erase devices, install/launch apps.
  *   [macos-spm-app-packaging](https://github.com/openclaw/skills/tree/main/skills/dimillian/macos-spm-app-packaging/SKILL.md)
       - Scaffold, build, and package SwiftPM-based macOS apps without an Xcode project.
  *   [PagerKit](https://github.com/openclaw/skills/tree/main/skills/szpakkamil/pagerkit/SKILL.md)
       - Expert guidance on PagerKit, a SwiftUI library for advanced, customizable page-based navigation.
  *   [sfsymbol-generator](https://github.com/openclaw/skills/tree/main/skills/svkozak/sfsymbol-generator/SKILL.md)
       - Generate an Xcode SF Symbol asset catalog .symbolset from an SVG.
  *   [swift-concurrency-expert](https://github.com/openclaw/skills/tree/main/skills/steipete/swift-concurrency-expert/SKILL.md)
       - Swift Concurrency review and remediation for Swift 6.2+.
  *   [swiftui-empty-app-init](https://github.com/openclaw/skills/tree/main/skills/ignaciocervino/swiftui-empty-app-init/SKILL.md)
       - Initialize a minimal SwiftUI iOS app in the current directory by generating a single `.xcodeproj`.
  *   [swiftui-liquid-glass](https://github.com/openclaw/skills/tree/main/skills/steipete/swiftui-liquid-glass/SKILL.md)
       - Implement, review, or improve SwiftUI features using the iOS 26+ Liquid Glass API.
  *   [swiftui-performance-audit](https://github.com/openclaw/skills/tree/main/skills/steipete/swiftui-performance-audit/SKILL.md)
       - Audit and improve SwiftUI runtime performance from code review and architecture.
  *   [swiftui-ui-patterns](https://github.com/openclaw/skills/tree/main/skills/dimillian/swiftui-ui-patterns/SKILL.md)
       - Best practices and example-driven guidance for building SwiftUI views and components.
  *   [swiftui-view-refactor](https://github.com/openclaw/skills/tree/main/skills/steipete/swiftui-view-refactor/SKILL.md)
       - Refactor and review SwiftUI view files for consistent structure, dependency injection.
  
  ### Marketing & Sales
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#marketing--sales)
  
  *   [ab-test-setup](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/ab-test-setup/SKILL.md)
       - When the user wants to plan, design, or implement an A/B test or experiment.
  *   [apollo](https://github.com/openclaw/skills/tree/main/skills/jhumanj/apollo/SKILL.md)
       - Interact with Apollo.io REST API (people/org enrichment, search, lists).
  *   [basecamp-cli](https://github.com/openclaw/skills/tree/main/skills/emredoganer/basecamp-cli/SKILL.md)
       - Manage Basecamp (via bc3 API / 37signals Launchpad) projects, to-dos, messages.
  *   [bearblog](https://github.com/openclaw/skills/tree/main/skills/azade-c/bearblog/SKILL.md)
       - Create and manage blog posts on Bear Blog (bearblog.dev).
  *   [bird](https://github.com/openclaw/skills/tree/main/skills/steipete/bird/SKILL.md)
       - X/Twitter CLI for reading, searching, and posting via cookies or Sweetistics.
  *   [bluesky](https://github.com/openclaw/skills/tree/main/skills/jeffaf/bluesky/SKILL.md)
       - Read, post, and interact with Bluesky (AT Protocol) via CLI.
  *   [competitor-alternatives](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/competitor-alternatives/SKILL.md)
       - When the user wants to create competitor comparison or alternative pages for SEO.
  *   [copy-editing](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/copy-editing/SKILL.md)
       - When the user wants to edit, review, or improve existing marketing copy.
  *   [copywriting](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/copywriting/SKILL.md)
       - When the user wants to write, rewrite, or improve marketing copy.
  *   [email-sequence](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/email-sequence/SKILL.md)
       - When the user wants to create or optimize an email sequence, drip campaign, automated email flow.
  *   [form-cro](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/form-cro/SKILL.md)
       - When the user wants to optimize any form that is NOT signup/registration — including lead capture.
  *   [free-tool-strategy](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/free-tool-strategy/SKILL.md)
       - When the user wants to plan, evaluate, or build a free tool.
  *   [ga4](https://github.com/openclaw/skills/tree/main/skills/jdrhyne/ga4/SKILL.md)
       - Query Google Analytics 4 (GA4) data via the Analytics Data API.
  *   [gong](https://github.com/openclaw/skills/tree/main/skills/jdrhyne/gong/SKILL.md)
       - Gong API for searching calls, transcripts, and conversation intelligence.
  *   [google-ads](https://github.com/openclaw/skills/tree/main/skills/jdrhyne/google-ads/SKILL.md)
       - Query, audit, and optimize Google Ads campaigns.
  *   [gsc](https://github.com/openclaw/skills/tree/main/skills/jdrhyne/gsc/SKILL.md)
       - Query Google Search Console for SEO data - search queries, top pages, CTR opportunities.
  *   [hubspot](https://github.com/openclaw/skills/tree/main/skills/kwall1/hubspot/SKILL.md)
       - HubSpot CRM and CMS API integration for contacts, companies, deals, owners, and content management.
  *   [humanizer](https://github.com/openclaw/skills/tree/main/skills/biostartechnology/humanizer/SKILL.md)
       - |.
  *   [marketing-mode](https://github.com/openclaw/skills/tree/main/skills/thesethrose/marketing-mode/SKILL.md)
       - Marketing Mode combines 23 comprehensive marketing skills covering strategy, psychology, content.
  *   [marketing-psychology](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/marketing-psychology/SKILL.md)
       - When the user wants to apply psychological principles, mental models.
  *   [marketing-skills](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/SKILL.md)
       - TL;DR: 23 marketing playbooks (CRO, SEO, copy, analytics, experiments, pricing, launches, ads.
  *   [otter](https://github.com/openclaw/skills/tree/main/skills/dbhurley/otter/SKILL.md)
       - Otter.ai transcription CLI - list, search, download, and sync meeting transcripts to CRM.
  *   [paywall-upgrade-cro](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/paywall-upgrade-cro/SKILL.md)
       - When the user wants to create or optimize in-app paywalls, upgrade screens, upsell modals.
  *   [pinch-to-post](https://github.com/openclaw/skills/tree/main/skills/nickhamze/pinch-to-post/SKILL.md)
       - WordPress automation for Clawdbot. Manage posts, pages, WooCommerce products, orders, inventory.
  *   [popup-cro](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/popup-cro/SKILL.md)
       - When the user wants to create or optimize popups, modals, overlays, slide-ins.
  *   [pricing-strategy](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/pricing-strategy/SKILL.md)
       - When the user wants help with pricing decisions, packaging, or monetization strategy.
  *   [programmatic-seo](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/programmatic-seo/SKILL.md)
       - When the user wants to create SEO-driven pages at scale using templates and data.
  *   [reddit](https://github.com/openclaw/skills/tree/main/skills/theglove44/reddit/SKILL.md)
       - Browse, search, post, and moderate Reddit.
  *   [reddit-search](https://github.com/openclaw/skills/tree/main/skills/thesethrose/reddit-search/SKILL.md)
       - Search Reddit for subreddits and get information about them.
  *   [referral-program](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/referral-program/SKILL.md)
       - When the user wants to create, optimize, or analyze a referral program, affiliate program.
  *   [schema-markup](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/schema-markup/SKILL.md)
       - When the user wants to add, fix, or optimize schema markup and structured data on their site.
  *   [signup-flow-cro](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/signup-flow-cro/SKILL.md)
       - When the user wants to optimize signup, registration, account creation, or trial activation flows.
  *   [solobuddy](https://github.com/openclaw/skills/tree/main/skills/humanji7/solobuddy/SKILL.md)
       - Build-in-public companion for indie hackers — content workflow, Twitter engagement.
  *   [twenty-crm](https://github.com/openclaw/skills/tree/main/skills/jhumanj/twenty-crm/SKILL.md)
       - Interact with Twenty CRM (self-hosted) via REST/GraphQL.
  *   [typefully](https://github.com/openclaw/skills/tree/main/skills/thesethrose/typefully/SKILL.md)
       - |.
  *   [x-article-editor](https://github.com/openclaw/skills/tree/main/skills/jchopard69/x-article-editor/SKILL.md)
       - TL;DR: Turn a topic or draft into a high-engagement X Article. STEP 1 final copy/paste article.
  *   [shashwatgtm-skills](https://github.com/openclaw/skills/tree/main/skills/shashwatgtm)
       - B2B marketing: competitive intelligence, content writing, newsletters, personal branding, social media management.
  *   [sales-toolkit](https://github.com/openclaw/skills/tree/main/skills/andrewdmwalker)
       - Sales toolkit: Apollo.io enrichment, Attio CRM, PhantomBuster automation, Firecrawl web scraping.
  *   [octolens](https://github.com/openclaw/skills/tree/main/skills/garrrikkotua/octolens/SKILL.md)
       - Brand mention tracking across Twitter, Reddit, GitHub, LinkedIn with sentiment analysis.
  *   [geo-optimization](https://github.com/openclaw/skills/tree/main/skills/andrewdmwalker/geo-optimization/SKILL.md)
       - Optimize content for AI search visibility (ChatGPT, Perplexity, Claude).
  *   [recruitment-automation](https://github.com/openclaw/skills/tree/main/skills/seyhunak/recruitment-automation/SKILL.md)
       - Automated recruitment: job specs, candidate evaluation, outreach emails.
  *   [late-api](https://github.com/openclaw/skills/tree/main/skills/mikipalet/late-api/SKILL.md)
       - Late API for scheduling posts across 13 social media platforms.
  
  ### Productivity & Tasks
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#productivity--tasks)
  
  *   [clawd-docs-v2](https://github.com/openclaw/skills/tree/main/skills/aranej/clawd-docs-v2/SKILL.md)
       - Smart ClawdBot documentation access with local search index, cached snippets, and on-demand fetch.
  *   [clickup-mcp](https://github.com/openclaw/skills/tree/main/skills/pvoo/clickup-mcp/SKILL.md)
       - Manage ClickUp tasks, docs, time tracking, comments, chat, and search via official MCP.
  *   [dex](https://github.com/openclaw/skills/tree/main/skills/gricha/dex/SKILL.md)
       - Task tracking for async/multi-step work.
  *   [dexcom](https://github.com/openclaw/skills/tree/main/skills/chris-clem/dexcom/SKILL.md)
       - Monitor blood glucose via Dexcom G7/G6 CGM.
  *   [dexter](https://github.com/openclaw/skills/tree/main/skills/igorhvr/dexter/SKILL.md)
       - Autonomous financial research agent for stock analysis, financial statements, metrics, prices.
  *   [dvsa-tc-audit-readiness-operator-licence-uk](https://github.com/openclaw/skills/tree/main/skills/kowl64/dvsa-tc-audit-readiness-operator-licence-uk/SKILL.md)
       - Builds DVSA/Traffic Commissioner “show me” audit readiness checklists and evidence indexes.
  *   [gno](https://github.com/openclaw/skills/tree/main/skills/gmickel/gno/SKILL.md)
       - Search local documents, files, notes, and knowledge bases.
  *   [jira](https://github.com/openclaw/skills/tree/main/skills/jdrhyne/jira/SKILL.md)
       - Manage Jira issues, boards, sprints, and projects via the jira-cli.
  *   [linear](https://github.com/openclaw/skills/tree/main/skills/manuelhettich/linear/SKILL.md)
       - Query and manage Linear issues, projects, and team workflows.
  *   [morning-manifesto](https://github.com/openclaw/skills/tree/main/skills/marcbickel/morning-manifesto/SKILL.md)
       - Daily morning reflection workflow with task sync to Obsidian, Apple Reminders, and Linear.
  *   [plan-my-day](https://github.com/openclaw/skills/tree/main/skills/itsflow/plan-my-day/SKILL.md)
       - Generate an energy-optimized, time-blocked daily plan.
  *   [prd](https://github.com/openclaw/skills/tree/main/skills/bjesuiter/prd/SKILL.md)
       - Create and manage Product Requirements Documents (PRDs).
  *   [prowlarr](https://github.com/openclaw/skills/tree/main/skills/jmagar/prowlarr/SKILL.md)
       - Search indexers and manage Prowlarr. Use when the user asks to "search.
  *   [qmd](https://github.com/openclaw/skills/tree/main/skills/steipete/qmd/SKILL.md)
       - Local search/indexing CLI (BM25 + vectors + rerank) with MCP mode.
  *   [samsung-smart-tv](https://github.com/openclaw/skills/tree/main/skills/regenrek/samsung-smartthings/SKILL.md)
       - Control Samsung TVs via SmartThings (OAuth app + device control).
  *   [task](https://github.com/openclaw/skills/tree/main/skills/amirbrooks/task/SKILL.md)
       - Tasker docstore task management via tool-dispatch.
  *   [task-tracker](https://github.com/openclaw/skills/tree/main/skills/kesslerio/task-tracker/SKILL.md)
       - Personal task management with daily standups and weekly reviews.
  *   [things-mac](https://github.com/openclaw/skills/tree/main/skills/steipete/things-mac/SKILL.md)
       - Manage Things 3 via the `things` CLI on macOS (add/update projects+todos.
  *   [ticktick](https://github.com/openclaw/skills/tree/main/skills/manuelhettich/ticktick/SKILL.md)
       - Manage TickTick tasks and projects from the command line with OAuth2 auth, batch operations.
  *   [timesheet](https://github.com/openclaw/skills/tree/main/skills/florianrauscha/timesheet/SKILL.md)
       - Track time, manage projects and tasks using timesheet.io CLI.
  *   [todo-tracker](https://github.com/openclaw/skills/tree/main/skills/jdrhyne/todo-tracker/SKILL.md)
       - Persistent TODO scratch pad for tracking tasks across sessions.
  *   [todoist](https://github.com/openclaw/skills/tree/main/skills/mjrussell/todoist/SKILL.md)
       - Manage tasks and projects in Todoist. Use when user asks about tasks, to-dos, reminders.
  *   [topydo](https://github.com/openclaw/skills/tree/main/skills/bastos/topydo/SKILL.md)
       - Manage todo.txt tasks using topydo CLI. Add, list, complete, prioritize, tag.
  *   [trello](https://github.com/openclaw/skills/tree/main/skills/steipete/trello/SKILL.md)
       - Manage Trello boards, lists, and cards via the Trello REST API.
  *   [vikunja](https://github.com/openclaw/skills/tree/main/skills/dbhurley/vikunja/SKILL.md)
       - Manage projects and tasks in Vikunja, an open-source project management tool.
  *   [vikunja-fast](https://github.com/openclaw/skills/tree/main/skills/tmigone/vikunja-fast/SKILL.md)
       - Manage Vikunja projects and tasks (overdue/due/today), mark done.
  *   [web-perf](https://github.com/openclaw/skills/tree/main/skills/elithrar/web-perf/SKILL.md)
       - Analyzes web performance using Chrome DevTools MCP.
  *   [withings-health](https://github.com/openclaw/skills/tree/main/skills/hisxo/withings-health/SKILL.md)
       - Fetches health data from the Withings API including weight, body composition (fat, muscle, bone.
  *   [outlook](https://github.com/openclaw/skills/tree/main/skills/jotamed/outlook/SKILL.md)
       - Outlook email and calendar via Microsoft Graph API.
  *   [imap-email](https://github.com/openclaw/skills/tree/main/skills/mvarrieur/imap-email/SKILL.md)
       - Read and manage email via IMAP (ProtonMail, Gmail, etc.).
  *   [google-workspace](https://github.com/openclaw/skills/tree/main/skills/dru-ca/google-workspace-mcp/SKILL.md)
       - Gmail, Calendar, Drive with simple OAuth sign-in.
  *   [gogcli](https://github.com/openclaw/skills/tree/main/skills/luccast/gogcli/SKILL.md)
       - Google Workspace CLI: Gmail, Calendar, Drive, Sheets, Docs, Slides.
  *   [ticktick](https://github.com/openclaw/skills/tree/main/skills/kaiofreitas/ticktick-tasks/SKILL.md)
       - TickTick task manager: projects, tasks, reminders.
  *   [omnifocus](https://github.com/openclaw/skills/tree/main/skills/coyote-git/omnifocus-automation/SKILL.md)
       - OmniFocus tasks, projects, and GTD workflows via Omni Automation.
  *   [todoist](https://github.com/openclaw/skills/tree/main/skills/2mawi2/todoist-task-manager/SKILL.md)
       - Todoist CLI: list, add, modify, complete, delete tasks.
  *   [taskleef](https://github.com/openclaw/skills/tree/main/skills/xatter/taskleef/SKILL.md)
       - Taskleef.com todos, projects, and kanban boards.
  *   [linear-issues](https://github.com/openclaw/skills/tree/main/skills/emrekilinc/linear-issues/SKILL.md)
       - Linear issue tracking: create, update, list, search issues.
  *   [jira](https://github.com/openclaw/skills/tree/main/skills/kyjus25/clawdbot-jira-skill/SKILL.md)
       - Jira issues, transitions, and worklogs via REST API.
  *   [atlassian-mcp](https://github.com/openclaw/skills/tree/main/skills/atakanermis/atlassian-mcp/SKILL.md)
       - Atlassian MCP: Jira and Confluence integration via Docker.
  *   [asana](https://github.com/openclaw/skills/tree/main/skills/k0nkupa/asana/SKILL.md)
       - Asana tasks, projects, and workspaces via REST API.
  *   [mogcli](https://github.com/openclaw/skills/tree/main/skills/visionik/mogcli/SKILL.md)
       - Microsoft 365 CLI: Mail, Calendar, Drive, Word, Excel, OneNote.
  
  ### AI & LLMs
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#ai--llms)
  
  *   [antigravity-quota](https://github.com/openclaw/skills/tree/main/skills/mukhtharcm/antigravity-quota/SKILL.md)
       - Check Antigravity account quotas for Claude and Gemini models.
  *   [ask-questions-if-underspecified](https://github.com/openclaw/skills/tree/main/skills/lc0rp/ask-questions-if-underspecified/SKILL.md)
       - Clarify requirements before implementing. Do not use automatically, only when invoked explicitly.
  *   [claude-oauth-refresher](https://github.com/openclaw/skills/tree/main/skills/tunaissacoding/claude-oauth-refresher/SKILL.md)
       - Keep your Claude access token fresh 24/7.
  *   [council](https://github.com/openclaw/skills/tree/main/skills/emasoudy/council/SKILL.md)
       - Council Chamber orchestration with Memory Bridge.
  *   [de-ai-ify](https://github.com/openclaw/skills/tree/main/skills/itsflow/de-ai-ify/SKILL.md)
       - Remove AI-generated jargon and restore human voice to text.
  *   [gemini](https://github.com/openclaw/skills/tree/main/skills/steipete/gemini/SKILL.md)
       - Gemini CLI for one-shot Q&A, summaries, and generation.
  *   [gemini-computer-use](https://github.com/openclaw/skills/tree/main/skills/am-will/gemini-computer-use/SKILL.md)
       - Build and run Gemini 2.5 Computer Use browser-control agents with Playwright.
  *   [gemini-deep-research](https://github.com/openclaw/skills/tree/main/skills/arun-8687/gemini-deep-research/SKILL.md)
       - Perform complex, long-running research tasks using Gemini Deep Research Agent.
  *   [gemini-stt](https://github.com/openclaw/skills/tree/main/skills/araa47/gemini-stt/SKILL.md)
       - Transcribe audio files using Google's Gemini API or Vertex AI.
  *   [llm-council](https://github.com/openclaw/skills/tree/main/skills/am-will/llm-council/SKILL.md)
       - Orchestrate multi-LLM councils to produce and merge implementation plans.
  *   [lmstudio-subagents](https://github.com/openclaw/skills/tree/main/skills/t-sinclair2500/lm-studio-subagents/SKILL.md)
       - Equips agents to search for and offload tasks to local models in LM Studio.
  *   [minimax-usage](https://github.com/openclaw/skills/tree/main/skills/thesethrose/minimax-usage/SKILL.md)
       - Monitor Minimax Coding Plan usage to stay within API limits.
  *   [model-router](https://github.com/openclaw/skills/tree/main/skills/digitaladaption/model-router/SKILL.md)
       - A comprehensive AI model routing system that automatically selects the optimal model for any task.
  *   [nano-banana-pro](https://github.com/openclaw/skills/tree/main/skills/steipete/nano-banana-pro/SKILL.md)
       - Generate/edit images with Nano Banana Pro (Gemini 3 Pro Image).
  *   [openai-docs-skill](https://github.com/openclaw/skills/tree/main/skills/am-will/openai-docs/SKILL.md)
       - Query the OpenAI developer documentation via the OpenAI Docs MCP server using CLI (curl/jq).
  *   [openai-image-gen](https://github.com/openclaw/skills/tree/main/skills/steipete/openai-image-gen/SKILL.md)
       - Batch-generate images via OpenAI Images API. Random prompt sampler + `index.html` gallery.
  *   [openai-tts](https://github.com/openclaw/skills/tree/main/skills/pors/openai-tts/SKILL.md)
       - Text-to-speech via OpenAI Audio Speech API.
  *   [openrouter-transcribe](https://github.com/openclaw/skills/tree/main/skills/obviyus/openrouter-transcribe/SKILL.md)
       - Transcribe audio files via OpenRouter using audio-capable models (Gemini, GPT-4o-audio, etc).
  *   [oracle](https://github.com/openclaw/skills/tree/main/skills/steipete/oracle/SKILL.md)
       - Use the @steipete/oracle CLI to bundle a prompt plus the right files.
  *   [perplexity](https://github.com/openclaw/skills/tree/main/skills/zats/perplexity/SKILL.md)
       - Search the web with AI-powered answers via Perplexity API.
  *   [personas](https://github.com/openclaw/skills/tree/main/skills/robbyczgw-cla/personas/SKILL.md)
       - Transform into 31 specialized AI personalities on demand.
  *   [pi-orchestration](https://github.com/openclaw/skills/tree/main/skills/dbhurley/pi-orchestration/SKILL.md)
       - Orchestrate multiple AI models (GLM, MiniMax, etc.) as workers using Pi Coding Agent.
  *   [recipe-to-list](https://github.com/openclaw/skills/tree/main/skills/borahm/recipe-to-list/SKILL.md)
       - Turn recipes into a Todoist Shopping list.
  *   [research](https://github.com/openclaw/skills/tree/main/skills/pors/research/SKILL.md)
       - Deep research via Gemini CLI — runs in background sub-agent so you don't burn your Claude tokens.
  *   [screen-monitor](https://github.com/openclaw/skills/tree/main/skills/emasoudy/screen-monitor/SKILL.md)
       - Dual-mode screen sharing and analysis. Model-agnostic (Gemini/Claude/Qwen3-VL).
  *   [search-x](https://github.com/openclaw/skills/tree/main/skills/mvanhorn/search-x/SKILL.md)
       - Search X/Twitter in real-time using Grok. Find tweets, trends, and discussions with citations.
  *   [self-improvement](https://github.com/openclaw/skills/tree/main/skills/pskoett/self-improving-agent/SKILL.md)
       - Captures learnings, errors, and corrections to enable continuous improvement.
  *   [smart-followups](https://github.com/openclaw/skills/tree/main/skills/robbyczgw-cla/smart-followups/SKILL.md)
       - Generate contextual follow-up suggestions after AI responses.
  *   [xai](https://github.com/openclaw/skills/tree/main/skills/mvanhorn/xai/SKILL.md)
       - Chat with Grok models via xAI API. Supports Grok-3, Grok-3-mini, vision, and more.
  *   [manus](https://github.com/openclaw/skills/tree/main/skills/mvanhorn/manus/SKILL.md)
       - Create and manage AI agent tasks via Manus API.
  *   [hokipoki](https://github.com/openclaw/skills/tree/main/skills/budjoskop/hokipoki/SKILL.md)
       - Switch between Claude, Codex, and Gemini when one gets stuck.
  *   [council-of-the-wise](https://github.com/openclaw/skills/tree/main/skills/jeffaf/council-of-the-wise/SKILL.md)
       - Multi-perspective feedback from spawned sub-agent personas.
  *   [multi-viewpoint-debates](https://github.com/openclaw/skills/tree/main/skills/latentfreedom/multi-viewpoint-debates/SKILL.md)
       - Debate decisions from multiple worldviews to expose blind spots.
  *   [chaos-lab](https://github.com/openclaw/skills/tree/main/skills/jbbottoms/chaos-lab/SKILL.md)
       - AI alignment exploration through conflicting optimization targets.
  *   [ralph-loop](https://github.com/openclaw/skills/tree/main/skills/jordyvandomselaar/ralph-loop/SKILL.md)
       - Generate bash scripts for AI agent loops (Codex, Claude, OpenCode).
  *   [research-tracker](https://github.com/openclaw/skills/tree/main/skills/julian1645/research-tracker/SKILL.md)
       - Manage autonomous AI research agents with SQLite tracking.
  *   [claude-code-wingman](https://github.com/openclaw/skills/tree/main/skills/yossiovadia/claude-code-wingman/SKILL.md)
       - Run Claude Code as a skill, control from WhatsApp.
  *   [adversarial-prompting](https://github.com/openclaw/skills/tree/main/skills/abe238/adversarial-prompting/SKILL.md)
       - Adversarial analysis to critique, fix, and consolidate solutions.
  
  ### Finance
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#finance)
  
  *   [analytics-tracking](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/analytics-tracking/SKILL.md)
       - When the user wants to set up, improve, or audit analytics tracking and measurement.
  *   [api-credentials-hygiene](https://github.com/openclaw/skills/tree/main/skills/kowl64/api-credentials-hygiene/SKILL.md)
       - Audits and hardens API credential handling (env vars, separation, rotation plan, least privilege.
  *   [app-store-changelog](https://github.com/openclaw/skills/tree/main/skills/dimillian/app-store-changelog/SKILL.md)
       - Create user-facing App Store release notes by collecting.
  *   [clawdbot-release-check](https://github.com/openclaw/skills/tree/main/skills/pors/clawdbot-release-check/SKILL.md)
       - Check for new clawdbot releases and notify once per new version.
  *   [copilot-money](https://github.com/openclaw/skills/tree/main/skills/jayhickey/copilot-money/SKILL.md)
       - Query Copilot Money personal finance data (accounts, transactions, net worth, holdings.
  *   [create-content](https://github.com/openclaw/skills/tree/main/skills/itsflow/create-content/SKILL.md)
       - Thinking partner that transforms ideas into platform-optimized content.
  *   [harvey](https://github.com/openclaw/skills/tree/main/skills/udiedrichsen/harvey/SKILL.md)
       - Harvey is an imaginary friend and conversation companion.
  *   [ibkr-trading](https://github.com/openclaw/skills/tree/main/skills/flokiew/ibkr-trader/SKILL.md)
       - Interactive Brokers (IBKR) trading automation via Client Portal API.
  *   [idea](https://github.com/openclaw/skills/tree/main/skills/andrewjiang/idea/SKILL.md)
       - Launch background Claude sessions to explore and analyze business ideas.
  *   [just-fucking-cancel](https://github.com/openclaw/skills/tree/main/skills/chipagosfinest/just-fucking-cancel/SKILL.md)
       - Analyze bank transaction CSVs to find recurring charges, categorize subscriptions.
  *   [launch-strategy](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/launch-strategy/SKILL.md)
       - When the user wants to plan a product launch, feature announcement, or release strategy.
  *   [marketing-ideas](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/marketing-ideas/SKILL.md)
       - When the user needs marketing ideas, inspiration, or strategies for their SaaS or software product.
  *   [nordpool-fi](https://github.com/openclaw/skills/tree/main/skills/ovaris/nordpool-fi/SKILL.md)
       - Hourly electricity prices for Finland with optimal EV charging window calculation (3h, 4h, 5h).
  *   [openssl](https://github.com/openclaw/skills/tree/main/skills/asleep123/openssl/SKILL.md)
       - Generate secure random strings, passwords, and cryptographic tokens using OpenSSL.
  *   [page-cro](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/page-cro/SKILL.md)
       - When the user wants to optimize, improve, or increase conversions on any marketing page — including.
  *   [plaid](https://github.com/openclaw/skills/tree/main/skills/jverdi/plaid/SKILL.md)
       - plaid-cli a cli for interacting with the plaid finance platform.
  *   [publisher](https://github.com/openclaw/skills/tree/main/skills/tunaissacoding/publisher/SKILL.md)
       - Make your skills easy to understand and impossible to ignore.
  *   [relationship-skills](https://github.com/openclaw/skills/tree/main/skills/jhillin8/relationship-skills/SKILL.md)
       - Improve relationships with communication tools, conflict resolution, and connection ideas.
  *   [solo-cli](https://github.com/openclaw/skills/tree/main/skills/rursache/solo-cli/SKILL.md)
       - Monitor and interact with SOLO.ro accounting platform via CLI.
  *   [swissweather](https://github.com/openclaw/skills/tree/main/skills/xenofex7/swissweather/SKILL.md)
       - Get current weather and forecasts from MeteoSwiss (official Swiss weather service).
  *   [yahoo-finance](https://github.com/openclaw/skills/tree/main/skills/ajanraj/yahoo-finance/SKILL.md)
       - Get stock prices, quotes, fundamentals, earnings, options, dividends.
  *   [ynab](https://github.com/openclaw/skills/tree/main/skills/obviyus/ynab/SKILL.md)
       - Manage YNAB budgets, accounts, categories, and transactions via CLI.
  *   [monarch-money](https://github.com/openclaw/skills/tree/main/skills/davideasaf/monarch-money/SKILL.md)
       - Monarch Money budget management and transaction tracking.
  *   [tax-professional](https://github.com/openclaw/skills/tree/main/skills/scottfo/tax-professional/SKILL.md)
       - US tax advisor, deduction optimizer, and expense tracker.
  *   [card-optimizer](https://github.com/openclaw/skills/tree/main/skills/scottfo/card-optimizer/SKILL.md)
       - Credit card rewards optimizer for cashback, points, and miles.
  *   [watch-my-money](https://github.com/openclaw/skills/tree/main/skills/andreolf/watch-my-money/SKILL.md)
       - Analyze bank transactions, categorize spending, track budgets.
  *   [refund-radar](https://github.com/openclaw/skills/tree/main/skills/andreolf/refund-radar/SKILL.md)
       - Scan bank statements for recurring charges and draft refund requests.
  *   [expense-tracker-pro](https://github.com/openclaw/skills/tree/main/skills/jhillin8/expense-tracker-pro/SKILL.md)
       - Track expenses via natural language with budget summaries.
  *   [financial-market-analysis](https://github.com/openclaw/skills/tree/main/skills/seyhunak/financial-market-analysis/SKILL.md)
       - Stock and market sentiment analysis via Yahoo Finance.
  
  ### Media & Streaming
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#media--streaming)
  
  *   [apple-media](https://github.com/openclaw/skills/tree/main/skills/aaronn/apple-media/SKILL.md)
       - Control Apple TV, HomePod, and AirPlay devices via pyatv (scan, stream, playback, volume.
  *   [blucli](https://github.com/openclaw/skills/tree/main/skills/steipete/blucli/SKILL.md)
       - BluOS CLI (blu) for discovery, playback, grouping, and volume.
  *   [chill-institute](https://github.com/openclaw/skills/tree/main/skills/baanish/chill-institute/SKILL.md)
       - Use chill.institute (web UI) to search for content and click “send to put.io” (best paired.
  *   [chromecast](https://github.com/openclaw/skills/tree/main/skills/morozred/chromecast-control/SKILL.md)
       - Control Chromecast devices on your local network - discover, cast media, control playback.
  *   [lastfm](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/lastfm/SKILL.md)
       - Access Last.fm listening history, music stats, and discovery.
  *   [overseerr](https://github.com/openclaw/skills/tree/main/skills/j1philli/overseerr/SKILL.md)
       - Request movies/TV and monitor request status via the Overseerr API (stable Overseerr.
  *   [pet](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/pet/SKILL.md)
       - Simple command-line snippet manager. Use it to save and reuse complex commands.
  *   [plex](https://github.com/openclaw/skills/tree/main/skills/dbhurley/plex/SKILL.md)
       - Control Plex Media Server - browse libraries, search, play media, manage playback.
  *   [pocket-casts](https://github.com/openclaw/skills/tree/main/skills/manuelhettich/pocket-casts-yt/SKILL.md)
       - Download YouTube videos and upload them to Pocket Casts Files for offline viewing.
  *   [putio](https://github.com/openclaw/skills/tree/main/skills/baanish/putio/SKILL.md)
       - Manage a put.io account via the kaput CLI (transfers, files, search) — hoist the mainsail.
  *   [qbittorrent](https://github.com/openclaw/skills/tree/main/skills/jmagar/qbittorrent/SKILL.md)
       - Manage torrents with qBittorrent. Use when the user asks to "list torrents", "add torrent".
  *   [radarr](https://github.com/openclaw/skills/tree/main/skills/jordyvandomselaar/radarr/SKILL.md)
       - Search and add movies to Radarr. Supports collections, search-on-add option.
  *   [roku](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/roku/SKILL.md)
       - CLI interface to control Roku devices via python-roku.
  *   [sabnzbd](https://github.com/openclaw/skills/tree/main/skills/jmagar/sabnzbd/SKILL.md)
       - Manage Usenet downloads with SABnzbd. Use when the user asks to "check SABnzbd", "list NZB queue".
  *   [sonarr](https://github.com/openclaw/skills/tree/main/skills/jordyvandomselaar/sonarr/SKILL.md)
       - Search and add TV shows to Sonarr. Supports monitor options, search-on-add.
  *   [sonoscli](https://github.com/openclaw/skills/tree/main/skills/steipete/sonoscli/SKILL.md)
       - Control Sonos speakers (discover/status/play/volume/group).
  *   [spotify](https://github.com/openclaw/skills/tree/main/skills/2mawi2/spotify/SKILL.md)
       - Control Spotify playback on macOS. Play/pause, skip tracks, control volume.
  *   [spotify-applescript](https://github.com/openclaw/skills/tree/main/skills/andrewjiang/spotify-applescript/SKILL.md)
       - Control Spotify desktop app via AppleScript.
  *   [spotify-history](https://github.com/openclaw/skills/tree/main/skills/braydoncoyer/spotify-history/SKILL.md)
       - Access Spotify listening history, top artists/tracks.
  *   [spotify-player](https://github.com/openclaw/skills/tree/main/skills/steipete/spotify-player/SKILL.md)
       - Terminal Spotify playback/search via spogo (preferred) or spotify\_player.
  *   [spotify-web-api](https://github.com/openclaw/skills/tree/main/skills/mvanhorn/spotify-web-api/SKILL.md)
       - Spotify control via Web API - playback, history, top tracks, search.
  *   [summarize](https://github.com/openclaw/skills/tree/main/skills/steipete/summarize/SKILL.md)
       - Summarize URLs or files with the summarize CLI (web, PDFs, images, audio, YouTube).
  *   [thinking-partner](https://github.com/openclaw/skills/tree/main/skills/itsflow/thinking-partner/SKILL.md)
       - Collaborative thinking partner for exploring complex problems through questioning.
  *   [trakt](https://github.com/openclaw/skills/tree/main/skills/mjrussell/trakt/SKILL.md)
       - Track and view your watched movies and TV shows via trakt.tv.
  *   [video-transcript-downloader](https://github.com/openclaw/skills/tree/main/skills/steipete/video-transcript-downloader/SKILL.md)
       - Download videos, audio, subtitles, and clean paragraph-style transcripts from YouTube.
  *   [youtube-instant-article](https://github.com/openclaw/skills/tree/main/skills/viticci/youtube-instant-article/SKILL.md)
       - Transform YouTube videos into Telegraph Instant View articles with visual slides.
  *   [youtube-watcher](https://github.com/openclaw/skills/tree/main/skills/michaelgathara/youtube-watcher/SKILL.md)
       - Fetch and read transcripts from YouTube videos.
  *   [ytmusic](https://github.com/openclaw/skills/tree/main/skills/gentrycopsy/ytmusic/SKILL.md)
       - YouTube Music library, playlists, and discovery.
  *   [apple-music](https://github.com/openclaw/skills/tree/main/skills/epheterson/mcp-applemusic/SKILL.md)
       - Apple Music integration via AppleScript or MusicKit API.
  
  ### Notes & PKM
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#notes--pkm)
  
  *   [apple-mail](https://github.com/openclaw/skills/tree/main/skills/tyler6204/apple-mail/SKILL.md)
       - Apple Mail.app integration for macOS. Read inbox, search emails, send emails, reply.
  *   [apple-notes](https://github.com/openclaw/skills/tree/main/skills/steipete/apple-notes/SKILL.md)
       - Manage Apple Notes via the `memo` CLI on macOS (create, view, edit, delete, search, move.
  *   [bear-notes](https://github.com/openclaw/skills/tree/main/skills/steipete/bear-notes/SKILL.md)
       - Create, search, and manage Bear notes via grizzly CLI.
  *   [better-notion](https://github.com/openclaw/skills/tree/main/skills/tyler6204/better-notion/SKILL.md)
       - Full CRUD for Notion pages, databases, and blocks. Create, read, update, delete, search, and query.
  *   [bookstack](https://github.com/openclaw/skills/tree/main/skills/xenofex7/bookstack/SKILL.md)
       - BookStack Wiki & Documentation API integration.
  *   [calctl](https://github.com/openclaw/skills/tree/main/skills/rainbat/calctl/SKILL.md)
       - Manage Apple Calendar events via icalBuddy + AppleScript CLI.
  *   [craft](https://github.com/openclaw/skills/tree/main/skills/noah-ribaudo/craft/SKILL.md)
       - Manage Craft notes, documents, and tasks via CLI.
  *   [fizzy-cli](https://github.com/openclaw/skills/tree/main/skills/tobiasbischoff/fizzy-cli/SKILL.md)
       - Use the fizzy-cli tool to authenticate and manage Fizzy kanban boards, cards, comments, tags.
  *   [gkeep](https://github.com/openclaw/skills/tree/main/skills/vacinc/gkeep/SKILL.md)
       - Google Keep notes via gkeepapi. List, search, create, and manage notes.
  *   [granola](https://github.com/openclaw/skills/tree/main/skills/mvanhorn/granola-notes/SKILL.md)
       - Access Granola AI meeting notes - CSV import, shared note fetching.
  *   [nb](https://github.com/openclaw/skills/tree/main/skills/bjesuiter/nb/SKILL.md)
       - Manage notes, bookmarks, and notebooks using the nb CLI.
  *   [Notebook](https://github.com/openclaw/skills/tree/main/skills/thesethrose/notebook/SKILL.md)
       - Local-first personal knowledge base for tracking ideas, projects, tasks, habits.
  *   [notectl](https://github.com/openclaw/skills/tree/main/skills/rainbat/notectl/SKILL.md)
       - Manage Apple Notes via AppleScript CLI.
  *   [notion](https://github.com/openclaw/skills/tree/main/skills/steipete/notion/SKILL.md)
       - Notion API for creating and managing pages, databases, and blocks.
  *   [obsidian](https://github.com/openclaw/skills/tree/main/skills/steipete/obsidian/SKILL.md)
       - Work with Obsidian vaults (plain Markdown notes) and automate via obsidian-cli.
  *   [obsidian-conversation-backup](https://github.com/openclaw/skills/tree/main/skills/laserducktales/obsidian-conversation-backup/SKILL.md)
       - Automatic conversation backup system for Obsidian with incremental snapshots, hourly breakdowns.
  *   [obsidian-daily](https://github.com/openclaw/skills/tree/main/skills/bastos/obsidian-daily/SKILL.md)
       - Manage Obsidian Daily Notes via obsidian-cli.
  *   [onboarding-cro](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/onboarding-cro/SKILL.md)
       - When the user wants to optimize post-signup onboarding, user activation, first-run experience.
  *   [purelymail](https://github.com/openclaw/skills/tree/main/skills/dbhurley/purelymail/SKILL.md)
       - Set up and test PurelyMail email for Clawdbot agents.
  *   [resend](https://github.com/openclaw/skills/tree/main/skills/mjrussell/resend/SKILL.md)
       - Manage received (inbound) emails and attachments via Resend API.
  *   [second-brain](https://github.com/openclaw/skills/tree/main/skills/christinetyip/second-brain/SKILL.md)
       - Personal knowledge base powered by Ensue for capturing and retrieving understanding.
  *   [shared-memory](https://github.com/openclaw/skills/tree/main/skills/christinetyip/shared-memory/SKILL.md)
       - Share memories and state with other users.
  *   [skillcraft](https://github.com/openclaw/skills/tree/main/skills/jmz1/skillcraft/SKILL.md)
       - Create, design, and package Clawdbot skills.
  *   [sports-ticker](https://github.com/openclaw/skills/tree/main/skills/robbyczgw-cla/sports-ticker/SKILL.md)
       - Live sports alerts for Soccer, NFL, NBA, NHL, MLB, F1 and more.
  *   [reflect](https://github.com/openclaw/skills/tree/main/skills/sergical/reflect/SKILL.md)
       - Append to daily notes and create notes in Reflect app.
  *   [notion-api](https://github.com/openclaw/skills/tree/main/skills/timenotspace/notion-api/SKILL.md)
       - Notion API CLI: search, query databases, create pages.
  *   [granola](https://github.com/openclaw/skills/tree/main/skills/scald/granola/SKILL.md)
       - Access Granola meeting transcripts and notes.
  *   [fabric-api](https://github.com/openclaw/skills/tree/main/skills/tristanmanchester/fabric-api/SKILL.md)
       - Create/search Fabric resources via HTTP API (notepads, folders, bookmarks, files).
  *   [instapaper](https://github.com/openclaw/skills/tree/main/skills/vburojevic/instapaper/SKILL.md)
       - Use when operating the instapaper-cli (ip) tool or troubleshooting it: authenticating.
  *   [karakeep](https://github.com/openclaw/skills/tree/main/skills/jayphen/karakeep/SKILL.md)
       - Manage bookmarks and links in a Karakeep instance.
  *   [linkding](https://github.com/openclaw/skills/tree/main/skills/jmagar/linkding/SKILL.md)
       - Manage bookmarks with Linkding. Use when the user asks to "save a bookmark", "add link".
  *   [readeck](https://github.com/openclaw/skills/tree/main/skills/jayphen/readeck/SKILL.md)
       - Readeck integration for saving and managing articles.
  *   [readwise](https://github.com/openclaw/skills/tree/main/skills/refrigerator/readwise/SKILL.md)
       - Access Readwise highlights and Reader saved articles.
  *   [twitter-bookmark-sync](https://github.com/openclaw/skills/tree/main/skills/tunaissacoding/twitter-bookmark-sync/SKILL.md)
       - Automatically ranks your Twitter bookmarks daily and delivers a curated reading list.
  *   [raindrop](https://github.com/openclaw/skills/tree/main/skills/velvet-shark/raindrop/SKILL.md)
       - Raindrop.io bookmarks: search, list, add, organize with tags.
  *   [substack-formatter](https://github.com/openclaw/skills/tree/main/skills/maddiedreese/substack-formatter/SKILL.md)
       - Transform text into Substack article format with HTML formatting.
  *   [bbc-news](https://github.com/openclaw/skills/tree/main/skills/ddrayne/bbc-news/SKILL.md)
       - Fetch and display BBC News stories from various sections and regions via RSS feeds.
  *   [blogwatcher](https://github.com/openclaw/skills/tree/main/skills/steipete/blogwatcher/SKILL.md)
       - Monitor blogs and RSS/Atom feeds for updates using the blogwatcher CLI.
  *   [hn](https://github.com/openclaw/skills/tree/main/skills/dbhurley/hn/SKILL.md)
       - Browse Hacker News - top stories, new, best, ask, show, jobs, and story details with comments.
  *   [hn-digest](https://github.com/openclaw/skills/tree/main/skills/cpojer/hn-digest/SKILL.md)
       - Fetch and send Hacker News front-page posts on demand.
  *   [miniflux](https://github.com/openclaw/skills/tree/main/skills/shekohex/miniflux/SKILL.md)
       - Browse, read, and manage Miniflux feed articles.
  *   [news-summary](https://github.com/openclaw/skills/tree/main/skills/joargp/news-summary/SKILL.md)
       - This skill should be used when the user asks for news updates, daily briefings.
  *   [newsletter-digest](https://github.com/openclaw/skills/tree/main/skills/jhillin8/newsletter-digest/SKILL.md)
       - Summarize newsletters and articles, extract key insights, create reading lists.
  *   [orf-digest](https://github.com/openclaw/skills/tree/main/skills/cpojer/orf/SKILL.md)
       - On-demand ORF news digest in German. Use when the user says 'orf', 'pull orf', or 'orf 10'.
  
  ### Transportation
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#transportation)
  
  *   [anachb](https://github.com/openclaw/skills/tree/main/skills/manmal/a-nach-b/SKILL.md)
       - Austrian public transport (VOR AnachB) for all of Austria.
  *   [charger](https://github.com/openclaw/skills/tree/main/skills/borahm/charger/SKILL.md)
       - Check EV charger availability (favorites, nearby search) via Google Places.
  *   [flight-tracker](https://github.com/openclaw/skills/tree/main/skills/xenofex7/flight-tracker/SKILL.md)
       - Flight tracking and scheduling. Track live flights in real-time by region, callsign.
  *   [flights](https://github.com/openclaw/skills/tree/main/skills/dbhurley/flights/SKILL.md)
       - Track flight status, delays, and search routes. Uses FlightAware data.
  *   [gotrain](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/gotrain/SKILL.md)
       - MTA system train departures (NYC Subway, LIRR, Metro-North).
  *   [incident-pcn-evidence-appeal-corrective-actions-uk](https://github.com/openclaw/skills/tree/main/skills/kowl64/incident-pcn-evidence-appeal-corrective-actions-uk/SKILL.md)
       - Builds incident/PCN evidence packs with timelines, appeal drafts, corrective actions.
  *   [mbta](https://github.com/openclaw/skills/tree/main/skills/dbhurley/mbta/SKILL.md)
       - Real-time MBTA transit predictions for Boston-area subway, bus, commuter rail, and ferry.
  *   [oebb-scotty](https://github.com/openclaw/skills/tree/main/skills/manmal/oebb-scotty/SKILL.md)
       - Austrian rail travel planner (ÖBB Scotty).
  *   [openerz](https://github.com/openclaw/skills/tree/main/skills/mbjoern/erz-entsorgung-recycling-zurich/SKILL.md)
       - Abfuhrkalender für Zürich via OpenERZ API.
  *   [railil](https://github.com/openclaw/skills/tree/main/skills/lirantal/railil/SKILL.md)
       - Search for Israel Rail train schedules using the railil CLI.
  *   [rejseplanen](https://github.com/openclaw/skills/tree/main/skills/bjarkehs/rejseplanen/SKILL.md)
       - Query Danish public transport departures, arrivals, and journey planning via Rejseplanen API.
  *   [skanetrafiken](https://github.com/openclaw/skills/tree/main/skills/rezkam/skanetrafiken/SKILL.md)
       - Skåne public transport trip planner (Skånetrafiken). Plans bus/train journeys with real-time delays.
  *   [swiss-geo](https://github.com/openclaw/skills/tree/main/skills/mbjoern/swiss-geo-and-tourism-assistant/SKILL.md)
       - Schweizer Geodaten, POIs und Tourismus. Orte/Adressen suchen, Höhen abfragen.
  *   [swiss-phone-directory](https://github.com/openclaw/skills/tree/main/skills/xenofex7/swiss-phone-directory/SKILL.md)
       - Swiss phone directory lookup via search.ch API.
  *   [swiss-transport](https://github.com/openclaw/skills/tree/main/skills/xenofex7/swiss-transport/SKILL.md)
       - Swiss Public Transport real-time information.
  *   [tachograph-infringement-triage-root-cause-uk](https://github.com/openclaw/skills/tree/main/skills/kowl64/tachograph-infringement-triage-root-cause-uk/SKILL.md)
       - Triages tachograph infringements, identifies common patterns.
  *   [tesla](https://github.com/openclaw/skills/tree/main/skills/mvanhorn/tesla/SKILL.md)
       - Control your Tesla vehicles - lock/unlock, climate, location, charge status, and more.
  *   [tesla-commands](https://github.com/openclaw/skills/tree/main/skills/ovaris/tesla-commands/SKILL.md)
       - Control your Tesla via MyTeslaMate API. Supports multi-vehicle accounts, climate control.
  *   [tessie](https://github.com/openclaw/skills/tree/main/skills/baanish/tessie/SKILL.md)
       - tessie
  *   [tfl-journey-disruption](https://github.com/openclaw/skills/tree/main/skills/diegopetrucci/transport-for-london-journey-disruption/SKILL.md)
       - Plan TfL journeys from start/end/time, resolve locations (prefer postcodes)
  *   [transport-investigation-acas-aligned-pack](https://github.com/openclaw/skills/tree/main/skills/kowl64/transport-investigation-acas-aligned-pack/SKILL.md)
       - Generates ACAS-aligned investigation invite wording, neutral question sets, and evidence logs.
  *   [trimet](https://github.com/openclaw/skills/tree/main/skills/mjrussell/trimet/SKILL.md)
       - Get Portland transit information including arrivals, trip planning, and alerts.
  *   [virus-monitor](https://github.com/openclaw/skills/tree/main/skills/pasogott/virus-monitor/SKILL.md)
       - Virus-Monitoring für Wien (Abwasser + Sentinel).
  *   [wienerlinien](https://github.com/openclaw/skills/tree/main/skills/hjanuschka/wienerlinien/SKILL.md)
       - Vienna public transport (Wiener Linien) real-time data.
  *   [uk-trains](https://github.com/openclaw/skills/tree/main/skills/jabbslad/uk-trains/SKILL.md)
       - UK National Rail departures, arrivals, delays, platforms.
  *   [trein](https://github.com/openclaw/skills/tree/main/skills/joehoel/trein/SKILL.md)
       - Dutch Railways (NS) departures, trips, disruptions.
  *   [bahn](https://github.com/openclaw/skills/tree/main/skills/tobiasbischoff/bahn/SKILL.md)
       - Deutsche Bahn train connections and travel planning.
  *   [railil](https://github.com/openclaw/skills/tree/main/skills/lirantal/skill-railil/SKILL.md)
       - Israel Rail train schedules with fuzzy station search.
  *   [wheels-router](https://github.com/openclaw/skills/tree/main/skills/anscg/wheels-router/SKILL.md)
       - Public transit planning globally via Transitous.
  *   [flight-tracker](https://github.com/openclaw/skills/tree/main/skills/copey02/aviationstack-flight-tracker/SKILL.md)
       - Real-time flight tracking with gate info and delays.
  *   [aviation-weather](https://github.com/openclaw/skills/tree/main/skills/dimitryvin/aviation-weather/SKILL.md)
       - Aviation weather: METAR, TAF, PIREPs for flight planning.
  *   [travel-concierge](https://github.com/openclaw/skills/tree/main/skills/arein/travel-concierge/SKILL.md)
       - Find contact details for Airbnb, Booking.com, VRBO listings.
  *   [surfline](https://github.com/openclaw/skills/tree/main/skills/miguelcarranza/surfline/SKILL.md)
       - Surf forecasts and conditions from Surfline.
  *   [mechanic](https://github.com/openclaw/skills/tree/main/skills/scottfo/mechanic/SKILL.md)
       - Vehicle maintenance tracker with service intervals and recalls.
  
  ### Personal Development
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#personal-development)
  
  *   [daily-review](https://github.com/openclaw/skills/tree/main/skills/henrino3/daily-review/SKILL.md)
       - Comprehensive daily performance review with communication tracking, meeting analysis.
  *   [drivers-hours-wtd-infringement-coach-uk](https://github.com/openclaw/skills/tree/main/skills/kowl64/drivers-hours-wtd-infringement-coach-uk/SKILL.md)
       - Creates a 1-page driver-facing tacho/WTD infringement note plus corrective actions and review date.
  *   [graphiti](https://github.com/openclaw/skills/tree/main/skills/emasoudy/graphiti/SKILL.md)
       - Knowledge graph operations via Graphiti API.
  *   [morning-routine](https://github.com/openclaw/skills/tree/main/skills/jhillin8/morning-routine/SKILL.md)
       - Build a powerful morning routine with habit checklists, timing, and streak tracking.
  *   [munger-observer](https://github.com/openclaw/skills/tree/main/skills/jdrhyne/munger-observer/SKILL.md)
       - Daily wisdom review applying Charlie Munger's mental models to your work and thinking.
  *   [night-routine](https://github.com/openclaw/skills/tree/main/skills/jhillin8/night-routine/SKILL.md)
       - Build a restful night routine with wind-down habits, sleep prep, and next-day planning.
  *   [overcome-problem](https://github.com/openclaw/skills/tree/main/skills/jhillin8/overcome-problem/SKILL.md)
       - Break down any problem with structured thinking, action plans, and progress tracking.
  *   [procrastination-buster](https://github.com/openclaw/skills/tree/main/skills/jhillin8/procrastination-buster/SKILL.md)
       - Beat procrastination with task breakdown, 2-minute starts, and accountability tracking.
  *   [quit-alcohol](https://github.com/openclaw/skills/tree/main/skills/jhillin8/quit-alcohol/SKILL.md)
       - Track sobriety with alcohol-free streaks, craving management, and recovery milestones.
  *   [quit-caffeine](https://github.com/openclaw/skills/tree/main/skills/jhillin8/quit-caffeine/SKILL.md)
       - Reduce or quit caffeine with withdrawal tracking, tapering plans, and energy milestones.
  *   [quit-overspending](https://github.com/openclaw/skills/tree/main/skills/jhillin8/quit-overspending/SKILL.md)
       - Break impulse buying habits with spending streaks, urge tracking, and savings milestones.
  *   [quit-porn](https://github.com/openclaw/skills/tree/main/skills/jhillin8/quit-porn/SKILL.md)
       - Break free from porn addiction with streak tracking, urge management, and recovery milestones.
  *   [quit-smoking](https://github.com/openclaw/skills/tree/main/skills/jhillin8/quit-smoking/SKILL.md)
       - Quit cigarettes with smoke-free tracking, craving support, and health recovery timeline.
  *   [quit-vaping](https://github.com/openclaw/skills/tree/main/skills/jhillin8/quit-vaping/SKILL.md)
       - Quit vaping with nicotine-free streak tracking, craving tools, and health milestones.
  *   [quit-weed](https://github.com/openclaw/skills/tree/main/skills/jhillin8/quit-weed/SKILL.md)
       - Take a tolerance break or quit cannabis with streak tracking and craving support.
  *   [self-love-confidence](https://github.com/openclaw/skills/tree/main/skills/jhillin8/self-love-confidence/SKILL.md)
       - Build self-love and confidence with affirmations, wins logging, and inner critic management.
  *   [social-media-detox](https://github.com/openclaw/skills/tree/main/skills/jhillin8/social-media-detox/SKILL.md)
       - Break social media addiction with screen-free streaks, urge tracking, and digital wellness.
  *   [stress-relief](https://github.com/openclaw/skills/tree/main/skills/jhillin8/stress-relief/SKILL.md)
       - Manage stress with quick techniques, stress logging, and recovery tools.
  *   [study-habits](https://github.com/openclaw/skills/tree/main/skills/jhillin8/study-habits/SKILL.md)
       - Build effective study habits with spaced repetition, active recall, and session tracking.
  *   [therapy-mode](https://github.com/openclaw/skills/tree/main/skills/thesethrose/therapy-mode/SKILL.md)
       - Comprehensive AI-assisted therapeutic support framework.
  *   [weekly-synthesis](https://github.com/openclaw/skills/tree/main/skills/itsflow/weekly-synthesis/SKILL.md)
       - Create a comprehensive synthesis of the week's work and thinking.
  *   [wellness-skills](https://github.com/openclaw/skills/tree/main/skills/jhillin8)
       - 12 wellness skills: anxiety relief, meditation, habit tracking, fasting, gratitude, discipline, motivation, and more.
  *   [thinking-frameworks](https://github.com/openclaw/skills/tree/main/skills/artyomx33)
       - 6 thinking frameworks: first principles, inversion, JTBD, pre-mortem, cross-pollination, reasoning personas.
  *   [adhd-body-doubling](https://github.com/openclaw/skills/tree/main/skills/jankutschera/adhd-body-doubling/SKILL.md)
       - Punk-style ADHD body doubling for founders with focus sessions.
  *   [fix-life-in-1-day](https://github.com/openclaw/skills/tree/main/skills/evgyur/fix-life-in-1-day/SKILL.md)
       - 10 psychological sessions based on Dan Koe's method.
  *   [daily-review-ritual](https://github.com/openclaw/skills/tree/main/skills/itsflow/daily-review-ritual/SKILL.md)
       - End-of-day review to capture progress and plan tomorrow.
  *   [whatdo](https://github.com/openclaw/skills/tree/main/skills/scottfo/whatdo/SKILL.md)
       - Activity discovery with weather, movie times, streaming, and group profiles.
  
  ### Health & Fitness
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#health--fitness)
  
  *   [endurance-coach](https://github.com/openclaw/skills/tree/main/skills/shiv19/endurance-coach/SKILL.md)
       - Create personalized triathlon, marathon, and ultra-endurance training plans.
  *   [fitbit](https://github.com/openclaw/skills/tree/main/skills/mjrussell/fitbit/SKILL.md)
       - Query Fitbit health data including sleep, heart rate, activity, SpO2, and breathing rate.
  *   [fitbit-analytics](https://github.com/openclaw/skills/tree/main/skills/kesslerio/fitbit-analytics/SKILL.md)
       - Fitbit health and fitness data integration.
  *   [hevy](https://github.com/openclaw/skills/tree/main/skills/mjrussell/hevy/SKILL.md)
       - Query workout data from Hevy including workouts, routines, exercises, and history.
  *   [huckleberry](https://github.com/openclaw/skills/tree/main/skills/jayhickey/huckleberry/SKILL.md)
       - Track baby sleep, feeding, diapers, and growth via the Huckleberry CLI.
  *   [muscle-gain](https://github.com/openclaw/skills/tree/main/skills/jhillin8/muscle-gain/SKILL.md)
       - Track muscle building with weight progression, protein tracking, and strength milestones.
  *   [oura](https://github.com/openclaw/skills/tree/main/skills/ruhrpotter/oura/SKILL.md)
       - oura
  *   [oura-analytics](https://github.com/openclaw/skills/tree/main/skills/kesslerio/oura-analytics/SKILL.md)
       - Oura Ring data integration and analytics.
  *   [pregnancy-tracker](https://github.com/openclaw/skills/tree/main/skills/jhillin8/pregnancy-tracker/SKILL.md)
       - Track pregnancy journey with weekly updates, symptom logging, and milestone countdowns.
  *   [ranked-gym](https://github.com/openclaw/skills/tree/main/skills/jhillin8/ranked-gym/SKILL.md)
       - Gamify your gym sessions with XP, levels, achievements, and workout streaks.
  *   [strava](https://github.com/openclaw/skills/tree/main/skills/bohdanpodvirnyi/strava/SKILL.md)
       - Load and analyze Strava activities, stats, and workouts using the Strava API.
  *   [testosterone-optimization](https://github.com/openclaw/skills/tree/main/skills/jhillin8/testosterone-optimization/SKILL.md)
       - Optimize natural testosterone with sleep, exercise, nutrition, and lifestyle tracking.
  *   [the-sports-db](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/the-sports-db/SKILL.md)
       - Access sports data via TheSportsDB (teams, events, scores).
  *   [weight-loss](https://github.com/openclaw/skills/tree/main/skills/jhillin8/weight-loss/SKILL.md)
       - Track weight loss journey with weigh-ins, trend analysis, and goal milestones.
  *   [whoop](https://github.com/openclaw/skills/tree/main/skills/borahm/whoop/SKILL.md)
       - WHOOP morning check-in (recovery/sleep/strain) with suggestions.
  *   [whoop-morning](https://github.com/openclaw/skills/tree/main/skills/borahm/whoop-morning/SKILL.md)
       - Check WHOOP recovery/sleep/strain each morning and send suggestions.
  *   [whoopskill](https://github.com/openclaw/skills/tree/main/skills/koala73/whoopskill/SKILL.md)
       - WHOOP CLI with health insights, trends analysis, and data fetching (sleep, recovery, HRV, strain).
  *   [workout](https://github.com/openclaw/skills/tree/main/skills/gricha/workout/SKILL.md)
       - Track workouts, log sets, manage exercises and templates with workout-cli.
  *   [workout-logger](https://github.com/openclaw/skills/tree/main/skills/jhillin8/workout-logger/SKILL.md)
       - Log workouts, track progress, get exercise suggestions and PR tracking.
  *   [garmin-health](https://github.com/openclaw/skills/tree/main/skills/eversonl/garmin-health-analysis/SKILL.md)
       - Garmin data: sleep, HRV, VO2 max, Body Battery, training readiness.
  *   [whoop-health](https://github.com/openclaw/skills/tree/main/skills/rodrigouroz/whoop-health-analysis/SKILL.md)
       - Whoop health data with interactive charts and visualizations.
  *   [oura-ring](https://github.com/openclaw/skills/tree/main/skills/sameerbajaj/oura-ring-skill/SKILL.md)
       - Oura Ring readiness, sleep scores, and 7-day trends.
  *   [strava-cycling](https://github.com/openclaw/skills/tree/main/skills/ericrosenberg/strava-cycling-coach/SKILL.md)
       - Strava cycling performance analysis and coaching insights.
  *   [who-growth-charts](https://github.com/openclaw/skills/tree/main/skills/odrobnik/who-growth-charts/SKILL.md)
       - WHO child growth charts with percentile curves.
  *   [intervals-icu](https://github.com/openclaw/skills/tree/main/skills/pseuss/intervals-icu-api/SKILL.md)
       - Intervals.icu training data: activities, workouts, wellness.
  
  ### Communication
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#communication)
  
  *   [apple-mail-search-safe](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/apple-mail-search-safe/SKILL.md)
       - Fast & safe Apple Mail search with body content support.
  *   [beeper](https://github.com/openclaw/skills/tree/main/skills/krausefx/beeper/SKILL.md)
       - Search and browse local Beeper chat history (threads, messages, full-text search).
  *   [camelcamelcamel-alerts](https://github.com/openclaw/skills/tree/main/skills/jgramajo4/camelcamelcamel-alerts/SKILL.md)
       - Monitor CamelCamelCamel price drop alerts via RSS and send Telegram notifications when items go on.
  *   [discord-doctor](https://github.com/openclaw/skills/tree/main/skills/jhillock/discord-doctor/SKILL.md)
       - Quick diagnosis and repair for Discord bot, Gateway, OAuth token, and legacy config issues.
  *   [google-chat](https://github.com/openclaw/skills/tree/main/skills/darconada/google-chat/SKILL.md)
       - Send messages to Google Chat spaces and users via webhooks or OAuth.
  *   [himalaya](https://github.com/openclaw/skills/tree/main/skills/lamelas/himalaya/SKILL.md)
       - CLI to manage emails via IMAP/SMTP. Use `himalaya` to list, read, write, reply, forward, search.
  *   [imsg](https://github.com/openclaw/skills/tree/main/skills/steipete/imsg/SKILL.md)
       - iMessage/SMS CLI for listing chats, history, watch, and sending.
  *   [linkedin](https://github.com/openclaw/skills/tree/main/skills/biostartechnology/linkedin/SKILL.md)
       - LinkedIn automation via browser relay or cookies for messaging, profile viewing.
  *   [linkedin-cli](https://github.com/openclaw/skills/tree/main/skills/arun-8687/linkedin-cli/SKILL.md)
       - A bird-like LinkedIn CLI for searching profiles, checking messages.
  *   [ms365](https://github.com/openclaw/skills/tree/main/skills/cvsloane/ms365/SKILL.md)
       - ms365
  *   [paid-ads](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/paid-ads/SKILL.md)
       - When the user wants help with paid advertising campaigns on Google Ads, Meta (Facebook/Instagram)
  *   [protonmail](https://github.com/openclaw/skills/tree/main/skills/durchblick-nl/protonmail/SKILL.md)
       - Read, search, and scan ProtonMail via IMAP bridge (Proton Bridge or hydroxide).
  *   [social-content](https://github.com/openclaw/skills/tree/main/skills/jchopard69/marketing-skills/references/social-content/SKILL.md)
       - When the user wants help creating, scheduling, or optimizing social media content.
  *   [table-image](https://github.com/openclaw/skills/tree/main/skills/joargp/table-image/SKILL.md)
       - Generate images from tables for better readability in messaging apps like Telegram.
  *   [telegram-usage](https://github.com/openclaw/skills/tree/main/skills/c-drew/telegram-usage/SKILL.md)
       - Display session usage statistics (quota, session time, tokens, context).
  *   [wacli](https://github.com/openclaw/skills/tree/main/skills/steipete/wacli/SKILL.md)
       - Send WhatsApp messages to other people or search/sync WhatsApp history.
  *   [webchat-audio-notifications](https://clawdhub.com/brokemac79/webchat-audio-notifications)
       - Browser audio notifications for webchat with 5 intensity levels, custom sounds, and smart tab detection.
  *   [whatsapp-video-mockup](https://github.com/openclaw/skills/tree/main/skills/danpeg/whatsapp-video-mockup/SKILL.md)
       - whatsapp-video-mockup
  *   [postiz](https://github.com/openclaw/skills/tree/main/skills/nevo-david/postiz/SKILL.md)
       - Schedule posts to 28+ channels: X, LinkedIn, Reddit, Instagram, TikTok, and more.
  *   [walkie-talkie](https://github.com/openclaw/skills/tree/main/skills/rubenfb23/walkie-talkie/SKILL.md)
       - WhatsApp voice conversations: transcribe audio, respond with TTS.
  *   [claw-me-maybe](https://github.com/openclaw/skills/tree/main/skills/nickhamze/claw-me-maybe/SKILL.md)
       - Beeper integration: WhatsApp, Telegram, Signal, Discord, Slack, iMessage, LinkedIn.
  *   [tootbot](https://github.com/openclaw/skills/tree/main/skills/behrangsa/tootbot/SKILL.md)
       - Publish content to Mastodon.
  *   [upload-post](https://github.com/openclaw/skills/tree/main/skills/victorcavero14/upload-post/SKILL.md)
       - Upload to TikTok, Instagram, YouTube, LinkedIn, Facebook, X, and more.
  *   [gram](https://github.com/openclaw/skills/tree/main/skills/arein/gram/SKILL.md)
       - Instagram CLI: feeds, posts, profiles, engagement.
  *   [reddit-cli](https://github.com/openclaw/skills/tree/main/skills/kelsia14/reddit-cli/SKILL.md)
       - Reddit CLI for browsing posts and subreddits.
  *   [discord-voice](https://github.com/openclaw/skills/tree/main/skills/avatarneil/discord-voice/SKILL.md)
       - Real-time voice conversations in Discord with Claude AI.
  
  ### Speech & Transcription
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#speech--transcription)
  
  *   [assemblyai-transcribe](https://github.com/openclaw/skills/tree/main/skills/tristanmanchester/assemblyai-transcribe/SKILL.md)
       - Transcribe audio/video with AssemblyAI (local upload.
  *   [audio-gen](https://github.com/openclaw/skills/tree/main/skills/udiedrichsen/audio-gen/SKILL.md)
       - Generate audiobooks, podcasts, or educational audio content on demand.
  *   [audio-reply](https://github.com/openclaw/skills/tree/main/skills/matrixy/audio-reply-skill/SKILL.md)
       - Generate audio replies using TTS. Trigger with "read it to me \[URL\]" to fetch.
  *   [edge-tts](https://github.com/openclaw/skills/tree/main/skills/i3130002/edge-tts/SKILL.md)
       - |.
  *   [gettr-transcribe-summarize](https://github.com/openclaw/skills/tree/main/skills/kevin37li/gettr-transcribe-summarize/SKILL.md)
       - Download audio from a GETTR post (via HTML og:video), transcribe it locally.
  *   [llmwhisperer](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/llmwhisperer/SKILL.md)
       - Extract text and layout from images and PDFs using LLMWhisperer API.
  *   [local-whisper](https://github.com/openclaw/skills/tree/main/skills/araa47/local-whisper/SKILL.md)
       - Local speech-to-text using OpenAI Whisper. Runs fully offline after model download.
  *   [mlx-whisper](https://github.com/openclaw/skills/tree/main/skills/kevin37li/mlx-whisper/SKILL.md)
       - Local speech-to-text with MLX Whisper (Apple Silicon optimized, no API key).
  *   [openai-whisper](https://github.com/openclaw/skills/tree/main/skills/steipete/openai-whisper/SKILL.md)
       - Local speech-to-text with the Whisper CLI (no API key).
  *   [openai-whisper-api](https://github.com/openclaw/skills/tree/main/skills/steipete/openai-whisper-api/SKILL.md)
       - Transcribe audio via OpenAI Audio Transcriptions API (Whisper).
  *   [parakeet-mlx](https://github.com/openclaw/skills/tree/main/skills/kylehowells/parakeet-mlx/SKILL.md)
       - Local speech-to-text with Parakeet MLX (ASR) for Apple Silicon (no API key).
  *   [parakeet-stt](https://github.com/openclaw/skills/tree/main/skills/carlulsoe/parakeet-stt/SKILL.md)
       - >-.
  *   [pocket-transcripts](https://github.com/openclaw/skills/tree/main/skills/tmustier/heypocket-reader/SKILL.md)
       - Read transcripts and summaries from Pocket AI (heypocket.com) recording devices.
  *   [pocket-tts](https://github.com/openclaw/skills/tree/main/skills/sherajdev/pocket-tts/SKILL.md)
       - pocket-tts
  *   [tts-whatsapp](https://github.com/openclaw/skills/tree/main/skills/hopyky/tts-whatsapp/SKILL.md)
       - Send high-quality text-to-speech voice messages on WhatsApp in 40+ languages with automatic delivery.
  *   [video-subtitles](https://github.com/openclaw/skills/tree/main/skills/ngutman/video-subtitles/SKILL.md)
       - Generate SRT subtitles from video/audio with translation support.
  *   [voice-transcribe](https://github.com/openclaw/skills/tree/main/skills/darinkishore/voice-transcribe/SKILL.md)
       - Transcribe audio files using OpenAI's gpt-4o-mini-transcribe model with vocabulary hints.
  *   [elevenlabs-voices](https://github.com/openclaw/skills/tree/main/skills/robbyczgw-cla/elevenlabs-voices/SKILL.md)
       - ElevenLabs voice synthesis: 18 personas, 32 languages, sound effects.
  *   [elevenlabs-media](https://github.com/openclaw/skills/tree/main/skills/clawdbotborges)
       - ElevenLabs music generation and speech-to-text (Scribe v2).
  *   [elevenlabs-agents](https://github.com/openclaw/skills/tree/main/skills/pennyroyaltea/elevenlabs-agents/SKILL.md)
       - Create and manage ElevenLabs conversational AI agents.
  *   [tts](https://github.com/openclaw/skills/tree/main/skills/amstko/tts/SKILL.md)
       - Text-to-speech using Hume AI or OpenAI API.
  
  ### Smart Home & IoT
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#smart-home--iot)
  
  *   [anova-oven](https://github.com/openclaw/skills/tree/main/skills/dodeja/anova-skill/SKILL.md)
       - Control Anova Precision Ovens and Precision Cookers (sous vide) via WiFi WebSocket API.
  *   [bambu-cli](https://github.com/openclaw/skills/tree/main/skills/tobiasbischoff/bambu-cli/SKILL.md)
       - Operate and troubleshoot BambuLab printers with the bambu-cli (status/watch.
  *   [beestat](https://github.com/openclaw/skills/tree/main/skills/mjrussell/beestat/SKILL.md)
       - Query ecobee thermostat data via Beestat API including temperature, humidity, air quality (CO2.
  *   [dyson-cli](https://github.com/openclaw/skills/tree/main/skills/tmustier/dyson-cli/SKILL.md)
       - Control Dyson air purifiers, fans, and heaters via local MQTT.
  *   [eightctl](https://github.com/openclaw/skills/tree/main/skills/steipete/eightctl/SKILL.md)
       - Control Eight Sleep pods (status, temperature, alarms, schedules).
  *   [google-home](https://github.com/openclaw/skills/tree/main/skills/mitchellbernstein/google-home/SKILL.md)
       - Control Google Nest devices (thermostats, cameras, doorbells)
  *   [govee-lights](https://github.com/openclaw/skills/tree/main/skills/joeynyc/govee-lights/SKILL.md)
       - Control Govee smart lights via the Govee API.
  *   [homeassistant](https://github.com/openclaw/skills/tree/main/skills/dbhurley/homeassistant/SKILL.md)
       - Control Home Assistant - smart plugs, lights, scenes, automations.
  *   [homey](https://github.com/openclaw/skills/tree/main/skills/maxsumrall/homey/SKILL.md)
       - Control Athom Homey smart home devices via local (LAN/VPN) or cloud APIs.
  *   [homey-cli](https://github.com/openclaw/skills/tree/main/skills/krausefx/homey-cli/SKILL.md)
       - Control Homey home automation hub via CLI.
  *   [nanoleaf](https://github.com/openclaw/skills/tree/main/skills/rstierli/nanoleaf/SKILL.md)
       - Control Nanoleaf light panels via the Picoleaf CLI.
  *   [nest-devices](https://github.com/openclaw/skills/tree/main/skills/amogower/nest-devices/SKILL.md)
       - Control Nest smart home devices (thermostat, cameras, doorbell) via the Device Access API.
  *   [openhue](https://github.com/openclaw/skills/tree/main/skills/steipete/openhue/SKILL.md)
       - Control Philips Hue lights/scenes via the OpenHue CLI.
  *   [pihole](https://github.com/openclaw/skills/tree/main/skills/baanish/pihole/SKILL.md)
       - pihole
  *   [printer](https://github.com/openclaw/skills/tree/main/skills/dhvanilpatel/printer/SKILL.md)
       - Manage printers via CUPS on macOS (discover, add, print, queue, status, wake).
  *   [voicemonkey](https://github.com/openclaw/skills/tree/main/skills/jayakumark/voicemonkey/SKILL.md)
       - Control Alexa devices via VoiceMonkey API v2 - make announcements, trigger routines, start flows.
  *   [tesla-fleet-api](https://github.com/openclaw/skills/tree/main/skills/odrobnik/tesla-fleet-api/SKILL.md)
       - Tesla Fleet API: HVAC, charge controls, wake vehicle, OAuth flows.
  *   [lg-thinq](https://github.com/openclaw/skills/tree/main/skills/kaiofreitas/lg-thinq/SKILL.md)
       - Control LG smart appliances: fridge, washer, dryer, AC.
  *   [bambu-local](https://github.com/openclaw/skills/tree/main/skills/tanguyvans/bambu-local/SKILL.md)
       - Control Bambu Lab 3D printers locally via MQTT.
  *   [netatmo](https://github.com/openclaw/skills/tree/main/skills/florianbeer/netatmo/SKILL.md)
       - Netatmo thermostat control and weather station data.
  *   [starlink](https://github.com/openclaw/skills/tree/main/skills/danfedick/starlink/SKILL.md)
       - Starlink dish: status, speed test, WiFi clients, stow/unstow.
  *   [homebridge](https://github.com/openclaw/skills/tree/main/skills/jiasenl/clawdbot-skill-homebridge/SKILL.md)
       - Control smart home devices via Homebridge REST API.
  *   [robo-rock](https://github.com/openclaw/skills/tree/main/skills/dru-ca/robo-rock/SKILL.md)
       - Control Roborock robot vacuums: clean, maps, consumables.
  *   [home-music](https://github.com/openclaw/skills/tree/main/skills/asteinberger/home-music/SKILL.md)
       - Whole-house music scenes with Spotify + Airfoil speakers.
  *   [enzoldhazam](https://github.com/openclaw/skills/tree/main/skills/daniel-laszlo/enzoldhazam/SKILL.md)
       - NGBS iCON Smart Home thermostat control.
  *   [little-snitch](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/little-snitch/SKILL.md)
       - Little Snitch firewall control on macOS.
  *   [daily-recap](https://github.com/openclaw/skills/tree/main/skills/dbhurley/daily-recap/SKILL.md)
       - Generate a daily recap image with your agent holding a posterboard of accomplishments.
  *   [snow-report](https://github.com/openclaw/skills/tree/main/skills/davemorin/snow-report/SKILL.md)
       - Get snow conditions, forecasts, and ski reports for any mountain resort worldwide.
  *   [weather](https://github.com/openclaw/skills/tree/main/skills/steipete/weather/SKILL.md)
       - Get current weather and forecasts (no API key required).
  *   [weather-pollen](https://github.com/openclaw/skills/tree/main/skills/thesethrose/weather-pollen/SKILL.md)
       - Weather and pollen reports for any location using free APIs.
  *   [weathercli](https://github.com/openclaw/skills/tree/main/skills/pjtf93/weathercli/SKILL.md)
       - Get current weather conditions and forecasts for any location worldwide.
  
  ### Shopping & E-commerce
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#shopping--e-commerce)
  
  *   [anylist](https://github.com/openclaw/skills/tree/main/skills/mjrussell/anylist/SKILL.md)
       - Manage grocery and shopping lists via AnyList.
  *   [bring-shopping](https://github.com/openclaw/skills/tree/main/skills/cutzenfriend/bring-shopping/SKILL.md)
       - Manage Bring! shopping lists via the unofficial bring-shopping Node.js library.
  *   [checkers-sixty60](https://github.com/openclaw/skills/tree/main/skills/snopoke/checkers-sixty60/SKILL.md)
       - Shop on Checkers.co.za Sixty60 delivery service via browser automation.
  *   [event-planner](https://github.com/openclaw/skills/tree/main/skills/udiedrichsen/event-planner/SKILL.md)
       - Plan events (night out, weekend, date night, team outing, meals, trips) by searching venues.
  *   [food-order](https://github.com/openclaw/skills/tree/main/skills/steipete/food-order/SKILL.md)
       - Reorder Foodora orders + track ETA/status with ordercli.
  *   [grocery-list](https://github.com/openclaw/skills/tree/main/skills/dbhurley/grocery-list/SKILL.md)
       - Standalone grocery lists, recipes, and meal planning with local storage.
  *   [gurkerlcli](https://github.com/openclaw/skills/tree/main/skills/pasogott/gurkerlcli/SKILL.md)
       - Austrian online grocery shopping via gurkerl.at.
  *   [idealista](https://github.com/openclaw/skills/tree/main/skills/quifago/idealista/SKILL.md)
       - Query Idealista API via idealista-cli (OAuth2 client credentials).
  *   [irish-takeaway](https://github.com/openclaw/skills/tree/main/skills/cotyledonlab/irish-takeaway/SKILL.md)
       - Find nearby takeaways in Ireland and browse menus via Deliveroo/Just Eat.
  *   [marktplaats](https://github.com/openclaw/skills/tree/main/skills/pvoo/marktplaats/SKILL.md)
       - Search Marktplaats.nl classifieds across all categories with filtering support.
  *   [ordercli](https://github.com/openclaw/skills/tree/main/skills/steipete/ordercli/SKILL.md)
       - Foodora-only CLI for checking past orders and active order status (Deliveroo WIP).
  *   [paprika](https://github.com/openclaw/skills/tree/main/skills/mjrussell/paprika/SKILL.md)
       - Access recipes, meal plans, and grocery lists from Paprika Recipe Manager.
  *   [picnic](https://github.com/openclaw/skills/tree/main/skills/mpociot/picnic/SKILL.md)
       - Order groceries from Picnic supermarket - search products, manage cart, schedule delivery.
  *   [plan2meal](https://github.com/openclaw/skills/tree/main/skills/okikesolutions/plan2meal/SKILL.md)
       - plan2meal
  *   [shopping-expert](https://github.com/openclaw/skills/tree/main/skills/udiedrichsen/shopping-expert/SKILL.md)
       - Find and compare products online (Google Shopping) and locally (stores near you).
  *   [whcli](https://github.com/openclaw/skills/tree/main/skills/pasogott/whcli/SKILL.md)
       - Willhaben CLI for searching Austria's largest classifieds marketplace.
  *   [wolt-orders](https://github.com/openclaw/skills/tree/main/skills/dviros/wolt-orders/SKILL.md)
       - Wolt: discover restaurants, order, track, auto-detect delays.
  *   [gurkerl](https://github.com/openclaw/skills/tree/main/skills/florianbeer/gurkerl/SKILL.md)
       - Gurkerl.at grocery shopping via MCP.
  *   [agent-commerce](https://github.com/openclaw/skills/tree/main/skills/nowloady)
       - Agentic e-commerce engine and Sichuan food delivery.
  *   [jellyseerr](https://github.com/openclaw/skills/tree/main/skills/ericrosenberg/jellyseerr/SKILL.md)
       - Request movies and TV shows through Jellyseerr.
  *   [clawdbites](https://github.com/openclaw/skills/tree/main/skills/kylelol/clawdbites/SKILL.md)
       - Extract recipes from Instagram reels.
  *   [marketplace-clis](https://github.com/openclaw/skills/tree/main/skills/pjtf93)
       - Spanish marketplace CLIs: Wallapop, Idealista, Coches.net.
  
  ### Calendar & Scheduling
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#calendar--scheduling)
  
  *   [accli](https://github.com/openclaw/skills/tree/main/skills/joargp/accli/SKILL.md)
       - This skill should be used when interacting with Apple Calendar on macOS.
  *   [apple-calendar](https://github.com/openclaw/skills/tree/main/skills/tyler6204/apple-calendar/SKILL.md)
       - Apple Calendar.app integration for macOS.
  *   [apple-reminders](https://github.com/openclaw/skills/tree/main/skills/steipete/apple-reminders/SKILL.md)
       - Manage Apple Reminders via the `remindctl` CLI on macOS (list, add, edit, complete, delete).
  *   [calcurse](https://github.com/openclaw/skills/tree/main/skills/gumadeiras/calcurse/SKILL.md)
       - A text-based calendar and scheduling application. Use strictly for CLI-based calendar management.
  *   [caldav-calendar](https://github.com/openclaw/skills/tree/main/skills/asleep123/caldav-calendar/SKILL.md)
       - Sync and query CalDAV calendars (iCloud, Google, Fastmail, Nextcloud, etc.)
  *   [clippy](https://github.com/openclaw/skills/tree/main/skills/foeken/clippy/SKILL.md)
       - Microsoft 365 / Outlook CLI for calendar and email.
  *   [cpc-mpqc-competence-tracker-compliance-uk](https://github.com/openclaw/skills/tree/main/skills/kowl64/cpc-mpqc-competence-tracker-compliance-uk/SKILL.md)
       - Plans CPC/MPQC competence tracking with reminders, evidence lists, and compliance reporting.
  *   [gog](https://github.com/openclaw/skills/tree/main/skills/steipete/gog/SKILL.md)
       - Google Workspace CLI for Gmail, Calendar, Drive, Contacts, Sheets, and Docs.
  *   [holocube](https://github.com/openclaw/skills/tree/main/skills/andrewjiang/holocube/SKILL.md)
       - Control GeekMagic HelloCubic-Lite holographic cube display with HoloClawd firmware.
  *   [mcd-cn](https://github.com/openclaw/skills/tree/main/skills/ryanchen01/mcd-cn/SKILL.md)
       - Query McDonald's China MCP server via the mcd-cn CLI for campaign calendars, coupons.
  *   [morning-email-rollup](https://github.com/openclaw/skills/tree/main/skills/am-will/morning-email-rollup/SKILL.md)
       - Daily morning rollup of important emails and calendar events at 8am with AI-generated summaries.
  *   [remind-me](https://github.com/openclaw/skills/tree/main/skills/julianengel/remind-me/SKILL.md)
       - Set reminders using natural language. Automatically creates one-time cron jobs and logs to markdown.
  *   [roadrunner](https://github.com/openclaw/skills/tree/main/skills/johntheyoung/roadrunner/SKILL.md)
       - Beeper Desktop CLI for chats, messages, search, and reminders.
  *   [timer](https://github.com/openclaw/skills/tree/main/skills/hisxo/timer/SKILL.md)
       - Set timers and alarms. When a background timer completes.
  *   [gcal-pro](https://github.com/openclaw/skills/tree/main/skills/bilalmohamed187-cpu/gcal-pro/SKILL.md)
       - Google Calendar: view, create, manage events with natural language.
  *   [meeting-prep](https://github.com/openclaw/skills/tree/main/skills/hougangdev/meeting-prep/SKILL.md)
       - Meeting preparation and daily commit summaries.
  
  ### PDF & Documents
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#pdf--documents)
  
  *   [confluence](https://github.com/openclaw/skills/tree/main/skills/francisbrero/confluence/SKILL.md)
       - Search and manage Confluence pages and spaces using confluence-cli.
  *   [excel](https://github.com/openclaw/skills/tree/main/skills/dbhurley/excel/SKILL.md)
       - Read, write, edit, and format Excel files (.xlsx).
  *   [excel-weekly-dashboard](https://github.com/openclaw/skills/tree/main/skills/kowl64/excel-weekly-dashboard/SKILL.md)
       - Designs refreshable Excel dashboards (Power Query + structured tables + validation + pivot.
  *   [intomd](https://github.com/openclaw/skills/tree/main/skills/rezhajulio/intomd/SKILL.md)
       - Fetch and convert any documentation URL to Markdown using into.md service.
  *   [invoice-generator](https://github.com/openclaw/skills/tree/main/skills/tmigone/invoice-generator/SKILL.md)
       - Generate professional PDF invoices from JSON data.
  *   [markdown-converter](https://github.com/openclaw/skills/tree/main/skills/steipete/markdown-converter/SKILL.md)
       - Convert documents and files to Markdown using markitdown.
  *   [mineru-pdf](https://github.com/openclaw/skills/tree/main/skills/kesslerio/mineru-pdf-parser-clawdbot-skill/SKILL.md)
       - Parse PDFs locally (CPU) into Markdown/JSON using MinerU.
  *   [nano-pdf](https://github.com/openclaw/skills/tree/main/skills/steipete/nano-pdf/SKILL.md)
       - Edit PDFs with natural-language instructions using the nano-pdf CLI.
  *   [nudocs](https://github.com/openclaw/skills/tree/main/skills/jdrhyne/nudocs/SKILL.md)
       - Upload, edit, and export documents via Nudocs.ai.
  *   [pdf-form-filler](https://github.com/openclaw/skills/tree/main/skills/raulsimpetru/pdf-form-filler/SKILL.md)
       - Fill PDF forms programmatically with text values and checkboxes.
  *   [pptx-creator](https://github.com/openclaw/skills/tree/main/skills/dbhurley/pptx-creator/SKILL.md)
       - Create professional PowerPoint presentations from outlines, data sources, or AI-generated content.
  *   [pymupdf-pdf](https://github.com/openclaw/skills/tree/main/skills/kesslerio/pymupdf-pdf-parser-clawdbot-skill/SKILL.md)
       - Fast local PDF parsing with PyMuPDF (fitz) for Markdown/JSON outputs and optional images/tables.
  
  ### Self-Hosted & Automation
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#self-hosted--automation)
  
  *   [bridle](https://github.com/openclaw/skills/tree/main/skills/bjesuiter/bridle/SKILL.md)
       - Unified configuration manager for AI coding assistants.
  *   [fathom](https://github.com/openclaw/skills/tree/main/skills/stopmoclay/fathom/SKILL.md)
       - Connect to Fathom AI to fetch call recordings, transcripts, and summaries.
  *   [frappecli](https://github.com/openclaw/skills/tree/main/skills/pasogott/frappecli/SKILL.md)
       - CLI for Frappe Framework / ERPNext instances.
  *   [gotify](https://github.com/openclaw/skills/tree/main/skills/jmagar/gotify/SKILL.md)
       - Send push notifications via Gotify when long-running tasks complete or important events occur.
  *   [meetgeek](https://github.com/openclaw/skills/tree/main/skills/nexty5870/meetgeek/SKILL.md)
       - Query MeetGeek meeting intelligence from CLI - list meetings, get AI summaries, transcripts.
  *   [n8n](https://github.com/openclaw/skills/tree/main/skills/thomasansems/n8n/SKILL.md)
       - Manage n8n workflows and automations via API.
  *   [n8n-workflow-automation](https://github.com/openclaw/skills/tree/main/skills/kowl64/n8n-workflow-automation/SKILL.md)
       - Designs and outputs n8n workflow JSON with robust triggers, idempotency, error handling, logging.
  *   [paperless](https://github.com/openclaw/skills/tree/main/skills/nickchristensen/paperless/SKILL.md)
       - Interact with Paperless-NGX document management system via ppls CLI.
  *   [unifi](https://github.com/openclaw/skills/tree/main/skills/jmagar/unifi/SKILL.md)
       - Query and monitor UniFi network via local gateway API (Cloud Gateway Max / UniFi OS).
  *   [paperless-ngx](https://github.com/openclaw/skills/tree/main/skills/oskarstark/paperless-ngx/SKILL.md)
       - Paperless-ngx document management: search, upload, tag, organize.
  *   [n8n](https://github.com/openclaw/skills/tree/main/skills/pntrivedy/n8n-1-0-2/SKILL.md)
       - Manage n8n workflows, executions, and automation tasks.
  
  ### Security & Passwords
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#security--passwords)
  
  *   [1password](https://github.com/openclaw/skills/tree/main/skills/steipete/1password/SKILL.md)
       - Set up and use 1Password CLI (op). Use when installing the CLI, enabling desktop app integration.
  *   [bitwarden](https://github.com/openclaw/skills/tree/main/skills/asleep123/bitwarden/SKILL.md)
       - Access and manage Bitwarden/Vaultwarden passwords securely using the rbw CLI.
  *   [dashlane](https://github.com/openclaw/skills/tree/main/skills/gnarco/dashlane/SKILL.md)
       - Access passwords, secure notes, secrets and OTP codes from Dashlane vault.
  *   [security-skills](https://github.com/openclaw/skills/tree/main/skills/chandrasekar-r)
       - Security audit and real-time monitoring for Clawdbot deployments.
  *   [security-suite](https://github.com/openclaw/skills/tree/main/skills/gtrusler/clawdbot-security-suite/SKILL.md)
       - Advanced security validation: pattern detection, command sanitization.
  *   [bitwarden-vault](https://github.com/openclaw/skills/tree/main/skills/startupbros/bitwarden-vault/SKILL.md)
       - Bitwarden CLI setup, authentication, and secret reading.
  
  🤝 Contributing
  ---------------
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#-contributing)
  
  We welcome contributions! See [CONTRIBUTING.md](https://github.com/VoltAgent/awesome-openclaw-skills/blob/main/CONTRIBUTING.md)
   for detailed guidelines.
  
  *   Submit new skills via PR
  *   Improve existing definitions
  
  **Note:** Please don't submit skills you created 3 hours ago. We're now focusing on community-adopted skills, especially those published by development teams and proven in real-world usage. Quality over quantity.
  
  License
  -------
  
  [](https://github.com/VoltAgent/awesome-openclaw-skills#license)
  
  MIT License - see [LICENSE](https://github.com/VoltAgent/awesome-openclaw-skills/blob/main/LICENSE)
  
  Skills in this list are sourced from the [OpenClaw official skills repo](https://github.com/openclaw/skills/tree/main/skills)
   and categorized for easier discovery. Skills listed here are created and maintained by their respective authors, not by us. We do not audit, endorse, or guarantee the security or correctness of listed projects. They are not security-audited and should be reviewed before production use.
  
  If you find an issue with a listed skill or want your skill removed, please [open an issue](https://github.com/VoltAgent/awesome-openclaw-skills/issues)
   and we'll take care of it promptly.
  
  About
  -----
  
  The awesome collection of OpenClaw Skills. Formerly known as Moltbot, originally Clawdbot.
  
  [github.com/VoltAgent/voltagent](https://github.com/VoltAgent/voltagent "https://github.com/VoltAgent/voltagent")
  
  ### Topics
  
  [awesome-list](https://github.com/topics/awesome-list "Topic: awesome-list")
   [agent-skills](https://github.com/topics/agent-skills "Topic: agent-skills")
   [clawd](https://github.com/topics/clawd "Topic: clawd")
   [clawdbot](https://github.com/topics/clawdbot "Topic: clawdbot")
   [clawdhub](https://github.com/topics/clawdhub "Topic: clawdhub")
   [clawdbot-skill](https://github.com/topics/clawdbot-skill "Topic: clawdbot-skill")
   [moltbot](https://github.com/topics/moltbot "Topic: moltbot")
   [moltbot-skills](https://github.com/topics/moltbot-skills "Topic: moltbot-skills")
   [openclaw](https://github.com/topics/openclaw "Topic: openclaw")
   [openclaw-skills](https://github.com/topics/openclaw-skills "Topic: openclaw-skills")
  
  ### Resources
  
  [Readme](https://github.com/VoltAgent/awesome-openclaw-skills#readme-ov-file)
  
  ### License
  
  [MIT license](https://github.com/VoltAgent/awesome-openclaw-skills#MIT-1-ov-file)
  
  ### Contributing
  
  [Contributing](https://github.com/VoltAgent/awesome-openclaw-skills#contributing-ov-file)
  
  ### Uh oh!
  
  There was an error while loading. [Please reload this page](https://github.com/VoltAgent/awesome-openclaw-skills)
  .
  
  [Activity](https://github.com/VoltAgent/awesome-openclaw-skills/activity)
  
  [Custom properties](https://github.com/VoltAgent/awesome-openclaw-skills/custom-properties)
  
  ### Stars
  
  [**6.2k** stars](https://github.com/VoltAgent/awesome-openclaw-skills/stargazers)
  
  ### Watchers
  
  [**38** watching](https://github.com/VoltAgent/awesome-openclaw-skills/watchers)
  
  ### Forks
  
  [**582** forks](https://github.com/VoltAgent/awesome-openclaw-skills/forks)
  
  [Report repository](https://github.com/contact/report-content?content_url=https%3A%2F%2Fgithub.com%2FVoltAgent%2Fawesome-openclaw-skills&report=VoltAgent+%28user%29)
  
  [Releases](https://github.com/VoltAgent/awesome-openclaw-skills/releases)
  
  --------------------------------------------------------------------------
  
  No releases published
  
  [Packages 0](https://github.com/orgs/VoltAgent/packages?repo_name=awesome-openclaw-skills)
  
  -------------------------------------------------------------------------------------------
  
  No packages published  
  
  [Contributors 8](https://github.com/VoltAgent/awesome-openclaw-skills/graphs/contributors)
  
  -------------------------------------------------------------------------------------------
  
  *   [![@necatiozmen](https://avatars.githubusercontent.com/u/18739364?s=64&v=4)](https://github.com/necatiozmen)
      
  *   [![@claude](https://avatars.githubusercontent.com/u/81847?s=64&v=4)](https://github.com/claude)
      
  *   [![@Gonzih](https://avatars.githubusercontent.com/u/266275?s=64&v=4)](https://github.com/Gonzih)
      
  *   [![@shiv19](https://avatars.githubusercontent.com/u/9407019?s=64&v=4)](https://github.com/shiv19)
      
  *   [![@haroldrandom](https://avatars.githubusercontent.com/u/14357159?s=64&v=4)](https://github.com/haroldrandom)
      
  *   [![@agmmnn](https://avatars.githubusercontent.com/u/16024979?s=64&v=4)](https://github.com/agmmnn)
      
  *   [![@elestirelbilinc-sketch](https://avatars.githubusercontent.com/u/228533731?s=64&v=4)](https://github.com/elestirelbilinc-sketch)
      
  *   [![@brokemac79](https://avatars.githubusercontent.com/u/255583030?s=64&v=4)](https://github.com/brokemac79)
      
  
  You can’t perform that action at this time.
  --- End Content ---

I built MARVIN, my personal AI agent, and now 4 of my colleagues ...
  URL: https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/
  Jan 24, 2026 ... ... markdown files for skills, memory, and state. It's low ... The skills/ is where all the template skills are located with a skill creator ...

  --- Content ---
  [Skip to main content](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/#main-content)
   I built MARVIN, my personal AI agent, and now 4 of my colleagues are using him too. : r/ClaudeAI
  
  [![r/ClaudeAI icon](https://styles.redditmedia.com/t5_7t8hvt/styles/communityIcon_97yk0vsmp4cf1.png?width=96&height=96&frame=1&auto=webp&crop=96%3A96%2Csmart&s=de73db6eb89604488f2125b81c2080f7a14c2a38)\
  \
  Go to ClaudeAI](https://www.reddit.com/r/ClaudeAI/)
  
  [r/ClaudeAI](https://www.reddit.com/r/ClaudeAI/) • 8d ago
  
  [RealSaltLakeRioT](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  [繁體中文](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=zh-hant)
  [Tiếng Việt](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=vi)
  [日本語](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=ja)
  [简体中文](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=zh-hans)
  [Português (Brasil)](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=pt-br)
  [Español (España)](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=es-es)
  [Ελληνικά](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=el)
  [Dansk](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=da)
  [ไทย](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=th)
  [Srpski](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=sr)
  [한국어](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=ko)
  [Română](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=ro)
  [Norsk (Bokmål)](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=no)
  [Deutsch](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=de)
  [Українська](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=uk)
  [Svenska](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=sv)
  [Filipino](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=fil)
  [Suomi](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=fi)
  
  I built MARVIN, my personal AI agent, and now 4 of my colleagues are using him too.
  ===================================================================================
  
  Over the holiday break, like a lot of other devs, I sat around and started building stuff. One of them was a personal assistant agent that I call MARVIN (yes, that Marvin from Hitchhiker's Guide to the Galaxy). MARVIN runs on Claude Code as the harness.
  
  At first I just wanted him to help me keep up with my emails, both personal and work. Then I added calendars. Then Jira. Then Confluence, Attio, Granola, and more. Before I realized it, I'd built 15+ integrations and MCP servers into a system that actually knows how I work.
  
  But it was just a pet project. I didn't expect it to leave my laptop.
  
  A few weeks ago, I showed a colleague on our marketing team what MARVIN could do. She asked if she could use him too. I onboarded her, and 30 minutes later she messaged me: "I just got something done in 30 minutes that normally would've taken me 4+ hours. He's my new bestie."
  
  She started telling other colleagues. Yesterday I onboarded two more. Last night, another. One of them messaged me almost immediately: "Holy shit. I forgot to paste a Confluence link I was referring to and MARVIN beat me to it." MARVIN had inferred from context what doc he needed, pulled it from Confluence, and updated his local files before he even asked.
  
  Four people in two weeks, all from word of mouth. That's when I realized this thing might actually be useful beyond my laptop.
  
  Here's what I've learned about building agents:
  
  **1\. Real agents are** _**messy**_\*\*. They have to be customizable.\*\*
  
  It's not one size fits all. MARVIN knows my writing style, my goals, my family's schedule, my boss's name. He knows I hate sycophantic AI responses. He knows not to use em dashes in my writing. That context makes him useful. Without it, he'd just be another chatbot.
  
  **2\. Personality matters more than I expected.**
  
  MARVIN is named after the Paranoid Android for a reason. He's sardonic. He sighs dramatically before checking my email. When something breaks, he says "Well, that's exactly what I expected to happen." This sounds like a gimmick, but it actually makes the interaction feel less like using a tool and more like working with a (slightly pessimistic) colleague. I find myself actually wanting to work with him, which means I use him more, which means he gets better.
  
  **3\. Persistent memory is hard. Context rot is real.**
  
  MARVIN uses a bookend approach to the day. `/marvin` starts the session by reading `state/current.md` to see what happened yesterday, including all tasks and context. `/end` closes the session by breaking everything into commits, generating an end-of-day report, and updating `current.md` for tomorrow. Throughout the day, `/update` checkpoints progress so context isn't lost when Claude compacts or I start another session.
  
  **4\. Markdown is the new coding language for agents.**
  
  Structured formatting helps MARVIN stay organized. Skills live in markdown files. State lives in markdown. Session logs are markdown. Since there's no fancy UI, my marketing colleagues can open any `.md` file in Cursor and see exactly what's happening. Low overhead, high visibility.
  
  **5\. You have to train your agent. You won't one-shot it.**
  
  If I hired a human assistant, I'd give them 3 months before expecting them to be truly helpful. They'd need to learn processes, find information, understand context. Agents are the same. I didn't hand MARVIN my email and say "go." I started with one email I needed to respond to. We drafted a response together. When it was good, I gave MARVIN feedback and had him update his skills. Then we did it again. After 30 minutes of iteration, I had confidence that MARVIN could respond in my voice to emails that needed attention.
  
  **The impact:**
  
  I've been training and using MARVIN for 3 weeks. I've done more in a week than I used to do in a month. In the last 3 weeks I've:
  
  *   3 CFPs submitted
      
  *   2 personal blogs published + 5 in draft
      
  *   2 work blogs published + 3 in draft
      
  *   6+ meetups created with full speaker lineups
      
  *   4 colleagues onboarded
      
  *   15+ integrations built or enhanced
      
  *   25 skills operational
      
  
  I went from "I want to triage my email" to "I have a replicable AI chief of staff that non-technical marketers are setting up themselves" in 3 weeks.
  
  The best part is that I'm stepping away from work earlier to spend time with my kids. I'm not checking slack or email during dinner. I turn them off. I know that MARVIN will help me stay on top of things tomorrow. I'm taking time for myself, which hasn't happened in a long time. I've always felt underwater with my job, but now I've got it in hand.
  
  Read more
  
  Share
  
  * * *
  
  [![u/ClaudeAI-mod-bot avatar](https://styles.redditmedia.com/t5_f6scc2/styles/profileIcon_ww9fzh4n2jjf1.jpg?width=64&height=64&frame=1&auto=webp&crop=64%3A64%2Csmart&s=d876dfd5e7f169e74f9abac26d8c55a73974df4a)](https://www.reddit.com/user/ClaudeAI-mod-bot/)
  
  [ClaudeAI-mod-bot](https://www.reddit.com/user/ClaudeAI-mod-bot/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1ie0mh/)
  
  **TL;DR generated automatically after 100 comments.**
  
  Alright, let's get you up to speed. The thread is overwhelmingly positive, and everyone thinks OP's [personal AI agent](https://www.reddit.com/search/?q=building+personal+AI+agent&cId=414f59eb-c018-42e4-87d7-64f8a9b9faa9&iId=b035cc9c-7771-4c2c-b301-1d213ce3ec51) , MARVIN, is awesome.
  
  **The consensus is that building your own customizable, trainable AI assistant is a massive productivity hack, and OP's project is a fantastic example of how to do it right.** OP even dropped the GitHub link in the top comment so you can try it yourself.
  
  Here's the breakdown of the chatter:
  
  *   **How it works:** It's not some black box. MARVIN runs on Claude Code in the terminal, using a clever system of markdown files for skills, memory, and state. It's low-tech on the surface but powerful under the hood.
      
  *   **You're not alone:** A lot of you are building similar personal agents. Commenters mentioned using setups with Obsidian (like "Claudesidian") and other tools. The creator of another popular agent, "Doris," even showed up to compare notes with OP. It's a whole vibe.
      
  *   **The "Normie" Problem:** A key challenge OP and others have found is onboarding non-technical folks. Getting your marketing colleagues comfortable with the terminal and markdown is the real final boss.
      
  *   **Security Alert:** One sharp-eyed user spotted a hardcoded Google Client ID in the GitHub repo. OP confirmed it was a mistake and has since pushed a fix. Good looking out, team.
      
  *   **What's next?** OP uses a Telegram integration for their personal MARVIN and plans to add it to the public template. There's also talk of moving to a local AI model for better privacy and to have the agent running 24/7.
      
  
  1
  
   1 more reply
  
  1 more reply[Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1ie0mh/?force-legacy-sct=1)
  
  [](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  [RealSaltLakeRioT](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1gzbuf/)
  
  If you wanna try him out yourself, here is the link: [https://github.com/SterlingChin/marvin-template](https://github.com/SterlingChin/marvin-template)
  
  I'd love your feedback and criticism. Reddit, do your thing. :P
  
  135
  
  [![u/nickkickers avatar](https://www.redditstatic.com/avatars/defaults/v2/avatar_default_4.png)](https://www.reddit.com/user/nickkickers/)
  
  [nickkickers](https://www.reddit.com/user/nickkickers/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1hddqq/)
  
  Just started! Super user friendly. I want to start using it! Can you let me know the secret ;)
  
  11
  
  [](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  [RealSaltLakeRioT](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1heuvn/)
  
  Treat him like you're onboarding a new junior assistant or dev. Be patient and provide feedback. Teaching him is key to being successful. He won't be right the first time all the time. So provide him feedback. I'm always telling my Marvin to update our workflow and skills so we don't make the same mistake the next time.
  
  21
  
  [](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  [RealSaltLakeRioT](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1hezdz/)
  
  Can't wait to hear your feedback! Let me know how it goes!
  
  4
  
   1 more reply
  
  1 more reply[Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1hezdz/?force-legacy-sct=1) [Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1hddqq/?force-legacy-sct=1)
  
  [](https://www.reddit.com/user/Ok_Locksmith_8260/)
  
  [Ok\_Locksmith\_8260](https://www.reddit.com/user/Ok_Locksmith_8260/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1h5gpj/)
  
  Looks cool! Did you think of integrating with Clawdbot or one of those tools for a sturdier ecosystem? What about security ?
  
  5
  
  [](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  [RealSaltLakeRioT](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1h6yjs/)
  
  Haha, not the first time MARVIN has been compared to Clawdbot. Honestly, I built MARVIN on my own and didn't even hear about Clawdbot until after I'd been using him for a while.
  
  I need to look more into Clawdbot and see if there is a larger ecosystem I can help with.
  
  Security is all local. For my marketing colleagues, I set up a developer Google project that they connect to so it keeps that all in house. The other MCP servers, like Atlassian all have their own auth.
  
  All work is done behind the VPN, so I'm not worried _yet_ about major security issues.
  
  7
  
   1 more reply
  
  1 more reply[Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1h6yjs/?force-legacy-sct=1)
    1 more reply
  
  1 more reply
  
  [Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1h5gpj/?force-legacy-sct=1)
    5 more replies
  
  5 more replies
  
  [Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1gzbuf/?force-legacy-sct=1)
  
  [](https://www.reddit.com/user/AncientFudge1984/)
  
  [AncientFudge1984](https://www.reddit.com/user/AncientFudge1984/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1i5yv4/)
  
  Hey, I was looking at the Google Workspace setup script and noticed it uses a hardcoded [OAuth Client ID](https://www.reddit.com/search/?q=Google+Workspace+OAuth+Client+ID+security&cId=5f6a2c63-5de4-46dd-ae17-6216f1565b5b&iId=cf208be5-9a6b-42f9-b3d1-8cb09d49de11) . Was that intentional for convenience, or should users be setting up their own Google Cloud credentials? Just want to understand the security model before connecting my accounts.
  
  17
  
  [](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  [RealSaltLakeRioT](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1i7qag/)
  
  Holy crap, that was supposed to be removed. Thanks for catching that!
  
  12
  
  [![u/nickkickers avatar](https://www.redditstatic.com/avatars/defaults/v2/avatar_default_4.png)](https://www.reddit.com/user/nickkickers/)
  
  [nickkickers](https://www.reddit.com/user/nickkickers/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1klp59/)
  
  I ran into this too!
  
  4
  
   2 more replies
  
  2 more replies[Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1klp59/?force-legacy-sct=1) [Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1i7qag/?force-legacy-sct=1) [Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1i5yv4/?force-legacy-sct=1)
  
  [![u/C1rc1es avatar](https://www.redditstatic.com/avatars/defaults/v2/avatar_default_3.png)](https://www.reddit.com/user/C1rc1es/)
  
  [C1rc1es](https://www.reddit.com/user/C1rc1es/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1h8vgy/)
  
  I did the same thing using CC as the harness but went for a PA with Claude’s default personality. It’s worth sharing the idea but frankly everyone has a unique style of working and communicating I think they should build their own and tune it as they go. Took 1 days to build out the tools, 1 week to tune through daily discourse and now it does 95% of my work admin. Everyone deserves a personal AI assistant.
  
  14
  
  [](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  [RealSaltLakeRioT](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1h9qjb/)
  
  Because I'm a developer it's easy to add the integrations, but while I was onboarding the marketers I was recording the sessions to get feedback on where the pain points were for them. It's really intimidating to use a coding tool if you're non-technical. After an hour onboarding session, I made some major changes to the onboarding to make it easier for them. Hopefully this can continue to grow.
  
  And yes, everyone deserves a personal AI assistant.
  
  7
  
   2 more replies
  
  2 more replies[Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1h9qjb/?force-legacy-sct=1) [Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1h8vgy/?force-legacy-sct=1)
  
  [![u/Cute_Witness3405 avatar](https://www.redditstatic.com/avatars/defaults/v2/avatar_default_1.png)](https://www.reddit.com/user/Cute_Witness3405/)
  
  [Cute\_Witness3405](https://www.reddit.com/user/Cute_Witness3405/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1hvks7/)
  
  Cool project. I looked at the skills and it became clear that this is pretty focused on people who create content for a living. Might be helpful to edit your post to be more clear about that up front. Or share other use cases that are outside that which you’ve found it to work well for. Most people don’t do what you do.
  
  14
  
  [](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  [RealSaltLakeRioT](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1hxa3q/)
  
  That's great feedback. And you're right, I've stepped back from writing code all day and do more writing. If others start to adopt him, I'll for sure make updates to him. Right now my user base is from the marketing team at my company, so the template has been maximized for them.
  
  4
  
  [Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1hvks7/?force-legacy-sct=1)
  
  [](https://www.reddit.com/user/grindbehind/)
  
  [grindbehind](https://www.reddit.com/user/grindbehind/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1h8d2l/)
  
  This is awesome. These are the sort of AI experiments I like.
  
  Any particular challenges or frustrations in getting this going?
  
  And can it remind me to bring a towel?
  
  20
  
  [](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  [RealSaltLakeRioT](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1hamtp/)
  
  Thanks! It's been a lot of fun to build him.
  
  The challenges I'm facing are getting non-technical people onboarded. Teaching them markdown and the terminal has been hard. This is where [AI adoption](https://www.reddit.com/search/?q=AI+adoption+challenges&cId=ebb274eb-810b-49cc-941c-bf31a0463136&iId=21657f17-80f2-4506-8aea-bcd2564bdfb4) is really going to get stuck. We have to make it easy for the normies to use it and see the value.
  
  And my Marvin is dry and sarcastic, and swears. In the personality section my favorite line is
  
  > a well placed "for fuck's sake" is always a good choice
  
  11
  
   5 more replies
  
  5 more replies[Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1hamtp/?force-legacy-sct=1) [Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1h8d2l/?force-legacy-sct=1)
  
  [](https://www.reddit.com/user/NunoM21/)
  
  [NunoM21](https://www.reddit.com/user/NunoM21/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1ilbwt/)
  
  This is actually great, props! I’m curious on how you actually use it day to day. One thing that immediately comes to mind (as a developer) is to link something like this to Discord/Telegram/WhatsApp to improve UX. Is that something you tested or even considered doing?
  
  9
  
  [](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  [RealSaltLakeRioT](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1iw1st/)
  
  My personal MARVIN setup uses Telegram! I can use him wherever I am if it's running on my machine. It's why I'm getting a Linux box. But for right now, getting my colleagues in marketing set up was my first priority. I'm adding new MCP servers and telegram soon.
  
  6
  
   1 more reply
  
  1 more reply[Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1iw1st/?force-legacy-sct=1)
  [](https://www.reddit.com/user/Hileotech/)
  
  [Hileotech](https://www.reddit.com/user/Hileotech/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1iuu8u/)
  
  +1 for WhatsApp… possibly avoiding Business API because I can’t get them (I don't have a VAT number so I can't access the WhatsApp Business API).
  
  5
  
   4 more replies
  
  4 more replies[Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1iuu8u/?force-legacy-sct=1) [Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1ilbwt/?force-legacy-sct=1)
  
  [![u/grandeparade avatar](https://www.redditstatic.com/avatars/defaults/v2/avatar_default_3.png)](https://www.reddit.com/user/grandeparade/)
  
  [grandeparade](https://www.reddit.com/user/grandeparade/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1iep0e/)
  
  It's like Claude running inside an Obsidian vault, with custom skills and commands, right?
  
  Like this project: [https://github.com/heyitsnoah/claudesidian](https://github.com/heyitsnoah/claudesidian)
  
  Been using something similar for 3 months. It's been life changing. Will look into yours as well 👍
  
  6
  
   8 more replies
  
  8 more replies[Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1iep0e/?force-legacy-sct=1)
  
  [![u/shan23 avatar](https://www.redditstatic.com/avatars/defaults/v2/avatar_default_1.png)](https://www.reddit.com/user/shan23/)
  
  [shan23](https://www.reddit.com/user/shan23/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1hcyho/)
  
  What is the architecture?
  
  4
  
  [](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  [RealSaltLakeRioT](https://www.reddit.com/user/RealSaltLakeRioT/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1hhmmi/)
  
  Claude Code is the harness. I have a `.marvin` where all the machinery is located. These are the onboarding stuff, core scripts and MCP server setups. The `skills/` is where all the template skills are located with a skill creator skill (yes, I added that, because he was struggling making skills for non-tech users).
  
  The `CLAUDE.md` file is where Marvin is directed to save all core personality, details that act as core memories (like names of people I talk about all the time, like my boss and colleagues), goals, and the skills index
  
  The rest are folders of markdown where we organize everything, like sessions, end of week reports, current state, research etc. The user can add new folders based on their needs and use cases.
  
  6
  
  [Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1hcyho/?force-legacy-sct=1)
  
  [](https://www.reddit.com/user/spacenglish/)
  
  [spacenglish](https://www.reddit.com/user/spacenglish/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1j941v/)
  
  This is interesting, kudos! I have been thinking about creating something for my own use. Where do you recommend I should begin?
  
  And with Marvin how do you manage context and tokens?
  
  4
  
  [](https://www.reddit.com/user/green_skies_258/)
  
  [green\_skies\_258](https://www.reddit.com/user/green_skies_258/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1mrons/)
  
  If anyone is leaving under a rock, just use Clawdbot instead.
  
  [https://clawd.bot](https://clawd.bot/)
  
  4
  
   5 more replies
  
  5 more replies[Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1mrons/?force-legacy-sct=1)
  [](https://www.reddit.com/user/OldError7529/)
  
  [OldError7529](https://www.reddit.com/user/OldError7529/)
  
  • [8d ago](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1ha2bj/)
  
  This is so good. Thank you for sharing. I couldn’t agree more with points 3-5. I’ve spent a lot of time thinking about and working on these pieces, and you’ve provided valuable confirmation and ideas.
  
  3
  
   1 more reply
  
  1 more reply[Continue this thread](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/comment/o1ha2bj/?force-legacy-sct=1) 
  
  * * *
  
  View Post in
  
  
  ----------------
  
  [हिन्दी](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=hi)
  
  [Français](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=fr)
  
  [Русский](https://www.reddit.com/r/ClaudeAI/comments/1qlurq6/i_built_marvin_my_personal_ai_agent_and_now_4_of/?tl=ru)
  
  [Reddit Rules](https://www.redditinc.com/policies/content-policy) [Privacy Policy](https://www.reddit.com/policies/privacy-policy) [User Agreement](https://www.redditinc.com/policies/user-agreement) [Your Privacy Choices](https://support.reddithelp.com/hc/articles/43980704794004) [Accessibility](https://support.reddithelp.com/hc/sections/38303584022676-Accessibility) [Reddit, Inc. © 2026. All rights reserved.](https://redditinc.com/)
  
  Expand Navigation Collapse Navigation
  
  ![](https://id.rlcdn.com/472486.gif)
  --- End Content ---

skill-creator - Agent Skill by openclaw | SkillsMP
  URL: https://skillsmp.com/skills/openclaw-openclaw-skills-skill-creator-skill-md
  Skill Creator This skill provides guidance for creating effective skills. About Skills Skills are modular, self-contained packages that extend Codex's capabilities by providing specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific domains or tasks—they transform Codex from a general-purpose agent into a specialized agent equipped with procedural ...
