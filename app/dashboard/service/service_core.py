import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.exceptions import PasswordsMismatchError, UserAlreadyExistsError, InvalidCredentialsError, \
    UserNotFoundError, \
    UserAlreadyHasAccessError, CannotInviteOwnerError
from app.dashboard.repository import select_user_by_username, add_new_user, \
    add_new_project, select_owned_projects, select_member_projects, select_members_by_project_id, insert_member, \
    select_documents_by_project_id
from app.dashboard.schemas import UserRegister, UserResponse, ProjectResponse, ProjectCreate, ProjectInfo, \
    ProjectFullInfo, UserProjects, ProjectUpdate, UserLogin, ProjectInvite, DocsResponse, DocResponse
from app.dashboard.service.helpers import hash_password, get_project_or_403, get_project_for_owner
from app.dashboard.service.security import verify_password

from app.config.config import SECRET_KEY
from app.database.models import User, Project, Member


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
    owned_projects = await select_owned_projects(session, user_id)
    participant_projects = await select_member_projects(session, user_id)
    projects = owned_projects + participant_projects
    user_projects = []

    for project in projects:
        docs = await select_documents_by_project_id(session, project.id)
        project_info = ProjectInfo.model_validate(project)
        user_projects.append(
            ProjectFullInfo(
                **project_info.model_dump(),
                documents=[DocResponse.model_validate(d) for d in docs]))
    return UserProjects(projects=user_projects)


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


async def get_project_documents(session: AsyncSession, user_id: int, project_id: int) -> DocsResponse:
    await get_project_or_403(session, user_id, project_id)
    result = await select_documents_by_project_id(session, project_id)
    return DocsResponse(documents=[DocResponse.model_validate(d) for d in result])
