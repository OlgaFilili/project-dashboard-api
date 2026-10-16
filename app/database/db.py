from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_config

config = get_config()
CONNECTION_STRING = config.connection_string
engine = create_async_engine(CONNECTION_STRING)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
