import boto3
from botocore.exceptions import ClientError

from app.config import get_config

config = get_config()

storage_client = boto3.client(
    service_name="s3",
    endpoint_url=f"http://{config.storage_endpoint}",
    aws_access_key_id=config.storage_access_key,
    aws_secret_access_key=config.storage_secret_key,)


async def init_storage():
    try:
        storage_client.head_bucket(Bucket=config.storage_bucket)

    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]

        if error_code in ("404", "NoSuchBucket"):
            storage_client.create_bucket(Bucket=config.storage_bucket)
        else:
            raise
