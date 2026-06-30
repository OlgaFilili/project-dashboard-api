import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from app.dashboard.exceptions import ProjectNotFoundError, NoAccessError, UserNotOwnerError
from app.dashboard.schemas import ProjectCreate, ProjectInfo, UserProjects, ProjectUpdate
from app.dashboard.service import insert_project, get_projects, get_project, get_project_or_404, get_project_or_403, \
    update_project, get_project_for_owner, del_project
from database.models import Project


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
async def test_get_projects_success(project_factory, monkeypatch):
    async def fake_get_owned_projects(*args, **kwargs):
        return [
            project_factory(
                owner_id=1),
            project_factory(
                id=2,
                name="Fast API project",
                description="",
                created_at=datetime(2026, 6, 1, 16, 0, 0),
                owner_id=1
            )
        ]

    async def fake_get_participant_projects(*args, **kwargs):
        return [project_factory(
            id=3,
            name="Flask project",
            description="Description",
            created_at=datetime(2026, 6, 1, 7, 0, 0),
            owner_id=2,
        )]

    monkeypatch.setattr(
        "app.dashboard.service.get_owned_projects",
        fake_get_owned_projects)
    monkeypatch.setattr(
        "app.dashboard.service.get_participant_projects",
        fake_get_participant_projects)

    result = await get_projects(None, user_id=1)

    assert result == UserProjects(
        projects=[ProjectInfo(
            project_id=1,
            name="Project",
            description="Project Description",
            created_at=datetime(2026, 6, 1, 12, 0, 0),
            owner_id=1),
            ProjectInfo(
                project_id=2,
                name="Fast API project",
                description="",
                created_at=datetime(2026, 6, 1, 16, 0, 0),
                owner_id=1),
            ProjectInfo(
                project_id=3,
                name="Flask project",
                description="Description",
                created_at=datetime(2026, 6, 1, 7, 0, 0),
                owner_id=2
            )
        ]
    )


@pytest.mark.asyncio
async def test_get_projects_returns_empty_list(monkeypatch):
    async def fake_get_owned_projects(*args, **kwargs):
        return []

    async def fake_get_participant_projects(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "app.dashboard.service.get_owned_projects",
        fake_get_owned_projects)
    monkeypatch.setattr(
        "app.dashboard.service.get_participant_projects",
        fake_get_participant_projects)

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
        fake_get_project_for_owner
    )
    await del_project(session=session, user_id=1, project_id=2)

    session.delete.assert_awaited_once_with(sample_project)
    session.commit.assert_awaited_once()
