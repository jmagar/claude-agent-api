#!/usr/bin/env python3
"""
Comprehensive API endpoint testing script.
Tests all endpoints systematically with progress tracking.
Endpoint count is determined dynamically from _define_all_endpoints().
"""

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias

# Type alias for JSON values (recursive)
JsonValue: TypeAlias = (
    str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
)


@dataclass
class EndpointTest:
    """Single endpoint test definition."""

    method: str
    path: str
    auth_type: str  # "native" or "openai"
    body: dict[str, JsonValue] | None = None
    requires: list[str] = field(default_factory=list)
    group: str = ""
    query_params: str = ""
    is_streaming: bool = False
    timeout_seconds: int = 30
    expected_statuses: list[int] = field(default_factory=lambda: [200, 201, 204])


@dataclass
class TestResult:
    """Result of a single endpoint test."""

    endpoint: EndpointTest
    status: str  # "success", "partial", "failed"
    status_code: int
    duration_ms: float
    response_body: str
    error_message: str = ""


class EndpointTester:
    """Main test orchestrator."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.resource_ids: dict[str, str] = {}
        self.results: list[TestResult] = []
        self.total_endpoints = 0
        self.tested = 0
        self.working = 0
        self.partial = 0
        self.failed = 0

    def test_endpoint(self, endpoint: EndpointTest) -> TestResult:
        """Test a single endpoint."""
        self.tested += 1
        print(
            f"\n[{self.tested}/{self.total_endpoints}] Testing {endpoint.method} {endpoint.path}"
        )

        # Resolve dependencies
        path = endpoint.path
        for dep in endpoint.requires:
            if dep not in self.resource_ids:
                print(f"  ⚠️  Missing dependency: {dep}")
                return TestResult(
                    endpoint=endpoint,
                    status="failed",
                    status_code=0,
                    duration_ms=0,
                    response_body="",
                    error_message=f"Missing dependency: {dep}",
                )
            path = path.replace(f"{{{dep}}}", self.resource_ids[dep])

        # Add query params
        if endpoint.query_params:
            path += f"?{endpoint.query_params}"

        # Build curl command
        url = f"{self.base_url}{path}"
        cmd = ["curl", "-s", "-w", "\\n%{http_code}", "-X", endpoint.method]

        # Auth header passed via stdin (--config -) to avoid exposing
        # API key in process arguments visible via `ps aux`
        if endpoint.auth_type == "native":
            auth_config = f'header = "X-API-Key: {self.api_key}"'
        else:  # openai
            auth_config = f'header = "Authorization: Bearer {self.api_key}"'
        cmd.extend(["--config", "-"])

        # Add body
        if endpoint.body:
            body = self._resolve_placeholders(endpoint.body)
            cmd.extend(["-H", "Content-Type: application/json"])
            cmd.extend(["-d", json.dumps(body)])

        # Add streaming flag
        if endpoint.is_streaming:
            cmd.append("-N")

        cmd.append(url)

        # Execute
        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=endpoint.timeout_seconds,
                check=False,
                input=auth_config,
            )
            duration_ms = (time.time() - start) * 1000

            # Parse response
            output = result.stdout
            # Split status code from body
            parts = output.rsplit("\n", 1)
            if len(parts) == 2:
                response_body, status_str = parts
                try:
                    status_code = int(status_str)
                except ValueError:
                    status_code = 0
                    response_body = output
            else:
                status_code = 0
                response_body = output

            # SSE fallback: when curl streams with -N, status code parsing
            # can fail (status_code == 0). Validate the output actually
            # contains SSE protocol markers before inferring success.
            if (
                endpoint.is_streaming
                and status_code == 0
                and self._is_valid_sse_output(output)
            ):
                status_code = 200

            # Determine status
            if status_code in endpoint.expected_statuses:
                status = "success"
                self.working += 1
                icon = "✅"
            elif 200 <= status_code < 300:
                status = "partial"
                self.partial += 1
                icon = "⚠️"
            else:
                status = "failed"
                self.failed += 1
                icon = "❌"

            print(f"  {icon} {status_code} ({duration_ms:.0f}ms)")

            # Extract resource IDs from response
            if response_body:
                try:
                    data = json.loads(response_body)
                    self._extract_resource_ids(data, endpoint.group)
                except json.JSONDecodeError:
                    if endpoint.is_streaming:
                        self._extract_resource_ids_from_sse(
                            response_body, endpoint.group
                        )

            return TestResult(
                endpoint=endpoint,
                status=status,
                status_code=status_code,
                duration_ms=duration_ms,
                response_body=response_body,
            )

        except subprocess.TimeoutExpired:
            self.failed += 1
            print("  ❌ Timeout")
            return TestResult(
                endpoint=endpoint,
                status="failed",
                status_code=0,
                duration_ms=float(endpoint.timeout_seconds * 1000),
                response_body="",
                error_message="Request timeout",
            )
        except Exception as e:
            self.failed += 1
            print(f"  ❌ Error: {e}")
            return TestResult(
                endpoint=endpoint,
                status="failed",
                status_code=0,
                duration_ms=0,
                response_body="",
                error_message=str(e),
            )

    def _extract_resource_ids(self, data: dict[str, JsonValue], group: str) -> None:
        """Extract resource IDs from response."""
        # Extract common ID fields
        id_mappings = {
            "projects": ("id", "project_id"),
            "agents": ("id", "agent_id"),
            "sessions": ("session_id", "session_id"),
            "skills": ("id", "skill_id"),
            "slash-commands": ("id", "command_id"),
            "mcp-servers": ("name", "server_name"),
            "memories": ("id", "memory_id"),
            "tool-presets": ("id", "preset_id"),
            "assistants": ("id", "assistant_id"),
            "threads": ("id", "thread_id"),
            "messages": ("id", "message_id"),
            "runs": ("id", "run_id"),
        }

        if group in id_mappings:
            field_name, storage_key = id_mappings[group]
            if field_name in data:
                self.resource_ids[storage_key] = str(data[field_name])
                print(f"  💾 Saved {storage_key}={data[field_name]}")

        # Extract share token
        if "token" in data and group == "mcp-servers":
            self.resource_ids["share_token"] = str(data["token"])
            print(f"  💾 Saved share_token={data['token']}")
        if "share_token" in data and group == "mcp-servers":
            self.resource_ids["share_token"] = str(data["share_token"])
            print(f"  💾 Saved share_token={data['share_token']}")

        # Extract checkpoint UUID
        checkpoints_raw = data.get("checkpoints")
        if (
            isinstance(checkpoints_raw, list)
            and checkpoints_raw
            and isinstance(checkpoints_raw[0], dict)
        ):
            uuid = checkpoints_raw[0].get("user_message_uuid")
            if isinstance(uuid, str):
                self.resource_ids["checkpoint_uuid"] = uuid
                print(f"  💾 Saved checkpoint_uuid={uuid}")

        # Extract memory ID from memory add/list responses
        if group == "memories":
            memory_lists: list[list[JsonValue]] = []
            memories_raw = data.get("memories")
            if isinstance(memories_raw, list):
                memory_lists.append(memories_raw)
            results_raw = data.get("results")
            if isinstance(results_raw, list):
                memory_lists.append(results_raw)

            for memories in memory_lists:
                if memories and isinstance(memories[0], dict):
                    memory_id = memories[0].get("id")
                    if isinstance(memory_id, str) and memory_id:
                        self.resource_ids["memory_id"] = memory_id
                        print(f"  💾 Saved memory_id={memory_id}")
                        break

    def _extract_resource_ids_from_sse(self, output: str, group: str) -> None:
        """Extract IDs from SSE response payloads."""
        if group == "sessions":
            match = re.search(r'"session_id"\s*:\s*"([^"]+)"', output)
            if match:
                session_id = match.group(1)
                self.resource_ids["session_id"] = session_id
                print(f"  💾 Saved session_id={session_id}")
        if group == "checkpoints":
            match = re.search(r'"user_message_uuid"\s*:\s*"([^"]+)"', output)
            if match:
                checkpoint_uuid = match.group(1)
                self.resource_ids["checkpoint_uuid"] = checkpoint_uuid
                print(f"  💾 Saved checkpoint_uuid={checkpoint_uuid}")

    @staticmethod
    def _is_valid_sse_output(output: str) -> bool:
        """Check whether output contains valid SSE protocol markers.

        SSE streams use a specific line-based protocol (RFC 8895). A valid
        stream must contain at least one recognized field prefix from the set:
        ``data:``, ``event:``, ``id:``, or ``retry:``.

        To reduce false positives (e.g. a JSON error response that happens to
        contain the substring "event:"), we require *at least two* distinct
        SSE field lines, which is the minimum for any real event (typically
        ``event:`` + ``data:``).
        """
        # SSE field prefixes per the spec (must appear at line start)
        sse_field_pattern = re.compile(r"^(?:data|event|id|retry):", re.MULTILINE)
        matches = sse_field_pattern.findall(output)
        return len(matches) >= 2

    def _resolve_placeholders(self, obj: JsonValue) -> JsonValue:
        """Recursively resolve {resource_id} placeholders in request bodies."""
        if isinstance(obj, str):
            resolved = obj
            for key, value in self.resource_ids.items():
                resolved = resolved.replace(f"{{{key}}}", value)
            return resolved
        if isinstance(obj, list):
            return [self._resolve_placeholders(item) for item in obj]
        if isinstance(obj, dict):
            return {k: self._resolve_placeholders(v) for k, v in obj.items()}
        return obj

    def generate_report(self, output_file: str) -> None:
        """Generate markdown report."""
        print(f"\n\n📝 Generating report: {output_file}")
        total = self.total_endpoints or 1

        with Path(output_file).open("w") as f:
            # Header
            f.write("# Complete API Endpoint Testing Results\n\n")
            f.write(f"**Test Run:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Base URL:** {self.base_url}\n")
            f.write(f"**Total Endpoints:** {self.total_endpoints}\n")
            f.write(f"**Tested:** {self.tested}/{self.total_endpoints} (100%)\n")
            f.write(
                f"**Working:** {self.working} ({self.working / total * 100:.1f}%)\n"
            )
            f.write(
                f"**Partially Working:** {self.partial} ({self.partial / total * 100:.1f}%)\n"
            )
            f.write(f"**Failed:** {self.failed} ({self.failed / total * 100:.1f}%)\n\n")

            # Progress tracker
            f.write("## Progress Tracker\n\n")
            for i, result in enumerate(self.results, 1):
                icon = {"success": "✅", "partial": "⚠️", "failed": "❌"}[result.status]
                f.write(
                    f"- [x] {i}/{self.total_endpoints} - {result.endpoint.method} {result.endpoint.path} - "
                    f"{icon} {result.status.title()} ({result.duration_ms:.0f}ms)\n"
                )

            # Detailed results
            f.write("\n## Detailed Results\n\n")
            for i, result in enumerate(self.results, 1):
                f.write(f"### {i}. {result.endpoint.method} {result.endpoint.path}\n\n")
                f.write(f"**Status:** {result.status.title()}\n")
                f.write(f"**Status Code:** {result.status_code}\n")
                f.write(f"**Duration:** {result.duration_ms:.0f}ms\n")
                f.write(f"**Group:** {result.endpoint.group}\n\n")

                if result.error_message:
                    f.write(f"**Error:** {result.error_message}\n\n")

                # Response preview
                if result.response_body:
                    f.write("**Response Preview:**\n```json\n")
                    preview = result.response_body[:500]
                    if len(result.response_body) > 500:
                        preview += "\n... (truncated)"
                    f.write(preview)
                    f.write("\n```\n\n")

        print(f"✅ Report saved to {output_file}")

    def run_all_tests(self) -> None:
        """Execute all endpoint tests."""
        endpoints = self._define_all_endpoints()
        self.total_endpoints = len(endpoints)

        print(f"🚀 Starting comprehensive test of {len(endpoints)} endpoints...")
        print(f"📍 Base URL: {self.base_url}")

        for endpoint in endpoints:
            result = self.test_endpoint(endpoint)
            self.results.append(result)

        print("\n" + "=" * 60)
        print("🎉 Testing Complete!")
        print(f"✅ Working: {self.working}")
        print(f"⚠️  Partial: {self.partial}")
        print(f"❌ Failed: {self.failed}")
        print("=" * 60)

    def _define_all_endpoints(self) -> list[EndpointTest]:
        """Define all endpoint test cases."""
        return [
            # Root & Health (2)
            EndpointTest("GET", "/", "native", group="root"),
            EndpointTest("GET", "/health", "native", group="health"),
            # Projects CRUD (5)
            EndpointTest(
                "POST",
                "/api/v1/projects",
                "native",
                {"name": "Test Project", "path": "/tmp/test-project"},
                group="projects",
            ),
            EndpointTest("GET", "/api/v1/projects", "native", group="projects"),
            EndpointTest(
                "GET",
                "/api/v1/projects/{project_id}",
                "native",
                requires=["project_id"],
                group="projects",
            ),
            EndpointTest(
                "PATCH",
                "/api/v1/projects/{project_id}",
                "native",
                {"name": "Updated Project"},
                requires=["project_id"],
                group="projects",
            ),
            EndpointTest(
                "DELETE",
                "/api/v1/projects/{project_id}",
                "native",
                requires=["project_id"],
                group="projects",
            ),
            # Agents CRUD (6)
            EndpointTest(
                "POST",
                "/api/v1/agents",
                "native",
                {
                    "name": "Test Agent",
                    "description": "Test agent",
                    "prompt": "You are a test agent",
                },
                group="agents",
            ),
            EndpointTest("GET", "/api/v1/agents", "native", group="agents"),
            EndpointTest(
                "GET",
                "/api/v1/agents/{agent_id}",
                "native",
                requires=["agent_id"],
                group="agents",
            ),
            EndpointTest(
                "PUT",
                "/api/v1/agents/{agent_id}",
                "native",
                {
                    "id": "agent-update",
                    "name": "Updated Agent",
                    "description": "Updated",
                    "prompt": "You are an updated test agent",
                },
                requires=["agent_id"],
                group="agents",
            ),
            EndpointTest(
                "POST",
                "/api/v1/agents/{agent_id}/share",
                "native",
                requires=["agent_id"],
                group="agents",
            ),
            EndpointTest(
                "DELETE",
                "/api/v1/agents/{agent_id}",
                "native",
                requires=["agent_id"],
                group="agents",
            ),
            # Query & Sessions (3)
            EndpointTest(
                "POST",
                "/api/v1/query/single",
                "native",
                {
                    "prompt": "Reply with exactly OK.",
                    "model": "haiku",
                    "max_turns": 1,
                    "permission_mode": "bypassPermissions",
                },
                group="sessions",
                timeout_seconds=180,
            ),
            EndpointTest(
                "POST",
                "/api/v1/query",
                "native",
                {"prompt": "Test streaming", "model": "haiku"},
                group="sessions",
                is_streaming=True,
                timeout_seconds=90,
            ),
            EndpointTest("GET", "/api/v1/sessions", "native", group="sessions"),
            # Session Detail & Control (8)
            EndpointTest(
                "GET",
                "/api/v1/sessions/{session_id}",
                "native",
                requires=["session_id"],
                group="sessions",
            ),
            EndpointTest(
                "POST",
                "/api/v1/sessions/{session_id}/promote",
                "native",
                {"project_id": "test-project"},
                requires=["session_id"],
                group="sessions",
            ),
            EndpointTest(
                "PATCH",
                "/api/v1/sessions/{session_id}/tags",
                "native",
                {"tags": ["test", "automated"]},
                requires=["session_id"],
                group="sessions",
            ),
            EndpointTest(
                "POST",
                "/api/v1/sessions/{session_id}/resume",
                "native",
                {"prompt": "Resume test"},
                requires=["session_id"],
                group="sessions",
                timeout_seconds=120,
            ),
            EndpointTest(
                "POST",
                "/api/v1/sessions/{session_id}/fork",
                "native",
                {"prompt": "Fork test"},
                requires=["session_id"],
                group="sessions",
            ),
            EndpointTest(
                "POST",
                "/api/v1/sessions/{session_id}/interrupt",
                "native",
                requires=["session_id"],
                group="sessions",
                expected_statuses=[200, 404],
            ),
            EndpointTest(
                "POST",
                "/api/v1/sessions/{session_id}/control",
                "native",
                {"type": "permission_mode_change", "permission_mode": "default"},
                requires=["session_id"],
                group="sessions",
                expected_statuses=[200, 404],
            ),
            EndpointTest(
                "POST",
                "/api/v1/sessions/{session_id}/answer",
                "native",
                {"answer": "Test answer"},
                requires=["session_id"],
                group="sessions",
                expected_statuses=[200, 404],
            ),
            # Checkpoints (2)
            EndpointTest(
                "GET",
                "/api/v1/sessions/{session_id}/checkpoints",
                "native",
                requires=["session_id"],
                group="checkpoints",
            ),
            EndpointTest(
                "POST",
                "/api/v1/sessions/{session_id}/rewind",
                "native",
                {"checkpoint_id": "test-checkpoint"},
                requires=["session_id"],
                group="checkpoints",
                expected_statuses=[200, 400],
            ),
            # Skills CRUD (6)
            EndpointTest("GET", "/api/v1/skills", "native", group="skills"),
            EndpointTest(
                "GET",
                "/api/v1/skills",
                "native",
                query_params="source=filesystem",
                group="skills",
            ),
            EndpointTest(
                "POST",
                "/api/v1/skills",
                "native",
                {
                    "name": "test-skill",
                    "description": "Test skill",
                    "content": "# test-skill\n\nTest instructions",
                    "enabled": True,
                },
                group="skills",
            ),
            EndpointTest(
                "GET",
                "/api/v1/skills/{skill_id}",
                "native",
                requires=["skill_id"],
                group="skills",
            ),
            EndpointTest(
                "PUT",
                "/api/v1/skills/{skill_id}",
                "native",
                {
                    "id": "skill-update",
                    "name": "updated-skill",
                    "description": "Updated",
                    "content": "# updated-skill\n\nUpdated instructions",
                    "enabled": True,
                },
                requires=["skill_id"],
                group="skills",
            ),
            EndpointTest(
                "DELETE",
                "/api/v1/skills/{skill_id}",
                "native",
                requires=["skill_id"],
                group="skills",
            ),
            # Slash Commands CRUD (5)
            EndpointTest(
                "GET", "/api/v1/slash-commands", "native", group="slash-commands"
            ),
            EndpointTest(
                "POST",
                "/api/v1/slash-commands",
                "native",
                {
                    "name": "test",
                    "description": "Test command",
                    "content": "echo 'test'",
                    "enabled": True,
                },
                group="slash-commands",
            ),
            EndpointTest(
                "GET",
                "/api/v1/slash-commands/{command_id}",
                "native",
                requires=["command_id"],
                group="slash-commands",
            ),
            EndpointTest(
                "PUT",
                "/api/v1/slash-commands/{command_id}",
                "native",
                {
                    "id": "command-update",
                    "name": "updated",
                    "description": "Updated",
                    "content": "echo 'updated'",
                    "enabled": True,
                },
                requires=["command_id"],
                group="slash-commands",
            ),
            EndpointTest(
                "DELETE",
                "/api/v1/slash-commands/{command_id}",
                "native",
                requires=["command_id"],
                group="slash-commands",
            ),
            # MCP Servers CRUD (10)
            EndpointTest("GET", "/api/v1/mcp-servers", "native", group="mcp-servers"),
            EndpointTest(
                "GET",
                "/api/v1/mcp-servers",
                "native",
                query_params="source=database",
                group="mcp-servers",
            ),
            EndpointTest(
                "POST",
                "/api/v1/mcp-servers",
                "native",
                {
                    "name": "test-server",
                    "type": "stdio",
                    "config": {
                        "command": "echo",
                        "args": ["hello"],
                        "resources": [
                            {
                                "uri": "resource://demo",
                                "name": "demo",
                                "description": "Demo resource",
                                "mimeType": "text/plain",
                                "text": "health",
                            }
                        ],
                    },
                },
                group="mcp-servers",
            ),
            EndpointTest(
                "GET",
                "/api/v1/mcp-servers/{server_name}",
                "native",
                requires=["server_name"],
                group="mcp-servers",
            ),
            EndpointTest(
                "PUT",
                "/api/v1/mcp-servers/{server_name}",
                "native",
                {"type": "stdio", "config": {"enabled": False}},
                requires=["server_name"],
                group="mcp-servers",
            ),
            EndpointTest(
                "GET",
                "/api/v1/mcp-servers/{server_name}/resources",
                "native",
                requires=["server_name"],
                group="mcp-servers",
            ),
            EndpointTest(
                "GET",
                "/api/v1/mcp-servers/{server_name}/resources/resource://demo",
                "native",
                requires=["server_name"],
                group="mcp-servers",
            ),
            EndpointTest(
                "POST",
                "/api/v1/mcp-servers/{server_name}/share",
                "native",
                {"config": {"type": "stdio", "command": "echo", "args": ["hello"]}},
                requires=["server_name"],
                group="mcp-servers",
            ),
            EndpointTest(
                "GET",
                "/api/v1/mcp-servers/share/{share_token}",
                "native",
                requires=["share_token"],
                group="mcp-servers",
            ),
            EndpointTest(
                "DELETE",
                "/api/v1/mcp-servers/{server_name}",
                "native",
                requires=["server_name"],
                group="mcp-servers",
            ),
            # Memories CRUD (5)
            EndpointTest(
                "POST",
                "/api/v1/memories",
                "native",
                {"messages": "Test memory content", "enable_graph": False},
                group="memories",
                timeout_seconds=90,
            ),
            EndpointTest(
                "POST",
                "/api/v1/memories/search",
                "native",
                {"query": "test"},
                group="memories",
            ),
            EndpointTest("GET", "/api/v1/memories", "native", group="memories"),
            EndpointTest(
                "DELETE",
                "/api/v1/memories/{memory_id}",
                "native",
                requires=["memory_id"],
                group="memories",
            ),
            EndpointTest("DELETE", "/api/v1/memories", "native", group="memories"),
            # Tool Presets CRUD (5)
            EndpointTest("GET", "/api/v1/tool-presets", "native", group="tool-presets"),
            EndpointTest(
                "POST",
                "/api/v1/tool-presets",
                "native",
                {"name": "test-preset", "tools": ["mcp__swag__swag"]},
                group="tool-presets",
            ),
            EndpointTest(
                "GET",
                "/api/v1/tool-presets/{preset_id}",
                "native",
                requires=["preset_id"],
                group="tool-presets",
            ),
            EndpointTest(
                "PUT",
                "/api/v1/tool-presets/{preset_id}",
                "native",
                {"name": "updated-preset", "tools": ["mcp__swag__swag"]},
                requires=["preset_id"],
                group="tool-presets",
            ),
            EndpointTest(
                "DELETE",
                "/api/v1/tool-presets/{preset_id}",
                "native",
                requires=["preset_id"],
                group="tool-presets",
            ),
            # OpenAI Chat (1)
            EndpointTest(
                "POST",
                "/v1/chat/completions",
                "openai",
                {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Test"}],
                },
                group="openai-chat",
                timeout_seconds=90,
            ),
            # OpenAI Models (2)
            EndpointTest("GET", "/v1/models", "openai", group="openai-models"),
            EndpointTest("GET", "/v1/models/gpt-4", "openai", group="openai-models"),
            # OpenAI Assistants CRUD (5)
            EndpointTest(
                "POST",
                "/v1/assistants",
                "openai",
                {"model": "gpt-4", "name": "Test Assistant"},
                group="assistants",
            ),
            EndpointTest("GET", "/v1/assistants", "openai", group="assistants"),
            EndpointTest(
                "GET",
                "/v1/assistants/{assistant_id}",
                "openai",
                requires=["assistant_id"],
                group="assistants",
            ),
            EndpointTest(
                "POST",
                "/v1/assistants/{assistant_id}",
                "openai",
                {"name": "Updated Assistant"},
                requires=["assistant_id"],
                group="assistants",
            ),
            EndpointTest(
                "DELETE",
                "/v1/assistants/{assistant_id}",
                "openai",
                requires=["assistant_id"],
                group="assistants",
            ),
            # OpenAI Threads CRUD (4)
            EndpointTest("POST", "/v1/threads", "openai", {}, group="threads"),
            EndpointTest(
                "GET",
                "/v1/threads/{thread_id}",
                "openai",
                requires=["thread_id"],
                group="threads",
            ),
            EndpointTest(
                "POST",
                "/v1/threads/{thread_id}",
                "openai",
                {"metadata": {"test": "updated"}},
                requires=["thread_id"],
                group="threads",
            ),
            EndpointTest(
                "DELETE",
                "/v1/threads/{thread_id}",
                "openai",
                requires=["thread_id"],
                group="threads",
            ),
            # OpenAI Messages CRUD (4)
            EndpointTest(
                "POST",
                "/v1/threads/{thread_id}/messages",
                "openai",
                {"role": "user", "content": "Test message"},
                requires=["thread_id"],
                group="messages",
            ),
            EndpointTest(
                "GET",
                "/v1/threads/{thread_id}/messages",
                "openai",
                requires=["thread_id"],
                group="messages",
            ),
            EndpointTest(
                "GET",
                "/v1/threads/{thread_id}/messages/{message_id}",
                "openai",
                requires=["thread_id", "message_id"],
                group="messages",
            ),
            EndpointTest(
                "POST",
                "/v1/threads/{thread_id}/messages/{message_id}",
                "openai",
                {"metadata": {"test": "updated"}},
                requires=["thread_id", "message_id"],
                group="messages",
            ),
            # OpenAI Runs CRUD (4)
            EndpointTest(
                "POST",
                "/v1/threads/{thread_id}/runs",
                "openai",
                {"assistant_id": "{assistant_id}"},
                requires=["thread_id", "assistant_id"],
                group="runs",
            ),
            EndpointTest(
                "GET",
                "/v1/threads/{thread_id}/runs",
                "openai",
                requires=["thread_id"],
                group="runs",
            ),
            EndpointTest(
                "GET",
                "/v1/threads/{thread_id}/runs/{run_id}",
                "openai",
                requires=["thread_id", "run_id"],
                group="runs",
            ),
            EndpointTest(
                "POST",
                "/v1/threads/{thread_id}/runs/{run_id}/cancel",
                "openai",
                requires=["thread_id", "run_id"],
                group="runs",
            ),
        ]


def main():
    """Main entry point."""
    base_url = os.getenv("API_BASE_URL", "http://100.120.242.29:54000")
    api_key = os.getenv("API_KEY", "")
    if not api_key:
        print("❌ Error: API_KEY environment variable not set")
        sys.exit(1)

    output_file = "/tmp/complete_endpoint_testing.md"

    tester = EndpointTester(base_url, api_key)
    tester.run_all_tests()
    tester.generate_report(output_file)

    print(f"\n📄 Full report: {output_file}")
    sys.exit(0 if tester.failed == 0 else 1)


if __name__ == "__main__":
    main()
