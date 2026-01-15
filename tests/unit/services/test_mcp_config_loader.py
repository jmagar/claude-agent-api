"""Unit tests for McpConfigLoader (TDD: RED-GREEN-REFACTOR).

Tests for application config loading, env var resolution, and merge logic.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from apps.api.services.mcp_config_loader import McpConfigLoader


# RED PHASE: Tests for load_application_config()
class TestLoadApplicationConfig:
    """Tests for load_application_config() method."""

    def test_load_application_config_success(self, tmp_path: Path) -> None:
        """Test loading valid .mcp-server-config.json file."""
        # Arrange: Create valid config file
        config_file = tmp_path / ".mcp-server-config.json"
        config_data = {
            "mcpServers": {
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
                }
            }
        }
        config_file.write_text(json.dumps(config_data))

        loader = McpConfigLoader(project_path=tmp_path)

        # Act: Load config
        result = loader.load_application_config()

        # Assert: Should return mcpServers section
        assert result == config_data["mcpServers"]
        assert "github" in result
        assert result["github"]["command"] == "npx"

    def test_load_application_config_missing_file(self, tmp_path: Path) -> None:
        """Test behavior when .mcp-server-config.json is missing."""
        # Arrange: No config file exists
        loader = McpConfigLoader(project_path=tmp_path)

        # Act: Load config
        result = loader.load_application_config()

        # Assert: Should return empty dict
        assert result == {}

    def test_load_application_config_malformed_json(self, tmp_path: Path) -> None:
        """Test behavior when .mcp-server-config.json contains invalid JSON."""
        # Arrange: Create malformed config file
        config_file = tmp_path / ".mcp-server-config.json"
        config_file.write_text("{ invalid json }")

        loader = McpConfigLoader(project_path=tmp_path)

        # Act: Load config (should not raise exception)
        result = loader.load_application_config()

        # Assert: Should return empty dict and log warning
        assert result == {}

    def test_load_application_config_caching(self, tmp_path: Path) -> None:
        """Test that config is cached and file is read only once."""
        # Arrange: Create config file
        config_file = tmp_path / ".mcp-server-config.json"
        config_data = {"mcpServers": {"test": {"command": "echo"}}}
        config_file.write_text(json.dumps(config_data))

        loader = McpConfigLoader(project_path=tmp_path)

        # Act: Load config twice
        result1 = loader.load_application_config()

        # Modify file after first load
        config_file.write_text(json.dumps({"mcpServers": {"modified": {"command": "ls"}}}))

        result2 = loader.load_application_config()

        # Assert: Should return cached result (original, not modified)
        # NOTE: This test will FAIL because caching is not implemented yet
        assert result1 == result2
        assert "test" in result2
        assert "modified" not in result2
