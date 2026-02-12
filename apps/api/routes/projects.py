"""Project management endpoints."""

from typing import TYPE_CHECKING, cast

from fastapi import APIRouter

from apps.api.dependencies import ApiKey, ProjectSvc
from apps.api.exceptions import APIError
from apps.api.schemas.requests.projects import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
)
from apps.api.schemas.responses import ProjectListResponse, ProjectResponse

if TYPE_CHECKING:
    from apps.api.types import JsonValue

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    _api_key: ApiKey,
    project_service: ProjectSvc,
) -> ProjectListResponse:
    """<summary>List all projects.</summary>"""
    projects = await project_service.list_projects()
    return ProjectListResponse(
        projects=[
            ProjectResponse.model_validate(p, from_attributes=True) for p in projects
        ],
        total=len(projects),
    )


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    request: ProjectCreateRequest,
    _api_key: ApiKey,
    project_service: ProjectSvc,
) -> ProjectResponse:
    """<summary>Create a new project.</summary>"""
    project = await project_service.create_project(
        request.name,
        request.path,
        cast("dict[str, JsonValue] | None", request.metadata),
    )
    if project is None:
        raise APIError(
            message="Project with this name or path already exists",
            code="PROJECT_EXISTS",
            status_code=409,
        )
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    _api_key: ApiKey,
    project_service: ProjectSvc,
) -> ProjectResponse:
    """<summary>Get project details.</summary>"""
    project = await project_service.get_project(project_id)
    if project is None:
        raise APIError(
            message="Project not found",
            code="PROJECT_NOT_FOUND",
            status_code=404,
        )
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    _api_key: ApiKey,
    project_service: ProjectSvc,
) -> ProjectResponse:
    """<summary>Update a project.</summary>"""
    project = await project_service.update_project(
        project_id, request.name, cast("dict[str, JsonValue] | None", request.metadata)
    )
    if project is None:
        raise APIError(
            message="Project not found",
            code="PROJECT_NOT_FOUND",
            status_code=404,
        )
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    _api_key: ApiKey,
    project_service: ProjectSvc,
) -> None:
    """<summary>Delete a project.</summary>"""
    deleted = await project_service.delete_project(project_id)
    if not deleted:
        raise APIError(
            message="Project not found",
            code="PROJECT_NOT_FOUND",
            status_code=404,
        )
