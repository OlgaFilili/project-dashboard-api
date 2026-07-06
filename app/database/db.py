from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os
from app.config.config import CONNECTION_STRING
from app.database.models import Base

engine = create_async_engine(CONNECTION_STRING)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
