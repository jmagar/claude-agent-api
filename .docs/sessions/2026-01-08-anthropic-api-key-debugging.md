# Session: ANTHROPIC_API_KEY Environment Variable Debugging

**Date**: 2026-01-08
**Duration**: ~45 minutes
**Status**: Resolved - Container restart required

## Session Overview

Debugged persistent `ANTHROPIC_API_KEY=claude-max-session` environment variable causing "Invalid API key · Fix external API key" errors in the Claude Agent API service. Root cause was shell environment variable inheritance from a previous session, despite the .env file having the variable properly commented out.

## Timeline

### 1. Initial Investigation (14:50)
- User asked how to view environment variables
- Provided commands: `env`, `printenv`, `env | grep CLAUDE`
- User discovered `ANTHROPIC_API_KEY=claude-max-session` was still set

### 2. File-Based Search (14:52)
- Searched for "claude-max-session" in codebase - not found in active files
- Searched for ANTHROPIC_API_KEY references:
  - `.docs/api-test-results.md`
  - `.docs/sessions/2026-01-08-code-review-fixes.md`
  - `comments-grouped.json`
  - `CLAUDE.md:44`
  - `tests/integration/test_query.py`
  - `tests/unit/test_config.py`
  - `specs/001-claude-agent-api/quickstart.md`
- Found Claude file history showing the variable was previously set but commented out

### 3. Root Cause Analysis (14:55)
- Launched `root-cause-analyzer` agent (ID: a037e23)
- **Key Finding**: Variable was set in running uvicorn parent process environment
  - Process PID 3023174 (uv run)
  - Process PID 3023177 (uvicorn)
  - Process PID 3023170 (parent uv run) - **contained the stale variable**
- Confirmed `.env:3` has variable properly commented out
- Variable was inherited when `make dev-restart` was executed in a shell that still had it exported

### 4. Process Cleanup (15:00)
- Verified uvicorn processes were killed
- Confirmed port 54000 was no longer in use
- Old PIDs (3023170, 3023174, 3023177) were terminated

### 5. Persistent Issue Investigation (15:03)
- User reported variable still showing with `env | grep ANTHROPIC`
- Investigated all possible sources:
  - ❌ Not in `~/.zshrc`, `~/.zshenv`, `~/.zprofile`, `~/.zlogin`
  - ❌ Not in `/etc/profile`, `/etc/environment`
  - ❌ Not in systemd user environment
  - ❌ Not in direnv configuration
  - ❌ Not in Claude hooks
  - ❌ Not in docker-compose.yaml
  - ❌ Not in Makefile
- Tested fresh processes:
  - `uv run python -c` → Variable **NOT SET** ✅
  - `zsh -c 'echo $ANTHROPIC_API_KEY'` → Variable **empty** ✅
  - User's active shell → Variable **SET** ❌

### 6. Resolution (15:10)
- **Root Cause Confirmed**: The variable persists in the user's active shell session
- Variable was exported at some point (likely when .env had it uncommented)
- Shell environment variables persist until explicitly unset or terminal is closed
- **Solution**: Container restart to get completely clean environment

## Key Findings

### Environment Variable Inheritance Issue

**Location**: Shell process environment
**Issue**: `ANTHROPIC_API_KEY=claude-max-session` was exported in user's shell session and inherited by all child processes

**Evidence**:
- `/proc/3023170/environ` - Parent uv process contained `ANTHROPIC_API_KEY=claude-max-session`
- `.env:3` - Variable properly commented out in config file
- Fresh shell processes did not have the variable set
- User's active shell had the variable exported

**Impact**: Claude Agent SDK detected the invalid API key and failed with "Invalid API key · Fix external API key"

### SDK Authentication Behavior

**File**: `apps/api/services/agent/service.py:235`
**File**: `apps/api/services/agent/options.py:98-118`

The Claude Agent SDK reads `ANTHROPIC_API_KEY` directly from the process environment. When set to an invalid value like "claude-max-session":
- SDK attempts to authenticate with the invalid key
- Fails instead of falling back to Claude Max OAuth authentication
- Expected behavior: If `ANTHROPIC_API_KEY` is unset, SDK uses Claude Max authentication

**Reference**: CLAUDE.md:44 states: "Do not set environment variable `ANTHROPIC_API_KEY`, we are logged in with our Claude Max subscription"

## Technical Decisions

### Why Container Restart?

1. **Shell Persistence**: Environment variables in active shell sessions persist indefinitely
2. **Multiple Terminals**: User may have multiple terminal tabs/windows with stale exports
3. **Clean Slate**: Container restart guarantees no stale environment variables anywhere
4. **Time Efficient**: Faster than hunting down every open shell and unsetting manually

### Alternative Solutions Considered

1. **Manual unset in each shell**: `unset ANTHROPIC_API_KEY` - requires finding all open terminals
2. **Close all terminals**: Effective but loses session state
3. **Kill and restart service**: Only fixes the service process, not the user's shells

## Files Referenced

- `.env:1-3` - Environment configuration (ANTHROPIC_API_KEY commented out)
- `CLAUDE.md:44` - Documentation about not setting ANTHROPIC_API_KEY
- `apps/api/services/agent/service.py:235` - SDK client initialization
- `apps/api/services/agent/options.py:98-118` - SDK options building
- `Makefile:23-29` - Development server commands
- `docker-compose.yaml` - Container configuration

## Commands Executed

```bash
# Check environment variables
env | grep ANTHROPIC
# Result: ANTHROPIC_API_KEY=claude-max-session (in user's shell)

# Check running processes
pgrep -af uvicorn
# Result: No processes (successfully killed)

# Check port availability
ss -tuln | grep 54000
# Result: Port not in use

# Test fresh process
uv run python -c "import os; print('ANTHROPIC_API_KEY:', os.environ.get('ANTHROPIC_API_KEY', 'NOT SET'))"
# Result: NOT SET (proves .env is correctly commented)

# Check process environment
cat /proc/3023170/environ | tr '\0' '\n' | grep ANTHROPIC
# Result: ANTHROPIC_API_KEY=claude-max-session (stale in running process)
```

## Root Cause Summary

**Problem**: Claude Agent API returns "Invalid API key · Fix external API key"
**Root Cause**: `ANTHROPIC_API_KEY=claude-max-session` was exported in shell environment from a previous session
**Why It Persisted**: Shell environment variables remain set until explicitly unset or terminal is closed
**Why It Mattered**: Claude Agent SDK reads this variable and tries to use it instead of Claude Max OAuth
**Resolution**: Container restart to clear all environment variables

## Next Steps

1. ✅ Container restart (user action)
2. ⏳ Verify `env | grep ANTHROPIC` returns nothing after restart
3. ⏳ Test API endpoint: `curl -X POST http://localhost:54000/api/v1/query`
4. ⏳ Confirm SDK uses Claude Max authentication successfully

## Lessons Learned

### Shell Environment Persistence
- Exported variables persist in shell sessions indefinitely
- Commenting out .env values doesn't affect already-running processes
- Process restarts inherit parent shell environment
- Fresh shells (new terminal windows) read config files anew

### Debugging Environment Issues
1. Check .env files and config files first
2. Check running process environment (`/proc/PID/environ`)
3. Check parent process environment (variables inherit down the tree)
4. Distinguish between config files vs. active runtime environment
5. Test with fresh processes to isolate the issue

### Claude Agent SDK Authentication
- SDK prioritizes `ANTHROPIC_API_KEY` environment variable over Claude Max OAuth
- Invalid API key values (like "claude-max-session") cause hard failures
- No automatic fallback to OAuth when API key is present but invalid
- Best practice: Leave `ANTHROPIC_API_KEY` completely unset for Claude Max users

## Related Issues

- GitHub Issue #11587: Auth conflict when both token and API key are set
- GitHub Issue #11171: "Invalid API key · Fix external API key" error
- GitHub Issue #9694: API key validation failures

## Agent Usage

- **root-cause-analyzer** (ID: a037e23): Successfully identified the stale environment variable in parent process
  - Investigated process inheritance chain
  - Tested fresh processes vs. existing processes
  - Provided comprehensive root cause analysis with supporting evidence
