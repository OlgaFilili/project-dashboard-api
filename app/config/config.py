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

MINIO_BUCKET = os.getenv("MINIO_BUCKET")
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}
