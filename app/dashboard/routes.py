from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from app.dashboard.exceptions import PasswordsMismatchError, UserAlreadyExistsError, NoAccessError, ProjectNotFoundError, UserNotOwnerError
from app.dashboard.service import insert_user, insert_project, get_projects, get_project, update_project, del_project
from app.dashboard.schemas import UserRegister, UserResponse, ProjectResponse, ProjectCreate, UserProjects, ProjectInfo, \
    ProjectUpdate

router = APIRouter(tags=["project"])


@router.post("/auth", response_model=UserResponse, status_code=201)
async def create_user(creds: UserRegister, async_session: AsyncSession = Depends(get_session)):
    try:
        return await insert_user(async_session, creds)
    except PasswordsMismatchError:
        raise HTTPException(status_code=422, detail="Passwords do not match")
    except UserAlreadyExistsError:
        raise HTTPException(status_code=409, detail="User already exists")


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(project: ProjectCreate, async_session: AsyncSession = Depends(get_session)):
    owner_id = 1
    return await insert_project(async_session, project, owner_id)


@router.get("/projects", response_model=UserProjects)
async def show_projects(async_session: AsyncSession = Depends(get_session)) -> UserProjects:
    user_id = 1
    projects = await get_projects(async_session, user_id)
    return projects


@router.get("/project/{project_id}/info", response_model=ProjectInfo)
async def show_project(project_id: int, async_session: AsyncSession = Depends(get_session)) -> ProjectInfo:
    user_id = 1
    try:
        return await get_project(async_session, user_id, project_id)
    except NoAccessError:
        raise HTTPException(status_code=403, detail="User has no access to the project")
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")


@router.put("/project/{project_id}/info", response_model=ProjectInfo)
async def modify_project(project_info: ProjectUpdate, project_id: int,
                         async_session: AsyncSession = Depends(get_session)) -> ProjectInfo:
    user_id = 1
    try:
        return await update_project(async_session, user_id, project_id, project_info)
    except NoAccessError:
        raise HTTPException(status_code=403, detail="User has no access to the project")
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")

@router.delete("/project/{project_id}", status_code=204)
async def delete_project(project_id: int, async_session: AsyncSession = Depends(get_session)):
    user_id = 1
    try:
        await del_project(async_session, user_id, project_id)
    except UserNotOwnerError:
        raise HTTPException(status_code=403, detail="User is not the project owner")
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
