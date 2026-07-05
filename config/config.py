import os

from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = (
    f"postgresql+asyncpg://{os.getenv('DATABASE_USER')}:"
    f"{os.getenv('DATABASE_PASSWORD')}@"
    f"{os.getenv('DATABASE_HOST')}:5432/"
    f"{os.getenv('DATABASE_NAME')}"
)

SECRET_KEY = os.getenv('SECRET_KEY')

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}