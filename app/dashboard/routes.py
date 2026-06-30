from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from app.dashboard.exceptions import NoAccessError, ProjectNotFoundError, UserNotOwnerError
from app.dashboard.service import insert_project, get_projects, get_project, update_project, del_project, \
    get_current_user
from app.dashboard.schemas import ProjectResponse, ProjectCreate, UserProjects, ProjectInfo, ProjectUpdate
from database.models import User

router = APIRouter(tags=["project"])


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(project: ProjectCreate, owner: User = Depends(get_current_user),
                         async_session: AsyncSession = Depends(get_session)):
    return await insert_project(async_session, project, owner.id)


@router.get("/projects", response_model=UserProjects)
async def show_projects(user: User = Depends(get_current_user), async_session: AsyncSession = Depends(get_session)) -> UserProjects:
    projects = await get_projects(async_session, user.id)
    return projects


@router.get("/project/{project_id}/info", response_model=ProjectInfo)
async def show_project(project_id: int, user: User = Depends(get_current_user), async_session: AsyncSession = Depends(get_session)) -> ProjectInfo:
    try:
        return await get_project(async_session, user.id, project_id)
    except NoAccessError:
        raise HTTPException(status_code=403, detail="User has no access to the project")
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")


@router.put("/project/{project_id}/info", response_model=ProjectInfo)
async def modify_project(project_info: ProjectUpdate, project_id: int, user: User = Depends(get_current_user),
                         async_session: AsyncSession = Depends(get_session)) -> ProjectInfo:
    try:
        return await update_project(async_session, user.id, project_id, project_info)
    except NoAccessError:
        raise HTTPException(status_code=403, detail="User has no access to the project")
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")


@router.delete("/project/{project_id}", status_code=204)
async def delete_project(project_id: int, owner: User = Depends(get_current_user), async_session: AsyncSession = Depends(get_session)):
    try:
        await del_project(async_session, owner.id, project_id)
    except UserNotOwnerError:
        raise HTTPException(status_code=403, detail="User is not the project owner")
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
