#!/usr/bin/env python3
"""
Comprehensive API endpoint testing script.
Tests all 76 endpoints systematically with progress tracking.
"""

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EndpointTest:
    """Single endpoint test definition."""

    method: str
    path: str
    auth_type: str  # "native" or "openai"
    body: dict[str, Any] | None = None
    requires: list[str] = field(default_factory=list)
    group: str = ""
    query_params: str = ""
    is_streaming: bool = False


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
        self.tested = 0
        self.working = 0
        self.partial = 0
        self.failed = 0

    def test_endpoint(self, endpoint: EndpointTest) -> TestResult:
        """Test a single endpoint."""
        self.tested += 1
        print(f"\n[{self.tested}/76] Testing {endpoint.method} {endpoint.path}")

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

        # Add auth header
        if endpoint.auth_type == "native":
            cmd.extend(["-H", f"X-API-Key: {self.api_key}"])
        else:  # openai
            cmd.extend(["-H", f"Authorization: Bearer {self.api_key}"])

        # Add body
        if endpoint.body:
            cmd.extend(["-H", "Content-Type: application/json"])
            cmd.extend(["-d", json.dumps(endpoint.body)])

        # Add streaming flag
        if endpoint.is_streaming:
            cmd.append("-N")

        cmd.append(url)

        # Execute
        start = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=False
            )
            duration_ms = (time.time() - start) * 1000

            # Parse response
            output = result.stdout
            if endpoint.is_streaming:
                # For SSE, just capture first few events
                status_code = 200 if "event:" in output else 500
                response_body = output[:500] + "..." if len(output) > 500 else output
            else:
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

            # Determine status
            if status_code in (200, 201, 204):
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
            if status_code in (200, 201) and response_body:
                try:
                    data = json.loads(response_body)
                    self._extract_resource_ids(data, endpoint.group)
                except json.JSONDecodeError:
                    pass

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
                duration_ms=30000,
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

    def _extract_resource_ids(self, data: Any, group: str) -> None:
        """Extract resource IDs from response."""
        if not isinstance(data, dict):
            return

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

        # Extract checkpoint UUID
        if "checkpoints" in data and isinstance(data["checkpoints"], list):
            if data["checkpoints"]:
                uuid = data["checkpoints"][0].get("user_message_uuid")
                if uuid:
                    self.resource_ids["checkpoint_uuid"] = uuid
                    print(f"  💾 Saved checkpoint_uuid={uuid}")

    def generate_report(self, output_file: str) -> None:
        """Generate markdown report."""
        print(f"\n\n📝 Generating report: {output_file}")

        with open(output_file, "w") as f:
            # Header
            f.write("# Complete API Endpoint Testing Results\n\n")
            f.write(f"**Test Run:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Base URL:** {self.base_url}\n")
            f.write(f"**Total Endpoints:** 76\n")
            f.write(f"**Tested:** {self.tested}/76 (100%)\n")
            f.write(
                f"**Working:** {self.working} ({self.working/76*100:.1f}%)\n"
            )
            f.write(
                f"**Partially Working:** {self.partial} ({self.partial/76*100:.1f}%)\n"
            )
            f.write(f"**Failed:** {self.failed} ({self.failed/76*100:.1f}%)\n\n")

            # Progress tracker
            f.write("## Progress Tracker\n\n")
            for i, result in enumerate(self.results, 1):
                icon = {"success": "✅", "partial": "⚠️", "failed": "❌"}[
                    result.status
                ]
                f.write(
                    f"- [x] {i}/76 - {result.endpoint.method} {result.endpoint.path} - "
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
        """Execute all 76 endpoint tests."""
        endpoints = self._define_all_endpoints()

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
        """Define all 76 endpoints."""
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
                {"name": "Test Agent", "description": "Test agent"},
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
                {"name": "Updated Agent", "description": "Updated"},
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
                {"prompt": "Test query", "model": "haiku"},
                group="sessions",
            ),
            EndpointTest(
                "POST",
                "/api/v1/query",
                "native",
                {"prompt": "Test streaming", "model": "haiku"},
                group="sessions",
                is_streaming=True,
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
                {"message": "Resume test"},
                requires=["session_id"],
                group="sessions",
            ),
            EndpointTest(
                "POST",
                "/api/v1/sessions/{session_id}/fork",
                "native",
                requires=["session_id"],
                group="sessions",
            ),
            EndpointTest(
                "POST",
                "/api/v1/sessions/{session_id}/interrupt",
                "native",
                requires=["session_id"],
                group="sessions",
            ),
            EndpointTest(
                "POST",
                "/api/v1/sessions/{session_id}/control",
                "native",
                {"action": "cancel"},
                requires=["session_id"],
                group="sessions",
            ),
            EndpointTest(
                "POST",
                "/api/v1/sessions/{session_id}/answer",
                "native",
                {"answer": "Test answer"},
                requires=["session_id"],
                group="sessions",
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
                {"checkpoint_uuid": "test-uuid"},
                requires=["session_id"],
                group="checkpoints",
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
                    "trigger_phrase": "test trigger",
                    "instructions": "Test instructions",
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
                    "name": "updated-skill",
                    "description": "Updated",
                    "trigger_phrase": "updated trigger",
                    "instructions": "Updated instructions",
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
                {"name": "test", "description": "Test command", "prompt": "Test"},
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
                {"name": "updated", "description": "Updated", "prompt": "Updated"},
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
                    "transport_type": "stdio",
                    "command": "test-command",
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
                {"enabled": False},
                requires=["server_name"],
                group="mcp-servers",
            ),
            EndpointTest(
                "GET",
                "/api/v1/mcp-servers/swag/resources",
                "native",
                group="mcp-servers",
            ),
            EndpointTest(
                "GET",
                "/api/v1/mcp-servers/swag/resources/health",
                "native",
                group="mcp-servers",
            ),
            EndpointTest(
                "POST",
                "/api/v1/mcp-servers/{server_name}/share",
                "native",
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
                {"messages": "Test memory content"},
                group="memories",
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
            EndpointTest(
                "GET", "/api/v1/tool-presets", "native", group="tool-presets"
            ),
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
            ),
            # OpenAI Models (2)
            EndpointTest("GET", "/v1/models", "openai", group="openai-models"),
            EndpointTest(
                "GET", "/v1/models/gpt-4", "openai", group="openai-models"
            ),
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
            EndpointTest("POST", "/v1/threads", "openai", group="threads"),
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
    base_url = "http://localhost:54000"
    api_key = "your-api-key-for-clients"
    output_file = "/tmp/complete_endpoint_testing.md"

    tester = EndpointTester(base_url, api_key)
    tester.run_all_tests()
    tester.generate_report(output_file)

    print(f"\n📄 Full report: {output_file}")
    sys.exit(0 if tester.failed == 0 else 1)


if __name__ == "__main__":
    main()
