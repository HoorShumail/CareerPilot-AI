
import io
import json
import uuid
from datetime import date, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient
from src.api.main import app
from src.api.routes import application as application_routes
from src.api.routes import job as job_routes

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


def make_job():
    return {
        "id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "title": "DevOps Engineer",
        "company": "ExampleCorp",
        "url": "https://example.com/job/1",
        "raw_description": "Test job description",
        "required_skills": {"required_skills": ["Docker", "Kubernetes"]},
        "preferred_skills": {"preferred_skills": ["Terraform"]},
        "experience_level": "Mid",
        "salary_range": "100000-120000",
        "location": "Remote",
        "is_remote": True,
        "ai_summary": {"headline": "Exciting cloud role"},
        "ats_keywords": {"keywords": ["Docker", "Kubernetes"]},
        "hidden_requirements": {"details": "Team player"},
        "interview_focus": {"topics": ["architecture"]},
        "missing_certifications": {"notes": "None"},
        "red_flags": {"concerns": "None"},
        "extracted_keywords": {"keywords": ["CI/CD"]},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


def make_application(job_id, resume_version_id):
    return {
        "id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "job_id": job_id,
        "resume_version_id": resume_version_id,
        "status": "saved",
        "applied_date": date.today().isoformat(),
        "match_score": 82.5,
        "skills_match": {"matched": ["Docker"]},
        "gap_analysis": {"summary": "Some gaps"},
        "notes": {"content": "Follow up after applying."},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


def test_create_job_text_route(monkeypatch):
    async def fake_create_job_from_text(self, db, user_id, raw_description, title, company, url=None):
        job = make_job()
        job["title"] = title
        job["company"] = company
        job["raw_description"] = raw_description
        return SimpleNamespace(**job)

    async def fake_current_user():
        return make_user()

    monkeypatch.setitem(app.dependency_overrides, job_routes.get_current_user, fake_current_user)
    monkeypatch.setattr("src.api.routes.job.get_db_session", lambda: None)
    monkeypatch.setattr("src.api.routes.job.JobService.create_job_from_text", fake_create_job_from_text)

    response = client.post(
        "/api/v1/jobs/",
        json={
            "title": "DevOps Engineer",
            "company": "ExampleCorp",
            "raw_description": "A detailed description",
        },
    )

    assert response.status_code == 201
    assert response.json()["title"] == "DevOps Engineer"
    assert response.json()["company"] == "ExampleCorp"


def test_upload_job_pdf_route(monkeypatch):
    async def fake_create_job_from_pdf(self, db, user_id, file_bytes, content_type, title, company, url=None):
        job = make_job()
        job["title"] = title
        job["company"] = company
        return SimpleNamespace(**job)

    async def fake_current_user():
        return make_user()

    monkeypatch.setitem(app.dependency_overrides, job_routes.get_current_user, fake_current_user)
    monkeypatch.setattr("src.api.routes.job.get_db_session", lambda: None)
    monkeypatch.setattr("src.api.routes.job.JobService.create_job_from_pdf", fake_create_job_from_pdf)

    response = client.post(
        "/api/v1/jobs/",
        files={"file": ("job.pdf", b"PDF-BYTES", "application/pdf")},
        data={"title": "DevOps Engineer", "company": "ExampleCorp"},
    )

    assert response.status_code == 201
    assert response.json()["title"] == "DevOps Engineer"


def test_list_jobs_route(monkeypatch):
    async def fake_list_jobs(self, db, user_id):
        return [SimpleNamespace(**make_job())]

    async def fake_current_user():
        return make_user()

    monkeypatch.setitem(app.dependency_overrides, job_routes.get_current_user, fake_current_user)
    monkeypatch.setattr("src.api.routes.job.get_db_session", lambda: None)
    monkeypatch.setattr("src.api.routes.job.JobService.list_jobs", fake_list_jobs)

    response = client.get("/api/v1/jobs/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["company"] == "ExampleCorp"


def test_refresh_job_insights_route(monkeypatch):
    async def fake_refresh_job_insights(self, db, user_id, job_id):
        return SimpleNamespace(**make_job())

    async def fake_current_user():
        return make_user()

    job_id = str(uuid.uuid4())
    monkeypatch.setitem(app.dependency_overrides, job_routes.get_current_user, fake_current_user)
    monkeypatch.setattr("src.api.routes.job.get_db_session", lambda: None)
    monkeypatch.setattr("src.api.routes.job.JobService.refresh_job_insights", fake_refresh_job_insights)

    response = client.post(f"/api/v1/jobs/{job_id}/insights")

    assert response.status_code == 200
    assert response.json()["company"] == "ExampleCorp"


def test_create_application_route(monkeypatch):
    async def fake_create_application(self, db, user_id, job_id, resume_version_id, status, applied_date=None):
        app_data = make_application(job_id, resume_version_id)
        app_data["job_id"] = job_id
        app_data["resume_version_id"] = resume_version_id
        return SimpleNamespace(**app_data)

    async def fake_current_user():
        return make_user()

    monkeypatch.setitem(app.dependency_overrides, application_routes.get_current_user, fake_current_user)
    monkeypatch.setattr("src.api.routes.application.get_db_session", lambda: None)
    monkeypatch.setattr("src.api.routes.application.ApplicationService.create_application", fake_create_application)

    response = client.post(
        "/api/v1/applications/",
        json={
            "job_id": str(uuid.uuid4()),
            "resume_version_id": str(uuid.uuid4()),
            "status": "saved",
            "applied_date": date.today().isoformat(),
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "saved"


def test_refresh_application_match_route(monkeypatch):
    async def fake_refresh_match(self, db, user_id, application_id):
        return SimpleNamespace(**make_application(str(uuid.uuid4()), str(uuid.uuid4())))

    async def fake_current_user():
        return make_user()

    application_id = str(uuid.uuid4())
    monkeypatch.setitem(app.dependency_overrides, application_routes.get_current_user, fake_current_user)
    monkeypatch.setattr("src.api.routes.application.get_db_session", lambda: None)
    monkeypatch.setattr("src.api.routes.application.ApplicationService.refresh_match", fake_refresh_match)

    response = client.post(f"/api/v1/applications/{application_id}/match")

    assert response.status_code == 200
    assert "match_score" in response.json()


def test_job_route_not_found_returns_404(monkeypatch):
    async def fake_get_job(self, db, user_id, job_id):
        raise ValueError("Job not found")

    async def fake_current_user():
        return make_user()

    job_id = str(uuid.uuid4())
    monkeypatch.setitem(app.dependency_overrides, job_routes.get_current_user, fake_current_user)
    monkeypatch.setattr("src.api.routes.job.get_db_session", lambda: None)
    monkeypatch.setattr("src.api.routes.job.JobService.get_job", fake_get_job)

    response = client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_application_route_not_found_returns_404(monkeypatch):
    async def fake_get_application(self, db, user_id, application_id):
        raise ValueError("Application not found")

    async def fake_current_user():
        return make_user()

    application_id = str(uuid.uuid4())
    monkeypatch.setitem(app.dependency_overrides, application_routes.get_current_user, fake_current_user)
    monkeypatch.setattr("src.api.routes.application.get_db_session", lambda: None)
    monkeypatch.setattr("src.api.routes.application.ApplicationService.get_application", fake_get_application)

    response = client.get(f"/api/v1/applications/{application_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"
