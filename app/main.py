import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.dashboard.exceptions import UnauthorizedError
from app.dashboard.routes.routes_auth import router as auth_router
from app.dashboard.routes.routes_docs import router as docs_router
from app.dashboard.routes.routes_projects import router
from app.logging_config import setup_logging

from database.db import init_db
from object_storage.client import init_storage

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_storage()
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(_request: Request, _exc: UnauthorizedError):
    return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception path=%s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


app.include_router(router)
app.include_router(auth_router)
app.include_router(docs_router)
