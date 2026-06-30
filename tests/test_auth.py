import pytest
from datetime import datetime

from app.dashboard.schemas import UserRegister
from app.dashboard.service import insert_user
from app.dashboard.exceptions import PasswordsMismatchError, UserAlreadyExistsError
from database.models import User


@pytest.mark.asyncio
async def test_insert_user_success(monkeypatch):
    async def fake_select_user_by_username(*args, **kwargs):
        return None

    async def fake_add_new_user(*args, **kwargs):
        return User(
            id=1,
            username="Olga",
            password_hash="fake_hash",
            created_at=datetime(2026, 6, 1, 12, 0, 0)
        )

    monkeypatch.setattr(
        "app.dashboard.service.select_user_by_username",
        fake_select_user_by_username
    )

    monkeypatch.setattr(
        "app.dashboard.service.add_new_user",
        fake_add_new_user
    )

    user = UserRegister(
        login="Olga",
        password="123",
        repeat_password="123"
    )

    result = await insert_user(None, user)

    assert result.login == "Olga"
    assert result.user_id == 1
    assert result.created_at == datetime(2026, 6, 1, 12, 0, 0)


@pytest.mark.asyncio
async def test_insert_user_passwords_mismatch():
    user = UserRegister(
        login="Olga",
        password="l23",
        repeat_password="123"
    )
    with pytest.raises(PasswordsMismatchError):
        await insert_user(None, user)


class ExistingUser:
    pass


@pytest.mark.asyncio
async def test_insert_user_user_exists(monkeypatch):
    async def fake_select_user_by_username(*args, **kwargs):
        return ExistingUser()

    monkeypatch.setattr(
        "app.dashboard.service.select_user_by_username",
        fake_select_user_by_username
    )
    user = UserRegister(
        login="Olga",
        password="123",
        repeat_password="123"
    )
    with pytest.raises(UserAlreadyExistsError):
        await insert_user(None, user)
