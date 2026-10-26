from datetime import datetime
from io import BytesIO
from unittest.mock import Mock

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
    UploadResponse,
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
from app.dashboard.storage_models import FileMetadata, FileUploadRequest, UploadInfo
from app.database.models import DocVersion


@pytest.mark.asyncio
async def test_add_documents_success(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    def fake_get_file_metadata(*args, **kwargs):
        return FileMetadata(
            content_type="application/pdf",
            file_size=4400)

    async def fake_insert_docs(*args, **kwargs):
        return [DocVersion(
            doc_id=1,
            version_id=1,
            filename="a.pdf",
            s3_key="a_s3_key",
            content_type="application/pdf",
            file_size=4400,
            created_at=datetime(2026, 6, 3, 12, 0, 0))]

    monkeypatch.setattr(
        "app.dashboard.service.docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.get_file_metadata",
        fake_get_file_metadata)
    monkeypatch.setattr(
        "app.dashboard.service.docs.insert_docs",
        fake_insert_docs)

    storage_request = StoragesRequest(files=[StorageRequest(
        filename="a.pdf",
        s3_key="a_s3_key")])

    result = await add_documents(None, project_id=2, user_id=1, request=storage_request)
    doc = result.documents[0]
    assert isinstance(result, DocsResponse)
    assert len(result.documents) == 1
    assert doc.document_id == 1
    assert doc.filename == "a.pdf"
    assert doc.size == 4400
    assert doc.created_at == datetime(2026, 6, 3, 12, 0, 0)


@pytest.mark.asyncio
async def test_add_documents_storage_error(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    def fake_get_file_metadata(*args, **kwargs):
        raise StorageError()

    monkeypatch.setattr(
        "app.dashboard.service.docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.get_file_metadata",
        fake_get_file_metadata)

    storage_request = StoragesRequest(files=[StorageRequest(
        filename="a.docx",
        s3_key="a_s3_key")])

    with pytest.raises(StorageError):
        await add_documents(None, project_id=2, user_id=1, request=storage_request)


@pytest.mark.asyncio
async def test_add_documents_uploaded_file_not_found(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    def fake_get_file_metadata(*args, **kwargs):
        raise UploadedFileNotFoundError()

    monkeypatch.setattr(
        "app.dashboard.service.docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.get_file_metadata",
        fake_get_file_metadata)

    storage_request = StoragesRequest(files=[StorageRequest(
        filename="a.docx",
        s3_key="a_s3_key")])

    with pytest.raises(UploadedFileNotFoundError):
        await add_documents(None, project_id=2, user_id=1, request=storage_request)


@pytest.mark.asyncio
async def test_prepare_for_uploads_success(sample_project, monkeypatch):
    async def fake_get_project_or_403(*args, **kwargs):
        return sample_project

    def fake_generate_url_impl(request):
        return UploadInfo(
            filename=request.filename,
            s3_key="test_key",
            upload_url="http://test.url",
            content_type=request.content_type,
        )

    fake_generate_url = Mock(side_effect=fake_generate_url_impl)

    monkeypatch.setattr(
        "app.dashboard.service.docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.generate_url",
        fake_generate_url)

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
    assert fake_generate_url.call_count == len(storage_request.files)

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
        "app.dashboard.service.docs.get_project_or_403",
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

    def fake_generate_url(*args, **kwargs):
        raise StorageError()

    monkeypatch.setattr(
        "app.dashboard.service.docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.generate_url",
        fake_generate_url)

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
        "app.dashboard.service.docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.download_file",
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
        "app.dashboard.service.docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.get_project_or_403",
        fake_get_project_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.download_file",
        fake_download_file)

    with pytest.raises(StorageError):
        await get_document(None, document_id=3, user_id=1)


@pytest.mark.asyncio
async def test_del_document_success(session, sample_document, sample_doc_info, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    async def fake_select_document_keys_by_doc_id(*args, **kwargs):
        return [sample_document.s3_key]

    async def fake_select_doc_info_by_doc_id(*args, **kwargs):
        return sample_doc_info

    fake_delete_files = Mock()

    monkeypatch.setattr(
        "app.dashboard.service.docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.select_document_keys_by_doc_id",
        fake_select_document_keys_by_doc_id)
    monkeypatch.setattr(
        "app.dashboard.service.docs.select_doc_info_by_doc_id",
        fake_select_doc_info_by_doc_id)
    monkeypatch.setattr(
        "app.dashboard.service.docs.delete_files",
        fake_delete_files)

    await del_document(session=session, document_id=3, user_id=1)

    fake_delete_files.assert_called_once_with([sample_document.s3_key])
    session.delete.assert_awaited_once_with(sample_doc_info)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_del_document_storage_error(session, sample_document, sample_doc_info, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    async def fake_select_document_keys_by_doc_id(*args, **kwargs):
        return [sample_document.s3_key]

    async def fake_select_doc_info_by_doc_id(*args, **kwargs):
        return sample_doc_info

    def fake_delete_files(*args, **kwargs):
        raise StorageError()

    monkeypatch.setattr(
        "app.dashboard.service.docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.select_document_keys_by_doc_id",
        fake_select_document_keys_by_doc_id)
    monkeypatch.setattr(
        "app.dashboard.service.docs.select_doc_info_by_doc_id",
        fake_select_doc_info_by_doc_id)
    monkeypatch.setattr(
        "app.dashboard.service.docs.delete_files",
        fake_delete_files)

    with pytest.raises(StorageError):
        await del_document(session, document_id=3, user_id=1)


@pytest.mark.asyncio
async def test_put_document_success(session, sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    def fake_get_file_metadata(*args, **kwargs):
        return FileMetadata(
            content_type="application/pdf",
            file_size=4400)

    request = StorageRequest(
        filename="file_v1.pdf",
        s3_key="s3_key_v1")
    updated_doc = DocVersion(
        doc_id=sample_document.doc_id,
        version_id=sample_document.version_id + 1,
        filename=request.filename,
        s3_key=request.s3_key,
        file_size=4400,
        content_type=sample_document.content_type,
        created_at=datetime(2026, 6, 6, 12, 0, 0))

    async def fake_update_doc(*args, **kwargs):
        return updated_doc

    monkeypatch.setattr(
        "app.dashboard.service.docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.get_file_metadata",
        fake_get_file_metadata)
    monkeypatch.setattr(
        "app.dashboard.service.docs.update_doc",
        fake_update_doc)

    result = await put_document(session=session, document_id=3, user_id=1, request=request)

    assert result.document_id == 3
    assert result.filename == "file_v1.pdf"
    assert result.size == 4400
    assert result.created_at == datetime(2026, 6, 6, 12, 0, 0)


@pytest.mark.asyncio
async def test_put_document_unsupported_file_type(sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    def fake_get_file_metadata(*args, **kwargs):
        return FileMetadata(
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            file_size=4400)

    monkeypatch.setattr(
        "app.dashboard.service.docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.get_file_metadata",
        fake_get_file_metadata)

    request = StorageRequest(
        filename="file_v1.pdf",
        s3_key="s3_key_v1")

    with pytest.raises(FileMetadataMismatchError):
        await put_document(None, document_id=3, user_id=1, request=request)


@pytest.mark.asyncio
async def test_put_document_storage_error(sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    def fake_get_file_metadata(*args, **kwargs):
        raise StorageError()

    monkeypatch.setattr(
        "app.dashboard.service.docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.get_file_metadata",
        fake_get_file_metadata)

    request = StorageRequest(
        filename="file_v1.pdf",
        s3_key="s3_key_v1")

    with pytest.raises(StorageError):
        await put_document(None, document_id=3, user_id=1, request=request)


@pytest.mark.asyncio
async def test_put_document_uploaded_file_not_found(sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    def fake_get_file_metadata(*args, **kwargs):
        raise UploadedFileNotFoundError()

    monkeypatch.setattr(
        "app.dashboard.service.docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.get_file_metadata",
        fake_get_file_metadata)

    request = StorageRequest(
        filename="file_v1.pdf",
        s3_key="s3_key_v1")

    with pytest.raises(UploadedFileNotFoundError):
        await put_document(None, document_id=3, user_id=1, request=request)


@pytest.mark.asyncio
async def test_prepare_for_update_success(sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    file_update_request = FileUploadRequest(
        filename=sample_document.filename,
        content_type=sample_document.content_type)
    generated_info = UploadInfo(
        filename=file_update_request.filename,
        s3_key="test_key",
        upload_url="http://test.url",
        content_type=file_update_request.content_type)

    def fake_generate_url(request):
        assert isinstance(request, FileUploadRequest)
        assert request.filename == sample_document.filename
        assert request.content_type == sample_document.content_type
        return generated_info

    monkeypatch.setattr(
        "app.dashboard.service.docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.generate_url",
        fake_generate_url)

    result = await prepare_for_update(None, document_id=3, user_id=1)

    assert isinstance(result, UploadResponse)
    assert result.filename == generated_info.filename
    assert result.s3_key == generated_info.s3_key
    assert result.upload_url == generated_info.upload_url
    assert result.content_type == generated_info.content_type


@pytest.mark.asyncio
async def test_prepare_for_update_storage_error(sample_document, monkeypatch):
    async def fake_get_doc_or_403(*args, **kwargs):
        return sample_document

    def fake_generate_url(*args, **kwargs):
        raise StorageError()

    monkeypatch.setattr(
        "app.dashboard.service.docs.get_doc_or_403",
        fake_get_doc_or_403)
    monkeypatch.setattr(
        "app.dashboard.service.docs.generate_url",
        fake_generate_url)

    with pytest.raises(StorageError):
        await prepare_for_update(None, document_id=3, user_id=1)
