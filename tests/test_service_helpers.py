import pytest

from app.dashboard.exceptions import DocumentNotFoundError, NoAccessError, ProjectNotFoundError, UserNotOwnerError
from app.dashboard.service.helpers import (
    get_doc_or_403,
    get_doc_or_404,
    get_project_for_owner,
    get_project_or_403,
    get_project_or_404,
)


@pytest.mark.asyncio
async def test_get_project_or_404_success(sample_project, monkeypatch):
    async def fake_select_project_by_id(*args, **kwargs):
        return sample_project

    monkeypatch.setattr(
        "app.dashboard.service.helpers.select_project_by_id",
        fake_select_project_by_id)
    result = await get_project_or_404(None, project_id=2)

    assert result is sample_project


@pytest.mark.asyncio
async def test_get_project_or_404_project_not_found(monkeypatch):
    async def fake_select_project_by_id(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.dashboard.service.helpers.select_project_by_id",
        fake_select_project_by_id)

    with pytest.raises(ProjectNotFoundError):
        await get_project_or_404(None, project_id=10)


@pytest.mark.asyncio
async def test_get_project_or_403_owner_success(sample_project, monkeypatch):
    async def fake_get_project_or_404(*args, **kwargs):
        return sample_project

    monkeypatch.setattr(
        "app.dashboard.service.helpers.get_project_or_404",
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
        "app.dashboard.service.helpers.get_project_or_404",
        fake_get_project_or_404)
    monkeypatch.setattr(
        "app.dashboard.service.helpers.select_members_by_project_id",
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
        "app.dashboard.service.helpers.get_project_or_404",
        fake_get_project_or_404)
    monkeypatch.setattr(
        "app.dashboard.service.helpers.select_members_by_project_id",
        fake_select_members_by_project_id)

    with pytest.raises(NoAccessError):
        await get_project_or_403(None, user_id=2, project_id=2)


@pytest.mark.asyncio
async def test_get_project_for_owner_success(sample_project, monkeypatch):
    async def fake_get_project_or_404(*args, **kwargs):
        return sample_project

    monkeypatch.setattr(
        "app.dashboard.service.helpers.get_project_or_404",
        fake_get_project_or_404)
    result = await get_project_for_owner(None, user_id=1, project_id=2)

    assert result is sample_project


@pytest.mark.asyncio
async def test_get_project_for_owner_user_no_owner(sample_project, monkeypatch):
    async def fake_get_project_or_404(*args, **kwargs):
        return sample_project

    monkeypatch.setattr(
        "app.dashboard.service.helpers.get_project_or_404",
        fake_get_project_or_404)

    with pytest.raises(UserNotOwnerError):
        await get_project_for_owner(None, user_id=2, project_id=2)


@pytest.mark.asyncio
async def test_get_doc_or_404_success(sample_document, monkeypatch):
    async def fake_select_document_by_id(*args, **kwargs):
        return sample_document

    monkeypatch.setattr(
        "app.dashboard.service.helpers.select_document_by_id",
        fake_select_document_by_id)

    result = await get_doc_or_404(None, doc_id=3)

    assert result is sample_document


@pytest.mark.asyncio
async def test_get_doc_or_404_document_not_found(monkeypatch):
    async def fake_select_document_by_id(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.dashboard.service.helpers.select_document_by_id",
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
        "app.dashboard.service.helpers.get_doc_or_404",
        fake_get_doc_or_404)
    monkeypatch.setattr(
        "app.dashboard.service.helpers.get_project_or_403",
        fake_get_project_or_403)

    result = await get_doc_or_403(None, user_id=1, doc_id=3)

    assert result is sample_document
