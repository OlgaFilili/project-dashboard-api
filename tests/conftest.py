from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.database.models import Document, Project, User


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
            "created_at": datetime(2026, 6, 1, 12, 0, 0)
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

@pytest.fixture
def sample_document():
    return Document(
        id=3,
        project_id=2,
        filename="file.pdf",
        s3_key="file_s3_key",
        content_type="application/pdf",
        file_size= 6400,
        uploaded_at=datetime(2026, 6, 2, 16, 49, 27)
    )

@pytest.fixture
def document_factory():
    def make_document(**kwargs):
        data = {
            "id": 1,
            "project_id": 2,
            "filename": "spec.pdf",
            "s3_key": "spec_s3_key",
            "file_size": 120,
            "content_type": "application/pdf",
            "uploaded_at": datetime(2026, 6, 4, 13, 25, 8)
        }
        data.update(kwargs)
        return Document(**data)

    return make_document