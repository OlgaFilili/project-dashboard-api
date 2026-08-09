import pytest

from app.dashboard.schemas import ProjectCreate, ProjectInvite
from app.dashboard.service.projects import add_user_to_project, get_projects, insert_project


@pytest.mark.asyncio
async def test_invite_user_success(test_session, test_user, test_user_2):
    _, user_id = test_user
    username, invited_user_id = test_user_2

    project_data = ProjectCreate(name="Test Project", description="A test project description")
    test_user_project = await insert_project(test_session, project_data, user_id)

    invited_user_projects = await get_projects(test_session, invited_user_id)

    assert test_user_project.project_id not in [project.project_id for project in invited_user_projects.projects]

    login = ProjectInvite(login=username)
    await add_user_to_project(test_session, user_id, test_user_project.project_id, login)
    invited_user_projects = await get_projects(test_session, invited_user_id)
    project = next(project
                   for project in invited_user_projects.projects
                   if project.project_id == test_user_project.project_id)

    assert project.owner_id == user_id
    assert project.name == test_user_project.name
