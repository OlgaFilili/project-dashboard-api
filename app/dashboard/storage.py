import logging
from uuid import uuid4

from botocore.exceptions import ClientError
from botocore.response import StreamingBody

from app.config.config import MINIO_BUCKET
from app.dashboard.exceptions import StorageError
from app.dashboard.storage_models import FileToUpdate, FileToUpload, UploadedFileInfo
from app.object_storage.client import storage_client

logger = logging.getLogger(__name__)


def upload_file(file: FileToUpload) -> UploadedFileInfo:
    s3_key = str(uuid4())
    try:
        storage_client.upload_fileobj(
            Fileobj=file.stream,
            Bucket=MINIO_BUCKET,
            Key=s3_key,
            ExtraArgs={"ContentType": file.content_type})
    except ClientError:
        logger.exception("storage_upload_failed filename=%s", file.filename)
        raise StorageError()

    return UploadedFileInfo(
        filename=file.filename,
        s3_key=s3_key,
        content_type=file.content_type,
        file_size=file.file_size)


def download_file(s3_key: str) -> StreamingBody:
    try:
        response = storage_client.get_object(Bucket=MINIO_BUCKET, Key=s3_key)
    except ClientError:
        logger.exception("storage_download_failed s3_key=%s", s3_key)
        raise StorageError()
    return response["Body"]


def delete_file(s3_key: str):
    try:
        storage_client.delete_object(Bucket=MINIO_BUCKET, Key=s3_key)
    except ClientError:
        logger.exception("storage_delete_failed s3_key=%s", s3_key)
        raise StorageError()


def update_file(file: FileToUpdate):
    try:
        storage_client.upload_fileobj(
            Fileobj=file.stream,
            Bucket=MINIO_BUCKET,
            Key=file.s3_key,
            ExtraArgs={"ContentType": file.content_type})
    except ClientError:
        logger.exception("storage_update_failed filename=%s", file.filename)
        raise StorageError()
