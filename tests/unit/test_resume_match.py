import uuid
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.agents.job.job_matcher_agent import JobMatcherAgent
from src.api.dependencies import (
    get_current_user,
    get_db_session,
    get_resume_match_service,
)
from src.api.routes.matches import router as matches_router
from src.prompts.job_match_prompt import build_job_match_prompt
from src.schemas.match import MatchComparisonResponse, MatchResponse
from src.services.resume_match_service import ResumeMatchService


class DummyLLM:
    async def generate(self, prompt: str, system_prompt=None, **kwargs):
        return '{"overall_match_score": 88.0, "ats_score": 90.0, "matched_skills": ["Python"], "missing_skills": ["Kafka"], "missing_technologies": ["Redis"], "missing_certifications": ["AWS"], "experience_gap": {"summary": "3 years"}, "education_gap": {"summary": "None"}, "strength_analysis": {"summary": "Strong backend"}, "weakness_analysis": {"summary": "Needs cloud exposure"}, "priority_learning_roadmap": {"topics": ["Kafka"]}, "resume_improvements": {"recommendations": ["Highlight backend work"]}, "estimated_match_after_learning": 93.0, "interview_preparation": {"topics": ["System design"]}, "final_recommendation": {"summary": "Apply"}}'

    async def generate_structured(
        self,
        prompt: str,
        response_schema=None,
        system_prompt=None,
        **kwargs,
    ):
        return response_schema.model_validate({})

    async def get_embeddings(self, texts):
        return [[0.0] * 3 for _ in texts]


def test_build_job_match_prompt_contains_strict_json_contract():
    prompt = build_job_match_prompt(
        {"content": {"skills": ["Python"]}},
        {"title": "Backend Engineer"},
    )

    assert "Return STRICT JSON ONLY." in prompt
    assert "overall_match_score" in prompt
    assert "ats_score" in prompt
    assert "final_recommendation" in prompt


def test_job_matcher_agent_parses_resume_to_job_response():
    agent = JobMatcherAgent(DummyLLM())

    import asyncio

    result = asyncio.run(
        agent.compare_resume_job(
            {"content": {"skills": ["Python"]}},
            {"title": "Backend Engineer"},
        )
    )

    assert isinstance(result, MatchComparisonResponse)
    assert result.overall_match_score == 88.0
    assert result.ats_score == 90.0
    assert result.matched_skills["Python"] is True


def test_resume_match_service_creates_match_record(monkeypatch):
    service = ResumeMatchService(DummyLLM())

    fake_db = object()

    user_id = uuid.uuid4()
    resume_version_id = uuid.uuid4()
    job_id = uuid.uuid4()
    resume_id = uuid.uuid4()

    # ✅ Fixed: resume_version now includes created_at/updated_at
    resume_version = SimpleNamespace(
        id=resume_version_id,
        resume_id=resume_id,
        content={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    resume = SimpleNamespace(
        id=resume_id,
        user_id=user_id,
    )

    # ✅ Fixed: job now includes all required fields for JobResponse
    job = SimpleNamespace(
        id=job_id,
        user_id=user_id,
        title="AI Engineer",
        company="Google",
        is_remote=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    async def fake_get_resume_version(db, id):
        return resume_version

    async def fake_get_resume(db, id):
        return resume

    async def fake_get_job(db, id):
        return job

    monkeypatch.setattr(
        "src.services.resume_match_service.resume_version_repo.get",
        fake_get_resume_version,
    )

    monkeypatch.setattr(
        "src.services.resume_match_service.resume_repo.get",
        fake_get_resume,
    )

    monkeypatch.setattr(
        "src.services.resume_match_service.job_repo.get",
        fake_get_job,
    )

    created_match = None

    async def fake_create(db, *, obj_in):
        nonlocal created_match
        created_match = obj_in

        return SimpleNamespace(
            id=uuid.uuid4(),
            user_id=user_id,
            resume_version_id=resume_version_id,
            job_id=job_id,
            overall_match_score=88.0,
            ats_score=90.0,
            matched_skills={"Python": True},
            missing_skills={"Kafka": True},
            missing_technologies={"Redis": True},
            missing_certifications={"AWS": True},
            experience_gap={"summary": "3 years"},
            education_gap={"summary": "None"},
            strength_analysis={"summary": "Strong backend"},
            weakness_analysis={"summary": "Needs cloud exposure"},
            priority_learning_roadmap={"topics": ["Kafka"]},
            resume_improvements={"recommendations": ["Highlight backend work"]},
            estimated_match_after_learning=93.0,
            interview_preparation={"topics": ["System design"]},
            final_recommendation={"summary": "Apply"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    monkeypatch.setattr(
        "src.services.resume_match_service.match_repo.create",
        fake_create,
    )

    import asyncio

    result = asyncio.run(
        service.compare_resume_to_job(
            fake_db,
            user_id,
            resume_version_id,
            job_id,
        )
    )

    assert isinstance(result, MatchResponse)
    assert result.overall_match_score == 88.0
    assert created_match.user_id == user_id


def test_matches_router_comparison_endpoint(monkeypatch):
    class FakeService:
        async def compare_resume_to_job(
            self,
            db,
            user_id,
            resume_version_id,
            job_id,
        ):
            return MatchResponse(
                id=uuid.uuid4(),
                user_id=user_id,
                resume_version_id=resume_version_id,
                job_id=job_id,
                overall_match_score=84.0,
                ats_score=86.0,
                matched_skills={"Python": True},
                missing_skills={},
                missing_technologies={},
                missing_certifications={},
                experience_gap={},
                education_gap={},
                strength_analysis={},
                weakness_analysis={},
                priority_learning_roadmap={},
                resume_improvements={},
                estimated_match_after_learning=89.0,
                interview_preparation={},
                final_recommendation={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

    app = FastAPI()

    app.include_router(matches_router, prefix="/matches")

    app.dependency_overrides[get_current_user] = (
        lambda: SimpleNamespace(id=uuid.uuid4())
    )

    async def override_db():
        yield object()

    app.dependency_overrides[get_db_session] = override_db

    async def override_service():
        return FakeService()

    app.dependency_overrides[get_resume_match_service] = override_service

    client = TestClient(app)

    response = client.post(
        "/matches/compare",
        json={
            "resume_version_id": str(uuid.uuid4()),
            "job_id": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 200
    assert response.json()["overall_match_score"] == 84.0