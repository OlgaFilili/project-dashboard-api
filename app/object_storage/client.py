import boto3
from botocore.exceptions import ClientError

from app.config import get_config

config = get_config()
MINIO_BUCKET = config.minio_bucket
MINIO_ENDPOINT = config.minio_endpoint
MINIO_ROOT_USER = config.minio_root_user
MINIO_ROOT_PASSWORD = config.minio_root_password

storage_client = boto3.client(
    service_name="s3",
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ROOT_USER,
    aws_secret_access_key=MINIO_ROOT_PASSWORD)


async def init_storage():
    try:
        storage_client.head_bucket(Bucket=MINIO_BUCKET)

    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]

        if error_code in ("404", "NoSuchBucket"):
            storage_client.create_bucket(Bucket=MINIO_BUCKET)
        else:
            raise
