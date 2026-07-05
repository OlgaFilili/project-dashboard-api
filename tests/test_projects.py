from fileinput import filename
from unittest.mock import AsyncMock

import pytest
from datetime import datetime

from app.dashboard.exceptions import ProjectNotFoundError, NoAccessError, UserNotOwnerError, UserNotFoundError, \
    CannotInviteOwnerError, UserAlreadyHasAccessError, DocumentNotFoundError
from app.dashboard.schemas import ProjectCreate, ProjectInfo, UserProjects, ProjectUpdate, ProjectInvite, \
    ProjectFullInfo, DocResponse
from app.dashboard.service import insert_project, get_projects, get_project, get_project_or_404, get_project_or_403, \
    update_project, get_project_for_owner, del_project, add_user_to_project, get_doc_or_404, get_doc_or_403, \
    get_project_documents
from database.models import User, Document


@pytest.mark.asyncio
async def test_insert_project_success(project_factory, monkeypatch):
    async def fake_add_new_project(*args, **kwargs):
        return project_factory(
            name="Fast API project",
            description="",
            owner_id=1)

    monkeypatch.setattr(
        "app.dashboard.service.add_new_project",
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
        "app.dashboard.service.select_owned_projects",
        fake_select_owned_projects)
    monkeypatch.setattr(
        "app.dashboard.service.select_member_projects",
        fake_select_member_projects)
    monkeypatch.setattr(
        "app.dashboard.service.select_documents_by_project_id",
        fake_select_documents_by_project_id)

    result = await get_projects(session, user_id=1)

    assert len(result.projects) ==2
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
        "app.dashboard.service.select_owned_projects",
        fake_select_owned_projects)
    monkeypatch.setattr(
        "app.dashboard.service.select_member_projects",
        fake_select_member_projects)

    result = await get_projects(None, user_id=2)

    assert result == UserProjects(projects=[])


@pytest.mark.asyncio
async def test_get_project_or_404_success(sample_project, monkeypatch):
    async def fake_select_project_by_id(*args, **kwargs):
        return sample_project

    monkeypatch.setattr(
        "app.dashboard.service.select_project_by_id",
        fake_select_project_by_id)
    result = await get_project_or_404(None, project_id=2)

    assert result is sample_project


@pytest.mark.asyncio
async def test_get_project_or_404_project_not_found(monkeypatch):
    async def fake_select_project_by_id(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.dashboard.service.select_project_by_id",
        fake_select_project_by_id)

    with pytest.raises(ProjectNotFoundError):
        await get_project_or_404(None, project_id=10)


@pytest.mark.asyncio
async def test_get_project_or_403_owner_success(sample_project, monkeypatch):
    async def fake_get_project_or_404(*args, **kwargs):
        return sample_project

    monkeypatch.setattr(
        "app.dashboard.service.get_project_or_404",
        fake_get_project_or_404)
    result = await get_project_or_403(None, user_id=1, project_id=2)

    assert result is sample_project


@pytest.mark.asyncio
async def test_get_project_or_403_member_success(sample_project, monkeypatch):
    async def fake_get_project_or_404(*args, **kwargs):
        return sample_project

    async def fake_select_members_by_project_id(*args, **kwargs):
        return [2, 5, 10]

    monkeypatch.setattr(
        "app.dashboard.service.get_project_or_404",
        fake_get_project_or_404)
    monkeypatch.setattr(
        "app.dashboard.service.select_members_by_project_id",
        fake_select_members_by_project_id)

    result = await get_project_or_403(None, user_id=2, project_id=2)

    assert result is sample_project


@pytest.mark.asyncio
async def test_get_project_or_403_no_access(sample_project, monkeypatch):
    async def fake_get_project_or_404(*args, **kwargs):
        return sample_project

    async def fake_select_members_by_project_id(*args, **kwargs):
        return [4, 5, 10]

    monkeypatch.setattr(
        "app.dashboard.service.get_project_or_404",
        fake_get_project_or_404)
    monkeypatch.setattr(
        "app.dashboard.service.select_members_by_project_id",
        fake_select_members_by_project_id)

    with pytest.raises(NoAccessError):
        await get_project_or_403(None, user_id=2, project_id=2)


@pytest.mark.asyncio
async def test_get_project_success(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    monkeypatch.setattr(
        "app.dashboard.service.get_project_or_403",
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
        "app.dashboard.service.get_project_or_403",
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
        "app.dashboard.service.get_project_or_403",
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
async def test_get_project_for_owner_success(sample_project, monkeypatch):
    async def fake_get_project_or_404(*args, **kwargs):
        return sample_project

    monkeypatch.setattr(
        "app.dashboard.service.get_project_or_404",
        fake_get_project_or_404)
    result = await get_project_for_owner(None, user_id=1, project_id=2)

    assert result is sample_project


@pytest.mark.asyncio
async def test_get_project_for_owner_user_no_owner(sample_project, monkeypatch):
    async def fake_get_project_or_404(*args, **kwargs):
        return sample_project

    monkeypatch.setattr(
        "app.dashboard.service.get_project_or_404",
        fake_get_project_or_404)

    with pytest.raises(UserNotOwnerError):
        await get_project_for_owner(None, user_id=2, project_id=2)


@pytest.mark.asyncio
async def test_del_project_success(session, sample_project, monkeypatch):
    async def fake_get_project_for_owner(*args, **kwargs):
        return sample_project

    monkeypatch.setattr(
        "app.dashboard.service.get_project_for_owner",
        fake_get_project_for_owner)
    await del_project(session=session, user_id=1, project_id=2)

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
        "app.dashboard.service.get_project_for_owner",
        fake_get_project_for_owner)
    monkeypatch.setattr(
        "app.dashboard.service.select_user_by_username",
        fake_select_user_by_username)
    monkeypatch.setattr(
        "app.dashboard.service.select_members_by_project_id",
        fake_select_members_by_project_id)
    monkeypatch.setattr(
        "app.dashboard.service.insert_member",
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
        "app.dashboard.service.get_project_for_owner",
        fake_get_project_for_owner)
    monkeypatch.setattr(
        "app.dashboard.service.select_user_by_username",
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
        "app.dashboard.service.get_project_for_owner",
        fake_get_project_for_owner)
    monkeypatch.setattr(
        "app.dashboard.service.select_user_by_username",
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
        "app.dashboard.service.get_project_for_owner",
        fake_get_project_for_owner)
    monkeypatch.setattr(
        "app.dashboard.service.select_user_by_username",
        fake_select_user_by_username)
    monkeypatch.setattr(
        "app.dashboard.service.select_members_by_project_id",
        fake_select_members_by_project_id)

    with pytest.raises(UserAlreadyHasAccessError):
        await add_user_to_project(None, user_id=1, project_id=2, username=ProjectInvite(login="Bob"))


@pytest.mark.asyncio
async def test_get_doc_or_404_success(sample_document, monkeypatch):
    async def fake_select_document_by_id(*args, **kwargs):
        return sample_document

    monkeypatch.setattr(
        "app.dashboard.service.select_document_by_id",
        fake_select_document_by_id)

    result = await get_doc_or_404(None, doc_id=3)

    assert result is sample_document


@pytest.mark.asyncio
async def test_get_doc_or_404_document_not_found(monkeypatch):
    async def fake_select_document_by_id(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.dashboard.service.select_document_by_id",
        fake_select_document_by_id)

    with pytest.raises(DocumentNotFoundError):
        await get_doc_or_404(None, doc_id=10)


@pytest.mark.asyncio
async def test_get_doc_or_403_success(sample_document, sample_project, monkeypatch):
    async def fake_get_doc_or_404(*args, **kwargs):
        return sample_document

    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    monkeypatch.setattr(
        "app.dashboard.service.get_doc_or_404",
        fake_get_doc_or_404)
    monkeypatch.setattr(
        "app.dashboard.service.get_project_or_403",
        fake_get_project_or_403)

    result = await get_doc_or_403(None, user_id=1, doc_id=3)

    assert result is sample_document


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
        "app.dashboard.service.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.select_documents_by_project_id",
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
        "app.dashboard.service.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.select_documents_by_project_id",
        fake_select_documents_by_project_id)

    result = await get_project_documents(None, user_id=1, project_id=2)

    assert result.documents == []

