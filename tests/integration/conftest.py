import uuid

import boto3
import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_config
from app.dashboard.service.helpers import hash_password
from app.database.models import Base, Member, User

config = get_config()

test_engine = create_async_engine(config.test_connection_string)
TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def test_session():
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture
def test_storage_client():
    return boto3.client(
        service_name="s3",
        endpoint_url=f"http://{config.test_host}:9000",
        aws_access_key_id=config.minio_root_user,
        aws_secret_access_key=config.minio_root_password)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest_asyncio.fixture(scope="session")
async def test_user():
    async with TestSessionLocal() as session:
        test_username = "Test User 1"

        result = await session.execute(select(User).where(User.username == test_username))
        user = result.scalar_one_or_none()

        if user is None:
            hashed_password = hash_password("Test_password")
            user = User(
                username=test_username,
                password_hash=hashed_password)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user.username, user.id

@pytest_asyncio.fixture()
async def test_user_2():
    async with TestSessionLocal() as session:
        test_username = f"Test User 2 {uuid.uuid4()}"

        result = await session.execute(select(User).where(User.username == test_username))
        user = result.scalar_one_or_none()

        if user is None:
            hashed_password = hash_password("Test_password")
            user = User(
                username=test_username,
                password_hash=hashed_password)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        yield user.username, user.id

        await session.execute(delete(Member).where(Member.user_id == user.id))
        await session.delete(user)
        await session.commit()



