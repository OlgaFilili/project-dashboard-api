import pytest
from pydantic import ValidationError

from app.dashboard.schemas import ProjectCreate, ProjectMembership, UserRegister


def test_user_register_schema_empty_login():
    with pytest.raises(ValidationError):
        UserRegister(login="", password="1", repeat_password="1")


def test_user_register_schema_empty_password():
    with pytest.raises(ValidationError):
        UserRegister(login="Olga", password="", repeat_password="1")


def test_user_register_schema_empty_repeat_password():
    with pytest.raises(ValidationError):
        UserRegister(login="Olga", password="1", repeat_password="")


def test_project_create_validation_schema_empty_name():
    with pytest.raises(ValidationError):
        ProjectCreate(name="", description="Project`s description")

def test_project_membership_schema_empty_login():
    with pytest.raises(ValidationError):
        ProjectMembership(login="")
