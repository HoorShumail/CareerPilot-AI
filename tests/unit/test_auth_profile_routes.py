import uuid
from datetime import datetime

from fastapi.testclient import TestClient
from src.api.main import app
from src.api.routes import auth as auth_routes
from src.db.models.user import User

client = TestClient(app)


def make_user():
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashedpassword",
        full_name="Test User",
        avatar_url="https://example.com/avatar.png",
        preferences={"theme": "dark"},
        role="user",
        email_verified=True,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def test_update_profile_route(monkeypatch):
    async def fake_current_user():
        return make_user()

    async def fake_get_db_session():
        class DummySession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        yield DummySession()

    async def fake_update_user_profile(self, user, user_in):
        user.full_name = user_in.full_name
        user.avatar_url = user_in.avatar_url
        return user

    monkeypatch.setitem(app.dependency_overrides, auth_routes.get_current_user, fake_current_user)
    monkeypatch.setattr("src.api.routes.auth.get_db_session", fake_get_db_session)
    monkeypatch.setattr("src.api.routes.auth.AuthService.update_user_profile", fake_update_user_profile)

    response = client.put(
        "/api/v1/auth/me",
        json={"full_name": "Updated Name", "avatar_url": "https://example.com/new.png"},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"
    assert response.json()["avatar_url"] == "https://example.com/new.png"
