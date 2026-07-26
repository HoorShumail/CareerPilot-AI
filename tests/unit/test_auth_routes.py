import uuid
from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient
from src.api.main import app
from src.api.routes import auth as auth_routes

client = TestClient(app)


def make_user():
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashedpassword",
        full_name="Test User",
        avatar_url=None,
        preferences={"theme": "dark"},
        role="user",
        email_verified=False,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def test_register_route(monkeypatch):
    async def fake_get_db_session():
        class DummySession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        yield DummySession()

    async def fake_register_user(self, user_in):
        return make_user()

    monkeypatch.setattr("src.api.routes.auth.get_db_session", fake_get_db_session)
    monkeypatch.setattr("src.api.routes.auth.AuthService.register_user", fake_register_user)

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert response.json()["preferences"] == {"theme": "dark"}


def test_login_route(monkeypatch):
    async def fake_get_db_session():
        class DummySession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        yield DummySession()

    async def fake_authenticate_user(self, email, password):
        return {
            "access_token": "access",
            "refresh_token": "refresh",
            "token_type": "bearer",
        }

    monkeypatch.setattr("src.api.routes.auth.get_db_session", fake_get_db_session)
    monkeypatch.setattr("src.api.routes.auth.AuthService.authenticate_user", fake_authenticate_user)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access"
    assert response.json()["refresh_token"] == "refresh"


def test_me_route(monkeypatch):
    async def fake_current_user():
        return make_user()

    monkeypatch.setitem(app.dependency_overrides, auth_routes.get_current_user, fake_current_user)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
