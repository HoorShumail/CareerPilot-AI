import asyncio
import uuid
from datetime import datetime
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.agents.strategy.gap_analysis_agent import GapAnalysisAgent
from src.agents.strategy.roadmap_agent import RoadmapAgent
from src.agents.strategy.strategy_agent import StrategyAgent
from src.api.dependencies import get_career_strategy_service, get_current_user, get_db_session
from src.api.routes.career_strategy import router as career_strategy_router
from src.schemas.career_strategy import CareerStrategyCreate, CareerStrategyResponse
from src.services.career_strategy_service import CareerStrategyService


class DummyLLM:
    async def generate(self, prompt: str, system_prompt=None, **kwargs):
        return '{"gaps": [{"skill": "Python", "severity": "high", "reason": "Missing"}], "priority_skills": ["Python"], "weak_skills": [{"skill": "Kafka", "severity": "medium", "reason": "Needs practice"}], "emerging_skills": [{"skill": "ML", "severity": "medium", "reason": "Industry trend"}]}'

    async def generate_with_metadata(self, prompt: str, system_prompt=None, **kwargs):
        text = await self.generate(prompt, system_prompt, **kwargs)
        return text, {"model": "gpt-4o-mini", "finish_reason": "stop", "prompt_tokens": 100, "completion_tokens": 50}

    async def generate_structured(self, prompt: str, response_schema=None, system_prompt=None, **kwargs):
        return response_schema.model_validate({})

    async def get_embeddings(self, texts):
        return [[0.0] * 3 for _ in texts]


def test_gap_analysis_agent_parses_response():
    agent = GapAnalysisAgent(DummyLLM())
    result = asyncio.run(agent.analyze({"skills": ["Python"]}, {"jobs": []}))
    assert result.gaps
    assert result.priority_skills


def test_roadmap_agent_builds_plan():
    agent = RoadmapAgent(DummyLLM())
    result = asyncio.run(agent.build_roadmap({"gaps": [], "priority_skills": []}, {"profile": {}}, {"jobs": []}))
    assert result.roadmap
    assert result.weekly_roadmap


def test_strategy_agent_builds_strategy():
    agent = StrategyAgent(DummyLLM())
    result = asyncio.run(agent.build_strategy({"gaps": []}, {"roadmap": []}, {"profile": {}}, {"jobs": []}))
    assert result.strategy_id
    assert result.recommendations


def test_strategy_service_generates_strategy(monkeypatch):
    service = CareerStrategyService(DummyLLM())

    class FakeStrategy:
        def __init__(self, **kwargs):
            self.id = kwargs.get("id", uuid.uuid4())
            self.user_id = kwargs.get("user_id")
            self.strategy_version = kwargs.get("strategy_version", 1)
            self.generated_at = kwargs.get("generated_at", datetime.utcnow())
            self.skill_gap_analysis = kwargs.get("skill_gap_analysis")
            self.roadmap = kwargs.get("roadmap")
            self.certifications = kwargs.get("certifications")
            self.projects = kwargs.get("projects")
            self.weekly_goals = kwargs.get("weekly_goals")
            self.monthly_goals = kwargs.get("monthly_goals")
            self.progress_snapshot = kwargs.get("progress_snapshot")
            self.refresh_count = kwargs.get("refresh_count", 0)
            self.last_refreshed_at = kwargs.get("last_refreshed_at", datetime.utcnow())
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    async def fake_get_profile_by_user(db, user_id):
        return SimpleNamespace(id=uuid.uuid4(), user_id=user_id, skills={"mastered_skills": ["Python"]}, weak_skills={"skills": ["Kafka"]}, strongest_skills={}, weakest_skills={}, preferred_roles=[{"title": "Backend Engineer"}], learning_recommendations={}, career_summary={})

    async def fake_get_by_user(db, user_id):
        return []

    async def fake_get_by_resume(db, resume_id):
        return []

    async def fake_get(db, id):
        return None

    async def fake_get_by_job(db, job_id):
        return []

    async def fake_create(db, obj_in):
        return FakeStrategy(**obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in)

    async def fake_update(db, db_obj, obj_in):
        return db_obj

    monkeypatch.setattr("src.services.career_strategy_service.user_repo.get", fake_get)
    monkeypatch.setattr("src.services.career_strategy_service.career_profile_repo.get_by_user", fake_get_profile_by_user)
    monkeypatch.setattr("src.services.career_strategy_service.resume_repo.get_by_user", fake_get_by_user)
    monkeypatch.setattr("src.services.career_strategy_service.resume_version_repo.get_by_resume", fake_get_by_resume)
    monkeypatch.setattr("src.services.career_strategy_service.application_repo.get_by_user", fake_get_by_user)
    monkeypatch.setattr("src.services.career_strategy_service.job_repo.get", fake_get)
    monkeypatch.setattr("src.services.career_strategy_service.match_repo.get_by_user", fake_get_by_user)
    monkeypatch.setattr("src.services.career_strategy_service.interview_repo.get_by_user", fake_get_by_user)
    monkeypatch.setattr("src.services.career_strategy_service.career_strategy_repo.create", fake_create)
    monkeypatch.setattr("src.services.career_strategy_service.career_strategy_repo.update", fake_update)
    monkeypatch.setattr("src.services.career_strategy_service.career_strategy_progress_repo.get_by_user", fake_get_by_user)
    monkeypatch.setattr("src.services.career_strategy_service.career_strategy_progress_repo.create", fake_create)

    result = asyncio.run(service.generate_strategy(None, uuid.uuid4()))
    assert isinstance(result, CareerStrategyResponse)
    assert result.skill_gap_analysis is not None


def test_career_strategy_router_endpoints():
    class FakeService:
        async def generate_strategy(self, db, user_id):
            return CareerStrategyResponse(id=uuid.uuid4(), user_id=user_id, created_at=datetime.utcnow(), updated_at=datetime.utcnow(), strategy_version=1)
        async def get_strategy(self, db, user_id):
            return CareerStrategyResponse(id=uuid.uuid4(), user_id=user_id, created_at=datetime.utcnow(), updated_at=datetime.utcnow(), strategy_version=1)
        async def get_roadmap(self, db, user_id):
            return {"weekly_roadmap": []}
        async def get_weekly_goals(self, db, user_id):
            return []
        async def get_monthly_goals(self, db, user_id):
            return []
        async def get_certifications(self, db, user_id):
            return []
        async def get_projects(self, db, user_id):
            return []
        async def get_progress(self, db, user_id):
            return {"completed_items": 0, "progress_percent": 0.0}
        async def update_progress(self, db, user_id, payload):
            return {"status": "ok"}
        async def refresh_strategy(self, db, user_id):
            return CareerStrategyResponse(id=uuid.uuid4(), user_id=user_id, created_at=datetime.utcnow(), updated_at=datetime.utcnow(), strategy_version=2)

    app = FastAPI()
    app.include_router(career_strategy_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[get_db_session] = lambda: None
    app.dependency_overrides[get_career_strategy_service] = lambda: FakeService()

    client = TestClient(app)
    for path in [
        "/api/v1/career-strategy",
        "/api/v1/career-strategy/roadmap",
        "/api/v1/career-strategy/weekly-goals",
        "/api/v1/career-strategy/monthly-goals",
        "/api/v1/career-strategy/certifications",
        "/api/v1/career-strategy/projects",
        "/api/v1/career-strategy/progress",
    ]:
        response = client.get(path)
        assert response.status_code == 200

    generate_response = client.post("/api/v1/career-strategy/generate")
    assert generate_response.status_code == 404

    refresh_response = client.post("/api/v1/career-strategy/refresh")
    assert refresh_response.status_code == 200


def test_get_strategy_autogenerates_when_missing(monkeypatch):
    service = CareerStrategyService(DummyLLM())
    test_user_id = uuid.uuid4()

    class FakeStrategy:
        def __init__(self, **kwargs):
            self.id = kwargs.get("id", uuid.uuid4())
            self.user_id = kwargs.get("user_id", test_user_id)
            self.strategy_version = kwargs.get("strategy_version", 1)
            self.generated_at = datetime.utcnow()
            self.last_refreshed_at = datetime.utcnow()
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            self.skill_gap_analysis = {}
            self.roadmap = {}
            self.certifications = []
            self.projects = []
            self.weekly_goals = []
            self.monthly_goals = []
            self.progress_snapshot = {}
            self.refresh_count = 0

    fake_strategy = FakeStrategy(user_id=test_user_id)

    async def fake_generate_strategy(db, user_id):
        return CareerStrategyResponse.model_validate(fake_strategy)

    async def fake_get_by_user(db, user_id):
        return None

    monkeypatch.setattr(service, "generate_strategy", fake_generate_strategy)
    monkeypatch.setattr("src.services.career_strategy_service.career_strategy_repo.get_by_user", fake_get_by_user)

    result = asyncio.run(service.get_strategy(None, test_user_id))
    assert result.user_id == test_user_id