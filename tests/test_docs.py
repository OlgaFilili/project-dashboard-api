from unittest.mock import Mock

import pytest
from datetime import datetime
from io import BytesIO

from app.dashboard.exceptions import UnsupportedFileTypeError, StorageError
from app.dashboard.schemas import DocsResponse
from app.dashboard.service_docs import add_documents, get_document, del_document, put_document
from app.dashboard.storage_models import UploadedFileInfo, FileToUpdate
from database.models import Document


class FakeUploadFile:
    def __init__(self, filename, content_type, size, file):
        self.filename = filename
        self.content_type = content_type
        self.size = size
        self.file = file


@pytest.mark.asyncio
async def test_add_documents_success(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    def fake_upload_file(*args, **kwargs):
        return UploadedFileInfo(
            filename="a.pdf",
            s3_key="a_s3_key",
            content_type="application/pdf",
            file_size=4400)

    async def fake_insert_docs(*args, **kwargs):
        return [Document(
            id=1,
            project_id=2,
            filename="a.pdf",
            s3_key="a_s3_key",
            content_type="application/pdf",
            file_size=4400,
            uploaded_at=datetime(2026, 6, 3, 12, 0, 0))]

    monkeypatch.setattr(
        "app.dashboard.service_docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service_docs.upload_file",
        fake_upload_file)
    monkeypatch.setattr(
        "app.dashboard.service_docs.insert_docs",
        fake_insert_docs)

    files = [FakeUploadFile(
        filename="a.pdf",
        content_type="application/pdf",
        size=4400,
        file=BytesIO(b"hello"))]

    result = await add_documents(None, project_id=2, user_id=1, files=files)
    doc=result.documents[0]
    assert isinstance(result, DocsResponse)
    assert len(result.documents) == 1
    assert doc.document_id == 1
    assert doc.filename == "a.pdf"
    assert doc.size == 4400
    assert doc.uploaded_at == datetime(2026, 6, 3, 12, 0, 0)


@pytest.mark.asyncio
async def test_add_documents_unsupported_file_type(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    monkeypatch.setattr(
        "app.dashboard.service_docs.get_project_or_403",
        fake_get_project_or_403)

    files = [FakeUploadFile(
        filename="a.pdf",
        content_type="text/plain",
        size=4400,
        file=BytesIO(b"hello"))]

    with pytest.raises(UnsupportedFileTypeError):
        await add_documents(None, project_id=2, user_id=1, files=files)


@pytest.mark.asyncio
async def test_add_documents_storage_error(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    def fake_upload_file(*args, **kwargs):
        raise StorageError()

    monkeypatch.setattr(
        "app.dashboard.service_docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service_docs.upload_file",
        fake_upload_file)

    files = [FakeUploadFile(
        filename="b.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size=3200,
        file=BytesIO(b"hello"))]

    with pytest.raises(StorageError):
        await add_documents(None, project_id=2, user_id=1, files=files)


@pytest.mark.asyncio
async def test_get_document_success(sample_document, sample_project, monkeypatch):
    stream = BytesIO(b"hello")

    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    def fake_download_file(*args, **kwargs):
        return stream

    monkeypatch.setattr(
        "app.dashboard.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service_docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service_docs.download_file",
        fake_download_file)

    result = await get_document(None, document_id=3, user_id=1)
    body, doc = result
    assert len(result) == 2
    assert body is stream
    assert doc is sample_document


@pytest.mark.asyncio
async def test_get_document_storage_error(sample_document, sample_project, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    def fake_download_file(*args, **kwargs):
        raise StorageError()

    monkeypatch.setattr(
        "app.dashboard.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service_docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service_docs.download_file",
        fake_download_file)

    with pytest.raises(StorageError):
        await get_document(None, document_id=3, user_id=1)


@pytest.mark.asyncio
async def test_del_document_success(session, sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    fake_delete_file = Mock()

    monkeypatch.setattr(
        "app.dashboard.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service_docs.delete_file",
        fake_delete_file)

    await del_document(session=session, document_id=3, user_id=1)

    fake_delete_file.assert_called_once_with(sample_document.s3_key)
    session.delete.assert_awaited_once_with(sample_document)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_del_document_storage_error(sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    def fake_delete_file(*args, **kwargs):
        raise StorageError()

    monkeypatch.setattr(
        "app.dashboard.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service_docs.delete_file",
        fake_delete_file)

    with pytest.raises(StorageError):
        await del_document(None, document_id=3, user_id=1)


@pytest.mark.asyncio
async def test_put_document_success(session, sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    fake_update_file = Mock()

    monkeypatch.setattr(
        "app.dashboard.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service_docs.update_file",
        fake_update_file)

    file = FakeUploadFile(
        filename="file_v1.pdf",
        content_type="application/pdf",
        size=12000,
        file=BytesIO(b"hello, world!"))

    result= await put_document(session=session, document_id=3, user_id=1, file=file)

    called_arg = fake_update_file.call_args.args[0]

    assert called_arg.filename == "file_v1.pdf"
    assert called_arg.s3_key == sample_document.s3_key
    assert called_arg.content_type == "application/pdf"
    assert called_arg.stream is file.file

    session.commit.assert_awaited_once()
    assert result.document_id==3
    assert result.filename=="file_v1.pdf"
    assert result.size==12000
    assert result.uploaded_at==datetime(2026, 6, 2, 16, 49, 27)


@pytest.mark.asyncio
async def test_put_document_storage_error(session, sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    def fake_update_file(*args, **kwargs):
        raise StorageError()

    monkeypatch.setattr(
        "app.dashboard.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service_docs.update_file",
        fake_update_file)

    file = FakeUploadFile(
        filename="file_v1.pdf",
        content_type="application/pdf",
        size=12000,
        file=BytesIO(b"hello, world!"))

    with pytest.raises(StorageError):
        await put_document(session=session, document_id=3, user_id=1, file=file)




