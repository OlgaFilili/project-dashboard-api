from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.schemas import UploadDocInfo
from app.database.models import Document, DocVersion, Member, Project, User


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


async def insert_docs(session: AsyncSession, project_id: int, docs: list[UploadDocInfo]) -> list[DocVersion]:
    project_docs = [Document(
        project_id=project_id,
        version_id=1
    ) for _ in docs]
    session.add_all(project_docs)
    await session.flush()
    docs_version = [DocVersion(
        doc_id=project_doc.id,
        version_id=1,
        filename=d.filename,
        s3_key=d.s3_key,
        file_size=d.size,
        content_type=d.content_type,
    ) for project_doc, d in zip(project_docs, docs)]
    session.add_all(docs_version)
    await session.commit()
    for doc in docs_version:
        await session.refresh(doc)
    return docs_version


async def update_doc(session: AsyncSession, doc: DocVersion) -> DocVersion:
    session.add(doc)
    await session.flush()
    await session.execute(update(Document).where(Document.id == doc.doc_id).values(version_id=doc.version_id))
    await session.commit()
    await session.refresh(doc)
    return doc


async def select_project_id_by_doc_id(session: AsyncSession, doc_id: int) -> int | None:
    result = await session.execute(select(Document.project_id).where(Document.id == doc_id))
    return result.scalar_one_or_none()


async def select_doc_info_by_doc_id(session: AsyncSession, doc_id: int) -> Document | None:
    result = await session.execute(select(Document).where(Document.id == doc_id))
    return result.scalar_one_or_none()


async def select_document_by_id(session: AsyncSession, document_id: int) -> DocVersion:
    result = await session.execute(
        select(DocVersion)
        .join(Document, Document.id == DocVersion.doc_id)
        .where(
            Document.id == document_id,
            DocVersion.version_id == Document.version_id,
        )
    )
    return result.scalar_one()


async def select_documents_by_project_id(session: AsyncSession, project_id: int) -> list[DocVersion]:
    result = await session.execute(
        select(DocVersion)
        .join(Document, Document.id == DocVersion.doc_id)
        .where(
            Document.project_id == project_id,
            DocVersion.version_id == Document.version_id,
        )
    )
    return result.scalars().all()


async def select_documents_keys_by_project_id(session: AsyncSession, project_id: int) -> list[str]:
    result = await session.execute(
        select(DocVersion.s3_key)
        .join(Document, Document.id == DocVersion.doc_id)
        .where(Document.project_id == project_id)
    )
    return result.scalars().all()


async def select_document_keys_by_doc_id(session: AsyncSession, doc_id: int) -> list[str]:
    result = await session.execute(select(DocVersion.s3_key).where(DocVersion.doc_id == doc_id))
    return result.scalars().all()


async def delete_members_by_project_id(session: AsyncSession, project_id: int) -> None:
    await session.execute(delete(Member).where(Member.project_id == project_id))


async def select_membership(session: AsyncSession, project_id: int, user_id: int) -> Member | None:
    result = await session.execute(select(Member).where(Member.project_id == project_id, Member.user_id == user_id))
    return result.scalar_one_or_none()


async def select_oldest_member_by_project_id(session: AsyncSession, project_id: int) -> Member | None:
    result = await session.execute(
        select(Member)
        .where(Member.project_id == project_id)
        .order_by(Member.granted_at)
        .limit(1))
    return result.scalar_one_or_none()


async def delete_member_by_user_id(session: AsyncSession, user_id: int) -> None:
    await session.execute(delete(Member).where(Member.user_id == user_id))
