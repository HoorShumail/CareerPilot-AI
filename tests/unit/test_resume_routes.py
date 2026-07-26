import uuid
from datetime import datetime
from types import SimpleNamespace
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.routes import resume as resume_routes

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
        email_verified=True,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def make_resume():
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        original_filename="resume.pdf",
        file_path="uploads/resumes/resume.pdf",
        file_type="application/pdf",
        parsed_content={"name": "Test User", "email": "test@example.com"},
        is_primary=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def make_version(resume_id):
    return SimpleNamespace(
        id=uuid.uuid4(),
        resume_id=resume_id,
        content={"name": "Test User"},
        source_description="Initial upload",
        version_type="upload",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def test_list_resume_versions_owner_check(monkeypatch):
    async def fake_get_user_resumes(self, db, user_id):
        resume = make_resume()
        resume.id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        return [resume]

    async def fake_get_resume_versions(self, db, resume_id):
        return [make_version(resume_id)]

    async def fake_current_user():
        return make_user()

    monkeypatch.setattr("src.api.routes.resume.get_db_session", lambda: None)
    monkeypatch.setitem(app.dependency_overrides, resume_routes.get_current_user, fake_current_user)
    monkeypatch.setattr("src.api.routes.resume.ResumeService.get_user_resumes", fake_get_user_resumes)
    monkeypatch.setattr("src.api.routes.resume.ResumeService.get_resume_versions", fake_get_resume_versions)

    response = client.get("/api/v1/resumes/11111111-1111-1111-1111-111111111111/versions")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["version_type"] == "upload"


def test_list_resume_versions_not_found(monkeypatch):
    async def fake_get_user_resumes(self, db, user_id):
        return []

    async def fake_current_user():
        return make_user()

    monkeypatch.setattr("src.api.routes.resume.get_db_session", lambda: None)
    monkeypatch.setitem(app.dependency_overrides, resume_routes.get_current_user, fake_current_user)
    monkeypatch.setattr("src.api.routes.resume.ResumeService.get_user_resumes", fake_get_user_resumes)

    response = client.get("/api/v1/resumes/11111111-1111-1111-1111-111111111111/versions")
    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"
