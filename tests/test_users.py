from datetime import datetime
from unittest.mock import AsyncMock, Mock, call

import pytest

from app.dashboard.exceptions import StorageError
from app.dashboard.service.users import del_user, deletion_preview
from app.database.models import Member, User


@pytest.mark.asyncio
async def test_deletion_preview_success(session, project_factory, monkeypatch):
    owned_projects = [
        project_factory(),
        project_factory(
            id=2,
            name="Fast API project",
            created_at=datetime(2026, 6, 1, 16, 0, 0),
            owner_id=1)]

    participant = Member(
        project_id=1,
        user_id=2,
        granted_at=datetime(2026, 7, 4, 10, 0, 0))

    new_owner = User(
        id=2,
        username="Bob",
        password_hash="fake_hash",
        created_at=datetime(2026, 7, 1, 10, 0, 0))

    async def fake_select_owned_projects(*args, **kwargs):
        return owned_projects

    async def fake_select_oldest_member_by_project_id(session, project_id):
        return participant if project_id == owned_projects[0].id else None

    mock_select_user_by_id = AsyncMock(return_value=new_owner)

    monkeypatch.setattr(
        "app.dashboard.service.users.select_owned_projects",
        fake_select_owned_projects)
    monkeypatch.setattr(
        "app.dashboard.service.users.select_oldest_member_by_project_id",
        fake_select_oldest_member_by_project_id)
    monkeypatch.setattr(
        "app.dashboard.service.users.select_user_by_id",
        mock_select_user_by_id)

    result = await deletion_preview(session, owner_id=1)

    assert len(result.projects_to_delete) == 1
    assert result.projects_to_delete[0].project_id == owned_projects[1].id
    assert result.projects_to_delete[0].name == owned_projects[1].name

    assert len(result.projects_to_transfer) == 1
    mock_select_user_by_id.assert_awaited_once_with(session, new_owner.id)
    assert result.projects_to_transfer[0].project_id == owned_projects[0].id
    assert result.projects_to_transfer[0].project_name == owned_projects[0].name
    assert result.projects_to_transfer[0].new_owner_login == new_owner.username


@pytest.mark.asyncio
async def test_deletion_preview_no_projects(session, monkeypatch):
    async def fake_select_owned_projects(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "app.dashboard.service.users.select_owned_projects",
        fake_select_owned_projects,
    )

    result = await deletion_preview(session, owner_id=1)

    assert result.projects_to_delete == []
    assert result.projects_to_transfer == []


@pytest.mark.asyncio
async def test_del_user_success(session, sample_user, project_factory, monkeypatch):
    participant = Member(
        project_id=1,
        user_id=2,
        granted_at=datetime(2026, 7, 4, 10, 0, 0))

    owned_projects = [
        project_factory(),
        project_factory(
            id=2,
            name="Fast API project",
            created_at=datetime(2026, 6, 1, 16, 0, 0),
            owner_id=1)]

    docs_keys = ["fake_s3_key1", "fake_s3_key2"]

    async def fake_select_owned_projects(*args, **kwargs):
        return owned_projects

    async def fake_select_oldest_member_by_project_id(session, project_id):
        return participant if project_id == 1 else None

    mock_select_documents_keys_by_project_id = AsyncMock(return_value=docs_keys)
    mock_delete_member_by_user_id = AsyncMock()
    mock_delete_files = Mock()

    calls = Mock()
    calls.attach_mock(session.commit, "commit")
    calls.attach_mock(mock_delete_files, "delete_files")

    monkeypatch.setattr(
        "app.dashboard.service.users.select_owned_projects",
        fake_select_owned_projects)
    monkeypatch.setattr(
        "app.dashboard.service.users.select_oldest_member_by_project_id",
        fake_select_oldest_member_by_project_id)
    monkeypatch.setattr(
        "app.dashboard.service.users.select_documents_keys_by_project_id",
        mock_select_documents_keys_by_project_id)
    monkeypatch.setattr(
        "app.dashboard.service.users.delete_member_by_user_id",
        mock_delete_member_by_user_id)
    monkeypatch.setattr(
        "app.dashboard.service.users.delete_files",
        mock_delete_files)

    await del_user(session, sample_user)

    assert owned_projects[0].owner_id == participant.user_id
    assert owned_projects[1].owner_id == sample_user.id
    mock_select_documents_keys_by_project_id.assert_awaited_once_with(session, owned_projects[1].id)
    mock_delete_member_by_user_id.assert_awaited_once_with(session, sample_user.id)
    assert session.delete.await_count == 2
    assert session.delete.await_args_list == [call(participant), call(sample_user)]
    session.commit.assert_awaited_once()
    mock_delete_files.assert_called_once_with(docs_keys)
    assert calls.mock_calls == [call.commit(), call.delete_files(docs_keys)]


@pytest.mark.asyncio
async def test_del_user_storage_error(session, sample_user, project_factory, monkeypatch):
    participant = Member(
        project_id=1,
        user_id=2,
        granted_at=datetime(2026, 7, 4, 10, 0, 0))

    owned_projects = [
        project_factory(),
        project_factory(
            id=2,
            name="Fast API project",
            created_at=datetime(2026, 6, 1, 16, 0, 0),
            owner_id=1)]

    docs_keys = ["fake_s3_key1", "fake_s3_key2"]

    async def fake_select_owned_projects(*args, **kwargs):
        return owned_projects

    async def fake_select_oldest_member_by_project_id(session, project_id):
        return participant if project_id == 1 else None

    mock_select_documents_keys_by_project_id = AsyncMock(return_value=docs_keys)
    mock_delete_member_by_user_id = AsyncMock()
    mock_delete_files = Mock(side_effect=StorageError())

    monkeypatch.setattr(
        "app.dashboard.service.users.select_owned_projects",
        fake_select_owned_projects)
    monkeypatch.setattr(
        "app.dashboard.service.users.select_oldest_member_by_project_id",
        fake_select_oldest_member_by_project_id)
    monkeypatch.setattr(
        "app.dashboard.service.users.select_documents_keys_by_project_id",
        mock_select_documents_keys_by_project_id)
    monkeypatch.setattr(
        "app.dashboard.service.users.delete_member_by_user_id",
        mock_delete_member_by_user_id)
    monkeypatch.setattr(
        "app.dashboard.service.users.delete_files",
        mock_delete_files)

    await del_user(session, sample_user)

    mock_select_documents_keys_by_project_id.assert_awaited_once_with(session, owned_projects[1].id)
    mock_delete_member_by_user_id.assert_awaited_once_with(session, sample_user.id)
    assert session.delete.await_count == 2
    assert session.delete.await_args_list == [call(participant), call(sample_user)]
    session.commit.assert_awaited_once()
    mock_delete_files.assert_called_once_with(docs_keys)
