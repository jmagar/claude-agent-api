"""Request schemas package.

This package contains Pydantic request schemas organized by domain:

- config.py: Configuration schemas (MCP, hooks, agents, output format, etc.)
- control.py: Control request schemas (permission mode changes, rewind)
- query.py: Query request schema
- sessions.py: Session lifecycle schemas (resume, fork, answer)

Import directly from submodules:
    from apps.api.schemas.requests.query import QueryRequest
    from apps.api.schemas.requests.config import HooksConfigSchema
"""
