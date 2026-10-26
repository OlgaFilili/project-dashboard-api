import logging

from botocore.response import StreamingBody
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_config
from app.dashboard.exceptions import FileMetadataMismatchError, UnsupportedFileTypeError
from app.dashboard.repository import insert_docs, select_doc_info_by_doc_id, select_document_keys_by_doc_id, update_doc
from app.dashboard.schemas import (
    DocResponse,
    DocsResponse,
    StorageRequest,
    StoragesRequest,
    UploadDocInfo,
    UploadResponse,
    UploadsRequest,
    UploadsResponse,
)
from app.dashboard.service.helpers import get_doc_or_403, get_project_or_403
from app.dashboard.storage import (
    delete_files,
    download_file,
    generate_url,
    get_file_metadata,
)
from app.dashboard.storage_models import FileUploadRequest, UploadedFileInfo
from app.database.models import DocVersion

config = get_config()
ALLOWED_DOCUMENT_TYPES = config.allowed_document_types
logger = logging.getLogger(__name__)


async def prepare_for_uploads(session: AsyncSession, project_id: int, user_id: int,
                              request: UploadsRequest) -> UploadsResponse:
    logger.info("documents_upload_started project_id=%s user_id=%s files_count=%s", project_id, user_id,
                len(request.files))
    await get_project_or_403(session, user_id, project_id)

    for file in request.files:
        if file.content_type not in ALLOWED_DOCUMENT_TYPES:
            logger.warning(
                "unsupported_file_type project_id=%s user_id=%s filename=%s content_type=%s",
                project_id, user_id, file.filename, file.content_type)
            raise UnsupportedFileTypeError()

    files_upload_request = [
        FileUploadRequest(
            filename=file.filename,
            content_type=file.content_type)
        for file in request.files]

    upload_info = [UploadResponse.model_validate(generate_url(file)) for file in files_upload_request]
    logger.info("generate_upload_url_completed files_count=%s", len(upload_info))
    return UploadsResponse(files=upload_info)


async def add_documents(session: AsyncSession, project_id: int, user_id: int,
                        request: StoragesRequest) -> DocsResponse:
    logger.info("documents_upload_continue project_id=%s user_id=%s files_count=%s",
                project_id, user_id, len(request.files))
    await get_project_or_403(session, user_id, project_id)
    uploaded_files = []
    for file in request.files:
        metadata = get_file_metadata(file.s3_key)
        uploaded_files.append(UploadedFileInfo(
            filename=file.filename,
            s3_key=file.s3_key,
            file_size=metadata.file_size,
            content_type=metadata.content_type,
        ))
    logger.info("upload_to_storage_completed files_count=%s", len(uploaded_files))

    docs_data = [
        UploadDocInfo(
            filename=file.filename,
            s3_key=file.s3_key,
            size=file.file_size,
            content_type=file.content_type,
        )
        for file in uploaded_files]

    result = await insert_docs(session, project_id, docs_data)
    logger.info("document_upload_finished project_id=%s docs_created=%s", project_id, len(result))
    return DocsResponse(documents=[DocResponse.model_validate(d) for d in result])


async def get_document(session: AsyncSession, document_id: int, user_id: int) -> tuple[StreamingBody, DocVersion]:
    logger.info("document_download_started document_id=%s user_id=%s", document_id, user_id)
    doc = await get_doc_or_403(session, user_id, document_id)
    document_s3_key = doc.s3_key
    file = download_file(document_s3_key)
    logger.info("document_download_finished document_id=%s user_id=%s", document_id, user_id)
    return file, doc


async def del_document(session: AsyncSession, document_id: int, user_id: int) -> None:
    logger.info("document_delete_started document_id=%s user_id=%s", document_id, user_id)
    await get_doc_or_403(session, user_id, document_id)
    document_s3_keys = await select_document_keys_by_doc_id(session, document_id)
    doc_info = await select_doc_info_by_doc_id(session, document_id)
    await session.delete(doc_info)
    await session.commit()
    delete_files(document_s3_keys)
    logger.info("document_delete_finished document_id=%s", document_id)


async def prepare_for_update(session: AsyncSession, document_id: int, user_id: int) -> UploadResponse:
    logger.info("document_update_started document_id=%s user_id=%s", document_id, user_id)
    doc = await get_doc_or_403(session, user_id, document_id)
    file_update_request = FileUploadRequest(filename=doc.filename, content_type=doc.content_type)
    update_info = UploadResponse.model_validate(generate_url(request=file_update_request))
    logger.info("generate_update_url_completed for document_id=%s filename=%s", document_id, doc.filename)
    return update_info


async def put_document(session: AsyncSession, document_id: int, user_id: int, request: StorageRequest) -> DocResponse:
    logger.info("document_update_continue document_id=%s user_id=%s", document_id, user_id)
    doc = await get_doc_or_403(session, user_id, document_id)
    metadata = get_file_metadata(request.s3_key)
    if metadata.content_type != doc.content_type:
        logger.warning("document_update_rejected_due_to_content_type_mismatch "
                       "filename=%s expected=%s stored=%s",
                       request.filename, doc.content_type, metadata.content_type)
        raise FileMetadataMismatchError()
    logger.info("document_storage_metadata_verified document_id=%s", document_id)
    updated_doc = DocVersion(
        doc_id=document_id,
        version_id=doc.version_id + 1,
        filename=request.filename,
        s3_key=request.s3_key,
        file_size=metadata.file_size,
        content_type=metadata.content_type
    )
    updated_doc = await update_doc(session, updated_doc)
    logger.info("document_update_finished document_id=%s filename=%s", document_id, doc.filename)
    return DocResponse.model_validate(updated_doc)
