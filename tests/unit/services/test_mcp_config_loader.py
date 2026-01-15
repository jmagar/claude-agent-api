"""Unit tests for McpConfigLoader (TDD: RED-GREEN-REFACTOR).

Tests for application config loading, env var resolution, and merge logic.
"""

import json
import os
from pathlib import Path
from typing import cast
from unittest.mock import patch

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
        github_config = cast("dict[str, object]", result["github"])
        assert github_config["command"] == "npx"

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


# RED PHASE: Tests for resolve_env_vars()
class TestResolveEnvVars:
    """Tests for resolve_env_vars() method."""

    def test_resolve_env_vars_success(self) -> None:
        """Test successful resolution of environment variable placeholders."""
        # Arrange: Mock environment variable
        with patch.dict(os.environ, {"TEST_TOKEN": "secret123"}):
            config = {
                "github": {
                    "command": "npx",
                    "env": {"GITHUB_TOKEN": "${TEST_TOKEN}"},
                }
            }
            loader = McpConfigLoader()

            # Act: Resolve env vars
            result = loader.resolve_env_vars(config)

            # Assert: Should replace ${TEST_TOKEN} with "secret123"
            github_config = cast("dict[str, object]", result["github"])
            env_vars = cast("dict[str, object]", github_config["env"])
            assert env_vars["GITHUB_TOKEN"] == "secret123"

    def test_resolve_env_vars_missing_var(self) -> None:
        """Test behavior when environment variable is not found."""
        # Arrange: Config with undefined env var
        with patch.dict(os.environ, {}, clear=True):
            config = {
                "server": {
                    "env": {"MISSING_VAR": "${UNDEFINED_VAR}"},
                }
            }
            loader = McpConfigLoader()

            # Act: Resolve env vars (should not raise exception)
            result = loader.resolve_env_vars(config)

            # Assert: Should leave placeholder unchanged and log warning
            server_config = cast("dict[str, object]", result["server"])
            env_vars = cast("dict[str, object]", server_config["env"])
            assert env_vars["MISSING_VAR"] == "${UNDEFINED_VAR}"

    def test_resolve_env_vars_nested_objects(self) -> None:
        """Test deep resolution in nested dicts."""
        # Arrange: Deeply nested config with env vars
        with patch.dict(os.environ, {"DB_USER": "admin", "DB_PASS": "secret"}):
            config = {
                "database": {
                    "connection": {
                        "credentials": {
                            "username": "${DB_USER}",
                            "password": "${DB_PASS}",
                        },
                        "options": {
                            "ssl": True,
                        },
                    }
                }
            }
            loader = McpConfigLoader()

            # Act: Resolve env vars recursively
            result = loader.resolve_env_vars(config)

            # Assert: Should resolve vars at all nesting levels
            db_config = cast("dict[str, object]", result["database"])
            connection = cast("dict[str, object]", db_config["connection"])
            credentials = cast("dict[str, object]", connection["credentials"])
            assert credentials["username"] == "admin"
            assert credentials["password"] == "secret"

    def test_resolve_env_vars_in_arrays(self) -> None:
        """Test resolution in list items."""
        # Arrange: Config with env vars in list
        with patch.dict(os.environ, {"ARG1": "value1", "ARG2": "value2"}):
            config = {
                "server": {
                    "args": ["--user", "${ARG1}", "--pass", "${ARG2}"],
                }
            }
            loader = McpConfigLoader()

            # Act: Resolve env vars in array
            result = loader.resolve_env_vars(config)

            # Assert: Should resolve vars in list items
            server_config = cast("dict[str, object]", result["server"])
            args = cast("list[str]", server_config["args"])
            assert args[1] == "value1"
            assert args[3] == "value2"
