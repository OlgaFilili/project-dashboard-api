from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.dashboard.routes import router
from database.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)