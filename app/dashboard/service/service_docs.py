import logging

from botocore.response import StreamingBody
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.config import ALLOWED_DOCUMENT_TYPES
from app.dashboard.exceptions import UnsupportedFileTypeError
from app.dashboard.repository import insert_docs
from app.dashboard.schemas import DocResponse, DocsResponse
from app.dashboard.service.helpers import get_doc_or_403, get_project_or_403
from app.dashboard.storage import delete_file, download_file, update_file, upload_file
from app.dashboard.storage_models import FileToUpdate, FileToUpload
from app.database.models import Document

logger = logging.getLogger(__name__)


async def add_documents(session: AsyncSession, project_id: int, user_id: int,
                        files: list[UploadFile]) -> DocsResponse:
    logger.info("documents_upload_started project_id=%s user_id=%s files_count=%s", project_id, user_id, len(files))
    await get_project_or_403(session, user_id, project_id)

    for file in files:
        if file.content_type not in ALLOWED_DOCUMENT_TYPES:
            logger.warning(
                "unsupported_file_type project_id=%s user_id=%s filename=%s content_type=%s",
                project_id, user_id, file.filename, file.content_type)
            raise UnsupportedFileTypeError()

    files_to_upload = [
        FileToUpload(
            filename=file.filename,
            content_type=file.content_type,
            file_size=file.size,
            stream=file.file)
        for file in files]

    uploaded_files = [upload_file(file) for file in files_to_upload]
    logger.info("upload_to_storage_completed files_count=%s", len(uploaded_files))

    docs_data = [
        Document(
            project_id=project_id,
            filename=file.filename,
            s3_key=file.s3_key,
            file_size=file.file_size,
            content_type=file.content_type,
        )
        for file in uploaded_files]

    result = await insert_docs(session, docs_data)
    logger.info("document_upload_finished project_id=%s docs_created=%s", project_id, len(result))
    return DocsResponse(documents=[DocResponse.model_validate(d) for d in result])


async def get_document(session: AsyncSession, document_id: int, user_id: int) -> tuple[StreamingBody, Document]:
    logger.info("document_download_started document_id=%s user_id=%s", document_id, user_id)
    doc = await get_doc_or_403(session, user_id, document_id)
    document_s3_key = doc.s3_key
    file = download_file(document_s3_key)
    logger.info("document_download_finished document_id=%s user_id=%s", document_id, user_id)
    return file, doc


async def del_document(session: AsyncSession, document_id: int, user_id: int) -> None:
    logger.info("document_delete_started document_id=%s user_id=%s", document_id, user_id)
    doc = await get_doc_or_403(session, user_id, document_id)
    document_s3_key = doc.s3_key
    delete_file(document_s3_key)
    await session.delete(doc)
    await session.commit()
    logger.info("document_delete_finished document_id=%s", document_id)


async def put_document(session: AsyncSession, document_id: int, user_id: int, file: UploadFile) -> DocResponse:
    logger.info("document_update_started document_id=%s user_id=%s", document_id, user_id)
    doc = await get_doc_or_403(session, user_id, document_id)
    if file.content_type not in ALLOWED_DOCUMENT_TYPES:
        logger.warning(
            "unsupported_file_type user_id=%s filename=%s content_type=%s",
            user_id, file.filename, file.content_type)
        raise UnsupportedFileTypeError()
    file_to_update = FileToUpdate(
        filename=file.filename,
        s3_key=doc.s3_key,
        content_type=file.content_type,
        stream=file.file)
    # id, project_id, s3_key, uploaded_at stay the same
    update_file(file_to_update)
    logger.info("document_storage_update_done document_id=%s", document_id)
    doc.filename = file.filename
    doc.file_size = file.size
    doc.content_type = file.content_type

    await session.commit()
    await session.refresh(doc)
    logger.info("document_update_finished document_id=%s filename=%s", document_id, file.filename)
    return DocResponse.model_validate(doc)
