import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from config.config import SECRET_KEY
from database.db import get_session
from database.models import User, Project, Member
from app.dashboard.exceptions import PasswordsMismatchError, UserAlreadyExistsError, ProjectNotFoundError, \
    NoAccessError, UserNotOwnerError, InvalidCredentialsError, UnauthorizedError, UserNotFoundError, \
    UserAlreadyHasAccessError, CannotInviteOwnerError
from app.dashboard.schemas import UserRegister, UserResponse, ProjectResponse, ProjectCreate, ProjectInfo, \
    UserProjects, ProjectUpdate, UserLogin, ProjectInvite
from app.dashboard.repository import select_user_by_username, select_user_by_id, add_new_user, \
    add_new_project, get_owned_projects, get_member_projects, select_project_by_id, \
    select_members_by_project_id, insert_member

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


async def get_current_user(token: str = Depends(oauth2_scheme),
                           async_session: AsyncSession = Depends(get_session)) -> User:
    try:
        token_decode = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": True})
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError()
    except jwt.InvalidTokenError:
        raise UnauthorizedError()
    user = await select_user_by_id(async_session, token_decode["user_id"])
    if not user:
        raise UnauthorizedError()
    return user


async def insert_user(session: AsyncSession, user_data: UserRegister) -> UserResponse:
    if user_data.password != user_data.repeat_password:
        raise PasswordsMismatchError()
    user = await select_user_by_username(session, user_data.login)
    if user:
        raise UserAlreadyExistsError()
    hashed_password = hash_password(user_data.password)
    new_user = User(
        username=user_data.login,
        password_hash=hashed_password)
    new_user = await add_new_user(session, new_user)
    return UserResponse(user_id=new_user.id, login=new_user.username, created_at=new_user.created_at)


async def get_token(session: AsyncSession, creds: UserLogin) -> str:
    user = await select_user_by_username(session, creds.login)
    if not user:
        raise InvalidCredentialsError()
    if not verify_password(creds.password, user.password_hash):
        raise InvalidCredentialsError()
    token = jwt.encode(
        {"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        SECRET_KEY,
        algorithm="HS256")
    return token


async def insert_project(session: AsyncSession, project_data: ProjectCreate, owner_id: int) -> ProjectResponse:
    new_project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=owner_id,
    )
    project = await add_new_project(session, new_project)
    return ProjectResponse(project_id=project.id, name=project.name, created_at=project.created_at,
                           owner_id=project.owner_id)


async def get_projects(session: AsyncSession, user_id: int) -> UserProjects:
    owned_projects = await get_owned_projects(session, user_id)
    participant_projects = await get_member_projects(session, user_id)
    projects = owned_projects + participant_projects
    return UserProjects(projects=[ProjectInfo.model_validate(p) for p in projects])


async def get_project_or_404(session: AsyncSession, project_id: int) -> Project:
    project = await select_project_by_id(session, project_id)
    if not project:
        raise ProjectNotFoundError()
    return project


async def get_project_or_403(session: AsyncSession, user_id: int, project_id: int) -> Project:
    project = await get_project_or_404(session, project_id)
    if project.owner_id != user_id:
        members = await select_members_by_project_id(session, project_id)
        if not user_id in members:
            raise NoAccessError()
    return project


async def get_project(session: AsyncSession, user_id: int, project_id: int) -> ProjectInfo:
    project = await get_project_or_403(session, user_id, project_id)
    return ProjectInfo.model_validate(project)


async def update_project(session: AsyncSession, user_id: int, project_id: int,
                         project_info: ProjectUpdate) -> ProjectInfo:
    project = await get_project_or_403(session, user_id, project_id)
    update_data = project_info.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    await session.commit()
    return ProjectInfo.model_validate(project)


async def get_project_for_owner(session: AsyncSession, user_id: int, project_id: int) -> Project:
    project = await get_project_or_404(session, project_id)
    if project.owner_id != user_id:
        raise UserNotOwnerError()
    return project


async def del_project(session: AsyncSession, user_id: int, project_id: int) -> None:
    project = await get_project_for_owner(session, user_id, project_id)
    await session.delete(project)
    await session.commit()


async def add_user_to_project(session: AsyncSession, user_id: int, project_id: int, username: ProjectInvite):
    project = await get_project_for_owner(session, user_id, project_id)
    user = await select_user_by_username(session, username.login)
    if not user:
        raise UserNotFoundError()
    if user.id == project.owner_id:
        raise CannotInviteOwnerError()
    participants = await select_members_by_project_id(session, project_id)
    if user.id in participants:
        raise UserAlreadyHasAccessError()
    new_participant = Member(
        project_id=project_id,
        user_id=user.id)
    await insert_member(session, new_participant)
