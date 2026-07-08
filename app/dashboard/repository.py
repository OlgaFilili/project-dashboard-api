from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Document, Member, Project, User


async def select_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def add_new_user(session: AsyncSession, new_user: User) -> User:
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


async def select_user_by_id(session: AsyncSession, id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    return user


async def add_new_project(session: AsyncSession, new_project: Project) -> Project:
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)
    return new_project


async def select_owned_projects(session: AsyncSession, owner_id: int) -> list[Project]:
    result = await session.execute(select(Project).where(Project.owner_id == owner_id))
    return result.scalars().all()


async def select_member_projects(session: AsyncSession, user_id: int) -> list[Project]:
    result = await session.execute(select(Member.project_id).where(Member.user_id == user_id))
    projects_ids = result.scalars().all()
    projects = await session.execute(select(Project).where(Project.id.in_(projects_ids)))
    return projects.scalars().all()


async def select_project_by_id(session: AsyncSession, project_id: int) -> Project | None:
    result = await session.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def select_members_by_project_id(session: AsyncSession, project_id: int) -> list[int]:
    result = await session.execute(select(Member.user_id).where(Member.project_id == project_id))
    return result.scalars().all()


async def insert_member(session: AsyncSession, member: Member):
    session.add(member)
    await session.commit()


async def insert_docs(session: AsyncSession, docs: list[Document]) -> list[Document]:
    session.add_all(docs)
    await session.commit()
    for doc in docs:
        await session.refresh(doc)
    return docs

async def select_document_by_id(session: AsyncSession, document_id: int) -> Document | None:
    result = await session.execute(select(Document).where(Document.id == document_id))
    return result.scalar_one_or_none()

async def select_documents_by_project_id(session: AsyncSession, project_id: int) -> list[Document]:
    result = await session.execute(select(Document).where(Document.project_id == project_id))
    return result.scalars().all()

