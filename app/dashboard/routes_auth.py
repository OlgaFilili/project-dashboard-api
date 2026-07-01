from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from app.dashboard.exceptions import PasswordsMismatchError, UserAlreadyExistsError, InvalidCredentialsError
from app.dashboard.service import insert_user, get_token
from app.dashboard.schemas import UserRegister, UserResponse, UserLogin

router = APIRouter(tags=["users"])


@router.post("/auth", response_model=UserResponse, status_code=201)
async def create_user(creds: UserRegister, async_session: AsyncSession = Depends(get_session)):
    try:
        return await insert_user(async_session, creds)
    except PasswordsMismatchError:
        raise HTTPException(status_code=422, detail="Passwords do not match")
    except UserAlreadyExistsError:
        raise HTTPException(status_code=409, detail="User already exists")

@router.post("/login")
async def login(creds: UserLogin, async_session: AsyncSession = Depends(get_session)):
    try:
        return await get_token(async_session, creds)
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
