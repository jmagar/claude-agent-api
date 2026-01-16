"""Project management endpoints."""

from fastapi import APIRouter

from apps.api.dependencies import ApiKey, Cache
from apps.api.exceptions import APIError
from apps.api.schemas.requests.projects import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
)
from apps.api.schemas.responses import ProjectListResponse, ProjectResponse
from apps.api.services.projects import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    _api_key: ApiKey,
    cache: Cache,
) -> ProjectListResponse:
    """<summary>List all projects.</summary>"""
    service = ProjectService(cache)
    projects = await service.list_projects()
    return ProjectListResponse(
        projects=[ProjectResponse(**p.__dict__) for p in projects], total=len(projects)
    )


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    request: ProjectCreateRequest,
    _api_key: ApiKey,
    cache: Cache,
) -> ProjectResponse:
    """<summary>Create a new project.</summary>"""
    service = ProjectService(cache)
    project = await service.create_project(request.name, request.path, request.metadata)
    if project is None:
        raise APIError(
            message="Project with this name or path already exists",
            code="PROJECT_EXISTS",
            status_code=409,
        )
    return ProjectResponse(**project.__dict__)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    _api_key: ApiKey,
    cache: Cache,
) -> ProjectResponse:
    """<summary>Get project details.</summary>"""
    service = ProjectService(cache)
    project = await service.get_project(project_id)
    if project is None:
        raise APIError(
            message="Project not found",
            code="PROJECT_NOT_FOUND",
            status_code=404,
        )
    return ProjectResponse(**project.__dict__)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    _api_key: ApiKey,
    cache: Cache,
) -> ProjectResponse:
    """<summary>Update a project.</summary>"""
    service = ProjectService(cache)
    project = await service.update_project(project_id, request.name, request.metadata)
    if project is None:
        raise APIError(
            message="Project not found",
            code="PROJECT_NOT_FOUND",
            status_code=404,
        )
    return ProjectResponse(**project.__dict__)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    _api_key: ApiKey,
    cache: Cache,
) -> None:
    """<summary>Delete a project.</summary>"""
    service = ProjectService(cache)
    deleted = await service.delete_project(project_id)
    if not deleted:
        raise APIError(
            message="Project not found",
            code="PROJECT_NOT_FOUND",
            status_code=404,
        )
