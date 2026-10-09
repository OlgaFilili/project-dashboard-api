import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.exceptions import StorageError
from app.dashboard.repository import (
    delete_member_by_user_id,
    select_documents_keys_by_project_id,
    select_oldest_member_by_project_id,
    select_owned_projects,
    select_user_by_id,
)
from app.dashboard.schemas import DeletionPreview, ProjectNewOwnerInfo
from app.dashboard.storage import delete_files
from app.database.models import User

logger = logging.getLogger(__name__)


async def deletion_preview(session: AsyncSession, owner_id: int) -> DeletionPreview:
    no_members_projects = []
    transfer_projects = []
    owned_projects = await select_owned_projects(session, owner_id)
    for project in owned_projects:
        oldest_member = await select_oldest_member_by_project_id(session, project.id)
        if not oldest_member:
            no_members_projects.append(project)
        else:
            new_owner = await select_user_by_id(session, oldest_member.user_id)
            transfer_projects.append(
                ProjectNewOwnerInfo(
                    project_id=project.id,
                    project_name=project.name,
                    new_owner_login=new_owner.username
                )
            )
    return DeletionPreview(projects_to_delete=no_members_projects, projects_to_transfer=transfer_projects)


async def del_user(session: AsyncSession, owner: User):
    docs_keys = []
    owned_projects = await select_owned_projects(session, owner.id)
    for project in owned_projects:
        oldest_member = await select_oldest_member_by_project_id(session, project.id)
        if not oldest_member:
            project_docs_keys = await select_documents_keys_by_project_id(session, project.id)
            docs_keys += project_docs_keys
        else:
            await session.delete(oldest_member)
            setattr(project, "owner_id", oldest_member.user_id)
    await delete_member_by_user_id(session, owner.id)
    await session.delete(owner)
    await session.commit()
    try:
        delete_files(docs_keys)
    except StorageError:
        logger.exception("Failed to cleanup files s3_key=%s", docs_keys)
