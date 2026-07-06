import boto3
from botocore.exceptions import ClientError

from app.config.config import MINIO_ENDPOINT, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, MINIO_BUCKET

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
