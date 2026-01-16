"""Redis key generation for MCP server configurations.

Centralized key builder with validation for API-key scoped MCP server storage.
"""


class McpRedisKeyBuilder:
    """Builds Redis keys for MCP server configurations with API-key scoping."""

    @staticmethod
    def validate_api_key(api_key: str) -> None:
        """Validate API key format for Redis key generation.

        Args:
            api_key: API key to validate

        Raises:
            ValueError: If API key is empty or contains invalid characters
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")

        # Prevent Redis key injection via special characters
        invalid_chars = [" ", "\n", "\r", "\t", ":", "*", "?", "[", "]"]
        for char in invalid_chars:
            if char in api_key:
                raise ValueError(
                    f"API key contains invalid character '{char}' "
                    f"(not allowed in Redis keys)"
                )

    @staticmethod
    def server_key(api_key: str, name: str) -> str:
        """Build cache key for an MCP server scoped to API key.

        Args:
            api_key: API key for tenant isolation
            name: Server name

        Returns:
            Redis key in format: mcp_server:{api_key}:{name}

        Raises:
            ValueError: If API key format is invalid

        Example:
            >>> McpRedisKeyBuilder.server_key("tenant-1", "my-server")
            'mcp_server:tenant-1:my-server'
        """
        McpRedisKeyBuilder.validate_api_key(api_key)
        return f"mcp_server:{api_key}:{name}"

    @staticmethod
    def index_key(api_key: str) -> str:
        """Build cache key for API key's server index.

        Args:
            api_key: API key for tenant isolation

        Returns:
            Redis key in format: mcp_servers:index:{api_key}

        Raises:
            ValueError: If API key format is invalid

        Example:
            >>> McpRedisKeyBuilder.index_key("tenant-1")
            'mcp_servers:index:tenant-1'
        """
        McpRedisKeyBuilder.validate_api_key(api_key)
        return f"mcp_servers:index:{api_key}"
