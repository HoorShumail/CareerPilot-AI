import pytest
from fastapi import HTTPException
from types import SimpleNamespace

from src.schemas.user import UserCreate
from src.services.auth_service import AuthService
from src.utils.security import get_password_hash
from src.db.models.user import User


class DummyAsyncSession:
    def __init__(self):
        self.added = []
        self.committed = False

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        return None


@pytest.fixture
def dummy_db():
    return DummyAsyncSession()


@pytest.mark.asyncio
async def test_register_user_success(monkeypatch, dummy_db):
    async def fake_get_by_email(db, email: str):
        return None

    monkeypatch.setattr(
        "src.services.auth_service.user_repo.get_by_email",
        fake_get_by_email,
    )

    service = AuthService(dummy_db)
    user_in = UserCreate(email="test@example.com", password="password123")
    user = await service.register_user(user_in)

    assert user.email == "test@example.com"
    assert hasattr(user, "password_hash")
    assert user.password_hash != "password123"
    assert dummy_db.committed


@pytest.mark.asyncio
async def test_register_user_conflict(monkeypatch, dummy_db):
    async def fake_get_by_email(db, email: str):
        return User(email=email, password_hash=get_password_hash("password"))

    monkeypatch.setattr(
        "src.services.auth_service.user_repo.get_by_email",
        fake_get_by_email,
    )

    service = AuthService(dummy_db)
    user_in = UserCreate(email="test@example.com", password="password123")

    with pytest.raises(HTTPException) as exc_info:
        await service.register_user(user_in)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_authenticate_user_success(monkeypatch, dummy_db):
    password = "password123"
    stored_user = User(
        email="test@example.com",
        password_hash=get_password_hash(password),
        is_active=True,
    )

    async def fake_get_by_email(db, email: str):
        return stored_user

    monkeypatch.setattr(
        "src.services.auth_service.user_repo.get_by_email",
        fake_get_by_email,
    )

    service = AuthService(dummy_db)
    token_data = await service.authenticate_user("test@example.com", password)

    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_authenticate_user_invalid_credentials(monkeypatch, dummy_db):
    async def fake_get_by_email(db, email: str):
        return None

    monkeypatch.setattr(
        "src.services.auth_service.user_repo.get_by_email",
        fake_get_by_email,
    )

    service = AuthService(dummy_db)

    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate_user("test@example.com", "wrongpassword")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_authenticate_user_inactive(monkeypatch, dummy_db):
    stored_user = User(
        email="test@example.com",
        password_hash=get_password_hash("password"),
        is_active=False,
    )

    async def fake_get_by_email(db, email: str):
        return stored_user

    monkeypatch.setattr(
        "src.services.auth_service.user_repo.get_by_email",
        fake_get_by_email,
    )

    service = AuthService(dummy_db)

    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate_user("test@example.com", "password")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_ensure_superuser_creates_admin(monkeypatch, dummy_db):
    async def fake_get_by_email(db, email: str):
        return None

    monkeypatch.setattr(
        "src.services.auth_service.user_repo.get_by_email",
        fake_get_by_email,
    )

    monkeypatch.setattr(
        "src.services.auth_service.settings",
        SimpleNamespace(
            FIRST_SUPERUSER="admin@example.com",
            FIRST_SUPERUSER_PASSWORD="adminpass",
        ),
    )

    service = AuthService(dummy_db)
    await service.ensure_superuser()

    assert len(dummy_db.added) == 1

    admin_user = dummy_db.added[0]

    assert admin_user.email == "admin@example.com"
    assert admin_user.role == "admin"
    assert admin_user.email_verified is True
    assert admin_user.is_active is True
    assert dummy_db.committed is True


@pytest.mark.asyncio
async def test_ensure_superuser_skips_existing_admin(monkeypatch, dummy_db):
    async def fake_get_by_email(db, email: str):
        return User(
            email=email,
            password_hash="hashedpass",
            role="admin",
        )

    monkeypatch.setattr(
        "src.services.auth_service.user_repo.get_by_email",
        fake_get_by_email,
    )

    monkeypatch.setattr(
        "src.services.auth_service.settings",
        SimpleNamespace(
            FIRST_SUPERUSER="admin@example.com",
            FIRST_SUPERUSER_PASSWORD="adminpass",
        ),
    )

    service = AuthService(dummy_db)
    await service.ensure_superuser()

    assert len(dummy_db.added) == 0