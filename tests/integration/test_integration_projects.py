import pytest
from sqlalchemy import select

from app.dashboard.schemas import ProjectCreate, ProjectResponse
from app.dashboard.service.projects import insert_project
from app.database.models import Project


@pytest.mark.asyncio
async def test_add_new_project_success(test_session, test_user):
    _, user_id = test_user

    project_data = ProjectCreate(name="Test Project", description="A test project description")
    new_project = await insert_project(test_session, project_data, user_id)

    assert isinstance(new_project, ProjectResponse)
    assert new_project.name == "Test Project"

    result = await test_session.execute(select(Project).where(Project.id == new_project.project_id))
    project = result.scalar_one_or_none()

    assert project is not None
    assert project.owner_id == user_id
    assert project.name == project_data.name
    assert project.description == project_data.description
