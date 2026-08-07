import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    connection_string: str | None
    secret_key: str | None
    minio_endpoint: str | None
    minio_root_user: str | None
    minio_root_password: str | None
    minio_bucket: str | None
    allowed_document_types: set[str]


@lru_cache
def get_config() -> Config:
    return Config(
        connection_string=(
            f"postgresql+asyncpg://{os.getenv('DATABASE_USER')}:"
            f"{os.getenv('DATABASE_PASSWORD')}@"
            f"{os.getenv('DATABASE_HOST')}:5432/"
            f"{os.getenv('DATABASE_NAME')}"
        ),
        secret_key=os.getenv('SECRET_KEY'),
        minio_endpoint=os.getenv("MINIO_ENDPOINT"),
        minio_root_user=os.getenv("MINIO_ROOT_USER"),
        minio_root_password=os.getenv("MINIO_ROOT_PASSWORD"),
        minio_bucket=os.getenv("MINIO_BUCKET"),
        allowed_document_types={
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
    )
