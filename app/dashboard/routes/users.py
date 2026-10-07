from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.schemas import DeletionPreview
from app.dashboard.service.security import get_current_user
from app.dashboard.service.users import del_user, deletion_preview
from app.database.db import get_session
from app.database.models import User

router = APIRouter(tags=["users"])


@router.get("/user/me/deletion-preview", response_model=DeletionPreview)
async def delete_user_preview(owner: User = Depends(get_current_user),
                              async_session: AsyncSession = Depends(get_session)):
    return await deletion_preview(async_session, owner.id)


@router.delete("/user/me", status_code=204)
async def delete_user(owner: User = Depends(get_current_user),
                      async_session: AsyncSession = Depends(get_session)):
    await del_user(async_session, owner)
