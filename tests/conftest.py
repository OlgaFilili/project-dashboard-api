import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from database.models import Project, User


@pytest.fixture
def sample_project():
    return Project(
        id=2,
        name="Learn Python",
        description="Description",
        created_at=datetime(2026, 6, 1, 14, 0, 0),
        owner_id=1
    )


@pytest.fixture
def project_factory():
    def make_project(**kwargs):
        data = {
            "id": 1,
            "name": "Project",
            "description": "Project Description",
            "owner_id": 1,
            "created_at": datetime(2026, 6, 1, 12, 0, 0),
        }
        data.update(kwargs)
        return Project(**data)

    return make_project

@pytest.fixture
def session():
    return AsyncMock()

@pytest.fixture
def sample_user():
    return User(
        id=1,
        username="Olga",
        password_hash="fake_hash",
        created_at=datetime(2026, 6, 1, 10, 0, 0)
    )