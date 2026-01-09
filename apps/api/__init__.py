"""Claude Agent API - HTTP API wrapper for Claude Agent Python SDK."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("claude-agent-api")
except PackageNotFoundError:
    __version__ = "1.0.0"  # fallback for development
