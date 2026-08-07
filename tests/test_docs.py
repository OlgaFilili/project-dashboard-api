from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock, Mock

import pytest

from app.dashboard.exceptions import (
    FileMetadataMismatchError,
    StorageError,
    UnsupportedFileTypeError,
    UploadedFileNotFoundError,
)
from app.dashboard.schemas import (
    DocsResponse,
    FileRequest,
    StorageRequest,
    StoragesRequest,
    UpdateResponse,
    UploadsRequest,
    UploadsResponse,
)
from app.dashboard.service.docs import (
    add_documents,
    del_document,
    get_document,
    prepare_for_update,
    prepare_for_uploads,
    put_document,
)
from app.dashboard.storage_models import FileMetadata, UploadInfo
from app.database.models import Document


@pytest.mark.asyncio
async def test_add_documents_success(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    def fake_get_file_metadata(*args, **kwargs):
        return FileMetadata(
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
        "app.dashboard.service.service_docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_file_metadata",
        fake_get_file_metadata)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.insert_docs",
        fake_insert_docs)

    storage_request = StoragesRequest(files=[StorageRequest(
        filename="a.pdf",
        s3_key="a_s3_key",
        content_type="application/pdf")])

    result = await add_documents(None, project_id=2, user_id=1, request=storage_request)
    doc = result.documents[0]
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
        "app.dashboard.service.service_docs.get_project_or_403",
        fake_get_project_or_403)

    storage_request = StoragesRequest(files=[StorageRequest(
        filename="a.docx",
        s3_key="a_s3_key",
        content_type="text/plain")])

    with pytest.raises(UnsupportedFileTypeError):
        await add_documents(None, project_id=2, user_id=1, request=storage_request)


@pytest.mark.asyncio
async def test_add_documents_file_metadata_mismatch(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    def fake_get_file_metadata(*args, **kwargs):
        return FileMetadata(
            content_type="application/pdf",
            file_size=4400)

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_file_metadata",
        fake_get_file_metadata)

    storage_request = StoragesRequest(files=[StorageRequest(
        filename="a.docx",
        s3_key="a_s3_key",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")])

    with pytest.raises(FileMetadataMismatchError):
        await add_documents(None, project_id=2, user_id=1, request=storage_request)


@pytest.mark.asyncio
async def test_add_documents_storage_error(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    def fake_get_file_metadata(*args, **kwargs):
        raise StorageError()

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_file_metadata",
        fake_get_file_metadata)

    storage_request = StoragesRequest(files=[StorageRequest(
        filename="a.docx",
        s3_key="a_s3_key",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")])

    with pytest.raises(StorageError):
        await add_documents(None, project_id=2, user_id=1, request=storage_request)


@pytest.mark.asyncio
async def test_add_documents_uploaded_file_not_found(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    def fake_get_file_metadata(*args, **kwargs):
        raise UploadedFileNotFoundError()

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_file_metadata",
        fake_get_file_metadata)

    storage_request = StoragesRequest(files=[StorageRequest(
        filename="a.docx",
        s3_key="a_s3_key",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")])

    with pytest.raises(UploadedFileNotFoundError):
        await add_documents(None, project_id=2, user_id=1, request=storage_request)


@pytest.mark.asyncio
async def test_prepare_for_uploads_success(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    def fake_generate_upload_url_impl(request):
        return UploadInfo(
            filename=request.filename,
            s3_key="test_key",
            upload_url="http://test.url",
            content_type=request.content_type,
        )

    fake_generate_upload_url = MagicMock(side_effect=fake_generate_upload_url_impl)

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.generate_upload_url",
        fake_generate_upload_url)

    storage_request = UploadsRequest(
        files=[FileRequest(
            filename="file1.pdf",
            content_type="application/pdf"),
            FileRequest(
                filename="file2.docx",
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")])

    result = await prepare_for_uploads(None, project_id=2, user_id=1, request=storage_request)

    assert isinstance(result, UploadsResponse)
    assert len(result.files) == 2
    assert fake_generate_upload_url.call_count == len(storage_request.files)

    file1 = result.files[0]
    file2 = result.files[1]
    assert file1.filename == "file1.pdf"
    assert file2.filename == "file2.docx"
    assert file1.content_type == "application/pdf"
    assert file2.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@pytest.mark.asyncio
async def test_prepare_for_uploads_unsupported_file_type(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_project_or_403",
        fake_get_project_or_403)

    storage_request = UploadsRequest(
        files=[FileRequest(
            filename="file1.txt",
            content_type="text/plain")])

    with pytest.raises(UnsupportedFileTypeError):
        await prepare_for_uploads(None, project_id=2, user_id=1, request=storage_request)


@pytest.mark.asyncio
async def test_prepare_for_uploads_storage_error(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    def fake_generate_upload_url(*args, **kwargs):
        raise StorageError()

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.generate_upload_url",
        fake_generate_upload_url)

    storage_request = UploadsRequest(
        files=[FileRequest(
            filename="file1.pdf",
            content_type="application/pdf")])

    with pytest.raises(StorageError):
        await prepare_for_uploads(None, project_id=2, user_id=1, request=storage_request)


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
        "app.dashboard.service.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.download_file",
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
        "app.dashboard.service.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.download_file",
        fake_download_file)

    with pytest.raises(StorageError):
        await get_document(None, document_id=3, user_id=1)


@pytest.mark.asyncio
async def test_del_document_success(session, sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    fake_delete_file = Mock()

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.delete_file",
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
        "app.dashboard.service.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.delete_file",
        fake_delete_file)

    with pytest.raises(StorageError):
        await del_document(None, document_id=3, user_id=1)


@pytest.mark.asyncio
async def test_put_document_success(session, sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    def fake_get_file_metadata(*args, **kwargs):
        return FileMetadata(
            content_type="application/pdf",
            file_size=4400)

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_file_metadata",
        fake_get_file_metadata)

    request = FileRequest(
        filename="file_v1.pdf",
        content_type="application/pdf")

    result = await put_document(session=session, document_id=3, user_id=1, request=request)

    session.commit.assert_awaited_once()
    assert result.document_id == 3
    assert result.filename == "file_v1.pdf"
    assert result.size == 4400
    assert result.uploaded_at == datetime(2026, 6, 2, 16, 49, 27)


@pytest.mark.asyncio
async def test_put_document_unsupported_file_type(sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_doc_or_403",
        fake_get_doc_or_403)

    request = FileRequest(
        filename="file_v1.txt",
        content_type="text/plain")

    with pytest.raises(UnsupportedFileTypeError):
        await put_document(None, document_id=3, user_id=1, request=request)


@pytest.mark.asyncio
async def test_put_document_file_metadata_mismatch(sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    def fake_get_file_metadata(*args, **kwargs):
        return FileMetadata(
            content_type="application/pdf",
            file_size=4400)

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_file_metadata",
        fake_get_file_metadata)

    request = FileRequest(
        filename="file_v1.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    with pytest.raises(FileMetadataMismatchError):
        await put_document(None, document_id=3, user_id=1, request=request)


@pytest.mark.asyncio
async def test_put_document_storage_error(sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    def fake_get_file_metadata(*args, **kwargs):
        raise StorageError()

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_file_metadata",
        fake_get_file_metadata)

    request = FileRequest(
        filename="file_v1.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    with pytest.raises(StorageError):
        await put_document(None, document_id=3, user_id=1, request=request)


@pytest.mark.asyncio
async def test_put_document_uploaded_file_not_found(sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    def fake_get_file_metadata(*args, **kwargs):
        raise UploadedFileNotFoundError()

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_file_metadata",
        fake_get_file_metadata)

    request = FileRequest(
        filename="file_v1.pdf",
        content_type="application/pdf")

    with pytest.raises(UploadedFileNotFoundError):
        await put_document(None, document_id=3, user_id=1, request=request)


@pytest.mark.asyncio
async def test_prepare_for_update_success(sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    def fake_generate_update_url_impl(*args, **kwargs):
        return "http://test.url"

    fake_generate_update_url = MagicMock(side_effect=fake_generate_update_url_impl)

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.generate_update_url",
        fake_generate_update_url)

    content_type = "application/pdf"

    result = await prepare_for_update(None, document_id=3, user_id=1, content_type=content_type)

    assert isinstance(result, UpdateResponse)
    assert fake_generate_update_url.called
    assert result.content_type == "application/pdf"


@pytest.mark.asyncio
async def test_prepare_for_update_unsupported_file_type(sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_doc_or_403",
        fake_get_doc_or_403)

    content_type = "text/plain"

    with pytest.raises(UnsupportedFileTypeError):
        await prepare_for_update(None, document_id=3, user_id=1, content_type=content_type)


@pytest.mark.asyncio
async def test_prepare_for_update_storage_error(sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    def fake_generate_update_url(*args, **kwargs):
        raise StorageError()

    monkeypatch.setattr(
        "app.dashboard.service.service_docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.service_docs.generate_update_url",
        fake_generate_update_url)

    content_type = "application/pdf"

    with pytest.raises(StorageError):
        await prepare_for_update(None, document_id=3, user_id=1, content_type=content_type)
