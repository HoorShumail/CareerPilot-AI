import asyncio
import uuid
from datetime import datetime
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.agents.career.career_twin_agent import CareerTwinAgent
from src.api.dependencies import get_career_twin_service, get_current_user, get_db_session
from src.api.routes.career_twin import router as career_twin_router
from src.prompts.career_twin_prompt import build_career_twin_prompt
from src.schemas.career_profile import CareerProfileCreate, CareerProfileResponse
from src.services.career_twin_service import CareerTwinService


class DummyLLM:
    async def generate(self, prompt: str, system_prompt=None, **kwargs):
        return '{"career_summary": {"summary": "Strong backend engineer"}, "experience_level": "senior", "strongest_skills": {"skills": ["Python"]}, "weakest_skills": {"skills": ["Kafka"]}, "ai_maturity_score": 78.0, "confidence_score": 82.0, "preferred_industries": ["Fintech"], "preferred_roles": ["Backend Engineer"], "preferred_locations": ["Remote"], "salary_expectations": {"min": 180000, "max": 240000, "currency": "USD"}, "remote_preference": {"preference": "remote"}, "skills": {"mastered_skills": ["Python"], "learning_skills": ["Kafka"], "missing_skills": ["Rust"], "trending_skills": ["ML"], "obsolete_skills": []}, "strengths": {"biggest_strengths": ["Python"], "supporting_evidence": ["backend work"]}, "weaknesses": {"biggest_weaknesses": ["Cloud"], "supporting_evidence": ["limited cloud exposure"]}, "career_gap_analysis": {"missing_experience": ["cloud"], "missing_education": [], "missing_certifications": ["AWS"], "biggest_strengths": ["Python"], "biggest_weaknesses": ["Cloud"]}, "growth_summary": {"overall_growth_score": 84.0, "readiness_score": 88.0, "promotion_readiness": 79.0, "ai_career_level": "Senior"}, "learning_recommendations": {"courses": ["AWS"], "certifications": ["AWS"], "projects": ["API"], "books": ["Designing Data-Intensive Applications"]}, "learning_roadmap": {"short_term": ["AWS"], "medium_term": ["Kafka"], "long_term": ["System design"]}, "skill_intelligence": {"current_focus": ["Python"], "next_focus": ["Cloud"], "risk_signals": ["stale skills"]}}'

    async def generate_structured(self, prompt: str, response_schema=None, system_prompt=None, **kwargs):
        return response_schema.model_validate({})

    async def get_embeddings(self, texts):
        return [[0.0] * 3 for _ in texts]


def test_build_career_twin_prompt_contains_strict_json_contract():
    prompt = build_career_twin_prompt({"skills": ["Python"]}, {"applications": []})
    assert "Return STRICT JSON ONLY." in prompt
    assert "learning_recommendations" in prompt
    assert "growth_summary" in prompt


def test_career_twin_agent_parses_response():
    agent = CareerTwinAgent(DummyLLM())
    result = asyncio.run(agent.refresh_profile({"skills": ["Python"]}, {"applications": []}))
    assert isinstance(result, type(CareerProfileCreate.model_validate({"user_id": uuid.uuid4()})))


def test_career_twin_service_refresh_creates_profile(monkeypatch):
    service = CareerTwinService(DummyLLM())
    user_id = uuid.uuid4()
    fake_db = object()

    async def fake_get_user(db, id):
        return SimpleNamespace(id=id)

    async def fake_get_profile_by_user(db, user_id):
        return None

    async def fake_get_multi_by_user(db, user_id):
        return []

    async def fake_get_by_user(db, user_id):
        return []

    async def fake_get_by_resume(db, resume_id):
        return []

    async def fake_get(db, id):
        return None

    async def fake_commit():
        return None

    async def fake_refresh(obj):
        return None

    monkeypatch.setattr("src.services.career_twin_service.user_repo.get", fake_get_user)
    monkeypatch.setattr("src.services.career_twin_service.career_profile_repo.get_by_user", fake_get_profile_by_user)
    monkeypatch.setattr("src.services.career_twin_service.resume_repo.get_by_user", fake_get_multi_by_user)
    monkeypatch.setattr("src.services.career_twin_service.resume_version_repo.get_by_resume", fake_get_by_resume)
    monkeypatch.setattr("src.services.career_twin_service.application_repo.get_by_user", fake_get_by_user)
    monkeypatch.setattr("src.services.career_twin_service.job_repo.get", fake_get)
    monkeypatch.setattr("src.services.career_twin_service.match_repo.get_by_user", fake_get_by_user)

    created_profiles = []

    class FakeProfile:
        def __init__(self, **kwargs):
            self.id = uuid.uuid4()
            self.user_id = kwargs.get("user_id")
            self.career_summary = kwargs.get("career_summary")
            self.experience_level = kwargs.get("experience_level")
            self.strongest_skills = kwargs.get("strongest_skills")
            self.weakest_skills = kwargs.get("weakest_skills")
            self.ai_maturity_score = kwargs.get("ai_maturity_score")
            self.confidence_score = kwargs.get("confidence_score")
            self.preferred_industries = kwargs.get("preferred_industries")
            self.preferred_roles = kwargs.get("preferred_roles")
            self.preferred_locations = kwargs.get("preferred_locations")
            self.salary_expectations = kwargs.get("salary_expectations")
            self.remote_preference = kwargs.get("remote_preference")
            self.skills = kwargs.get("skills")
            self.experience_summary = kwargs.get("experience_summary")
            self.education_summary = kwargs.get("education_summary")
            self.strengths = kwargs.get("strengths")
            self.weaknesses = kwargs.get("weaknesses")
            self.certifications = kwargs.get("certifications")
            self.overall_readiness_score = kwargs.get("overall_readiness_score")
            self.overall_growth_score = kwargs.get("overall_growth_score")
            self.readiness_score = kwargs.get("readiness_score")
            self.promotion_readiness = kwargs.get("promotion_readiness")
            self.ai_career_level = kwargs.get("ai_career_level")
            self.growth_summary = kwargs.get("growth_summary")
            self.learning_recommendations = kwargs.get("learning_recommendations")
            self.learning_roadmap = kwargs.get("learning_roadmap")
            self.skill_intelligence = kwargs.get("skill_intelligence")
            self.career_gap_analysis = kwargs.get("career_gap_analysis")
            self.last_synced = None
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    class FakeSession:
        def __init__(self):
            self.added = []
        def add(self, obj):
            self.added.append(obj)
        async def commit(self):
            return None
        async def refresh(self, obj):
            return None

    fake_session = FakeSession()
    monkeypatch.setattr("src.services.career_twin_service.CareerProfile", FakeProfile)

    result = asyncio.run(service.refresh_profile(fake_session, user_id))
    assert isinstance(result, CareerProfileResponse)


def test_career_twin_router_endpoints():
    class FakeService:
        async def get_profile(self, db, user_id):
            return CareerProfileResponse(id=uuid.uuid4(), user_id=user_id, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        async def get_timeline(self, db, user_id):
            return []
        async def refresh_profile(self, db, user_id):
            return CareerProfileResponse(id=uuid.uuid4(), user_id=user_id, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        async def get_recommendations(self, db, user_id):
            return {"courses": []}
        async def get_strengths(self, db, user_id):
            return {"biggest_strengths": []}
        async def get_weaknesses(self, db, user_id):
            return {"biggest_weaknesses": []}
        async def get_learning_roadmap(self, db, user_id):
            return {"short_term": []}

    app = FastAPI()
    app.include_router(career_twin_router, prefix="/career-twin")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[get_db_session] = lambda: None
    app.dependency_overrides[get_career_twin_service] = lambda: FakeService()

    client = TestClient(app)
    for path in ["/career-twin/profile", "/career-twin/timeline", "/career-twin/recommendations", "/career-twin/strengths", "/career-twin/weaknesses", "/career-twin/learning-roadmap"]:
        response = client.get(path)
        assert response.status_code == 200

    refresh_response = client.post("/career-twin/refresh")
    assert refresh_response.status_code == 200
