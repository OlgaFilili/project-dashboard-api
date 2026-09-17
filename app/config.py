import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    connection_string: str | None
    secret_key: str | None
    storage_endpoint: str | None
    storage_access_key: str | None
    storage_secret_key: str | None
    storage_bucket: str | None
    aws_region: str | None
    allowed_document_types: set[str]
    test_connection_string: str | None
    test_host: str | None


@lru_cache
def get_config() -> Config:
    return Config(
        connection_string=(
            f"postgresql+asyncpg://{os.getenv('DATABASE_USER')}:"
            f"{os.getenv('DATABASE_PASSWORD')}@"
            f"{os.getenv('DATABASE_HOST')}:5432/"
            f"{os.getenv('DATABASE_NAME')}"),
        secret_key=os.getenv('SECRET_KEY'),
        storage_endpoint=os.getenv("STORAGE_ENDPOINT"),
        storage_access_key=os.getenv("STORAGE_ACCESS_KEY"),
        storage_secret_key=os.getenv("STORAGE_SECRET_KEY"),
        storage_bucket=os.getenv("STORAGE_BUCKET"),
        aws_region=os.getenv("AWS_REGION"),
        allowed_document_types={
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        test_connection_string=(
            f"postgresql+asyncpg://{os.getenv('DATABASE_USER')}:"
            f"{os.getenv('DATABASE_PASSWORD')}@"
            f"{os.getenv('TEST_HOST')}:5432/"
            f"{os.getenv('TEST_DATABASE_NAME')}"),
        test_host=os.getenv("TEST_HOST")
    )
