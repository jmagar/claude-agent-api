# Dependency Injection Migration Guide

This guide helps migrate route handlers from direct service instantiation to FastAPI dependency injection.

## Overview

**Before DI:** Routes manually created service instances, leading to:
- Tight coupling between routes and service implementations
- Difficult testing (couldn't easily mock services)
- Code duplication (service creation logic repeated)
- No centralized service lifecycle management

**After DI:** Routes declare service dependencies, FastAPI provides them:
- Loose coupling (routes depend on abstractions, not implementations)
- Easy testing (override providers with mocks)
- Clean code (no instantiation boilerplate)
- Centralized service management in `dependencies.py`

## Migration Checklist

- [ ] Remove all service instantiation from route handlers
- [ ] Add service parameters with type annotations
- [ ] Import dependency types from `apps.api.dependencies`
- [ ] Remove unused imports (service classes, cache)
- [ ] Update tests to use `app.dependency_overrides`
- [ ] Verify type checking passes (`uv run ty check`)
- [ ] Verify tests pass (`uv run pytest`)

## Before/After Examples

### Single Service Dependency

**Before:**
```python
from fastapi import APIRouter, Depends
from apps.api.adapters.cache import RedisCache
from apps.api.dependencies import get_api_key, get_cache
from apps.api.services.projects import ProjectService

router = APIRouter()

@router.get("/projects")
async def list_projects(
    api_key: str = Depends(get_api_key),
    cache: RedisCache = Depends(get_cache),
):
    """List all projects."""
    project_svc = ProjectService(cache)  # Manual instantiation
    projects = await project_svc.list_projects(api_key)
    return [{"id": p.id, "name": p.name} for p in projects]
```

**After:**
```python
from fastapi import APIRouter
from apps.api.dependencies import ApiKey, ProjectSvc

router = APIRouter()

@router.get("/projects")
async def list_projects(
    api_key: ApiKey,
    project_svc: ProjectSvc,
):
    """List all projects."""
    projects = await project_svc.list_projects(api_key)
    return [{"id": p.id, "name": p.name} for p in projects]
```

**Changes:**
1. Removed `Depends()` imports (dependency types include it)
2. Removed `RedisCache` and service class imports
3. Changed `api_key: str = Depends(get_api_key)` → `api_key: ApiKey`
4. Changed `cache: RedisCache = Depends(get_cache)` → `project_svc: ProjectSvc`
5. Removed `ProjectService(cache)` instantiation

### Multiple Service Dependencies

**Before:**
```python
from fastapi import APIRouter, Depends
from apps.api.adapters.cache import RedisCache
from apps.api.dependencies import get_api_key, get_cache
from apps.api.services.agents import AgentService
from apps.api.services.projects import ProjectService
from apps.api.services.tool_presets import ToolPresetService

router = APIRouter()

@router.post("/agents")
async def create_agent(
    request: CreateAgentRequest,
    api_key: str = Depends(get_api_key),
    cache: RedisCache = Depends(get_cache),
):
    """Create a new agent."""
    # Manual instantiation of multiple services
    project_svc = ProjectService(cache)
    tool_preset_svc = ToolPresetService(cache)
    agent_svc = AgentService(cache)

    # Validate project exists
    project = await project_svc.get_project(api_key, request.project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Validate tool preset exists
    if request.tool_preset_id:
        preset = await tool_preset_svc.get_preset(api_key, request.tool_preset_id)
        if not preset:
            raise HTTPException(404, "Tool preset not found")

    # Create agent
    agent = await agent_svc.create_agent(api_key, request.to_dict())
    return {"id": agent.id, "name": agent.name}
```

**After:**
```python
from fastapi import APIRouter, HTTPException
from apps.api.dependencies import ApiKey, AgentSvc, ProjectSvc, ToolPresetSvc

router = APIRouter()

@router.post("/agents")
async def create_agent(
    request: CreateAgentRequest,
    api_key: ApiKey,
    agent_svc: AgentSvc,
    project_svc: ProjectSvc,
    tool_preset_svc: ToolPresetSvc,
):
    """Create a new agent."""
    # Validate project exists
    project = await project_svc.get_project(api_key, request.project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Validate tool preset exists
    if request.tool_preset_id:
        preset = await tool_preset_svc.get_preset(api_key, request.tool_preset_id)
        if not preset:
            raise HTTPException(404, "Tool preset not found")

    # Create agent
    agent = await agent_svc.create_agent(api_key, request.to_dict())
    return {"id": agent.id, "name": agent.name}
```

**Changes:**
1. Replaced single `cache` dependency with three service dependencies
2. Removed all service instantiation (`ProjectService(cache)`, etc.)
3. Business logic remains identical
4. Type annotations provide IntelliSense and type checking

### Nested Dependencies

**Before:**
```python
from fastapi import APIRouter, Depends
from apps.api.adapters.cache import RedisCache
from apps.api.dependencies import get_api_key, get_cache
from apps.api.services.mcp_server_configs import McpServerConfigService
from apps.api.services.mcp_share import McpShareService

router = APIRouter()

@router.get("/mcp-servers/{name}/share")
async def get_share_url(
    name: str,
    api_key: str = Depends(get_api_key),
    cache: RedisCache = Depends(get_cache),
):
    """Get share URL for MCP server."""
    mcp_config = McpServerConfigService(cache)
    mcp_share = McpShareService(cache)

    # Get server config
    server = await mcp_config.get_server_for_api_key(api_key, name)
    if not server:
        raise HTTPException(404, "MCP server not found")

    # Get or create share token
    share_token = await mcp_share.get_or_create_share_token(api_key, name)
    share_url = f"https://api.example.com/share/{share_token}"

    return {"share_url": share_url, "token": share_token}
```

**After:**
```python
from fastapi import APIRouter, HTTPException
from apps.api.dependencies import ApiKey, McpServerConfigSvc, McpShareSvc

router = APIRouter()

@router.get("/mcp-servers/{name}/share")
async def get_share_url(
    name: str,
    api_key: ApiKey,
    mcp_config: McpServerConfigSvc,
    mcp_share: McpShareSvc,
):
    """Get share URL for MCP server."""
    # Get server config
    server = await mcp_config.get_server_for_api_key(api_key, name)
    if not server:
        raise HTTPException(404, "MCP server not found")

    # Get or create share token
    share_token = await mcp_share.get_or_create_share_token(api_key, name)
    share_url = f"https://api.example.com/share/{share_token}"

    return {"share_url": share_url, "token": share_token}
```

## Common Patterns

### Pattern 1: List All Resources

```python
# Before
@router.get("/resources")
async def list_resources(
    api_key: str = Depends(get_api_key),
    cache: RedisCache = Depends(get_cache),
):
    svc = ResourceService(cache)
    return await svc.list_resources(api_key)

# After
@router.get("/resources")
async def list_resources(api_key: ApiKey, resource_svc: ResourceSvc):
    return await resource_svc.list_resources(api_key)
```

### Pattern 2: Get Single Resource

```python
# Before
@router.get("/resources/{id}")
async def get_resource(
    id: str,
    api_key: str = Depends(get_api_key),
    cache: RedisCache = Depends(get_cache),
):
    svc = ResourceService(cache)
    resource = await svc.get_resource(api_key, id)
    if not resource:
        raise HTTPException(404, "Not found")
    return resource

# After
@router.get("/resources/{id}")
async def get_resource(
    id: str,
    api_key: ApiKey,
    resource_svc: ResourceSvc,
):
    resource = await resource_svc.get_resource(api_key, id)
    if not resource:
        raise HTTPException(404, "Not found")
    return resource
```

### Pattern 3: Create Resource

```python
# Before
@router.post("/resources")
async def create_resource(
    request: CreateResourceRequest,
    api_key: str = Depends(get_api_key),
    cache: RedisCache = Depends(get_cache),
):
    svc = ResourceService(cache)
    return await svc.create_resource(api_key, request.to_dict())

# After
@router.post("/resources")
async def create_resource(
    request: CreateResourceRequest,
    api_key: ApiKey,
    resource_svc: ResourceSvc,
):
    return await resource_svc.create_resource(api_key, request.to_dict())
```

### Pattern 4: Update Resource

```python
# Before
@router.put("/resources/{id}")
async def update_resource(
    id: str,
    request: UpdateResourceRequest,
    api_key: str = Depends(get_api_key),
    cache: RedisCache = Depends(get_cache),
):
    svc = ResourceService(cache)
    resource = await svc.update_resource(api_key, id, request.to_dict())
    if not resource:
        raise HTTPException(404, "Not found")
    return resource

# After
@router.put("/resources/{id}")
async def update_resource(
    id: str,
    request: UpdateResourceRequest,
    api_key: ApiKey,
    resource_svc: ResourceSvc,
):
    resource = await resource_svc.update_resource(api_key, id, request.to_dict())
    if not resource:
        raise HTTPException(404, "Not found")
    return resource
```

### Pattern 5: Delete Resource

```python
# Before
@router.delete("/resources/{id}")
async def delete_resource(
    id: str,
    api_key: str = Depends(get_api_key),
    cache: RedisCache = Depends(get_cache),
):
    svc = ResourceService(cache)
    await svc.delete_resource(api_key, id)
    return {"status": "deleted"}

# After
@router.delete("/resources/{id}")
async def delete_resource(
    id: str,
    api_key: ApiKey,
    resource_svc: ResourceSvc,
):
    await resource_svc.delete_resource(api_key, id)
    return {"status": "deleted"}
```

## Testing Migration

### Before: Manual Mocking

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from apps.api.adapters.cache import RedisCache
from apps.api.services.projects import ProjectService

@pytest.fixture
def mock_cache():
    """Mock Redis cache."""
    cache = MagicMock(spec=RedisCache)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache

@pytest.mark.asyncio
async def test_list_projects(mock_cache):
    """Test project listing."""
    # Create service with mock cache
    project_svc = ProjectService(mock_cache)

    # Mock cache to return data
    mock_cache.get.return_value = [{"id": "1", "name": "Test"}]

    # Test service directly
    projects = await project_svc.list_projects("test-key")

    assert len(projects) == 1
    assert projects[0]["name"] == "Test"
```

### After: Dependency Override

```python
import pytest
from fastapi.testclient import TestClient
from apps.api.dependencies import get_project_service
from apps.api.main import app

@pytest.fixture
def mock_project_service():
    """Mock project service."""
    class MockProjectService:
        async def list_projects(self, api_key: str):
            return [{"id": "1", "name": "Test"}]

        async def get_project(self, api_key: str, project_id: str):
            if project_id == "1":
                return {"id": "1", "name": "Test"}
            return None

    return MockProjectService()

def test_list_projects(mock_project_service):
    """Test project listing endpoint."""
    # Override dependency
    app.dependency_overrides[get_project_service] = lambda: mock_project_service

    # Test via HTTP client
    client = TestClient(app)
    response = client.get(
        "/api/v1/projects",
        headers={"X-API-Key": "test-key"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Test"

    # Clean up
    app.dependency_overrides.clear()
```

**Benefits:**
- Test actual HTTP endpoints, not just service methods
- Verify request/response serialization
- Check authentication, authorization, error handling
- Closer to real-world usage

## Troubleshooting

### Issue: Type Checker Fails

**Error:**
```
error[unresolved-reference]: Name `ProjectSvc` used when not defined
```

**Solution:**
Import the dependency type from `dependencies.py`:
```python
from apps.api.dependencies import ProjectSvc
```

### Issue: Runtime Dependency Not Found

**Error:**
```
fastapi.exceptions.FastAPIError: Dependency 'ProjectSvc' not found
```

**Solution:**
Dependency types are `Annotated` aliases that include the provider function. Ensure you're using the correct import:
```python
# ❌ WRONG
from apps.api.services.projects import ProjectService
project_svc: ProjectService  # Missing Depends()

# ✅ CORRECT
from apps.api.dependencies import ProjectSvc
project_svc: ProjectSvc  # Includes Depends(get_project_service)
```

### Issue: Tests Fail After Migration

**Symptom:** Tests fail with "Service not available" or "Connection refused" errors.

**Solution:**
Override dependencies in tests instead of providing real services:
```python
# ❌ WRONG - tries to connect to real Redis
def test_endpoint():
    client = TestClient(app)
    response = client.get("/api/v1/projects")

# ✅ CORRECT - uses mock service
def test_endpoint(mock_project_service):
    app.dependency_overrides[get_project_service] = lambda: mock_project_service
    client = TestClient(app)
    response = client.get("/api/v1/projects")
    app.dependency_overrides.clear()
```

### Issue: IntelliSense Not Working

**Symptom:** IDE doesn't show autocomplete for service methods.

**Solution:**
Dependency types are type aliases. IDEs may need a hint. Use explicit type annotation if needed:
```python
from apps.api.services.projects import ProjectService
from apps.api.dependencies import ProjectSvc

@router.get("/projects")
async def list_projects(
    api_key: ApiKey,
    project_svc: ProjectSvc,  # IDE knows this is ProjectService
):
    # IntelliSense now works
    projects = await project_svc.list_projects(api_key)
```

## Migration Statistics

**Total Routes Migrated:** 35 endpoints across 6 route files

| Route File | Endpoints | Services Used |
|-----------|-----------|---------------|
| `projects.py` | 5 | ProjectSvc |
| `agents.py` | 6 | AgentSvc, ProjectSvc |
| `tool_presets.py` | 5 | ToolPresetSvc |
| `mcp_servers.py` | 9 | McpServerConfigSvc, McpDiscoverySvc, McpShareSvc |
| `skills.py` | 5 | SkillCrudSvc, SkillsService |
| `slash_commands.py` | 5 | SlashCommandSvc |

**Code Reduction:**
- Removed ~100 lines of service instantiation boilerplate
- Reduced import statements by ~50%
- Improved type safety (zero `Any` types)

## Next Steps

1. **Verify Migration:** Run tests and type checker
   ```bash
   uv run pytest tests/
   uv run ty check apps/api/
   ```

2. **Review Routes:** Check for remaining anti-patterns
   ```bash
   # Should return 0
   grep -r "= .*Service(cache)" apps/api/routes/ | wc -l
   grep -r "_get_.*_service()" apps/api/routes/ | wc -l
   ```

3. **Update Tests:** Migrate test fixtures to use dependency overrides

4. **Document Services:** Add docstrings to service provider functions in `dependencies.py`

## References

- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI Testing with Overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Project CLAUDE.md - Dependency Injection Section](../../CLAUDE.md#dependency-injection)
