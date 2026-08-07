import logging
from uuid import uuid4

from botocore.exceptions import ClientError
from botocore.response import StreamingBody

from app.config import get_config
from app.dashboard.exceptions import StorageError, UploadedFileNotFoundError
from app.dashboard.storage_models import FileMetadata, FileUpdateRequest, FileUploadRequest, UploadInfo
from app.object_storage.client import storage_client

config = get_config()
MINIO_BUCKET = config.minio_bucket
logger = logging.getLogger(__name__)


def generate_upload_url(request: FileUploadRequest) -> UploadInfo:
    s3_key = str(uuid4())
    try:
        upload_url = storage_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': MINIO_BUCKET, 'Key': s3_key, 'ContentType': request.content_type},
            ExpiresIn=3600)
    except ClientError:
        logger.exception("storage_generate_upload_url_failed filename=%s", request.filename)
        raise StorageError()
    return UploadInfo(
        filename=request.filename,
        s3_key=s3_key,
        upload_url=upload_url,
        content_type=request.content_type)


def get_file_metadata(s3_key: str) -> FileMetadata:
    try:
        response = storage_client.head_object(Bucket=MINIO_BUCKET, Key=s3_key)
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]

        if error_code in ("404", "NoSuchKey", "NotFound"):
            logger.warning("uploaded_file_not_found s3_key=%s", s3_key)
            raise UploadedFileNotFoundError()

        logger.exception("storage_metadata_check_failed s3_key=%s", s3_key)
        raise StorageError()

    return FileMetadata(
        file_size=response["ContentLength"],
        content_type=response["ContentType"])


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


def generate_update_url(request: FileUpdateRequest) -> str:
    try:
        update_url = storage_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': MINIO_BUCKET, 'Key': request.s3_key, 'ContentType': request.content_type},
            ExpiresIn=3600)
    except ClientError:
        logger.exception("storage_generate_update_url_failed s3_key=%s", request.s3_key)
        raise StorageError()
    return update_url


def delete_files(s3_keys: list[str]):
    try:
        response = storage_client.delete_objects(
            Bucket=MINIO_BUCKET,
            Delete={"Objects": [{"Key": key} for key in s3_keys]})
        if response.get("Errors"):
            logger.error("Some files were not deleted: %s", response["Errors"])
            raise StorageError()
    except ClientError:
        logger.exception("storage_batch_delete_failed keys=%s", s3_keys)
        raise StorageError()
