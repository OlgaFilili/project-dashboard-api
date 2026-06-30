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
