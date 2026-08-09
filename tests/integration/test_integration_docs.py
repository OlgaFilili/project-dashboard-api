from io import BytesIO
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError
from sqlalchemy import select

from app.config import get_config
from app.dashboard import storage
from app.dashboard.schemas import DocResponse, FileRequest, ProjectCreate
from app.dashboard.service.docs import del_document, prepare_for_update, put_document
from app.dashboard.service.projects import insert_project
from app.database.models import Document

config = get_config()


@pytest.mark.asyncio
async def test_update_and_delete_doc_success(test_session, test_user, test_storage_client, monkeypatch):
    monkeypatch.setattr(storage, "storage_client", test_storage_client)
    _, user_id = test_user

    project_data = ProjectCreate(name="Test project with doc", description="A test project for docs management check")
    project = await insert_project(test_session, project_data, user_id)

    file_content = b"Test document content"
    s3_key = str(uuid4())
    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    test_storage_client.upload_fileobj(
        Fileobj=BytesIO(file_content),
        Bucket=config.minio_bucket,
        Key=s3_key,
        ExtraArgs={"ContentType": content_type})
    response = test_storage_client.head_object(Bucket=config.minio_bucket, Key=s3_key)
    doc_data = Document(
        project_id=project.project_id,
        filename="test_document.docx",
        s3_key=s3_key,
        file_size=response['ContentLength'],
        content_type=content_type)
    test_session.add(doc_data)
    await test_session.commit()
    await test_session.refresh(doc_data)
    doc_id = doc_data.id

    result = await prepare_for_update(test_session, doc_id, user_id, content_type)

    assert result.content_type == content_type
    assert result.update_url

    updated_doc_data = await put_document(
        test_session, doc_id, user_id,
        request=FileRequest(filename="updated_test_document.docx", content_type=content_type))

    assert isinstance(updated_doc_data, DocResponse)
    assert updated_doc_data.document_id == doc_id
    assert updated_doc_data.filename == "updated_test_document.docx"

    result = await test_session.execute(select(Document).where(Document.id == doc_id))
    updated_doc = result.scalar_one()

    assert updated_doc.s3_key == s3_key
    assert updated_doc.filename == "updated_test_document.docx"

    await del_document(test_session, doc_id, user_id)

    result = await test_session.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()

    assert document is None

    with pytest.raises(ClientError):
        test_storage_client.head_object(Bucket=config.minio_bucket, Key=s3_key)
