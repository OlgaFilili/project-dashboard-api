import jwt
from fastapi import Depends
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.exceptions import UnauthorizedError
from app.dashboard.repository import select_user_by_id
from app.dashboard.service.helpers import pwd_context
from config.config import SECRET_KEY
from database.db import get_session
from database.models import User

oauth2_scheme = HTTPBearer()

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


async def get_current_user(token: str = Depends(oauth2_scheme),
                           async_session: AsyncSession = Depends(get_session)) -> User:
    try:
        token = token.credentials
        token_decode = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": True})
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError()
    except jwt.InvalidTokenError:
        raise UnauthorizedError()
    user = await select_user_by_id(async_session, token_decode["user_id"])
    if not user:
        raise UnauthorizedError()
    return user
