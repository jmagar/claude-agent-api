# Clarification Skills for Agent Orchestration

This document provides version references and guidance for Claude Code skills documentation.

## Skills Documentation Versions

**Current Recommended Version: 0.83**

Multiple versions exist to maintain backwards compatibility with different Claude Code CLI installations. Always prefer the latest version (0.83) unless working with a legacy system.

### Version 0.83 (Latest - Recommended)
[0.83] https://docs.openclaw.ai
  *   [Skills](https://docs.openclaw.ai/tools/skills)
  *   **Compatibility**: Latest features and API

### Version 0.82
[0.82] https://docs.openclaw.ai/cli
  *   [`skills`](https://docs.openclaw.ai/cli/skills)
  *   **Compatibility**: Compatible with 0.83, minor CLI improvements

### Version 0.80
[0.80] https://docs.openclaw.ai/start/wizard
  *   Skills: [Skills](https://docs.openclaw.ai/tools/skills)
  *   Skills config: [Skills config](https://docs.openclaw.ai/tools/skills-config)
  *   **Compatibility**: Major release, some breaking changes from 0.79

[0.80] https://docs.openclaw.ai/concepts/system-prompt
  *   [Skills](https://docs.openclaw.ai/concepts/system-prompt#skills)

### Version 0.79
[0.79] https://deepwiki.com/openclaw/openclaw
  *   [Skills System](https://deepwiki.com/openclaw/openclaw/6.3-skills-system)
  *   **Compatibility**: Legacy version, use only if required

## Retrieving Full Documentation

### Firecrawl Vector DB Retrieval

The Claude Code skills documentation is indexed in a vector database for semantic search and retrieval.

**When to use `firecrawl retrieve <url>`:**
- When you need complete document contents (not just page fragments)
- When following search results that only show snippets
- When documentation links return partial content

**Prerequisites:**
- `firecrawl` MCP tool must be installed and configured
- Firecrawl API credentials must be set in environment
- Vector DB must contain indexed documentation

**Usage:**
```bash
firecrawl retrieve <url>
```

**When NOT to use firecrawl:**
- Direct documentation links with full content visible
- API reference pages with complete schemas
- When you only need overview/summary information