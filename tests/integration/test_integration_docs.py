from io import BytesIO
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError
from sqlalchemy import select

from app.config import get_config
from app.dashboard import storage
from app.dashboard.schemas import DocResponse, ProjectCreate, StorageRequest, StoragesRequest
from app.dashboard.service.docs import add_documents, del_document, prepare_for_update, put_document
from app.dashboard.service.projects import insert_project
from app.database.models import Document, DocVersion

config = get_config()


@pytest.mark.asyncio
async def test_document_lifecycle_success(test_session, test_user, test_storage_client, monkeypatch):
    monkeypatch.setattr(storage, "storage_client", test_storage_client)
    _, user_id = test_user

    project_data = ProjectCreate(name="Test project with doc", description="A test project for docs management check")
    project = await insert_project(test_session, project_data, user_id)

    file_content = b"Test document content"
    s3_key = str(uuid4())
    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    test_storage_client.upload_fileobj(
        Fileobj=BytesIO(file_content),
        Bucket=config.storage_bucket,
        Key=s3_key,
        ExtraArgs={"ContentType": content_type})
    doc_data = StoragesRequest(files=
    [StorageRequest(
        filename="test_document.docx",
        s3_key=s3_key)])
    add_result = await add_documents(test_session, project.project_id, user_id, doc_data)
    doc_id = add_result.documents[0].document_id

    assert add_result.documents[0].filename == "test_document.docx"

    result = await test_session.execute(select(Document).where(Document.id == doc_id))
    uploaded_doc = result.scalar_one()

    assert uploaded_doc.version_id == 1
    assert uploaded_doc.project_id == project.project_id

    result = await test_session.execute(select(DocVersion).where(DocVersion.doc_id == doc_id))
    versions = result.scalars().all()

    assert len(versions) == 1
    assert versions[0].version_id == 1
    assert versions[0].filename == "test_document.docx"
    assert versions[0].s3_key == s3_key

    prep_update_result = await prepare_for_update(test_session, doc_id, user_id)

    assert prep_update_result.content_type == content_type

    update_file_content = b"Test document content update"
    test_storage_client.upload_fileobj(
        Fileobj=BytesIO(update_file_content),
        Bucket=config.storage_bucket,
        Key=prep_update_result.s3_key,
        ExtraArgs={"ContentType": content_type})
    updated_doc_data = await put_document(
        test_session, doc_id, user_id,
        request=StorageRequest(filename="updated_test_document.docx", s3_key=prep_update_result.s3_key))

    assert isinstance(updated_doc_data, DocResponse)
    assert updated_doc_data.document_id == doc_id
    assert updated_doc_data.filename == "updated_test_document.docx"

    result = await test_session.execute(select(Document).where(Document.id == doc_id))
    updated_doc = result.scalar_one()

    assert updated_doc.version_id == 2

    result = await test_session.execute(
        select(DocVersion)
        .where(DocVersion.doc_id == doc_id)
        .order_by(DocVersion.version_id))
    versions = result.scalars().all()

    assert len(versions) == 2
    assert versions[0].version_id == 1
    assert versions[0].filename == "test_document.docx"
    assert versions[0].s3_key == s3_key
    assert versions[1].filename == "updated_test_document.docx"
    assert versions[1].version_id == 2
    assert versions[1].s3_key == prep_update_result.s3_key
    assert versions[1].content_type == versions[0].content_type

    await del_document(test_session, doc_id, user_id)

    result = await test_session.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()

    assert document is None

    result = await test_session.execute(select(DocVersion).where(DocVersion.doc_id == doc_id))
    versions = result.scalars().all()

    assert len(versions) == 0

    with pytest.raises(ClientError):
        test_storage_client.head_object(Bucket=config.storage_bucket, Key=s3_key)
    with pytest.raises(ClientError):
        test_storage_client.head_object(Bucket=config.storage_bucket, Key=prep_update_result.s3_key)
