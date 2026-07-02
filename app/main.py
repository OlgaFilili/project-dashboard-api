from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.dashboard.exceptions import UnauthorizedError
from app.dashboard.routes import router
from app.dashboard.routes_auth import router as auth_router
from database.db import init_db
from object_storage.client import init_storage


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_storage()
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(_request: Request, _exc: UnauthorizedError):
    return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})


app.include_router(router)
app.include_router(auth_router)
