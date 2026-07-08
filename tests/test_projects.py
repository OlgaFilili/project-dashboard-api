from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.dashboard.exceptions import CannotInviteOwnerError, StorageError, UserAlreadyHasAccessError, UserNotFoundError
from app.dashboard.schemas import ProjectCreate, ProjectInfo, ProjectInvite, ProjectUpdate, UserProjects
from app.dashboard.service.service_core import (
    add_user_to_project,
    del_project,
    get_project,
    get_project_documents,
    get_projects,
    insert_project,
    update_project,
)
from app.database.models import Document, User


@pytest.mark.asyncio
async def test_insert_project_success(project_factory, monkeypatch):
    async def fake_add_new_project(*args, **kwargs):
        return project_factory(
            name="Fast API project",
            description="",
            owner_id=1)

    monkeypatch.setattr(
        "app.dashboard.service.service_core.add_new_project",
        fake_add_new_project)

    project = ProjectCreate(
        name="Fast API project",
        description="")

    result = await insert_project(None, project, owner_id=1)

    assert result.project_id == 1
    assert result.name == "Fast API project"
    assert result.created_at == datetime(2026, 6, 1, 12, 0, 0)
    assert result.owner_id == 1


@pytest.mark.asyncio
async def test_get_projects_success(session, project_factory, monkeypatch):
    async def fake_select_owned_projects(*args, **kwargs):
        return [project_factory(
            id=2,
            name="Fast API project",
            description="",
            created_at=datetime(2026, 6, 1, 16, 0, 0),
            owner_id=1)]

    async def fake_select_member_projects(*args, **kwargs):
        return [project_factory(
            id=5,
            name="Flask project",
            description="Description",
            created_at=datetime(2026, 6, 1, 7, 0, 0),
            owner_id=2)]

    async def fake_select_documents_by_project_id(session, project_id):
        if project_id == 2:
            return [
                Document(
                    id=10,
                    project_id=2,
                    filename="a.pdf",
                    s3_key="key1",
                    file_size=100,
                    content_type="application/pdf",
                    uploaded_at=datetime(2026, 6, 5, 10, 0, 0))]
        return []

    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_owned_projects",
        fake_select_owned_projects)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_member_projects",
        fake_select_member_projects)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_documents_by_project_id",
        fake_select_documents_by_project_id)

    result = await get_projects(session, user_id=1)

    assert len(result.projects) == 2
    project_2 = next(p for p in result.projects if p.project_id == 2)
    assert len(project_2.documents) == 1
    assert project_2.documents[0].document_id == 10
    project_5 = next(p for p in result.projects if p.project_id == 5)
    assert project_5.documents == []


@pytest.mark.asyncio
async def test_get_projects_returns_empty_list(monkeypatch):
    async def fake_select_owned_projects(*args, **kwargs):
        return []

    async def fake_select_member_projects(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_owned_projects",
        fake_select_owned_projects)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_member_projects",
        fake_select_member_projects)

    result = await get_projects(None, user_id=2)

    assert result == UserProjects(projects=[])


@pytest.mark.asyncio
async def test_get_project_success(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    monkeypatch.setattr(
        "app.dashboard.service.service_core.get_project_or_403",
        fake_get_project_or_403)

    result = await get_project(None, user_id=1, project_id=2)

    assert result == ProjectInfo(
        project_id=2,
        name="Learn Python",
        description="Description",
        created_at=datetime(2026, 6, 1, 14, 0, 0),
        owner_id=1
    )


@pytest.mark.asyncio
async def test_update_project_description_success(session, project_factory, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return project_factory(
            name="Old name",
            description="Old description")

    monkeypatch.setattr(
        "app.dashboard.service.service_core.get_project_or_403",
        fake_get_project_or_403)
    result = await update_project(
        session=session, user_id=1, project_id=2,
        project_info=ProjectUpdate(description="Implement 13 endpoints"))

    session.commit.assert_awaited_once()
    assert result == ProjectInfo(
        project_id=1,
        name="Old name",
        description="Implement 13 endpoints",
        created_at=datetime(2026, 6, 1, 12, 0, 0),
        owner_id=1)


@pytest.mark.asyncio
async def test_update_project_info_success(session, project_factory, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return project_factory(
            name="Old name",
            description="Old description")

    monkeypatch.setattr(
        "app.dashboard.service.service_core.get_project_or_403",
        fake_get_project_or_403)
    result = await update_project(
        session=session, user_id=1, project_id=2,
        project_info=ProjectUpdate(
            name="Backend FAST API project",
            description="Implement 13 endpoints")
    )

    session.commit.assert_awaited_once()
    assert result == ProjectInfo(
        project_id=1,
        name="Backend FAST API project",
        description="Implement 13 endpoints",
        created_at=datetime(2026, 6, 1, 12, 0, 0),
        owner_id=1
    )


@pytest.mark.asyncio
async def test_del_project_success(session, sample_project, monkeypatch):
    async def fake_get_project_for_owner(*args, **kwargs):
        return sample_project

    async def fake_select_documents_keys_by_project_id(*args, **kwargs):
        return ["doc1_s3_key", "doc2_s3_key"]

    fake_delete_members_by_project_id = AsyncMock()

    fake_delete_files = Mock()

    monkeypatch.setattr(
        "app.dashboard.service.service_core.get_project_for_owner",
        fake_get_project_for_owner)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_documents_keys_by_project_id",
        fake_select_documents_keys_by_project_id)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.delete_files",
        fake_delete_files)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.delete_members_by_project_id",
        fake_delete_members_by_project_id)

    await del_project(session=session, user_id=1, project_id=2)

    fake_delete_members_by_project_id.assert_awaited_once_with(session, 2)
    session.delete.assert_awaited_once_with(sample_project)
    session.commit.assert_awaited_once()
    fake_delete_files.assert_called_once_with(["doc1_s3_key", "doc2_s3_key"])


@pytest.mark.asyncio
async def test_del_project_storage_error(session, sample_project, monkeypatch):
    async def fake_get_project_for_owner(*args, **kwargs):
        return sample_project

    async def fake_select_documents_keys_by_project_id(*args, **kwargs):
        return ["doc1_s3_key", "doc2_s3_key"]

    fake_delete_members_by_project_id = AsyncMock()

    fake_delete_files = Mock(side_effect=StorageError())

    monkeypatch.setattr(
        "app.dashboard.service.service_core.get_project_for_owner",
        fake_get_project_for_owner)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_documents_keys_by_project_id",
        fake_select_documents_keys_by_project_id)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.delete_files",
        fake_delete_files)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.delete_members_by_project_id",
        fake_delete_members_by_project_id)

    await del_project(session=session, user_id=1, project_id=2)

    fake_delete_members_by_project_id.assert_awaited_once_with(session, 2)
    session.delete.assert_awaited_once_with(sample_project)
    session.commit.assert_awaited_once()
    fake_delete_files.assert_called_once()


@pytest.mark.asyncio
async def test_del_project_no_docs(session, sample_project, monkeypatch):
    async def fake_get_project_for_owner(*args, **kwargs):
        return sample_project

    async def fake_select_documents_keys_by_project_id(*args, **kwargs):
        return []

    fake_delete_members_by_project_id = AsyncMock()

    monkeypatch.setattr(
        "app.dashboard.service.service_core.get_project_for_owner",
        fake_get_project_for_owner)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_documents_keys_by_project_id",
        fake_select_documents_keys_by_project_id)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.delete_members_by_project_id",
        fake_delete_members_by_project_id)

    await del_project(session=session, user_id=1, project_id=2)

    fake_delete_members_by_project_id.assert_awaited_once_with(session, 2)
    session.delete.assert_awaited_once_with(sample_project)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_user_to_project_success(sample_project, monkeypatch):
    async def fake_get_project_for_owner(*args, **kwargs):
        return sample_project

    async def fake_select_user_by_username(*args, **kwargs):
        return User(
            id=2,
            username="Bob",
            password_hash="qwe",
            created_at=datetime(2026, 5, 1, 12, 0, 0))

    async def fake_select_members_by_project_id(*args, **kwargs):
        return [3, 5]

    fake_insert_member = AsyncMock()
    monkeypatch.setattr(
        "app.dashboard.service.service_core.get_project_for_owner",
        fake_get_project_for_owner)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_user_by_username",
        fake_select_user_by_username)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_members_by_project_id",
        fake_select_members_by_project_id)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.insert_member",
        fake_insert_member)

    await add_user_to_project(None, user_id=1, project_id=2, username=ProjectInvite(login="Bob"))
    _, member = fake_insert_member.await_args.args

    fake_insert_member.assert_awaited_once()
    assert member.project_id == 2
    assert member.user_id == 2


@pytest.mark.asyncio
async def test_add_user_to_project_user_not_found(sample_project, monkeypatch):
    async def fake_get_project_for_owner(*args, **kwargs):
        return sample_project

    async def fake_select_user_by_username(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.dashboard.service.service_core.get_project_for_owner",
        fake_get_project_for_owner)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_user_by_username",
        fake_select_user_by_username)

    with pytest.raises(UserNotFoundError):
        await add_user_to_project(None, user_id=1, project_id=2, username=ProjectInvite(login="Bob"))


@pytest.mark.asyncio
async def test_add_user_to_project_user_is_owner(sample_user, sample_project, monkeypatch):
    async def fake_get_project_for_owner(*args, **kwargs):
        return sample_project

    async def fake_select_user_by_username(*args, **kwargs):
        return sample_user

    monkeypatch.setattr(
        "app.dashboard.service.service_core.get_project_for_owner",
        fake_get_project_for_owner)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_user_by_username",
        fake_select_user_by_username)

    with pytest.raises(CannotInviteOwnerError):
        await add_user_to_project(None, user_id=1, project_id=2, username=ProjectInvite(login="Olga"))


@pytest.mark.asyncio
async def test_add_user_to_project_user_already_member(sample_project, monkeypatch):
    async def fake_get_project_for_owner(*args, **kwargs):
        return sample_project

    async def fake_select_user_by_username(*args, **kwargs):
        return User(
            id=2,
            username="Bob",
            password_hash="qwe",
            created_at=datetime(2026, 5, 1, 12, 0, 0))

    async def fake_select_members_by_project_id(*args, **kwargs):
        return [2, 5]

    monkeypatch.setattr(
        "app.dashboard.service.service_core.get_project_for_owner",
        fake_get_project_for_owner)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_user_by_username",
        fake_select_user_by_username)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_members_by_project_id",
        fake_select_members_by_project_id)

    with pytest.raises(UserAlreadyHasAccessError):
        await add_user_to_project(None, user_id=1, project_id=2, username=ProjectInvite(login="Bob"))


@pytest.mark.asyncio
async def test_get_project_documents_success(sample_project, document_factory, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    async def fake_select_documents_by_project_id(*args, **kwargs):
        return [document_factory(id=3),
                document_factory(
                    id=4,
                    filename="report.docx",
                    s3_key="report_s3_key",
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    file_size=6400,
                    uploaded_at=datetime(2026, 5, 31, 12, 49, 57))]

    monkeypatch.setattr(
        "app.dashboard.service.service_core.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_documents_by_project_id",
        fake_select_documents_by_project_id)

    result = await get_project_documents(None, user_id=1, project_id=2)

    assert len(result.documents) == 2
    ids = [d.document_id for d in result.documents]
    assert ids == [3, 4]


@pytest.mark.asyncio
async def test_get_project_documents_no_docs(sample_project, document_factory, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    async def fake_select_documents_by_project_id(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "app.dashboard.service.service_core.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_core.select_documents_by_project_id",
        fake_select_documents_by_project_id)

    result = await get_project_documents(None, user_id=1, project_id=2)

    assert result.documents == []
