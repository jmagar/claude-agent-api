Cron Jobs - OpenClaw
  URL: https://docs.openclaw.ai/automation/cron-jobs
  Cron vs Heartbeat? See Cron vs Heartbeat for guidance on when to use each. Cron is the Gateway's built-in scheduler. It persists jobs, wakes the agent at the right time, and can optionally deliver output back to a chat. If you want "run this every morning" or "poke the agent in 20 minutes", cron is the mechanism.

  --- Content ---
  [Skip to main content](https://docs.openclaw.ai/automation/cron-jobs#content-area)
  
  [OpenClaw home page![light logo](https://mintcdn.com/clawdhub/4rYvG-uuZrMK_URE/assets/pixel-lobster.svg?fit=max&auto=format&n=4rYvG-uuZrMK_URE&q=85&s=da2032e9eac3b5d9bfe7eb96ca6a8a26)![dark logo](https://mintcdn.com/clawdhub/4rYvG-uuZrMK_URE/assets/pixel-lobster.svg?fit=max&auto=format&n=4rYvG-uuZrMK_URE&q=85&s=da2032e9eac3b5d9bfe7eb96ca6a8a26)](https://docs.openclaw.ai/)
  
  ![US](https://d3gk2c5xim1je2.cloudfront.net/flags/US.svg)
  
  English
  
  Search...
  
  Ctrl K
  
  Search...
  
  Navigation
  
  Automation & Hooks
  
  Cron Jobs
  
  On this page
  
  *   [Cron jobs (Gateway scheduler)](https://docs.openclaw.ai/automation/cron-jobs#cron-jobs-gateway-scheduler)
      
  *   [TL;DR](https://docs.openclaw.ai/automation/cron-jobs#tl%3Bdr)
      
  *   [Quick start (actionable)](https://docs.openclaw.ai/automation/cron-jobs#quick-start-actionable)
      
  *   [Tool-call equivalents (Gateway cron tool)](https://docs.openclaw.ai/automation/cron-jobs#tool-call-equivalents-gateway-cron-tool)
      
  *   [Where cron jobs are stored](https://docs.openclaw.ai/automation/cron-jobs#where-cron-jobs-are-stored)
      
  *   [Beginner-friendly overview](https://docs.openclaw.ai/automation/cron-jobs#beginner-friendly-overview)
      
  *   [Concepts](https://docs.openclaw.ai/automation/cron-jobs#concepts)
      
  *   [Jobs](https://docs.openclaw.ai/automation/cron-jobs#jobs)
      
  *   [Schedules](https://docs.openclaw.ai/automation/cron-jobs#schedules)
      
  *   [Main vs isolated execution](https://docs.openclaw.ai/automation/cron-jobs#main-vs-isolated-execution)
      
  *   [Main session jobs (system events)](https://docs.openclaw.ai/automation/cron-jobs#main-session-jobs-system-events)
      
  *   [Isolated jobs (dedicated cron sessions)](https://docs.openclaw.ai/automation/cron-jobs#isolated-jobs-dedicated-cron-sessions)
      
  *   [Payload shapes (what runs)](https://docs.openclaw.ai/automation/cron-jobs#payload-shapes-what-runs)
      
  *   [Model and thinking overrides](https://docs.openclaw.ai/automation/cron-jobs#model-and-thinking-overrides)
      
  *   [Delivery (channel + target)](https://docs.openclaw.ai/automation/cron-jobs#delivery-channel-%2B-target)
      
  *   [Telegram delivery targets (topics / forum threads)](https://docs.openclaw.ai/automation/cron-jobs#telegram-delivery-targets-topics-%2F-forum-threads)
      
  *   [JSON schema for tool calls](https://docs.openclaw.ai/automation/cron-jobs#json-schema-for-tool-calls)
      
  *   [cron.add params](https://docs.openclaw.ai/automation/cron-jobs#cron-add-params)
      
  *   [cron.update params](https://docs.openclaw.ai/automation/cron-jobs#cron-update-params)
      
  *   [cron.run and cron.remove params](https://docs.openclaw.ai/automation/cron-jobs#cron-run-and-cron-remove-params)
      
  *   [Storage & history](https://docs.openclaw.ai/automation/cron-jobs#storage-%26-history)
      
  *   [Configuration](https://docs.openclaw.ai/automation/cron-jobs#configuration)
      
  *   [CLI quickstart](https://docs.openclaw.ai/automation/cron-jobs#cli-quickstart)
      
  *   [Gateway API surface](https://docs.openclaw.ai/automation/cron-jobs#gateway-api-surface)
      
  *   [Troubleshooting](https://docs.openclaw.ai/automation/cron-jobs#troubleshooting)
      
  *   [“Nothing runs”](https://docs.openclaw.ai/automation/cron-jobs#%E2%80%9Cnothing-runs%E2%80%9D)
      
  *   [Telegram delivers to the wrong place](https://docs.openclaw.ai/automation/cron-jobs#telegram-delivers-to-the-wrong-place)
      
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#cron-jobs-gateway-scheduler)
  
  Cron jobs (Gateway scheduler)
  ===============================================================================================================
  
  > **Cron vs Heartbeat?** See [Cron vs Heartbeat](https://docs.openclaw.ai/automation/cron-vs-heartbeat)
  >  for guidance on when to use each.
  
  Cron is the Gateway’s built-in scheduler. It persists jobs, wakes the agent at the right time, and can optionally deliver output back to a chat. If you want _“run this every morning”_ or _“poke the agent in 20 minutes”_, cron is the mechanism.
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#tl;dr)
  
  TL;DR
  -----------------------------------------------------------------
  
  *   Cron runs **inside the Gateway** (not inside the model).
  *   Jobs persist under `~/.openclaw/cron/` so restarts don’t lose schedules.
  *   Two execution styles:
      *   **Main session**: enqueue a system event, then run on the next heartbeat.
      *   **Isolated**: run a dedicated agent turn in `cron:<jobId>`, optionally deliver output.
  *   Wakeups are first-class: a job can request “wake now” vs “next heartbeat”.
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#quick-start-actionable)
  
  Quick start (actionable)
  -----------------------------------------------------------------------------------------------------
  
  Create a one-shot reminder, verify it exists, and run it immediately:
  
  Copy
  
      openclaw cron add \
        --name "Reminder" \
        --at "2026-02-01T16:00:00Z" \
        --session main \
        --system-event "Reminder: check the cron docs draft" \
        --wake now \
        --delete-after-run
      
      openclaw cron list
      openclaw cron run <job-id> --force
      openclaw cron runs --id <job-id>
      
  
  Schedule a recurring isolated job with delivery:
  
  Copy
  
      openclaw cron add \
        --name "Morning brief" \
        --cron "0 7 * * *" \
        --tz "America/Los_Angeles" \
        --session isolated \
        --message "Summarize overnight updates." \
        --deliver \
        --channel slack \
        --to "channel:C1234567890"
      
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#tool-call-equivalents-gateway-cron-tool)
  
  Tool-call equivalents (Gateway cron tool)
  ---------------------------------------------------------------------------------------------------------------------------------------
  
  For the canonical JSON shapes and examples, see [JSON schema for tool calls](https://docs.openclaw.ai/automation/cron-jobs#json-schema-for-tool-calls)
  .
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#where-cron-jobs-are-stored)
  
  Where cron jobs are stored
  -----------------------------------------------------------------------------------------------------------
  
  Cron jobs are persisted on the Gateway host at `~/.openclaw/cron/jobs.json` by default. The Gateway loads the file into memory and writes it back on changes, so manual edits are only safe when the Gateway is stopped. Prefer `openclaw cron add/edit` or the cron tool call API for changes.
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#beginner-friendly-overview)
  
  Beginner-friendly overview
  -----------------------------------------------------------------------------------------------------------
  
  Think of a cron job as: **when** to run + **what** to do.
  
  1.  **Choose a schedule**
      *   One-shot reminder → `schedule.kind = "at"` (CLI: `--at`)
      *   Repeating job → `schedule.kind = "every"` or `schedule.kind = "cron"`
      *   If your ISO timestamp omits a timezone, it is treated as **UTC**.
  2.  **Choose where it runs**
      *   `sessionTarget: "main"` → run during the next heartbeat with main context.
      *   `sessionTarget: "isolated"` → run a dedicated agent turn in `cron:<jobId>`.
  3.  **Choose the payload**
      *   Main session → `payload.kind = "systemEvent"`
      *   Isolated session → `payload.kind = "agentTurn"`
  
  Optional: `deleteAfterRun: true` removes successful one-shot jobs from the store.
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#concepts)
  
  Concepts
  -----------------------------------------------------------------------
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#jobs)
  
  Jobs
  
  A cron job is a stored record with:
  
  *   a **schedule** (when it should run),
  *   a **payload** (what it should do),
  *   optional **delivery** (where output should be sent).
  *   optional **agent binding** (`agentId`): run the job under a specific agent; if missing or unknown, the gateway falls back to the default agent.
  
  Jobs are identified by a stable `jobId` (used by CLI/Gateway APIs). In agent tool calls, `jobId` is canonical; legacy `id` is accepted for compatibility. Jobs can optionally auto-delete after a successful one-shot run via `deleteAfterRun: true`.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#schedules)
  
  Schedules
  
  Cron supports three schedule kinds:
  
  *   `at`: one-shot timestamp (ms since epoch). Gateway accepts ISO 8601 and coerces to UTC.
  *   `every`: fixed interval (ms).
  *   `cron`: 5-field cron expression with optional IANA timezone.
  
  Cron expressions use `croner`. If a timezone is omitted, the Gateway host’s local timezone is used.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#main-vs-isolated-execution)
  
  Main vs isolated execution
  
  #### 
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#main-session-jobs-system-events)
  
  Main session jobs (system events)
  
  Main jobs enqueue a system event and optionally wake the heartbeat runner. They must use `payload.kind = "systemEvent"`.
  
  *   `wakeMode: "next-heartbeat"` (default): event waits for the next scheduled heartbeat.
  *   `wakeMode: "now"`: event triggers an immediate heartbeat run.
  
  This is the best fit when you want the normal heartbeat prompt + main-session context. See [Heartbeat](https://docs.openclaw.ai/gateway/heartbeat)
  .
  
  #### 
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#isolated-jobs-dedicated-cron-sessions)
  
  Isolated jobs (dedicated cron sessions)
  
  Isolated jobs run a dedicated agent turn in session `cron:<jobId>`. Key behaviors:
  
  *   Prompt is prefixed with `[cron:<jobId> <job name>]` for traceability.
  *   Each run starts a **fresh session id** (no prior conversation carry-over).
  *   A summary is posted to the main session (prefix `Cron`, configurable).
  *   `wakeMode: "now"` triggers an immediate heartbeat after posting the summary.
  *   If `payload.deliver: true`, output is delivered to a channel; otherwise it stays internal.
  
  Use isolated jobs for noisy, frequent, or “background chores” that shouldn’t spam your main chat history.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#payload-shapes-what-runs)
  
  Payload shapes (what runs)
  
  Two payload kinds are supported:
  
  *   `systemEvent`: main-session only, routed through the heartbeat prompt.
  *   `agentTurn`: isolated-session only, runs a dedicated agent turn.
  
  Common `agentTurn` fields:
  
  *   `message`: required text prompt.
  *   `model` / `thinking`: optional overrides (see below).
  *   `timeoutSeconds`: optional timeout override.
  *   `deliver`: `true` to send output to a channel target.
  *   `channel`: `last` or a specific channel.
  *   `to`: channel-specific target (phone/chat/channel id).
  *   `bestEffortDeliver`: avoid failing the job if delivery fails.
  
  Isolation options (only for `session=isolated`):
  
  *   `postToMainPrefix` (CLI: `--post-prefix`): prefix for the system event in main.
  *   `postToMainMode`: `summary` (default) or `full`.
  *   `postToMainMaxChars`: max chars when `postToMainMode=full` (default 8000).
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#model-and-thinking-overrides)
  
  Model and thinking overrides
  
  Isolated jobs (`agentTurn`) can override the model and thinking level:
  
  *   `model`: Provider/model string (e.g., `anthropic/claude-sonnet-4-20250514`) or alias (e.g., `opus`)
  *   `thinking`: Thinking level (`off`, `minimal`, `low`, `medium`, `high`, `xhigh`; GPT-5.2 + Codex models only)
  
  Note: You can set `model` on main-session jobs too, but it changes the shared main session model. We recommend model overrides only for isolated jobs to avoid unexpected context shifts. Resolution priority:
  
  1.  Job payload override (highest)
  2.  Hook-specific defaults (e.g., `hooks.gmail.model`)
  3.  Agent config default
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#delivery-channel-+-target)
  
  Delivery (channel + target)
  
  Isolated jobs can deliver output to a channel. The job payload can specify:
  
  *   `channel`: `whatsapp` / `telegram` / `discord` / `slack` / `mattermost` (plugin) / `signal` / `imessage` / `last`
  *   `to`: channel-specific recipient target
  
  If `channel` or `to` is omitted, cron can fall back to the main session’s “last route” (the last place the agent replied). Delivery notes:
  
  *   If `to` is set, cron auto-delivers the agent’s final output even if `deliver` is omitted.
  *   Use `deliver: true` when you want last-route delivery without an explicit `to`.
  *   Use `deliver: false` to keep output internal even if a `to` is present.
  
  Target format reminders:
  
  *   Slack/Discord/Mattermost (plugin) targets should use explicit prefixes (e.g. `channel:<id>`, `user:<id>`) to avoid ambiguity.
  *   Telegram topics should use the `:topic:` form (see below).
  
  #### 
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#telegram-delivery-targets-topics-/-forum-threads)
  
  Telegram delivery targets (topics / forum threads)
  
  Telegram supports forum topics via `message_thread_id`. For cron delivery, you can encode the topic/thread into the `to` field:
  
  *   `-1001234567890` (chat id only)
  *   `-1001234567890:topic:123` (preferred: explicit topic marker)
  *   `-1001234567890:123` (shorthand: numeric suffix)
  
  Prefixed targets like `telegram:...` / `telegram:group:...` are also accepted:
  
  *   `telegram:group:-1001234567890:topic:123`
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#json-schema-for-tool-calls)
  
  JSON schema for tool calls
  -----------------------------------------------------------------------------------------------------------
  
  Use these shapes when calling Gateway `cron.*` tools directly (agent tool calls or RPC). CLI flags accept human durations like `20m`, but tool calls use epoch milliseconds for `atMs` and `everyMs` (ISO timestamps are accepted for `at` times).
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#cron-add-params)
  
  cron.add params
  
  One-shot, main session job (system event):
  
  Copy
  
      {
        "name": "Reminder",
        "schedule": { "kind": "at", "atMs": 1738262400000 },
        "sessionTarget": "main",
        "wakeMode": "now",
        "payload": { "kind": "systemEvent", "text": "Reminder text" },
        "deleteAfterRun": true
      }
      
  
  Recurring, isolated job with delivery:
  
  Copy
  
      {
        "name": "Morning brief",
        "schedule": { "kind": "cron", "expr": "0 7 * * *", "tz": "America/Los_Angeles" },
        "sessionTarget": "isolated",
        "wakeMode": "next-heartbeat",
        "payload": {
          "kind": "agentTurn",
          "message": "Summarize overnight updates.",
          "deliver": true,
          "channel": "slack",
          "to": "channel:C1234567890",
          "bestEffortDeliver": true
        },
        "isolation": { "postToMainPrefix": "Cron", "postToMainMode": "summary" }
      }
      
  
  Notes:
  
  *   `schedule.kind`: `at` (`atMs`), `every` (`everyMs`), or `cron` (`expr`, optional `tz`).
  *   `atMs` and `everyMs` are epoch milliseconds.
  *   `sessionTarget` must be `"main"` or `"isolated"` and must match `payload.kind`.
  *   Optional fields: `agentId`, `description`, `enabled`, `deleteAfterRun`, `isolation`.
  *   `wakeMode` defaults to `"next-heartbeat"` when omitted.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#cron-update-params)
  
  cron.update params
  
  Copy
  
      {
        "jobId": "job-123",
        "patch": {
          "enabled": false,
          "schedule": { "kind": "every", "everyMs": 3600000 }
        }
      }
      
  
  Notes:
  
  *   `jobId` is canonical; `id` is accepted for compatibility.
  *   Use `agentId: null` in the patch to clear an agent binding.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#cron-run-and-cron-remove-params)
  
  cron.run and cron.remove params
  
  Copy
  
      { "jobId": "job-123", "mode": "force" }
      
  
  Copy
  
      { "jobId": "job-123" }
      
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#storage-&-history)
  
  Storage & history
  -----------------------------------------------------------------------------------------
  
  *   Job store: `~/.openclaw/cron/jobs.json` (Gateway-managed JSON).
  *   Run history: `~/.openclaw/cron/runs/<jobId>.jsonl` (JSONL, auto-pruned).
  *   Override store path: `cron.store` in config.
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#configuration)
  
  Configuration
  ---------------------------------------------------------------------------------
  
  Copy
  
      {
        cron: {
          enabled: true, // default true
          store: "~/.openclaw/cron/jobs.json",
          maxConcurrentRuns: 1, // default 1
        },
      }
      
  
  Disable cron entirely:
  
  *   `cron.enabled: false` (config)
  *   `OPENCLAW_SKIP_CRON=1` (env)
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#cli-quickstart)
  
  CLI quickstart
  -----------------------------------------------------------------------------------
  
  One-shot reminder (UTC ISO, auto-delete after success):
  
  Copy
  
      openclaw cron add \
        --name "Send reminder" \
        --at "2026-01-12T18:00:00Z" \
        --session main \
        --system-event "Reminder: submit expense report." \
        --wake now \
        --delete-after-run
      
  
  One-shot reminder (main session, wake immediately):
  
  Copy
  
      openclaw cron add \
        --name "Calendar check" \
        --at "20m" \
        --session main \
        --system-event "Next heartbeat: check calendar." \
        --wake now
      
  
  Recurring isolated job (deliver to WhatsApp):
  
  Copy
  
      openclaw cron add \
        --name "Morning status" \
        --cron "0 7 * * *" \
        --tz "America/Los_Angeles" \
        --session isolated \
        --message "Summarize inbox + calendar for today." \
        --deliver \
        --channel whatsapp \
        --to "+15551234567"
      
  
  Recurring isolated job (deliver to a Telegram topic):
  
  Copy
  
      openclaw cron add \
        --name "Nightly summary (topic)" \
        --cron "0 22 * * *" \
        --tz "America/Los_Angeles" \
        --session isolated \
        --message "Summarize today; send to the nightly topic." \
        --deliver \
        --channel telegram \
        --to "-1001234567890:topic:123"
      
  
  Isolated job with model and thinking override:
  
  Copy
  
      openclaw cron add \
        --name "Deep analysis" \
        --cron "0 6 * * 1" \
        --tz "America/Los_Angeles" \
        --session isolated \
        --message "Weekly deep analysis of project progress." \
        --model "opus" \
        --thinking high \
        --deliver \
        --channel whatsapp \
        --to "+15551234567"
      
  
  Agent selection (multi-agent setups):
  
  Copy
  
      # Pin a job to agent "ops" (falls back to default if that agent is missing)
      openclaw cron add --name "Ops sweep" --cron "0 6 * * *" --session isolated --message "Check ops queue" --agent ops
      
      # Switch or clear the agent on an existing job
      openclaw cron edit <jobId> --agent ops
      openclaw cron edit <jobId> --clear-agent
      
  
  Manual run (debug):
  
  Copy
  
      openclaw cron run <jobId> --force
      
  
  Edit an existing job (patch fields):
  
  Copy
  
      openclaw cron edit <jobId> \
        --message "Updated prompt" \
        --model "opus" \
        --thinking low
      
  
  Run history:
  
  Copy
  
      openclaw cron runs --id <jobId> --limit 50
      
  
  Immediate system event without creating a job:
  
  Copy
  
      openclaw system event --mode now --text "Next heartbeat: check battery."
      
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#gateway-api-surface)
  
  Gateway API surface
  ---------------------------------------------------------------------------------------------
  
  *   `cron.list`, `cron.status`, `cron.add`, `cron.update`, `cron.remove`
  *   `cron.run` (force or due), `cron.runs` For immediate system events without a job, use [`openclaw system event`](https://docs.openclaw.ai/cli/system)
      .
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#troubleshooting)
  
  Troubleshooting
  -------------------------------------------------------------------------------------
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#%E2%80%9Cnothing-runs%E2%80%9D)
  
  “Nothing runs”
  
  *   Check cron is enabled: `cron.enabled` and `OPENCLAW_SKIP_CRON`.
  *   Check the Gateway is running continuously (cron runs inside the Gateway process).
  *   For `cron` schedules: confirm timezone (`--tz`) vs the host timezone.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-jobs#telegram-delivers-to-the-wrong-place)
  
  Telegram delivers to the wrong place
  
  *   For forum topics, use `-100…:topic:<id>` so it’s explicit and unambiguous.
  *   If you see `telegram:...` prefixes in logs or stored “last route” targets, that’s normal; cron delivery accepts them and still parses topic IDs correctly.
  
  [Gmail PubSub](https://docs.openclaw.ai/automation/gmail-pubsub)
  [Cron vs Heartbeat](https://docs.openclaw.ai/automation/cron-vs-heartbeat)
  
  Ctrl+I
  
  Assistant
  
  Responses are generated using AI and may contain mistakes.
  --- End Content ---

Here's what is going on under the hood of @openclaw
  URL: https://x.com/prescott/status/2017850501153341603
  23 hours ago ... A heartbeat in OpenClaw is a scheduled agent run that happens on a ... The memory architecture is fairly clever, we love a good skill ...

  --- Content ---
  Don’t miss what’s happening
  
  People on X are the first to know.
  
  [Log in](https://x.com/login)
  
  [Sign up](https://x.com/i/flow/signup)
  
  See new posts
  --- End Content ---

Cron vs heartbeat - OpenClaw
  URL: https://docs.openclaw.ai/automation/cron-vs-heartbeat
  Cron vs heartbeat Both heartbeats and cron jobs let you run tasks on a schedule. This guide helps you choose the right mechanism for your use case.

  --- Content ---
  [Skip to main content](https://docs.openclaw.ai/automation/cron-vs-heartbeat#content-area)
  
  [OpenClaw home page![light logo](https://mintcdn.com/clawdhub/4rYvG-uuZrMK_URE/assets/pixel-lobster.svg?fit=max&auto=format&n=4rYvG-uuZrMK_URE&q=85&s=da2032e9eac3b5d9bfe7eb96ca6a8a26)![dark logo](https://mintcdn.com/clawdhub/4rYvG-uuZrMK_URE/assets/pixel-lobster.svg?fit=max&auto=format&n=4rYvG-uuZrMK_URE&q=85&s=da2032e9eac3b5d9bfe7eb96ca6a8a26)](https://docs.openclaw.ai/)
  
  ![US](https://d3gk2c5xim1je2.cloudfront.net/flags/US.svg)
  
  English
  
  Search...
  
  Ctrl K
  
  Search...
  
  Navigation
  
  Automation & Hooks
  
  Cron vs Heartbeat
  
  On this page
  
  *   [Cron vs Heartbeat: When to Use Each](https://docs.openclaw.ai/automation/cron-vs-heartbeat#cron-vs-heartbeat%3A-when-to-use-each)
      
  *   [Quick Decision Guide](https://docs.openclaw.ai/automation/cron-vs-heartbeat#quick-decision-guide)
      
  *   [Heartbeat: Periodic Awareness](https://docs.openclaw.ai/automation/cron-vs-heartbeat#heartbeat%3A-periodic-awareness)
      
  *   [When to use heartbeat](https://docs.openclaw.ai/automation/cron-vs-heartbeat#when-to-use-heartbeat)
      
  *   [Heartbeat advantages](https://docs.openclaw.ai/automation/cron-vs-heartbeat#heartbeat-advantages)
      
  *   [Heartbeat example: HEARTBEAT.md checklist](https://docs.openclaw.ai/automation/cron-vs-heartbeat#heartbeat-example%3A-heartbeat-md-checklist)
      
  *   [Configuring heartbeat](https://docs.openclaw.ai/automation/cron-vs-heartbeat#configuring-heartbeat)
      
  *   [Cron: Precise Scheduling](https://docs.openclaw.ai/automation/cron-vs-heartbeat#cron%3A-precise-scheduling)
      
  *   [When to use cron](https://docs.openclaw.ai/automation/cron-vs-heartbeat#when-to-use-cron)
      
  *   [Cron advantages](https://docs.openclaw.ai/automation/cron-vs-heartbeat#cron-advantages)
      
  *   [Cron example: Daily morning briefing](https://docs.openclaw.ai/automation/cron-vs-heartbeat#cron-example%3A-daily-morning-briefing)
      
  *   [Cron example: One-shot reminder](https://docs.openclaw.ai/automation/cron-vs-heartbeat#cron-example%3A-one-shot-reminder)
      
  *   [Decision Flowchart](https://docs.openclaw.ai/automation/cron-vs-heartbeat#decision-flowchart)
      
  *   [Combining Both](https://docs.openclaw.ai/automation/cron-vs-heartbeat#combining-both)
      
  *   [Example: Efficient automation setup](https://docs.openclaw.ai/automation/cron-vs-heartbeat#example%3A-efficient-automation-setup)
      
  *   [Lobster: Deterministic workflows with approvals](https://docs.openclaw.ai/automation/cron-vs-heartbeat#lobster%3A-deterministic-workflows-with-approvals)
      
  *   [When Lobster fits](https://docs.openclaw.ai/automation/cron-vs-heartbeat#when-lobster-fits)
      
  *   [How it pairs with heartbeat and cron](https://docs.openclaw.ai/automation/cron-vs-heartbeat#how-it-pairs-with-heartbeat-and-cron)
      
  *   [Operational notes (from the code)](https://docs.openclaw.ai/automation/cron-vs-heartbeat#operational-notes-from-the-code)
      
  *   [Main Session vs Isolated Session](https://docs.openclaw.ai/automation/cron-vs-heartbeat#main-session-vs-isolated-session)
      
  *   [When to use main session cron](https://docs.openclaw.ai/automation/cron-vs-heartbeat#when-to-use-main-session-cron)
      
  *   [When to use isolated cron](https://docs.openclaw.ai/automation/cron-vs-heartbeat#when-to-use-isolated-cron)
      
  *   [Cost Considerations](https://docs.openclaw.ai/automation/cron-vs-heartbeat#cost-considerations)
      
  *   [Related](https://docs.openclaw.ai/automation/cron-vs-heartbeat#related)
      
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#cron-vs-heartbeat:-when-to-use-each)
  
  Cron vs Heartbeat: When to Use Each
  =====================================================================================================================================
  
  Both heartbeats and cron jobs let you run tasks on a schedule. This guide helps you choose the right mechanism for your use case.
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#quick-decision-guide)
  
  Quick Decision Guide
  -------------------------------------------------------------------------------------------------------
  
  | Use Case | Recommended | Why |
  | --- | --- | --- |
  | Check inbox every 30 min | Heartbeat | Batches with other checks, context-aware |
  | Send daily report at 9am sharp | Cron (isolated) | Exact timing needed |
  | Monitor calendar for upcoming events | Heartbeat | Natural fit for periodic awareness |
  | Run weekly deep analysis | Cron (isolated) | Standalone task, can use different model |
  | Remind me in 20 minutes | Cron (main, `--at`) | One-shot with precise timing |
  | Background project health check | Heartbeat | Piggybacks on existing cycle |
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#heartbeat:-periodic-awareness)
  
  Heartbeat: Periodic Awareness
  -------------------------------------------------------------------------------------------------------------------------
  
  Heartbeats run in the **main session** at a regular interval (default: 30 min). They’re designed for the agent to check on things and surface anything important.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#when-to-use-heartbeat)
  
  When to use heartbeat
  
  *   **Multiple periodic checks**: Instead of 5 separate cron jobs checking inbox, calendar, weather, notifications, and project status, a single heartbeat can batch all of these.
  *   **Context-aware decisions**: The agent has full main-session context, so it can make smart decisions about what’s urgent vs. what can wait.
  *   **Conversational continuity**: Heartbeat runs share the same session, so the agent remembers recent conversations and can follow up naturally.
  *   **Low-overhead monitoring**: One heartbeat replaces many small polling tasks.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#heartbeat-advantages)
  
  Heartbeat advantages
  
  *   **Batches multiple checks**: One agent turn can review inbox, calendar, and notifications together.
  *   **Reduces API calls**: A single heartbeat is cheaper than 5 isolated cron jobs.
  *   **Context-aware**: The agent knows what you’ve been working on and can prioritize accordingly.
  *   **Smart suppression**: If nothing needs attention, the agent replies `HEARTBEAT_OK` and no message is delivered.
  *   **Natural timing**: Drifts slightly based on queue load, which is fine for most monitoring.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#heartbeat-example:-heartbeat-md-checklist)
  
  Heartbeat example: HEARTBEAT.md checklist
  
  Copy
  
      # Heartbeat checklist
      
      - Check email for urgent messages
      - Review calendar for events in next 2 hours
      - If a background task finished, summarize results
      - If idle for 8+ hours, send a brief check-in
      
  
  The agent reads this on each heartbeat and handles all items in one turn.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#configuring-heartbeat)
  
  Configuring heartbeat
  
  Copy
  
      {
        agents: {
          defaults: {
            heartbeat: {
              every: "30m", // interval
              target: "last", // where to deliver alerts
              activeHours: { start: "08:00", end: "22:00" }, // optional
            },
          },
        },
      }
      
  
  See [Heartbeat](https://docs.openclaw.ai/gateway/heartbeat)
   for full configuration.
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#cron:-precise-scheduling)
  
  Cron: Precise Scheduling
  ---------------------------------------------------------------------------------------------------------------
  
  Cron jobs run at **exact times** and can run in isolated sessions without affecting main context.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#when-to-use-cron)
  
  When to use cron
  
  *   **Exact timing required**: “Send this at 9:00 AM every Monday” (not “sometime around 9”).
  *   **Standalone tasks**: Tasks that don’t need conversational context.
  *   **Different model/thinking**: Heavy analysis that warrants a more powerful model.
  *   **One-shot reminders**: “Remind me in 20 minutes” with `--at`.
  *   **Noisy/frequent tasks**: Tasks that would clutter main session history.
  *   **External triggers**: Tasks that should run independently of whether the agent is otherwise active.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#cron-advantages)
  
  Cron advantages
  
  *   **Exact timing**: 5-field cron expressions with timezone support.
  *   **Session isolation**: Runs in `cron:<jobId>` without polluting main history.
  *   **Model overrides**: Use a cheaper or more powerful model per job.
  *   **Delivery control**: Can deliver directly to a channel; still posts a summary to main by default (configurable).
  *   **No agent context needed**: Runs even if main session is idle or compacted.
  *   **One-shot support**: `--at` for precise future timestamps.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#cron-example:-daily-morning-briefing)
  
  Cron example: Daily morning briefing
  
  Copy
  
      openclaw cron add \
        --name "Morning briefing" \
        --cron "0 7 * * *" \
        --tz "America/New_York" \
        --session isolated \
        --message "Generate today's briefing: weather, calendar, top emails, news summary." \
        --model opus \
        --deliver \
        --channel whatsapp \
        --to "+15551234567"
      
  
  This runs at exactly 7:00 AM New York time, uses Opus for quality, and delivers directly to WhatsApp.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#cron-example:-one-shot-reminder)
  
  Cron example: One-shot reminder
  
  Copy
  
      openclaw cron add \
        --name "Meeting reminder" \
        --at "20m" \
        --session main \
        --system-event "Reminder: standup meeting starts in 10 minutes." \
        --wake now \
        --delete-after-run
      
  
  See [Cron jobs](https://docs.openclaw.ai/automation/cron-jobs)
   for full CLI reference.
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#decision-flowchart)
  
  Decision Flowchart
  ---------------------------------------------------------------------------------------------------
  
  Copy
  
      Does the task need to run at an EXACT time?
        YES -> Use cron
        NO  -> Continue...
      
      Does the task need isolation from main session?
        YES -> Use cron (isolated)
        NO  -> Continue...
      
      Can this task be batched with other periodic checks?
        YES -> Use heartbeat (add to HEARTBEAT.md)
        NO  -> Use cron
      
      Is this a one-shot reminder?
        YES -> Use cron with --at
        NO  -> Continue...
      
      Does it need a different model or thinking level?
        YES -> Use cron (isolated) with --model/--thinking
        NO  -> Use heartbeat
      
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#combining-both)
  
  Combining Both
  -------------------------------------------------------------------------------------------
  
  The most efficient setup uses **both**:
  
  1.  **Heartbeat** handles routine monitoring (inbox, calendar, notifications) in one batched turn every 30 minutes.
  2.  **Cron** handles precise schedules (daily reports, weekly reviews) and one-shot reminders.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#example:-efficient-automation-setup)
  
  Example: Efficient automation setup
  
  **HEARTBEAT.md** (checked every 30 min):
  
  Copy
  
      # Heartbeat checklist
      
      - Scan inbox for urgent emails
      - Check calendar for events in next 2h
      - Review any pending tasks
      - Light check-in if quiet for 8+ hours
      
  
  **Cron jobs** (precise timing):
  
  Copy
  
      # Daily morning briefing at 7am
      openclaw cron add --name "Morning brief" --cron "0 7 * * *" --session isolated --message "..." --deliver
      
      # Weekly project review on Mondays at 9am
      openclaw cron add --name "Weekly review" --cron "0 9 * * 1" --session isolated --message "..." --model opus
      
      # One-shot reminder
      openclaw cron add --name "Call back" --at "2h" --session main --system-event "Call back the client" --wake now
      
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#lobster:-deterministic-workflows-with-approvals)
  
  Lobster: Deterministic workflows with approvals
  -------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  Lobster is the workflow runtime for **multi-step tool pipelines** that need deterministic execution and explicit approvals. Use it when the task is more than a single agent turn, and you want a resumable workflow with human checkpoints.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#when-lobster-fits)
  
  When Lobster fits
  
  *   **Multi-step automation**: You need a fixed pipeline of tool calls, not a one-off prompt.
  *   **Approval gates**: Side effects should pause until you approve, then resume.
  *   **Resumable runs**: Continue a paused workflow without re-running earlier steps.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#how-it-pairs-with-heartbeat-and-cron)
  
  How it pairs with heartbeat and cron
  
  *   **Heartbeat/cron** decide _when_ a run happens.
  *   **Lobster** defines _what steps_ happen once the run starts.
  
  For scheduled workflows, use cron or heartbeat to trigger an agent turn that calls Lobster. For ad-hoc workflows, call Lobster directly.
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#operational-notes-from-the-code)
  
  Operational notes (from the code)
  
  *   Lobster runs as a **local subprocess** (`lobster` CLI) in tool mode and returns a **JSON envelope**.
  *   If the tool returns `needs_approval`, you resume with a `resumeToken` and `approve` flag.
  *   The tool is an **optional plugin**; enable it additively via `tools.alsoAllow: ["lobster"]` (recommended).
  *   If you pass `lobsterPath`, it must be an **absolute path**.
  
  See [Lobster](https://docs.openclaw.ai/tools/lobster)
   for full usage and examples.
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#main-session-vs-isolated-session)
  
  Main Session vs Isolated Session
  -------------------------------------------------------------------------------------------------------------------------------
  
  Both heartbeat and cron can interact with the main session, but differently:
  
  |     | Heartbeat | Cron (main) | Cron (isolated) |
  | --- | --- | --- | --- |
  | Session | Main | Main (via system event) | `cron:<jobId>` |
  | History | Shared | Shared | Fresh each run |
  | Context | Full | Full | None (starts clean) |
  | Model | Main session model | Main session model | Can override |
  | Output | Delivered if not `HEARTBEAT_OK` | Heartbeat prompt + event | Summary posted to main |
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#when-to-use-main-session-cron)
  
  When to use main session cron
  
  Use `--session main` with `--system-event` when you want:
  
  *   The reminder/event to appear in main session context
  *   The agent to handle it during the next heartbeat with full context
  *   No separate isolated run
  
  Copy
  
      openclaw cron add \
        --name "Check project" \
        --every "4h" \
        --session main \
        --system-event "Time for a project health check" \
        --wake now
      
  
  ### 
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#when-to-use-isolated-cron)
  
  When to use isolated cron
  
  Use `--session isolated` when you want:
  
  *   A clean slate without prior context
  *   Different model or thinking settings
  *   Output delivered directly to a channel (summary still posts to main by default)
  *   History that doesn’t clutter main session
  
  Copy
  
      openclaw cron add \
        --name "Deep analysis" \
        --cron "0 6 * * 0" \
        --session isolated \
        --message "Weekly codebase analysis..." \
        --model opus \
        --thinking high \
        --deliver
      
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#cost-considerations)
  
  Cost Considerations
  -----------------------------------------------------------------------------------------------------
  
  | Mechanism | Cost Profile |
  | --- | --- |
  | Heartbeat | One turn every N minutes; scales with HEARTBEAT.md size |
  | Cron (main) | Adds event to next heartbeat (no isolated turn) |
  | Cron (isolated) | Full agent turn per job; can use cheaper model |
  
  **Tips**:
  
  *   Keep `HEARTBEAT.md` small to minimize token overhead.
  *   Batch similar checks into heartbeat instead of multiple cron jobs.
  *   Use `target: "none"` on heartbeat if you only want internal processing.
  *   Use isolated cron with a cheaper model for routine tasks.
  
  [​](https://docs.openclaw.ai/automation/cron-vs-heartbeat#related)
  
  Related
  -----------------------------------------------------------------------------
  
  *   [Heartbeat](https://docs.openclaw.ai/gateway/heartbeat)
       - full heartbeat configuration
  *   [Cron jobs](https://docs.openclaw.ai/automation/cron-jobs)
       - full cron CLI and API reference
  *   [System](https://docs.openclaw.ai/cli/system)
       - system events + heartbeat controls
  
  [Cron Jobs](https://docs.openclaw.ai/automation/cron-jobs)
  [Polls](https://docs.openclaw.ai/automation/poll)
  
  Ctrl+I
  
  Assistant
  
  Responses are generated using AI and may contain mistakes.
  --- End Content ---

Cron vs heartbeat - ClawdBotAI
  URL: https://clawdbotai.co/docs/automation/cron-vs-heartbeat
  When to use heartbeat Multiple periodic checks: Instead of 5 separate cron jobs checking inbox, calendar, weather, notifications, and project status, a single heartbeat can batch all of these. Context-aware decisions: The agent has full main-session context, so it can make smart decisions about what's urgent vs. what can wait.

  --- Content ---
  [Home](https://clawdbotai.co/)
  Automation & HooksCron vs heartbeat
  
  Cron vs heartbeat
  =================
  
  Cron vs heartbeat
  
  Both heartbeats and cron jobs let you run tasks on a schedule. This guide helps you choose the right mechanism for your use case.
  
  [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#quick-decision-guide)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#quick-decision-guide)
  
  Quick Decision Guide
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  | Use Case | Recommended | Why |
  | --- | --- | --- |
  | Check inbox every 30 min | Heartbeat | Batches with other checks, context-aware |
  | Send daily report at 9am sharp | Cron (isolated) | Exact timing needed |
  | Monitor calendar for upcoming events | Heartbeat | Natural fit for periodic awareness |
  | Run weekly deep analysis | Cron (isolated) | Standalone task, can use different model |
  | Remind me in 20 minutes | Cron (main, `--at`) | One-shot with precise timing |
  | Background project health check | Heartbeat | Piggybacks on existing cycle |
  
  [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#heartbeat:-periodic-awareness)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#heartbeat:-periodic-awareness)
  
  Heartbeat: Periodic Awareness
  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  Heartbeats run in the **main session** at a regular interval (default: 30 min). They’re designed for the agent to check on things and surface anything important.
  
  ### [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#when-to-use-heartbeat)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#when-to-use-heartbeat)
  
  When to use heartbeat
  
  *   **Multiple periodic checks**: Instead of 5 separate cron jobs checking inbox, calendar, weather, notifications, and project status, a single heartbeat can batch all of these.
  *   **Context-aware decisions**: The agent has full main-session context, so it can make smart decisions about what’s urgent vs. what can wait.
  *   **Conversational continuity**: Heartbeat runs share the same session, so the agent remembers recent conversations and can follow up naturally.
  *   **Low-overhead monitoring**: One heartbeat replaces many small polling tasks.
  
  ### [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#heartbeat-advantages)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#heartbeat-advantages)
  
  Heartbeat advantages
  
  *   **Batches multiple checks**: One agent turn can review inbox, calendar, and notifications together.
  *   **Reduces API calls**: A single heartbeat is cheaper than 5 isolated cron jobs.
  *   **Context-aware**: The agent knows what you’ve been working on and can prioritize accordingly.
  *   **Smart suppression**: If nothing needs attention, the agent replies `HEARTBEAT_OK` and no message is delivered.
  *   **Natural timing**: Drifts slightly based on queue load, which is fine for most monitoring.
  
  ### [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#heartbeat-example:-heartbeat-md-checklist)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#heartbeat-example:-heartbeat-md-checklist)
  
  Heartbeat example: HEARTBEAT.md checklist
  
      # Heartbeat checklist
      
      - Check email for urgent messages
      - Review calendar for events in next 2 hours
      - If a background task finished, summarize results
      - If idle for 8+ hours, send a brief check-in
      
  
  The agent reads this on each heartbeat and handles all items in one turn.
  
  ### [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#configuring-heartbeat)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#configuring-heartbeat)
  
  Configuring heartbeat
  
      {
        agents: {
          defaults: {
            heartbeat: {
              every: "30m",        // interval
              target: "last",      // where to deliver alerts
              activeHours: { start: "08:00", end: "22:00" }  // optional
            }
          }
        }
      }
      
  
  See [Heartbeat](https://clawdbotai.co/gateway/heartbeat)
   for full configuration.
  
  [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#cron:-precise-scheduling)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#cron:-precise-scheduling)
  
  Cron: Precise Scheduling
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  Cron jobs run at **exact times** and can run in isolated sessions without affecting main context.
  
  ### [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#when-to-use-cron)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#when-to-use-cron)
  
  When to use cron
  
  *   **Exact timing required**: “Send this at 9:00 AM every Monday” (not “sometime around 9”).
  *   **Standalone tasks**: Tasks that don’t need conversational context.
  *   **Different model/thinking**: Heavy analysis that warrants a more powerful model.
  *   **One-shot reminders**: “Remind me in 20 minutes” with `--at`.
  *   **Noisy/frequent tasks**: Tasks that would clutter main session history.
  *   **External triggers**: Tasks that should run independently of whether the agent is otherwise active.
  
  ### [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#cron-advantages)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#cron-advantages)
  
  Cron advantages
  
  *   **Exact timing**: 5-field cron expressions with timezone support.
  *   **Session isolation**: Runs in `cron:<jobId>` without polluting main history.
  *   **Model overrides**: Use a cheaper or more powerful model per job.
  *   **Delivery control**: Can deliver directly to a channel; still posts a summary to main by default (configurable).
  *   **No agent context needed**: Runs even if main session is idle or compacted.
  *   **One-shot support**: `--at` for precise future timestamps.
  
  ### [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#cron-example:-daily-morning-briefing)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#cron-example:-daily-morning-briefing)
  
  Cron example: Daily morning briefing
  
      clawdbot cron add \
        --name "Morning briefing" \
        --cron "0 7 * * *" \
        --tz "America/New_York" \
        --session isolated \
        --message "Generate today's briefing: weather, calendar, top emails, news summary." \
        --model opus \
        --deliver \
        --channel whatsapp \
        --to "+15551234567"
      
  
  This runs at exactly 7:00 AM New York time, uses Opus for quality, and delivers directly to WhatsApp.
  
  ### [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#cron-example:-one-shot-reminder)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#cron-example:-one-shot-reminder)
  
  Cron example: One-shot reminder
  
      clawdbot cron add \
        --name "Meeting reminder" \
        --at "20m" \
        --session main \
        --system-event "Reminder: standup meeting starts in 10 minutes." \
        --wake now \
        --delete-after-run
      
  
  See [Cron jobs](https://clawdbotai.co/automation/cron-jobs)
   for full CLI reference.
  
  [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#decision-flowchart)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#decision-flowchart)
  
  Decision Flowchart
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  
      Does the task need to run at an EXACT time?
        YES -> Use cron
        NO  -> Continue...
      
      Does the task need isolation from main session?
        YES -> Use cron (isolated)
        NO  -> Continue...
      
      Can this task be batched with other periodic checks?
        YES -> Use heartbeat (add to HEARTBEAT.md)
        NO  -> Use cron
      
      Is this a one-shot reminder?
        YES -> Use cron with --at
        NO  -> Continue...
      
      Does it need a different model or thinking level?
        YES -> Use cron (isolated) with --model/--thinking
        NO  -> Use heartbeat
      
  
  [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#combining-both)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#combining-both)
  
  Combining Both
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  The most efficient setup uses **both**:
  
  1.  **Heartbeat** handles routine monitoring (inbox, calendar, notifications) in one batched turn every 30 minutes.
  2.  **Cron** handles precise schedules (daily reports, weekly reviews) and one-shot reminders.
  
  ### [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#example:-efficient-automation-setup)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#example:-efficient-automation-setup)
  
  Example: Efficient automation setup
  
  **HEARTBEAT.md** (checked every 30 min):
  
      # Heartbeat checklist
      - Scan inbox for urgent emails
      - Check calendar for events in next 2h
      - Review any pending tasks
      - Light check-in if quiet for 8+ hours
      
  
  **Cron jobs** (precise timing):
  
      # Daily morning briefing at 7am
      clawdbot cron add --name "Morning brief" --cron "0 7 * * *" --session isolated --message "..." --deliver
      
      # Weekly project review on Mondays at 9am
      clawdbot cron add --name "Weekly review" --cron "0 9 * * 1" --session isolated --message "..." --model opus
      
      # One-shot reminder
      clawdbot cron add --name "Call back" --at "2h" --session main --system-event "Call back the client" --wake now
      
  
  [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#lobster:-deterministic-workflows-with-approvals)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#lobster:-deterministic-workflows-with-approvals)
  
  Lobster: Deterministic workflows with approvals
  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  Lobster is the workflow runtime for **multi-step tool pipelines** that need deterministic execution and explicit approvals. Use it when the task is more than a single agent turn, and you want a resumable workflow with human checkpoints.
  
  ### [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#when-lobster-fits)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#when-lobster-fits)
  
  When Lobster fits
  
  *   **Multi-step automation**: You need a fixed pipeline of tool calls, not a one-off prompt.
  *   **Approval gates**: Side effects should pause until you approve, then resume.
  *   **Resumable runs**: Continue a paused workflow without re-running earlier steps.
  
  ### [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#how-it-pairs-with-heartbeat-and-cron)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#how-it-pairs-with-heartbeat-and-cron)
  
  How it pairs with heartbeat and cron
  
  *   **Heartbeat/cron** decide _when_ a run happens.
  *   **Lobster** defines _what steps_ happen once the run starts.
  
  For scheduled workflows, use cron or heartbeat to trigger an agent turn that calls Lobster. For ad-hoc workflows, call Lobster directly.
  
  ### [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#operational-notes-from-the-code)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#operational-notes-from-the-code)
  
  Operational notes (from the code)
  
  *   Lobster runs as a **local subprocess** (`lobster` CLI) in tool mode and returns a **JSON envelope**.
  *   If the tool returns `needs_approval`, you resume with a `resumeToken` and `approve` flag.
  *   The tool is an **optional plugin**; you must allowlist `lobster` in `tools.allow`.
  *   If you pass `lobsterPath`, it must be an **absolute path**.
  
  See [Lobster](https://clawdbotai.co/tools/lobster)
   for full usage and examples.
  
  [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#main-session-vs-isolated-session)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#main-session-vs-isolated-session)
  
  Main Session vs Isolated Session
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  Both heartbeat and cron can interact with the main session, but differently:
  
  |     | Heartbeat | Cron (main) | Cron (isolated) |
  | --- | --- | --- | --- |
  | Session | Main | Main (via system event) | `cron:<jobId>` |
  | History | Shared | Shared | Fresh each run |
  | Context | Full | Full | None (starts clean) |
  | Model | Main session model | Main session model | Can override |
  | Output | Delivered if not `HEARTBEAT_OK` | Heartbeat prompt + event | Summary posted to main |
  
  ### [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#when-to-use-main-session-cron)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#when-to-use-main-session-cron)
  
  When to use main session cron
  
  Use `--session main` with `--system-event` when you want:
  
  *   The reminder/event to appear in main session context
  *   The agent to handle it during the next heartbeat with full context
  *   No separate isolated run
  
      clawdbot cron add \
        --name "Check project" \
        --every "4h" \
        --session main \
        --system-event "Time for a project health check" \
        --wake now
      
  
  ### [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#when-to-use-isolated-cron)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#when-to-use-isolated-cron)
  
  When to use isolated cron
  
  Use `--session isolated` when you want:
  
  *   A clean slate without prior context
  *   Different model or thinking settings
  *   Output delivered directly to a channel (summary still posts to main by default)
  *   History that doesn’t clutter main session
  
      clawdbot cron add \
        --name "Deep analysis" \
        --cron "0 6 * * 0" \
        --session isolated \
        --message "Weekly codebase analysis..." \
        --model opus \
        --thinking high \
        --deliver
      
  
  [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#cost-considerations)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#cost-considerations)
  
  Cost Considerations
  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  
  | Mechanism | Cost Profile |
  | --- | --- |
  | Heartbeat | One turn every N minutes; scales with HEARTBEAT.md size |
  | Cron (main) | Adds event to next heartbeat (no isolated turn) |
  | Cron (isolated) | Full agent turn per job; can use cheaper model |
  
  **Tips**:
  
  *   Keep `HEARTBEAT.md` small to minimize token overhead.
  *   Batch similar checks into heartbeat instead of multiple cron jobs.
  *   Use `target: "none"` on heartbeat if you only want internal processing.
  *   Use isolated cron with a cheaper model for routine tasks.
  
  [#](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#related)
  
  [​](https://clawdbotai.co/docs/automation/cron-vs-heartbeat#related)
  
  Related
  ---------------------------------------------------------------------------------------------------------------------------------------------------
  
  *   [Heartbeat](https://clawdbotai.co/gateway/heartbeat)
       - full heartbeat configuration
  *   [Cron jobs](https://clawdbotai.co/automation/cron-jobs)
       - full cron CLI and API reference
  *   [System](https://clawdbotai.co/cli/system)
       - system events + heartbeat controls
  
  [Cron jobs](https://clawdbotai.co/docs/automation/cron-jobs)
  [Poll](https://clawdbotai.co/docs/automation/poll)
  --- End Content ---

Think Your Emails Are Safe? OpenClaw (Clawdbot) Proves Otherwise
  URL: https://agentnativedev.medium.com/think-your-emails-are-safe-openclaw-clawdbot-proves-otherwise-f563ec9893ac
  14 hours ago ... This design allows specialization without cross‑contamination of memory. Cron jobs and heartbeats. Agents don't stay awake all the time.

  --- Content ---
  [Sitemap](https://agentnativedev.medium.com/sitemap/sitemap.xml)
  
  [Open in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3DmobileNavBar&source=post_page---top_nav_layout_nav-----------------------------------------)
  
  Sign up
  
  [Sign in](https://medium.com/m/signin?operation=login&redirect=https%3A%2F%2Fagentnativedev.medium.com%2Fthink-your-emails-are-safe-openclaw-clawdbot-proves-otherwise-f563ec9893ac&source=post_page---top_nav_layout_nav-----------------------global_nav------------------)
  
  [Medium Logo](https://medium.com/?source=post_page---top_nav_layout_nav-----------------------------------------)
  
  [Write](https://medium.com/m/signin?operation=register&redirect=https%3A%2F%2Fmedium.com%2Fnew-story&source=---top_nav_layout_nav-----------------------new_post_topnav------------------)
  
  [Search](https://medium.com/search?source=post_page---top_nav_layout_nav-----------------------------------------)
  
  Sign up
  
  [Sign in](https://medium.com/m/signin?operation=login&redirect=https%3A%2F%2Fagentnativedev.medium.com%2Fthink-your-emails-are-safe-openclaw-clawdbot-proves-otherwise-f563ec9893ac&source=post_page---top_nav_layout_nav-----------------------global_nav------------------)
  
  ![](https://miro.medium.com/v2/resize:fill:32:32/1*dmbNkD5D-u45r44go_cf0g.png)
  
  Member-only story
  
  Think Your Emails Are Safe? OpenClaw (Clawdbot) Proves Otherwise
  ================================================================
  
  [![Agent Native](https://miro.medium.com/v2/resize:fill:32:32/1*aZiyRsTwMmjG54EApMtwsg.jpeg)](https://agentnativedev.medium.com/?source=post_page---byline--f563ec9893ac---------------------------------------)
  
  [Agent Native](https://agentnativedev.medium.com/?source=post_page---byline--f563ec9893ac---------------------------------------)
  
  Follow
  
  10 min read
  
  ·
  
  14 hours ago
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fvote%2Fp%2Ff563ec9893ac&operation=register&redirect=https%3A%2F%2Fagentnativedev.medium.com%2Fthink-your-emails-are-safe-openclaw-clawdbot-proves-otherwise-f563ec9893ac&user=Agent+Native&userId=3dea44a5d468&source=---header_actions--f563ec9893ac---------------------clap_footer------------------)
  
  31
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2Ff563ec9893ac&operation=register&redirect=https%3A%2F%2Fagentnativedev.medium.com%2Fthink-your-emails-are-safe-openclaw-clawdbot-proves-otherwise-f563ec9893ac&source=---header_actions--f563ec9893ac---------------------bookmark_footer------------------)
  
  [Listen](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2Fplans%3Fdimension%3Dpost_audio_button%26postId%3Df563ec9893ac&operation=register&redirect=https%3A%2F%2Fagentnativedev.medium.com%2Fthink-your-emails-are-safe-openclaw-clawdbot-proves-otherwise-f563ec9893ac&source=---header_actions--f563ec9893ac---------------------post_audio_button------------------)
  
  Share
  
  Before you plan delegating real work to OpenClaw, you have to understand exactly why it’s vulnerable and how you can mitigate the risks.
  
  Shodan scan in late January found more than 1800+ instances of OpenClaw on the public internet, over half were running with an unauthenticated gateway and another quarter trusted spoofed `X‑Forwarded‑For` headers to decide if a request came from `127.0.0.1`.
  
  The uncomfortable truth is that thousands of well-intentioned builders gave a fresh, fast-moving tool privileged access to their digital lives before they had a threat model.
  
  At the same time, OpenClaw’s adoption shows why developers are willing to take that bet.
  
  Bhanu Teja’s “Mission Control” demonstrates what happens when you treat agents like a team, e.g. multiple specialized sessions, shared workspace, persistent memory, and cron-based wakeups orchestrated like real coworkers.
  
  Press enter or click to view image in full size
  
  ![](https://miro.medium.com/v2/resize:fit:700/0*zG45NoMj380wdLRp)
  
  [https://x.com/pbteja1998/status/2017662163540971756](https://x.com/pbteja1998/status/2017662163540971756)
  
  Elvis Sun’s build-in-public story shows the solo-founder version where agents triaging user feedback, shipping fixes, automating deployments, even spinning up admin tooling, the “system that builds the product” vibe.
  
  Create an account to read the full story.
  
  
  ---------------------------------------------
  
  The author made this story available to Medium members only.  
  If you’re new to Medium, create a new account to read this story on us.
  
  [Continue in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3Dregwall&source=-----f563ec9893ac---------------------post_regwall------------------)
  
  Or, continue in mobile web
  
  [Sign up with Google](https://medium.com/m/connect/google?state=google-%7Chttps%3A%2F%2Fagentnativedev.medium.com%2Fthink-your-emails-are-safe-openclaw-clawdbot-proves-otherwise-f563ec9893ac%3Fsource%3D-----f563ec9893ac---------------------post_regwall------------------%26skipOnboarding%3D1%7Cregister&source=-----f563ec9893ac---------------------post_regwall------------------)
  
  [Sign up with Facebook](https://medium.com/m/connect/facebook?state=facebook-%7Chttps%3A%2F%2Fagentnativedev.medium.com%2Fthink-your-emails-are-safe-openclaw-clawdbot-proves-otherwise-f563ec9893ac%3Fsource%3D-----f563ec9893ac---------------------post_regwall------------------%26skipOnboarding%3D1%7Cregister&source=-----f563ec9893ac---------------------post_regwall------------------)
  
  Sign up with email
  
  Already have an account? [Sign in](https://medium.com/m/signin?operation=login&redirect=https%3A%2F%2Fagentnativedev.medium.com%2Fthink-your-emails-are-safe-openclaw-clawdbot-proves-otherwise-f563ec9893ac&source=-----f563ec9893ac---------------------post_regwall------------------)
  
  [![Agent Native](https://miro.medium.com/v2/resize:fill:48:48/1*aZiyRsTwMmjG54EApMtwsg.jpeg)](https://agentnativedev.medium.com/?source=post_page---post_author_info--f563ec9893ac---------------------------------------)
  
  [![Agent Native](https://miro.medium.com/v2/resize:fill:64:64/1*aZiyRsTwMmjG54EApMtwsg.jpeg)](https://agentnativedev.medium.com/?source=post_page---post_author_info--f563ec9893ac---------------------------------------)
  
  Follow
  
  [Written by Agent Native\
  -----------------------](https://agentnativedev.medium.com/?source=post_page---post_author_info--f563ec9893ac---------------------------------------)
  
  [3.5K followers](https://agentnativedev.medium.com/followers?source=post_page---post_author_info--f563ec9893ac---------------------------------------)
  
  ·[0 following](https://agentnativedev.medium.com/following?source=post_page---post_author_info--f563ec9893ac---------------------------------------)
  
  agi | quant macro | space | fusion
  
  Follow
  
  No responses yet
  ----------------
  
  [](https://policy.medium.com/medium-rules-30e5502c4eb4?source=post_page---post_responses--f563ec9893ac---------------------------------------)
  
  ![](https://miro.medium.com/v2/resize:fill:32:32/1*dmbNkD5D-u45r44go_cf0g.png)
  
  Write a response
  
  [What are your thoughts?](https://medium.com/m/signin?operation=register&redirect=https%3A%2F%2Fagentnativedev.medium.com%2Fthink-your-emails-are-safe-openclaw-clawdbot-proves-otherwise-f563ec9893ac&source=---post_responses--f563ec9893ac---------------------respond_sidebar------------------)
  
  Cancel
  
  Respond
  
  More from Agent Native
  ----------------------
  
  ![Local LLMs That Can Replace Claude Code](https://miro.medium.com/v2/resize:fit:679/format:webp/0*JpX_vOrpLzFhJfJM.png)
  
  [![Agent Native](https://miro.medium.com/v2/resize:fill:20:20/1*aZiyRsTwMmjG54EApMtwsg.jpeg)](https://agentnativedev.medium.com/?source=post_page---author_recirc--f563ec9893ac----0---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  [Agent Native](https://agentnativedev.medium.com/?source=post_page---author_recirc--f563ec9893ac----0---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  [Local LLMs That Can Replace Claude Code\
  ---------------------------------------\
  \
  ### Small team of engineers can easily burn >$2K/mo on Anthropic’s Claude Code (Sonnet/Opus 4.5). As budgets are tight, you might be wondering…](https://agentnativedev.medium.com/local-llms-that-can-replace-claude-code-6f5b6cac93bf?source=post_page---author_recirc--f563ec9893ac----0---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  Jan 20
  
  [A clap icon521\
  \
  A response icon13](https://agentnativedev.medium.com/local-llms-that-can-replace-claude-code-6f5b6cac93bf?source=post_page---author_recirc--f563ec9893ac----0---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F6f5b6cac93bf&operation=register&redirect=https%3A%2F%2Fagentnativedev.medium.com%2Flocal-llms-that-can-replace-claude-code-6f5b6cac93bf&source=---author_recirc--f563ec9893ac----0-----------------bookmark_preview----d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  ![Qwen3-Max-Thinking Outperforms Claude Opus 4.5 and Gpt-5.2: The Panic Is Real](https://miro.medium.com/v2/resize:fit:679/format:webp/0*Ov0kCUUipDdjB4JS.png)
  
  [![Agent Native](https://miro.medium.com/v2/resize:fill:20:20/1*aZiyRsTwMmjG54EApMtwsg.jpeg)](https://agentnativedev.medium.com/?source=post_page---author_recirc--f563ec9893ac----1---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  [Agent Native](https://agentnativedev.medium.com/?source=post_page---author_recirc--f563ec9893ac----1---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  [Qwen3-Max-Thinking Outperforms Claude Opus 4.5 and Gpt-5.2: The Panic Is Real\
  -----------------------------------------------------------------------------\
  \
  ### Alibaba’s Qwen3 family of models has become a major alternative in the LLM ecosystem.](https://agentnativedev.medium.com/qwen3-max-thinking-outperforms-claude-opus-4-5-and-gpt-5-2-the-panic-is-real-d4c2557879d4?source=post_page---author_recirc--f563ec9893ac----1---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  5d ago
  
  [A clap icon75\
  \
  A response icon4](https://agentnativedev.medium.com/qwen3-max-thinking-outperforms-claude-opus-4-5-and-gpt-5-2-the-panic-is-real-d4c2557879d4?source=post_page---author_recirc--f563ec9893ac----1---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2Fd4c2557879d4&operation=register&redirect=https%3A%2F%2Fagentnativedev.medium.com%2Fqwen3-max-thinking-outperforms-claude-opus-4-5-and-gpt-5-2-the-panic-is-real-d4c2557879d4&source=---author_recirc--f563ec9893ac----1-----------------bookmark_preview----d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  ![Automate Google NotebookLM from your AI agent with notebooklm-mcp](https://miro.medium.com/v2/resize:fit:679/format:webp/0*eT0vWPw6HS1EGu9i.png)
  
  [![Agent Native](https://miro.medium.com/v2/resize:fill:20:20/1*aZiyRsTwMmjG54EApMtwsg.jpeg)](https://agentnativedev.medium.com/?source=post_page---author_recirc--f563ec9893ac----2---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  [Agent Native](https://agentnativedev.medium.com/?source=post_page---author_recirc--f563ec9893ac----2---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  [Automate Google NotebookLM from your AI agent with notebooklm-mcp\
  -----------------------------------------------------------------\
  \
  ### NotebookLM is great at turning a pile of sources into answers, study material, and “studio” artifacts (audio overviews, slides, etc.). The…](https://agentnativedev.medium.com/automate-google-notebooklm-from-your-ai-agent-with-notebooklm-mcp-3c513a37396a?source=post_page---author_recirc--f563ec9893ac----2---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  Jan 16
  
  [A clap icon112](https://agentnativedev.medium.com/automate-google-notebooklm-from-your-ai-agent-with-notebooklm-mcp-3c513a37396a?source=post_page---author_recirc--f563ec9893ac----2---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F3c513a37396a&operation=register&redirect=https%3A%2F%2Fagentnativedev.medium.com%2Fautomate-google-notebooklm-from-your-ai-agent-with-notebooklm-mcp-3c513a37396a&source=---author_recirc--f563ec9893ac----2-----------------bookmark_preview----d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  ![GLM-4.7-Flash on 24GB GPU (llama.ccp, vLLM, SGLang, Transformers)](https://miro.medium.com/v2/resize:fit:679/format:webp/1*bnQ_e-NccoiBF9fwnU_GIg.png)
  
  [![Agent Native](https://miro.medium.com/v2/resize:fill:20:20/1*aZiyRsTwMmjG54EApMtwsg.jpeg)](https://agentnativedev.medium.com/?source=post_page---author_recirc--f563ec9893ac----3---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  [Agent Native](https://agentnativedev.medium.com/?source=post_page---author_recirc--f563ec9893ac----3---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  [GLM-4.7-Flash on 24GB GPU (llama.ccp, vLLM, SGLang, Transformers)\
  -----------------------------------------------------------------\
  \
  ### GLM-4.7-Flash is one of those rare open-weights releases that changes what “local-first” can realistically mean for coding + agentic…](https://agentnativedev.medium.com/glm-4-7-flash-on-24gb-gpu-llama-ccp-vllm-sglang-transformers-b3358d2f0e78?source=post_page---author_recirc--f563ec9893ac----3---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  Jan 22
  
  [A clap icon58\
  \
  A response icon1](https://agentnativedev.medium.com/glm-4-7-flash-on-24gb-gpu-llama-ccp-vllm-sglang-transformers-b3358d2f0e78?source=post_page---author_recirc--f563ec9893ac----3---------------------d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2Fb3358d2f0e78&operation=register&redirect=https%3A%2F%2Fagentnativedev.medium.com%2Fglm-4-7-flash-on-24gb-gpu-llama-ccp-vllm-sglang-transformers-b3358d2f0e78&source=---author_recirc--f563ec9893ac----3-----------------bookmark_preview----d2e24779_271b_4a9e_b2e7_242546c034b8--------------)
  
  [See all from Agent Native](https://agentnativedev.medium.com/?source=post_page---author_recirc--f563ec9893ac---------------------------------------)
  
  Recommended from Medium
  -----------------------
  
  ![Ollama LaunchOllama Launch](https://miro.medium.com/v2/resize:fit:679/format:webp/1*FU-zudfoF4r2b2q825bl_A.png)
  
  [![AI Software Engineer](https://miro.medium.com/v2/resize:fill:20:20/1*RZVWENvZRwVijHDlg5hw7w.png)](https://medium.com/ai-software-engineer?source=post_page---read_next_recirc--f563ec9893ac----0---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  In
  
  [AI Software Engineer](https://medium.com/ai-software-engineer?source=post_page---read_next_recirc--f563ec9893ac----0---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  by
  
  [Joe Njenga](https://medium.com/@joe.njenga?source=post_page---read_next_recirc--f563ec9893ac----0---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [I Tested (New) Ollama Launch For Claude Code, Codex, OpenCode (No More Configs)\
  -------------------------------------------------------------------------------\
  \
  ### Forget configuration headaches, Ollama launch is the new easy way to launch Claude Code, Codex, OpenCode, Moltbot, or any other CLI tool.](https://medium.com/@joe.njenga/i-tested-new-ollama-launch-for-claude-code-codex-opencode-more-bfae2af3c3db?source=post_page---read_next_recirc--f563ec9893ac----0---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  5d ago
  
  [A clap icon294\
  \
  A response icon3](https://medium.com/@joe.njenga/i-tested-new-ollama-launch-for-claude-code-codex-opencode-more-bfae2af3c3db?source=post_page---read_next_recirc--f563ec9893ac----0---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2Fbfae2af3c3db&operation=register&redirect=https%3A%2F%2Fmedium.com%2Fai-software-engineer%2Fi-tested-new-ollama-launch-for-claude-code-codex-opencode-more-bfae2af3c3db&source=---read_next_recirc--f563ec9893ac----0-----------------bookmark_preview----b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  ![Moltbot (Clawdbot) The most hyped AI Assistant Full Guide](https://miro.medium.com/v2/resize:fit:679/format:webp/1*MIwggS9uYbDt-nB19-hW8A.png)
  
  [![Reza Rezvani](https://miro.medium.com/v2/resize:fill:20:20/1*jDxVaEgUePd76Bw8xJrr2g.png)](https://alirezarezvani.medium.com/?source=post_page---read_next_recirc--f563ec9893ac----1---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [Reza Rezvani](https://alirezarezvani.medium.com/?source=post_page---read_next_recirc--f563ec9893ac----1---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [Everyone’s Installing Moltbot (Clawdbot). Here’s Why I’m Not Running It in Production (Yet).\
  --------------------------------------------------------------------------------------------\
  \
  ### What actually works, what doesn’t, and whether you should set this AI Assistant up](https://alirezarezvani.medium.com/everyones-installing-moltbot-clawdbot-here-s-why-i-m-not-running-it-in-production-yet-04f9ec596ef5?source=post_page---read_next_recirc--f563ec9893ac----1---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  5d ago
  
  [A clap icon155\
  \
  A response icon8](https://alirezarezvani.medium.com/everyones-installing-moltbot-clawdbot-here-s-why-i-m-not-running-it-in-production-yet-04f9ec596ef5?source=post_page---read_next_recirc--f563ec9893ac----1---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F04f9ec596ef5&operation=register&redirect=https%3A%2F%2Falirezarezvani.medium.com%2Feveryones-installing-moltbot-clawdbot-here-s-why-i-m-not-running-it-in-production-yet-04f9ec596ef5&source=---read_next_recirc--f563ec9893ac----1-----------------bookmark_preview----b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  ![Local LLMs That Can Replace Claude Code](https://miro.medium.com/v2/resize:fit:679/format:webp/0*JpX_vOrpLzFhJfJM.png)
  
  [![Agent Native](https://miro.medium.com/v2/resize:fill:20:20/1*aZiyRsTwMmjG54EApMtwsg.jpeg)](https://agentnativedev.medium.com/?source=post_page---read_next_recirc--f563ec9893ac----0---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [Agent Native](https://agentnativedev.medium.com/?source=post_page---read_next_recirc--f563ec9893ac----0---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [Local LLMs That Can Replace Claude Code\
  ---------------------------------------\
  \
  ### Small team of engineers can easily burn >$2K/mo on Anthropic’s Claude Code (Sonnet/Opus 4.5). As budgets are tight, you might be wondering…](https://agentnativedev.medium.com/local-llms-that-can-replace-claude-code-6f5b6cac93bf?source=post_page---read_next_recirc--f563ec9893ac----0---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  Jan 20
  
  [A clap icon521\
  \
  A response icon13](https://agentnativedev.medium.com/local-llms-that-can-replace-claude-code-6f5b6cac93bf?source=post_page---read_next_recirc--f563ec9893ac----0---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F6f5b6cac93bf&operation=register&redirect=https%3A%2F%2Fagentnativedev.medium.com%2Flocal-llms-that-can-replace-claude-code-6f5b6cac93bf&source=---read_next_recirc--f563ec9893ac----0-----------------bookmark_preview----b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  ![Run Claude Code Locally on Apple Silicon Using LM Studio and LiteLLM (Zero Cost)](https://miro.medium.com/v2/resize:fit:679/format:webp/1*VbfogaijaYX-N7TkoxSElg.jpeg)
  
  [![Data Science Collective](https://miro.medium.com/v2/resize:fill:20:20/1*0nV0Q-FBHj94Kggq00pG2Q.jpeg)](https://medium.com/data-science-collective?source=post_page---read_next_recirc--f563ec9893ac----1---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  In
  
  [Data Science Collective](https://medium.com/data-science-collective?source=post_page---read_next_recirc--f563ec9893ac----1---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  by
  
  [Manjunath Janardhan](https://medium.com/@manjunath.shiva?source=post_page---read_next_recirc--f563ec9893ac----1---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [Run Claude Code Locally on Apple Silicon Using LM Studio and LiteLLM (Zero Cost)\
  --------------------------------------------------------------------------------\
  \
  ### A step-by-step guide to running Claude Code with Qwen3-Coder-30B using MLX models on macOS](https://medium.com/@manjunath.shiva/run-claude-code-locally-on-apple-silicon-using-lm-studio-and-litellm-zero-cost-1416a6b984af?source=post_page---read_next_recirc--f563ec9893ac----1---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  Jan 21
  
  [A clap icon372\
  \
  A response icon4](https://medium.com/@manjunath.shiva/run-claude-code-locally-on-apple-silicon-using-lm-studio-and-litellm-zero-cost-1416a6b984af?source=post_page---read_next_recirc--f563ec9893ac----1---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F1416a6b984af&operation=register&redirect=https%3A%2F%2Fmedium.com%2Fdata-science-collective%2Frun-claude-code-locally-on-apple-silicon-using-lm-studio-and-litellm-zero-cost-1416a6b984af&source=---read_next_recirc--f563ec9893ac----1-----------------bookmark_preview----b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  ![How to Set Up Clawdbot — Step by Step guide to setup a personal bot](https://miro.medium.com/v2/resize:fit:679/format:webp/1*FQg5JLh5-AIM6G1Znr-qxw.png)
  
  [![Neural Notions](https://miro.medium.com/v2/resize:fill:20:20/1*Xv_4SeKtNfCiqRNi_wDAoA.png)](https://medium.com/modelmind?source=post_page---read_next_recirc--f563ec9893ac----2---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  In
  
  [Neural Notions](https://medium.com/modelmind?source=post_page---read_next_recirc--f563ec9893ac----2---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  by
  
  [Nikhil](https://nkwrites.medium.com/?source=post_page---read_next_recirc--f563ec9893ac----2---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [How to Set Up Clawdbot — Step by Step guide to setup a personal bot\
  -------------------------------------------------------------------\
  \
  ### Turn your own device into a personal AI assistant that lives inside your favorite apps](https://nkwrites.medium.com/how-to-set-up-clawdbot-step-by-step-guide-to-setup-a-personal-bot-3e7957ed2975?source=post_page---read_next_recirc--f563ec9893ac----2---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  Jan 25
  
  [A clap icon234\
  \
  A response icon5](https://nkwrites.medium.com/how-to-set-up-clawdbot-step-by-step-guide-to-setup-a-personal-bot-3e7957ed2975?source=post_page---read_next_recirc--f563ec9893ac----2---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F3e7957ed2975&operation=register&redirect=https%3A%2F%2Fmedium.com%2Fmodelmind%2Fhow-to-set-up-clawdbot-step-by-step-guide-to-setup-a-personal-bot-3e7957ed2975&source=---read_next_recirc--f563ec9893ac----2-----------------bookmark_preview----b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  ![How Agent Skills Became AI’s Most Important Standard in 90 Days](https://miro.medium.com/v2/resize:fit:679/format:webp/1*VqPChBhF5Apow495dgruIQ.png)
  
  [![AI Advances](https://miro.medium.com/v2/resize:fill:20:20/1*R8zEd59FDf0l8Re94ImV0Q.png)](https://ai.gopubby.com/?source=post_page---read_next_recirc--f563ec9893ac----3---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  In
  
  [AI Advances](https://ai.gopubby.com/?source=post_page---read_next_recirc--f563ec9893ac----3---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  by
  
  [Han HELOIR YAN, Ph.D. ☕️](https://medium.com/@han.heloir?source=post_page---read_next_recirc--f563ec9893ac----3---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [How Agent Skills Became AI’s Most Important Standard in 90 Days\
  ---------------------------------------------------------------\
  \
  ### The AI infrastructure War You Missed](https://medium.com/@han.heloir/how-agent-skills-became-ais-most-important-standard-in-90-days-a66b6369b1b7?source=post_page---read_next_recirc--f563ec9893ac----3---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  Jan 25
  
  [A clap icon2K\
  \
  A response icon15](https://medium.com/@han.heloir/how-agent-skills-became-ais-most-important-standard-in-90-days-a66b6369b1b7?source=post_page---read_next_recirc--f563ec9893ac----3---------------------b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2Fa66b6369b1b7&operation=register&redirect=https%3A%2F%2Fai.gopubby.com%2Fhow-agent-skills-became-ais-most-important-standard-in-90-days-a66b6369b1b7&source=---read_next_recirc--f563ec9893ac----3-----------------bookmark_preview----b0fbe8e5_ac22_46b8_b351_e3fdf3ae00c9--------------)
  
  [See more recommendations](https://medium.com/?source=post_page---read_next_recirc--f563ec9893ac---------------------------------------)
  
  [Help](https://help.medium.com/hc/en-us?source=post_page-----f563ec9893ac---------------------------------------)
  
  [Status](https://status.medium.com/?source=post_page-----f563ec9893ac---------------------------------------)
  
  [About](https://medium.com/about?autoplay=1&source=post_page-----f563ec9893ac---------------------------------------)
  
  [Careers](https://medium.com/jobs-at-medium/work-at-medium-959d1a85284e?source=post_page-----f563ec9893ac---------------------------------------)
  
  [Press](mailto:pressinquiries@medium.com)
  
  [Blog](https://blog.medium.com/?source=post_page-----f563ec9893ac---------------------------------------)
  
  [Privacy](https://policy.medium.com/medium-privacy-policy-f03bf92035c9?source=post_page-----f563ec9893ac---------------------------------------)
  
  [Rules](https://policy.medium.com/medium-rules-30e5502c4eb4?source=post_page-----f563ec9893ac---------------------------------------)
  
  [Terms](https://policy.medium.com/medium-terms-of-service-9db0094a1e0f?source=post_page-----f563ec9893ac---------------------------------------)
  
  [Text to speech](https://speechify.com/medium?source=post_page-----f563ec9893ac---------------------------------------)
  --- End Content ---

Awesome OpenClaw (Moltbot (Clawdbot)) Skills - GitHub
  URL: https://github.com/VoltAgent/awesome-openclaw-skills
  Awesome OpenClaw (Moltbot (Clawdbot)) Skills OpenClaw (previously known as Moltbot, originally Clawdbot... identity crisis included, no extra charge) is a locally-running AI assistant that operates directly on your machine.
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
  
  [![social](https://private-user-images.githubusercontent.com/18739364/542745161-a6f310af-8fed-4766-9649-b190575b399d.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NzAwMDkzODQsIm5iZiI6MTc3MDAwOTA4NCwicGF0aCI6Ii8xODczOTM2NC81NDI3NDUxNjEtYTZmMzEwYWYtOGZlZC00NzY2LTk2NDktYjE5MDU3NWIzOTlkLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNjAyMDIlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjYwMjAyVDA1MTEyNFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWYwNmMxZDI2ZWNhNmEzNzdjMGU0Yzg3YjBjMzc0YzQ0YjdiODJiNTY3NWY4YzRkYzcwMjM3NjQxNTRhZWU5NGQmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0._GwS7Xsj1xW3r0to9V3NlBSd7crwz70O6HF_LwXfQwo)](https://github.com/VoltAgent/voltagent)
    
    
  
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
  
    
  [![social](https://private-user-images.githubusercontent.com/18739364/540268501-4c40affa-8e20-443a-9ec5-1abb6679b170.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NzAwMDkzODQsIm5iZiI6MTc3MDAwOTA4NCwicGF0aCI6Ii8xODczOTM2NC81NDAyNjg1MDEtNGM0MGFmZmEtOGUyMC00NDNhLTllYzUtMWFiYjY2NzliMTcwLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNjAyMDIlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjYwMjAyVDA1MTEyNFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTgxYzRmMGE2NWUyNDgyNGE1ZGE0ZTkzYTRmNmU5Mzk1NWUxZjkwNjhkMjU2NDg3MGNhOWE0M2U1MjI2N2U1N2ImWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.ieC--7oeWy2SYl5ASWNK0kfQnBFUZ0EgFop7FdTYLIc)](https://github.com/VoltAgent/voltagent)
    
  
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
  
  ### Uh oh!
  
  There was an error while loading. [Please reload this page](https://github.com/VoltAgent/awesome-openclaw-skills)
  .
  
  You can’t perform that action at this time.
  --- End Content ---

If you're using @openclaw this writeup will probably make your ...
  URL: https://x.com/dabit3/status/2018029884430233903
  11 hours ago ... Multiple agents with different skills working together. A shared ... heartbeat cron. Ten agents equals ten sessions. Each waking up on ...

  --- Content ---
  Don’t miss what’s happening
  
  People on X are the first to know.
  
  [Log in](https://x.com/login)
  
  [Sign up](https://x.com/i/flow/signup)
  
  See new posts
  --- End Content ---

Taking a Look at OpenClaw (Clawdbot) | Moncef Abboud
  URL: https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/
  Two mechanisms are available for that: a cron job with exact timing and an independent context, or a heartbeat (basically a markdown file with a list of tasks) that runs every 30 min (configurable) in the main session. The former is more isolated and can use a different model and context.

  --- Content ---
  Taking a Look at OpenClaw (Clawdbot)
  
  Contents
  
  > Openclaw built-in web UI
  
  > Openclaw in Discord
  
  Openclaw, formerly known as Clawdbot (Anthropic didn’t take a liking to that name), exploded in popularity. The stars history chart is every open-source contributor’s dream. It’s making hockey sticks jealous. Tremendous popularity.
  
  Game changer? Latest overhyped shiny thing? Security nightmare? Hot takes abound.
  
  Let’s see for ourselves.
  
  What is Openclaw?[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#what-is-openclaw)
  
  ---------------------------------------------------------------------------------------------------------
  
  It’s an open-source AI assistant. You can run it on your own machine, another machine you own, or a VPS. Then you connect it to various tools via skills and it does things for you.
  
  But wait, isn’t this like Claude Code or Codex or something? Kinda.
  
  Openclaw brings some differentiators.
  
  First, it exposes a gateway and allows connecting various channels: Telegram, Discord, WhatsApp, etc. You configure a bot key or API key. And then you can chat with your Openclaw from your favorite messaging app. The gateway is subscribed to these messaging platforms’ servers and gets notified whenever you send a message.
  
  Second, it’s open-source and supports pretty much every model.
  
  Third, there are no guardrails or big company scared of causing some terrible security leak. With this freedom comes a lot of power. The agent can connect to your Google account using the GOG CLI (developed by the same author), and you create a Google test OAuth app to grant access to a Google account. This itself is a very important point. For a regular company offering a polished solution, getting approved by Google to access Gmail data is an extremely arduous process. When you run the app locally and use a test OAuth client, you’re free to do so without approval. That’s one of the reasons this only works when self-installed. Same logic applies for other APIs/apps. When you run things locally in test mode, you can do more things (but also more damage).
  
  Finally, an interesting feature is memory. The agent asks you things and writes them down in memory.md files. After completing tasks, it also persists some notes to memory.md files. It has some short-term ones and a longer-term one. And it’s proactive about it. This way, the agent actually learns more about you. Furthermore, it’s also able to create new skills and learn new things. Basically, it can do some research, write down its findings, and these become a new skill it can leverage. Real self-improvement! It does this using a `skill-creator` skill.
  
  `|     |     | | --- | --- | | 1<br>2<br>3<br>4 | {<br>  "name": "skill-creator",<br>  "description": "Create or update AgentSkills. Use when designing, structuring, or packaging skills with scripts, references, and assets."<br>} |`
  
  In addition to that, there’s `clawdhub.com` which is a registry of skills people can share and can install via `npm` or `clawdhub` CLI.
  
  Anyway, open-source, access via familiar messaging apps, absence of guardrails, memory, self-improvement, and Twitter/X hype resulted in +100k stars in a very short period of time.
  
  One other cool feature is the ability to schedule periodic tasks. Two mechanisms are available for that: a cron job with exact timing and an independent context, or a `heartbeat` (basically a markdown file with a list of tasks) that runs every 30 min (configurable) in the main session. The former is more isolated and can use a different model and context. This periodicity, or “heartbeat”, brings the agent to life and makes it more proactive. Example `heartbeat.md` from the docs:
  
  `|     |     | | --- | --- | | 1<br>2<br>3<br>4<br>5<br>6 | # Heartbeat checklist<br><br>- Check email for urgent messages<br>- Review calendar for events in next 2 hours<br>- If a background task finished, summarize results<br>- If idle for 8+ hours, send a brief check-in |`
  
  For me, interacting with it through a messaging app feels fundamentally different. Knowing I own the data—and can swap models without disrupting anything—changes the relationship. It feels more intimate. Running it locally with a self-hosted model would deepen that even more. Compared to ChatGPT or Claude Code, this feels like a radical shift. It’s the difference between buying a house and renting one: similar on the surface, but not the same thing.
  
  This tool is extremely powerful but also dangerous. It’s highly discouraged to set this up on your own machine or connect your personal accounts. Use a different machine or a VPS and give the bot its own account. Memes are circulating online of people buying Mac Minis to run Openclaw.
  
  Openclaw Setup Tutorial[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#openclaw-setup-tutorial)
  
  ----------------------------------------------------------------------------------------------------------------------
  
  Feel free to skip this section if you’ve already setup Openclaw.
  
  These steps assume (I am running this on GCP):
  
  *   You are using a Debian-based VPS
  *   You want to authenticate via SSH keys (no passwords)
  *   You will install Go, Node.js (via NVM), and Molt Bot
  
  * * *
  
  ### 1) Generate an SSH Key Pair (Local Machine)[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#1-generate-an-ssh-key-pair-local-machine)
  
  `|     |     | | --- | --- | | 1   | ssh-keygen -t ed25519 -f ~/.ssh/my_openclaw_key |`
  
  This creates:
  
  *   `~/.ssh/my_openclaw_key` (private key)
  *   `~/.ssh/my_openclaw_key.pub` (public key)
  
  ### 2) Add Public Key to VPS[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#2-add-public-key-to-vps)
  
  Copy your public key:
  
  `|     |     | | --- | --- | | 1   | cat ~/.ssh/my_openclaw_key.pub |`
  
  On the VPS, append it to:
  
  `|     |     | | --- | --- | | 1   | ~/.ssh/authorized_keys |`
  
  Result should look like:
  
  `|     |     | | --- | --- | | 1   | ssh-ed25519 AAAAC3NzaC1lZDI1ATE5BBBAIEXuUnKqzQxVd7PpvPM6IAavfII0ivROI8WmDoCmaBO4 cef@cefbox |`
  
  Ensure correct permissions:
  
  `|     |     | | --- | --- | | 1<br>2 | chmod 700 ~/.ssh<br>chmod 600 ~/.ssh/authorized_keys |`
  
  * * *
  
  ### 3) Test SSH Login[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#3-test-ssh-login)
  
  From your local machine:
  
  `|     |     | | --- | --- | | 1   | ssh -i ~/.ssh/my_openclaw_key cef@31.151.21.11 |`
  
  (Replace with your VPS IP.)
  
  * * *
  
  ### 4) Verify Password Authentication is Disabled[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#4-verify-password-authentication-is-disabled)
  
  On the VPS:
  
  `|     |     | | --- | --- | | 1   | sudo sshd -T \| grep passwordauthentication |`
  
  Expected output:
  
  `|     |     | | --- | --- | | 1   | passwordauthentication no |`
  
  * * *
  
  ### 5) Update System & Install Base Packages[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#5-update-system--install-base-packages)
  
  `|     |     | | --- | --- | | 1<br>2 | sudo apt update<br>sudo apt install -y libatomic1 make curl |`
  
  * * *
  
  ### 6) Install NVM (Node Version Manager)[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#6-install-nvm-node-version-manager)
  
  `|     |     | | --- | --- | | 1   | curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh \| bash |`
  
  Add environment variables:
  
  `|     |     | | --- | --- | | 1<br>2<br>3 | echo 'export XDG_RUNTIME_DIR=/run/user/$(id -u)' >> ~/.bashrc<br>echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.bashrc<br>source ~/.bashrc |`
  
  * * *
  
  ### 7) Install Go (1.25)[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#7-install-go-125)
  
  `|     |     | | --- | --- | | 1<br>2<br>3<br>4<br>5<br>6<br>7 | GO=1.25.0<br>ARCH=$(uname -m \| sed 's/x86_64/amd64/;s/aarch64/arm64/')<br>curl -LO https://golang.org/dl/go$GO.linux-$ARCH.tar.gz<br>sudo rm -rf /usr/local/go<br>sudo tar -C /usr/local -xzf go$GO.linux-$ARCH.tar.gz<br>grep -q /usr/local/go/bin ~/.bashrc \| echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc<br>source ~/.bashrc |`
  
  Verify:
  
  `|     |     | | --- | --- | | 1<br>2 | # we'll use golang for GOG later<br>go version |`
  
  * * *
  
  ### 8) Install Node.js 25[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#8-install-nodejs-25)
  
  `|     |     | | --- | --- | | 1<br>2 | nvm install 25<br>node -v |`
  
  * * *
  
  ### 9) Install Molt Bot[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#9-install-molt-bot)
  
  `|     |     | | --- | --- | | 1   | curl -fsSL https://openclaw.bot/install.sh \| bash |`
  
  (This may take a minute.)
  
  * * *
  
  ### 10) Onboard Molt Bot & Install Daemon[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#10-onboard-molt-bot--install-daemon)
  
  The `install.sh` script should trigger the install process. if it’s interrupted for whatever reason, you can trigger it using:
  
  `|     |     | | --- | --- | | 1   | openclaw onboard --install-daemon |`
  
  You can check the gateway service using \` systemctl –user status openclaw-gateway\`
  
  Follow the prompts. You’ll need a model/LLM API key and at least one channel. The quickest option is Telegram:
  
  Create a Telegram account. then open `@BotFather` and type `/newbot`.
  
  Provide and you’ll receive a bot token (e.g. `8511185791:ACEF6Hz3RnGXXR-OJ_gTdiWfdVNgfQQfvaTS8`).
  
  Paste the token into the onboarding flow.
  
  * * *
  
  ### 11) Create SSH Tunnel (Local Machine)[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#11-create-ssh-tunnel-local-machine)
  
  This forwards the Molt gateway to your local computer:
  
  `|     |     | | --- | --- | | 1   | ssh -i ~/.ssh/my_openclaw_key -N -L 18789:127.0.0.1:18789 cef@35.185.23.33 |`
  
  * * *
  
  ### 12) Complete Setup in Browser[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#12-complete-setup-in-browser)
  
  On your local machine, open:
  
  `|     |     | | --- | --- | | 1   | http://127.0.0.1:18789?token=... |`
  
  (Paste the full URL shown by Molt Bot.)
  
  you can also start using telegram by talking to the bot you created previously, but you’ll need to pair you account with Openclaw:
  
  `|     |     | | --- | --- | | 1<br>2<br>3<br>4<br>5<br>6<br>7<br>8 | Openclaw: access not configured.<br><br>Your Telegram user id: 6424115158<br><br>Pairing code: WZXXHBZ1<br><br>Ask the bot owner to approve with:<br>openclaw pairing approve telegram <code> |`
  
  Just run `openclaw pairing approve telegram <code>` in the CLI or provide the code in the web chat and ask the bot to pair.
  
  * * *
  
  ### 13) Set Up GoG (Google Gateway)[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#13-set-up-gog-google-gateway)
  
  `|     |     | | --- | --- | | 1<br>2<br>3<br>4<br>5<br>6<br>7<br>8<br>9<br>10<br>11<br>12<br>13<br>14 | # install required node packages<br>npm install -g clawdhub undici<br><br># install gog via clawdhub<br>clawdhub install gog<br><br># build gog CLI<br>git clone https://github.com/steipete/gogcli.git<br>cd gogcli<br>make<br><br># add gog to PATH<br>sudo ln -s $(pwd)/bin/gog /usr/local/go/bin/gog |`
  
  #### a) Create Google OAuth Credentials[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#a-create-google-oauth-credentials)
  
  Follow the GoG README to create an OAuth client and download the credentials file:
  
  [https://github.com/steipete/gogcli?tab=readme-ov-file#1-get-oauth2-credentials](https://github.com/steipete/gogcli?tab=readme-ov-file#1-get-oauth2-credentials)
  
  Download the Client Secret file as:
  
  `|     |     | | --- | --- | | 1   | client_secret_1190191145325-322ozz0pu1149vk4k7mxxnafflxxb6udddk.apps.googleusercontent.com.json |`
  
  Copy this file **to your VPS** (for example using `scp`):
  
  `|     |     | | --- | --- | | 1   | scp -i ~/.ssh/my_openclaw_key <secret_client_file>.json cef@35.185.23.33:~ |`
  
  * * *
  
  #### b) Start Google Authentication (on VPS)[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#b-start-google-authentication-on-vps)
  
  `|     |     | | --- | --- | | 1<br>2 | gog auth credentials google_secret.json<br>gog auth add you@gmail.com |`
  
  This command prints a **grant-permission URL** that points to:
  
  `|     |     | | --- | --- | | 1<br>2<br>3 | Opening browser for authorization…<br>If the browser doesn't open, visit this URL:<br>https://accounts.google.com/o/oauth2/auth?access_type=offline&client_id=1190191145325-322ozz0pu1149vk4k7mxxnafflxxb6udddk.apps.googleusercontent.com&include_granted_scopes=true&redirect_uri=http%3A%2F%2F127.0.0.1%3A34213%2Foauth2%2Fcallback&response_type=code |`
  
  notice `redirect_uri=http%3A%2F%2F127.0.0.1%3A34213%2F`, gog will start a server locally on `127.0.0.1:34213` (this port will be different in your case).
  
  Because this is running on the VPS, you must tunnel that port to your local machine.
  
  * * *
  
  #### c) Open SSH Tunnel (Local Machine)[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#c-open-ssh-tunnel-local-machine)
  
  1.  Copy the port number from the URL
      
  2.  Set the port and open tunnel:
      
  
  `|     |     | | --- | --- | | 1<br>2 | export g_port=34213<br>ssh -i ~/.ssh/my_openclaw_key -N -L $g_port:127.0.0.1:$g_port cef@35.185.23.33 |`
  
  * * *
  
  #### d) Complete Login[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#d-complete-login)
  
  Open in your **local browser**:
  
  `|     |     | | --- | --- | | 1   | http://127.0.0.1:34213 |`
  
  Approve Google access. Only provide necessary permissions. Be super careful if this is your personal/professional account. Once complete, GoG authentication is finished.
  
  You’ll need to provide a secret/password to encrypt the token. Openclaw will ask you about that password in your chat so it can use the GOG cli.
  
  Voila, your agent has access to the Google account.
  
  Molbot Security Risks[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#molbot-security-risks)
  
  ------------------------------------------------------------------------------------------------------------------
  
  Running Openclaw with its gateway exposed to the internet is extremely risky, localhost with an SSH tunnel or a VPN/Tailscale are table stakes. The consequences of a compromise are severe: attackers can read your private conversations, steal API keys and OAuth tokens, access your emails and messages, and even gain shell access to the host machine.
  
  Because AI agents both read untrusted content and take actions, a single crafted message or email can silently trigger data exfiltration without any traditional “hacking”. The tool was designed for local-only use and for tech-savvy people, but even those can make mistakes.
  
  Now What?[](https://cefboud.com/posts/openclaw-molt-bot-clawd-bot-exploration/#now-what)
  
  -----------------------------------------------------------------------------------------
  
  Coding Agents, Openclaw, Agentic Commerce, etc. Change is here and it’s here fast. We’re really living through unprecedented times. It can be scary, but it’s also exciting. The best way forward is to try things, stay curious, and embrace change. It’s going to happen either way.
  
    
  
  Newsletter
  
   Subscribe
  
  [Technical Writing](https://cefboud.com/categories/technical-writing/)
  , [Open Source](https://cefboud.com/categories/open-source/)
  
  [AI](https://cefboud.com/tags/ai/)
   [Open Source](https://cefboud.com/tags/open-source/)
   [Openclaw](https://cefboud.com/tags/openclaw/)
   [LLM](https://cefboud.com/tags/llm/)
   [AI Assistant](https://cefboud.com/tags/ai-assistant/)
  
  This post is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
   by the author.
  
  Share[](https://twitter.com/intent/tweet?text=Taking%20a%20Look%20at%20OpenClaw%20(Clawdbot)%20-%20Moncef%20Abboud&url=https%3A%2F%2Fcefboud.com%2Fposts%2Fopenclaw-molt-bot-clawd-bot-exploration%2F)
  [](https://www.facebook.com/sharer/sharer.php?title=Taking%20a%20Look%20at%20OpenClaw%20(Clawdbot)%20-%20Moncef%20Abboud&u=https%3A%2F%2Fcefboud.com%2Fposts%2Fopenclaw-molt-bot-clawd-bot-exploration%2F)
  [](https://t.me/share/url?url=https%3A%2F%2Fcefboud.com%2Fposts%2Fopenclaw-molt-bot-clawd-bot-exploration%2F&text=Taking%20a%20Look%20at%20OpenClaw%20(Clawdbot)%20-%20Moncef%20Abboud)
  
  Trending Tags
  -------------
  
  [Open Source](https://cefboud.com/tags/open-source/)
   [AI](https://cefboud.com/tags/ai/)
   [Apache Kafka](https://cefboud.com/tags/apache-kafka/)
   [MCP](https://cefboud.com/tags/mcp/)
   [LLM](https://cefboud.com/tags/llm/)
   [Linux](https://cefboud.com/tags/linux/)
   [C](https://cefboud.com/tags/c/)
   [Go](https://cefboud.com/tags/go/)
   [Programming](https://cefboud.com/tags/programming/)
   [Agentic Commerce](https://cefboud.com/tags/agentic-commerce/)
  --- End Content ---

How to Run OpenClaw with DigitalOcean's One-Click Deploy
  URL: https://www.digitalocean.com/community/tutorials/how-to-run-openclaw
  From the GUI, you can review the bot's usage, add communication channels, schedule cron jobs, add skills, and manage all aspects of OpenClaw.

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
      
      ### Connect on Discord
      
      Join the conversation in our Discord to connect with fellow developers
      
      [Visit Discord](https://discord.gg/digitalocean)
      
  
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
  
  This site uses cookies and related technologies, as described in our [privacy policy](https://www.digitalocean.com/legal/privacy-policy/)
  , for purposes that may include site operation, analytics, enhanced user experience, or advertising. You may choose to consent to our use of these technologies, or manage your own preferences. Please visit our [cookie policy](https://www.digitalocean.com/legal/cookie-policy)
   for more information.
  
  Agree & Proceed Decline All Manage Choices
  
  Loading...
  
  Community
  ---------
  
  Product Docs
  ------------
  
  Marketplace
  -----------
  
  DigitalOcean Blog
  -----------------
  
  navigate go exit
  --- End Content ---

openclaw/openclaw - DeepWiki
  URL: https://deepwiki.com/openclaw/openclaw
  Overview Relevant source files Purpose and Scope This document provides a technical introduction to the OpenClaw codebase: its purpose, architecture, core components, and how they fit together. It explains what OpenClaw is, how it's structured at a high level, and where to find key subsystems in code. For detailed installation steps, see Quick Start. For configuration reference, see ...

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
  
  Overview
  ========
  
  Relevant source files
  
  *   [.npmrc](https://github.com/openclaw/openclaw/blob/bf6ec64f/.npmrc)
      
  *   [AGENTS.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/AGENTS.md)
      
  *   [CHANGELOG.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/CHANGELOG.md)
      
  *   [README.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/README.md)
      
  *   [apps/android/app/build.gradle.kts](https://github.com/openclaw/openclaw/blob/bf6ec64f/apps/android/app/build.gradle.kts)
      
  *   [apps/ios/Sources/Info.plist](https://github.com/openclaw/openclaw/blob/bf6ec64f/apps/ios/Sources/Info.plist)
      
  *   [apps/ios/Tests/Info.plist](https://github.com/openclaw/openclaw/blob/bf6ec64f/apps/ios/Tests/Info.plist)
      
  *   [apps/ios/project.yml](https://github.com/openclaw/openclaw/blob/bf6ec64f/apps/ios/project.yml)
      
  *   [assets/avatar-placeholder.svg](https://github.com/openclaw/openclaw/blob/bf6ec64f/assets/avatar-placeholder.svg)
      
  *   [docs/docs.json](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/docs.json)
      
  *   [docs/help/faq.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/help/faq.md)
      
  *   [docs/help/index.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/help/index.md)
      
  *   [docs/help/troubleshooting.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/help/troubleshooting.md)
      
  *   [docs/install/index.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/install/index.md)
      
  *   [docs/install/installer.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/install/installer.md)
      
  *   [docs/install/migrating.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/install/migrating.md)
      
  *   [docs/northflank.mdx](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/northflank.mdx)
      
  *   [docs/platforms/digitalocean.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/platforms/digitalocean.md)
      
  *   [docs/platforms/exe-dev.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/platforms/exe-dev.md)
      
  *   [docs/platforms/fly.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/platforms/fly.md)
      
  *   [docs/platforms/gcp.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/platforms/gcp.md)
      
  *   [docs/platforms/index.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/platforms/index.md)
      
  *   [docs/platforms/linux.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/platforms/linux.md)
      
  *   [docs/platforms/mac/release.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/platforms/mac/release.md)
      
  *   [docs/platforms/oracle.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/platforms/oracle.md)
      
  *   [docs/platforms/windows.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/platforms/windows.md)
      
  *   [docs/reference/RELEASING.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/reference/RELEASING.md)
      
  *   [docs/start/hubs.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/start/hubs.md)
      
  *   [docs/vps.md](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/vps.md)
      
  *   [extensions/memory-core/package.json](https://github.com/openclaw/openclaw/blob/bf6ec64f/extensions/memory-core/package.json)
      
  *   [fly.private.toml](https://github.com/openclaw/openclaw/blob/bf6ec64f/fly.private.toml)
      
  *   [fly.toml](https://github.com/openclaw/openclaw/blob/bf6ec64f/fly.toml)
      
  *   [package.json](https://github.com/openclaw/openclaw/blob/bf6ec64f/package.json)
      
  *   [pnpm-lock.yaml](https://github.com/openclaw/openclaw/blob/bf6ec64f/pnpm-lock.yaml)
      
  *   [pnpm-workspace.yaml](https://github.com/openclaw/openclaw/blob/bf6ec64f/pnpm-workspace.yaml)
      
  *   [scripts/clawtributors-map.json](https://github.com/openclaw/openclaw/blob/bf6ec64f/scripts/clawtributors-map.json)
      
  *   [scripts/update-clawtributors.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/scripts/update-clawtributors.ts)
      
  *   [scripts/update-clawtributors.types.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/scripts/update-clawtributors.types.ts)
      
  *   [scripts/write-build-info.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/scripts/write-build-info.ts)
      
  *   [src/agents/pi-embedded-runner-extraparams.live.test.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner-extraparams.live.test.ts)
      
  *   [src/agents/pi-embedded-runner-extraparams.test.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/pi-embedded-runner-extraparams.test.ts)
      
  *   [src/discord/monitor/presence-cache.test.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/discord/monitor/presence-cache.test.ts)
      
  *   [src/index.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/index.ts)
      
  *   [src/infra/git-commit.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/infra/git-commit.ts)
      
  *   [ui/package.json](https://github.com/openclaw/openclaw/blob/bf6ec64f/ui/package.json)
      
  *   [ui/src/styles.css](https://github.com/openclaw/openclaw/blob/bf6ec64f/ui/src/styles.css)
      
  *   [ui/src/styles/layout.mobile.css](https://github.com/openclaw/openclaw/blob/bf6ec64f/ui/src/styles/layout.mobile.css)
      
  
  Purpose and Scope
  -----------------
  
  This document provides a technical introduction to the OpenClaw codebase: its purpose, architecture, core components, and how they fit together. It explains what OpenClaw is, how it's structured at a high level, and where to find key subsystems in code.
  
  For detailed installation steps, see [Quick Start](https://deepwiki.com/openclaw/openclaw/1.2-quick-start)
  . For configuration reference, see [Configuration File Structure](https://deepwiki.com/openclaw/openclaw/4.1-configuration-file-structure)
  . For deep dives into agent execution, see [Agent Execution Flow](https://deepwiki.com/openclaw/openclaw/5.1-agent-execution-flow)
  .
  
  * * *
  
  What is OpenClaw
  ----------------
  
  OpenClaw is a **personal AI assistant platform** that runs on your own infrastructure. It connects AI models (Claude, GPT, Gemini, local models) to messaging channels you already use (WhatsApp, Telegram, Discord, Slack, Signal, iMessage, Microsoft Teams, and 15+ more via plugins). The system is designed for single-user or small-team deployment with local-first control, extensive tooling, and multi-agent routing.
  
  **Sources:** [README.md1-23](https://github.com/openclaw/openclaw/blob/bf6ec64f/README.md#L1-L23)
   [package.json1-14](https://github.com/openclaw/openclaw/blob/bf6ec64f/package.json#L1-L14)
  
  * * *
  
  Core Architecture
  -----------------
  
  Extensions: extensions/\*
  
  Messaging Channels: src/
  
  Agent Runtime: src/agents/
  
  Gateway Control Plane: src/gateway/
  
  User Interfaces
  
  RPC
  
  WebSocket
  
  WebSocket
  
  Bridge Protocol
  
  Bonjour Discovery
  
  DNS-SD
  
  Route Messages
  
  Route Messages
  
  Route Messages
  
  Route Messages
  
  Route Messages
  
  Route Messages
  
  openclaw CLI  
  bin: openclaw.mjs
  
  Control UI  
  ui/src/
  
  Terminal UI  
  src/tui/
  
  macOS App  
  apps/macos/
  
  iOS Node  
  apps/ios/
  
  Android Node  
  apps/android/
  
  server.ts  
  WebSocket Server  
  default port 18789
  
  src/config/sessions.ts  
  Session Store
  
  src/config/config.ts  
  loadConfig()
  
  src/cron/  
  Cron Scheduler
  
  src/infra/presence.ts  
  Health Monitor
  
  piembeddedrunner.ts  
  Pi Agent Core RPC
  
  prompt-builder.ts  
  Context Assembly
  
  src/memory/  
  Hybrid Search
  
  src/agents/tools.ts  
  Tool Definitions
  
  src/agents/sandbox.ts  
  Docker Isolation
  
  provider-web.ts  
  Baileys
  
  telegram/  
  grammY
  
  discord/  
  discord.js
  
  slack/  
  Bolt
  
  signal/  
  signal-cli
  
  imessage/  
  imsg
  
  msteams/  
  @microsoft/agents-hosting
  
  matrix/  
  matrix-bot-sdk
  
  nostr/  
  nostr-tools
  
  voice-call/
  
  memory-core/
  
  bluebubbles/
  
  **Description:** OpenClaw's architecture centers on a **Gateway Control Plane** ([src/gateway/server.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/gateway/server.ts)
  ) that orchestrates all system components. The Gateway exposes a WebSocket server (default port 18789) that accepts connections from CLI, Control UI, TUI, and companion apps. It routes messages between channels and the agent runtime, manages sessions, handles cron jobs, and monitors system health. The **Agent Runtime** ([src/agents/piembeddedrunner.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/piembeddedrunner.ts)
  ) executes AI interactions using the Pi Agent Core library, builds dynamic system prompts, queries memory search, and invokes tools. The system is extensible via plugins loaded from [extensions/](https://github.com/openclaw/openclaw/blob/bf6ec64f/extensions/)
  
  **Sources:** [src/gateway/server.ts1-100](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/gateway/server.ts#L1-L100)
   [src/agents/piembeddedrunner.ts1-50](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/piembeddedrunner.ts#L1-L50)
   [src/index.ts1-95](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/index.ts#L1-L95)
   [README.md132-167](https://github.com/openclaw/openclaw/blob/bf6ec64f/README.md#L132-L167)
  
  * * *
  
  System Entry Points
  -------------------
  
  Core Services
  
  Command Routing
  
  CLI Entry: openclaw.mjs
  
  openclaw.mjs  
  Shebang wrapper
  
  src/index.ts  
  Main module
  
  src/cli/program.ts  
  buildProgram()
  
  src/commands/gateway.ts  
  gateway subcommands
  
  src/commands/agent.ts  
  agent subcommands
  
  src/commands/channels.ts  
  channels subcommands
  
  src/commands/configure.ts  
  config/configure/onboard
  
  src/commands/doctor.ts  
  doctor/setup
  
  src/gateway/server.ts  
  Gateway Service
  
  src/agents/piembeddedrunner.ts  
  Agent Service
  
  src/tui/  
  Terminal UI
  
  **Description:** The `openclaw` command ([openclaw.mjs](https://github.com/openclaw/openclaw/blob/bf6ec64f/openclaw.mjs)
  ) serves as the main entry point. It loads [src/index.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/index.ts)
   which sets up environment, installs error handlers, and builds the CLI program via [src/cli/program.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/cli/program.ts)
   using Commander.js. The program registers command groups under [src/commands/](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/commands/)
   (gateway, agent, channels, config, doctor, etc.), which route to their respective services. The Gateway and Agent services can run as background daemons (launchd/systemd) or interactively.
  
  **Sources:** [openclaw.mjs1-10](https://github.com/openclaw/openclaw/blob/bf6ec64f/openclaw.mjs#L1-L10)
   [src/index.ts47-94](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/index.ts#L47-L94)
   [src/cli/program.ts1-50](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/cli/program.ts#L1-L50)
   [package.json12-14](https://github.com/openclaw/openclaw/blob/bf6ec64f/package.json#L12-L14)
  
  * * *
  
  Configuration and State
  -----------------------
  
  OpenClaw stores configuration in `~/.openclaw/openclaw.json` (JSON5 format) and state/sessions in `~/.openclaw/`. The configuration loader ([src/config/config.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/config/config.ts#LNaN-LNaN)
  ) applies precedence: environment variables override config file values, which override system defaults. The [doctor command](https://deepwiki.com/openclaw/openclaw/12.6-diagnostic-commands)
   auto-migrates legacy paths and config schemas.
  
  ### Configuration File Location
  
  | Setting | Default Path | Override |
  | --- | --- | --- |
  | Config | `~/.openclaw/openclaw.json` | `OPENCLAW_CONFIG_PATH` |
  | State | `~/.openclaw/` | `OPENCLAW_STATE_DIR` |
  | Workspace | `~/.openclaw/workspace/` | `agents.defaults.workspace` |
  
  **Sources:** [src/config/config.ts1-100](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/config/config.ts#L1-L100)
   [docs/gateway/configuration.md1-50](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/gateway/configuration.md#L1-L50)
   [README.md295-313](https://github.com/openclaw/openclaw/blob/bf6ec64f/README.md#L295-L313)
  
  * * *
  
  Agent Execution Model
  ---------------------
  
  Inbound Message  
  from Channel
  
  resolveSessionKey()  
  src/config/sessions.ts
  
  Session Lock  
  sequential/concurrent
  
  PiEmbeddedRunner  
  src/agents/piembeddedrunner.ts
  
  buildSystemPrompt()  
  src/agents/prompt-builder.ts
  
  searchMemory()  
  src/memory/
  
  Model Provider  
  Anthropic/OpenAI/etc
  
  Tool Execution  
  src/agents/tools.ts
  
  Docker Sandbox  
  src/agents/sandbox.ts
  
  Stream Response  
  Block Streaming
  
  saveSessionStore()  
  src/config/sessions.ts
  
  **Description:** When a message arrives from a channel, [resolveSessionKey()](https://github.com/openclaw/openclaw/blob/bf6ec64f/resolveSessionKey())
   in [src/config/sessions.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/config/sessions.ts)
   determines the session ID (e.g., `main` for direct user chats, `dm:channel:id` for DMs, `group:channel:id` for groups). The [PiEmbeddedRunner](https://github.com/openclaw/openclaw/blob/bf6ec64f/PiEmbeddedRunner)
   in [src/agents/piembeddedrunner.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/piembeddedrunner.ts)
   loads session history, builds a system prompt via [src/agents/prompt-builder.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/prompt-builder.ts)
   queries memory search ([src/memory/](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/memory/)
  ), and streams the request to model providers. Tool calls are intercepted, executed (optionally in Docker sandboxes via [src/agents/sandbox.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/sandbox.ts)
  ), and results are streamed back to the channel. Session state is persisted after each turn.
  
  **Sources:** [src/agents/piembeddedrunner.ts1-360](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/piembeddedrunner.ts#L1-L360)
   [src/config/sessions.ts1-100](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/config/sessions.ts#L1-L100)
   [src/agents/prompt-builder.ts1-50](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/prompt-builder.ts#L1-L50)
   [src/memory/1-50](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/memory/#L1-L50)
  
  * * *
  
  Message Routing and Channel Integration
  ---------------------------------------
  
  OpenClaw routes messages through a unified auto-reply system ([src/auto-reply/reply.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/auto-reply/reply.ts#LNaN-LNaN)
  ) that handles access control, session resolution, and agent dispatch. Each channel adapter ([src/telegram/](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/telegram/)
   [src/discord/](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/discord/)
   [src/slack/](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/slack/)
   etc.) implements:
  
  1.  **Authentication** (bot tokens, QR login, OAuth)
  2.  **Inbound parsing** (text, media, reactions, threads)
  3.  **Access control** (allowlists, pairing, DM policies)
  4.  **Outbound formatting** (markdown, chunking, media uploads)
  
  Channels are enabled via configuration (e.g., `channels.discord.enabled: true`) and environment variables (e.g., `DISCORD_BOT_TOKEN`).
  
  **Sources:** [src/auto-reply/reply.ts1-100](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/auto-reply/reply.ts#L1-L100)
   [src/telegram/1-50](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/telegram/#L1-L50)
   [src/discord/1-50](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/discord/#L1-L50)
   [src/slack/1-50](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/slack/#L1-L50)
   [src/provider-web.ts1-100](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/provider-web.ts#L1-L100)
  
  * * *
  
  Plugin Architecture
  -------------------
  
  Integration Slots
  
  Plugin Types
  
  Plugin Loader  
  src/plugins/loader.ts
  
  package.json  
  openclaw.extensions field
  
  Config Schema  
  TypeBox Validation
  
  Channel Plugin  
  extensions/msteams/
  
  Tool Plugin  
  extensions/lobster/
  
  Memory Plugin  
  extensions/memory-core/
  
  Provider Plugin  
  Custom Inference
  
  Channel Slot  
  Message Routing
  
  Tool Slot  
  Agent Capabilities
  
  Memory Slot  
  Search Backend
  
  Provider Slot  
  Model Inference
  
  **Description:** Plugins live in [extensions/](https://github.com/openclaw/openclaw/blob/bf6ec64f/extensions/)
   as workspace packages. The [plugin loader](https://github.com/openclaw/openclaw/blob/bf6ec64f/plugin%20loader)
   in [src/plugins/loader.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/plugins/loader.ts)
   discovers plugins by scanning `package.json` files for the `openclaw.extensions` field. Each plugin declares its type (channel, tool, memory, provider), config schema (TypeBox), and entry point. The loader validates schemas, loads plugins via jiti, and registers them into the appropriate slot (channel router, tool registry, memory search, or model providers). Bundled plugins are auto-enabled when configuration is present.
  
  **Sources:** [extensions/memory-core/package.json1-18](https://github.com/openclaw/openclaw/blob/bf6ec64f/extensions/memory-core/package.json#L1-L18)
   [extensions/msteams/1-50](https://github.com/openclaw/openclaw/blob/bf6ec64f/extensions/msteams/#L1-L50)
   [extensions/matrix/1-50](https://github.com/openclaw/openclaw/blob/bf6ec64f/extensions/matrix/#L1-L50)
   [src/plugins/loader.ts1-100](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/plugins/loader.ts#L1-L100)
  
  * * *
  
  Deployment Models
  -----------------
  
  OpenClaw supports four primary deployment patterns:
  
  | Model | Environment | Gateway Host | State Storage | Access Method |
  | --- | --- | --- | --- | --- |
  | **Local Dev** | Developer machine | `pnpm dev` | `~/.openclaw/` | Loopback (`127.0.0.1:18789`) |
  | **macOS Production** | macOS App | LaunchAgent | `~/.openclaw/` | Loopback + SSH/Tailscale |
  | **Linux/VM** | VPS/VM | systemd service | `~/.openclaw/` | Loopback + SSH tunnel |
  | **Cloud (Fly.io)** | Docker container | Fly.io machine | Persistent volume | HTTPS ingress |
  
  All deployments support the same client interfaces (CLI, Web UI, mobile apps) with token/password authentication for non-loopback bindings.
  
  **Sources:** [docs/platforms/fly.md1-100](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/platforms/fly.md#L1-L100)
   [docs/platforms/linux.md1-50](https://github.com/openclaw/openclaw/blob/bf6ec64f/docs/platforms/linux.md#L1-L50)
   [fly.toml1-77](https://github.com/openclaw/openclaw/blob/bf6ec64f/fly.toml#L1-L77)
   [README.md211-220](https://github.com/openclaw/openclaw/blob/bf6ec64f/README.md#L211-L220)
  
  * * *
  
  Key Technologies
  ----------------
  
  | Component | Technology | Location |
  | --- | --- | --- |
  | **Runtime** | Node.js ≥22 | Required |
  | **Agent Core** | `@mariozechner/pi-agent-core` | [package.json166](https://github.com/openclaw/openclaw/blob/bf6ec64f/package.json#L166-L166) |
  | **CLI Framework** | Commander.js | [src/cli/program.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/cli/program.ts) |
  | **WebSocket Server** | `ws` library | [src/gateway/server.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/gateway/server.ts) |
  | **Messaging** | Baileys, grammY, discord.js, Bolt | [src/](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/) |
  | **UI** | Lit (web components) | [ui/](https://github.com/openclaw/openclaw/blob/bf6ec64f/ui/) |
  | **Storage** | JSON5 files, SQLite (memory) | [src/config/](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/config/)<br> [src/memory/](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/memory/) |
  | **Sandboxing** | Docker | [src/agents/sandbox.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/sandbox.ts) |
  | **Schema Validation** | TypeBox, Zod | [src/config/schema.ts](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/config/schema.ts) |
  
  **Sources:** [package.json155-210](https://github.com/openclaw/openclaw/blob/bf6ec64f/package.json#L155-L210)
   [src/gateway/server.ts1-50](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/gateway/server.ts#L1-L50)
   [src/agents/piembeddedrunner.ts1-50](https://github.com/openclaw/openclaw/blob/bf6ec64f/src/agents/piembeddedrunner.ts#L1-L50)
  
  * * *
  
  Directory Structure
  -------------------
  
      openclaw/
      ├── src/                    # TypeScript source
      │   ├── agents/            # Agent runtime, tools, sandbox
      │   ├── gateway/           # Gateway server, protocol
      │   ├── config/            # Configuration, sessions
      │   ├── cli/               # CLI commands
      │   ├── commands/          # Command implementations
      │   ├── telegram/          # Telegram channel
      │   ├── discord/           # Discord channel
      │   ├── slack/             # Slack channel
      │   ├── signal/            # Signal channel
      │   ├── imessage/          # iMessage channel
      │   ├── memory/            # Memory search
      │   ├── web/               # Control UI backend
      │   └── ...
      ├── extensions/            # Plugin workspace packages
      │   ├── msteams/          # Microsoft Teams plugin
      │   ├── matrix/           # Matrix plugin
      │   ├── memory-core/      # Core memory plugin
      │   └── ...
      ├── apps/                  # Companion apps
      │   ├── macos/            # macOS menu bar app (Swift)
      │   ├── ios/              # iOS node app (Swift)
      │   └── android/          # Android node app (Kotlin)
      ├── ui/                    # Control UI frontend (Lit)
      ├── docs/                  # Documentation (Mintlify)
      ├── skills/                # Bundled skills
      ├── dist/                  # Build output
      ├── openclaw.mjs          # CLI entry point
      ├── package.json          # npm package manifest
      ├── tsconfig.json         # TypeScript config
      └── fly.toml              # Fly.io deployment config
      
  
  **Sources:** [package.json16-79](https://github.com/openclaw/openclaw/blob/bf6ec64f/package.json#L16-L79)
   [pnpm-workspace.yaml1-15](https://github.com/openclaw/openclaw/blob/bf6ec64f/pnpm-workspace.yaml#L1-L15)
   [README.md130-167](https://github.com/openclaw/openclaw/blob/bf6ec64f/README.md#L130-L167)
  
  This wiki is featured in the [repository](https://github.com/openclaw/openclaw/blob/main/README.md)
  
  Dismiss
  
  Refresh this wiki
  
  This wiki was recently refreshed. Please wait 4 days to refresh again.
  
  ### On this page
  
  *   [Overview](https://deepwiki.com/openclaw/openclaw#overview)
      
  *   [Purpose and Scope](https://deepwiki.com/openclaw/openclaw#purpose-and-scope)
      
  *   [What is OpenClaw](https://deepwiki.com/openclaw/openclaw#what-is-openclaw)
      
  *   [Core Architecture](https://deepwiki.com/openclaw/openclaw#core-architecture)
      
  *   [System Entry Points](https://deepwiki.com/openclaw/openclaw#system-entry-points)
      
  *   [Configuration and State](https://deepwiki.com/openclaw/openclaw#configuration-and-state)
      
  *   [Configuration File Location](https://deepwiki.com/openclaw/openclaw#configuration-file-location)
      
  *   [Agent Execution Model](https://deepwiki.com/openclaw/openclaw#agent-execution-model)
      
  *   [Message Routing and Channel Integration](https://deepwiki.com/openclaw/openclaw#message-routing-and-channel-integration)
      
  *   [Plugin Architecture](https://deepwiki.com/openclaw/openclaw#plugin-architecture)
      
  *   [Deployment Models](https://deepwiki.com/openclaw/openclaw#deployment-models)
      
  *   [Key Technologies](https://deepwiki.com/openclaw/openclaw#key-technologies)
      
  *   [Directory Structure](https://deepwiki.com/openclaw/openclaw#directory-structure)
      
  
  Ask Devin about openclaw/openclaw
  
  Fast
  --- End Content ---
