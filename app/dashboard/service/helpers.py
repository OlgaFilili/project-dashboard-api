from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.exceptions import DocumentNotFoundError, NoAccessError, ProjectNotFoundError, UserNotOwnerError
from app.dashboard.repository import select_document_by_id, select_members_by_project_id, select_project_by_id
from app.database.models import Document, Project

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


async def get_project_or_404(session: AsyncSession, project_id: int) -> Project:
    project = await select_project_by_id(session, project_id)
    if not project:
        raise ProjectNotFoundError()
    return project


async def get_project_or_403(session: AsyncSession, user_id: int, project_id: int) -> Project:
    project = await get_project_or_404(session, project_id)
    if project.owner_id != user_id:
        members = await select_members_by_project_id(session, project_id)
        if user_id not in members:
            raise NoAccessError()
    return project


async def get_project_for_owner(session: AsyncSession, user_id: int, project_id: int) -> Project:
    project = await get_project_or_404(session, project_id)
    if project.owner_id != user_id:
        raise UserNotOwnerError()
    return project


async def get_doc_or_404(session: AsyncSession, doc_id: int) -> Document:
    doc = await select_document_by_id(session, doc_id)
    if not doc:
        raise DocumentNotFoundError()
    return doc


async def get_doc_or_403(session: AsyncSession, user_id: int, doc_id: int) -> Document:
    doc = await get_doc_or_404(session, doc_id)
    await get_project_or_403(session, user_id, doc.project_id)
    return doc
