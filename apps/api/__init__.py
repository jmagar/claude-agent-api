"""Claude Agent API - HTTP API wrapper for Claude Agent Python SDK."""

try:
    from importlib.metadata import version
    __version__ = version("claude-agent-api")
except Exception:
    __version__ = "1.0.0"  # fallback for development
