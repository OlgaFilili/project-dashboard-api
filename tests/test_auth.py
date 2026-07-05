import jwt
import pytest
from datetime import datetime
from fastapi.security import HTTPAuthorizationCredentials


from app.dashboard.schemas import UserRegister, UserLogin
from app.dashboard.service import insert_user, get_token, get_current_user
from app.dashboard.exceptions import PasswordsMismatchError, UserAlreadyExistsError, InvalidCredentialsError, \
    UnauthorizedError
from config.config import SECRET_KEY


@pytest.mark.asyncio
async def test_insert_user_success(sample_user, monkeypatch):
    async def fake_select_user_by_username(*args, **kwargs):
        return None

    async def fake_add_new_user(*args, **kwargs):
        return sample_user

    monkeypatch.setattr(
        "app.dashboard.service.select_user_by_username",
        fake_select_user_by_username)

    monkeypatch.setattr(
        "app.dashboard.service.add_new_user",
        fake_add_new_user)

    user = UserRegister(
        login="Olga",
        password="123",
        repeat_password="123")

    result = await insert_user(None, user)

    assert result.login == "Olga"
    assert result.user_id == 1
    assert result.created_at == datetime(2026, 6, 1, 10, 0, 0)


@pytest.mark.asyncio
async def test_insert_user_passwords_mismatch():
    user = UserRegister(
        login="Olga",
        password="l23",
        repeat_password="123")
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
        fake_select_user_by_username)
    user = UserRegister(
        login="Olga",
        password="123",
        repeat_password="123")
    with pytest.raises(UserAlreadyExistsError):
        await insert_user(None, user)


@pytest.mark.asyncio
async def test_get_token_success(sample_user, monkeypatch):
    async def fake_select_user_by_username(*args, **kwargs):
        return sample_user

    def fake_verify_password(*args, **kwargs):
        return True

    monkeypatch.setattr(
        "app.dashboard.service.select_user_by_username",
        fake_select_user_by_username)
    monkeypatch.setattr(
        "app.dashboard.service.verify_password",
        fake_verify_password)

    user = UserLogin(
        login="Olga",
        password="123")

    result = await get_token(None, user)

    payload = jwt.decode(result, SECRET_KEY, algorithms=["HS256"])

    assert payload["user_id"] == 1
    assert "exp" in payload


@pytest.mark.asyncio
async def test_get_token_invalid_login(monkeypatch):
    async def fake_select_user_by_username(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.dashboard.service.select_user_by_username",
        fake_select_user_by_username)

    user = UserLogin(
        login="Olga",
        password="123")

    with pytest.raises(InvalidCredentialsError):
        await get_token(None, user)


@pytest.mark.asyncio
async def test_get_token_invalid_token(sample_user, monkeypatch):
    async def fake_select_user_by_username(*args, **kwargs):
        return sample_user

    def fake_verify_password(*args, **kwargs):
        return False

    monkeypatch.setattr(
        "app.dashboard.service.select_user_by_username",
        fake_select_user_by_username)
    monkeypatch.setattr(
        "app.dashboard.service.verify_password",
        fake_verify_password)

    user = UserLogin(
        login="Olga",
        password="123")

    with pytest.raises(InvalidCredentialsError):
        await get_token(None, user)


@pytest.mark.asyncio
async def test_get_current_user_success(sample_user, monkeypatch):
    async def fake_select_user_by_id(*args, **kwargs):
        return sample_user

    monkeypatch.setattr(
        "app.dashboard.service.select_user_by_id",
        fake_select_user_by_id)
    payload = {
        "user_id": 1,
        "exp": datetime(2099, 1, 1, 0, 0, 0)}
    access_token= jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=access_token)
    result = await get_current_user(credentials, None)

    assert result is sample_user

@pytest.mark.asyncio
async def test_get_current_user_no_user(monkeypatch):
    async def fake_select_user_by_id(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.dashboard.service.select_user_by_id",
        fake_select_user_by_id)
    payload = {
        "user_id": 10,
        "exp": datetime(2099, 1, 1, 0, 0, 0)}
    access_token= jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=access_token)

    with pytest.raises(UnauthorizedError):
        await get_current_user(credentials, None)

@pytest.mark.asyncio
async def test_get_current_user_expired_token(monkeypatch):
    payload = {
        "user_id": 1,
        "exp": datetime(2000, 1, 1, 0, 0, 0)}
    access_token= jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=access_token)
    with pytest.raises(UnauthorizedError):
        await get_current_user(credentials, None)

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(monkeypatch):
    access_token= "invalid_token"
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=access_token)

    with pytest.raises(UnauthorizedError):
        await get_current_user(credentials, None)
