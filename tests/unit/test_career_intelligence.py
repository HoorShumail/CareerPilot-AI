import asyncio
import uuid
from datetime import datetime
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.agents.career.career_forecast_agent import CareerForecastAgent
from src.agents.career.career_coach_agent import CareerCoachAgent
from src.agents.career.market_intelligence_agent import MarketIntelligenceAgent
from src.agents.career.learning_planner_agent import LearningPlannerAgent
from src.api.dependencies import get_career_coach_service, get_career_forecast_service, get_current_user, get_db_session, get_learning_planner_service, get_market_intelligence_service
from src.api.routes.career_intelligence import router as career_intelligence_router
from src.schemas.career_intelligence import ForecastResponse, CoachChatResponse, MarketIntelligenceResponse, LearningPlanResponse
from src.services.career_intelligence_service import CareerForecastService, CareerCoachService, LearningPlannerService, MarketIntelligenceService


class DummyLLM:
    async def generate(self, prompt: str, system_prompt=None, **kwargs):
        return '{"forecast": {"horizon": "6 months", "predicted_job_titles": ["AI Engineer"], "salary_projection": {"min": 140000, "max": 180000, "currency": "USD"}, "hiring_probability": 0.74, "promotion_probability": 0.6, "career_trajectory": "upward", "confidence_score": 0.81, "estimated_timeline": "6 months"}, "coach_response": {"message": "Keep building Python and cloud skills.", "action_items": ["Take a cloud course"], "confidence": 0.8}, "market_summary": {"demanded_skills": ["Python"], "trends": ["AI"], "top_certifications": ["AWS"], "top_frameworks": ["FastAPI"]}, "learning_plan": {"daily": ["Practice Python"], "weekly": ["Build a project"], "monthly": ["Get certified"], "quarterly": ["Ship an MVP"], "yearly": ["Lead a team"]}}'

    async def generate_structured(self, prompt: str, response_schema=None, system_prompt=None, **kwargs):
        return response_schema.model_validate({})

    async def get_embeddings(self, texts):
        return [[0.0] * 3 for _ in texts]


def test_forecast_agent_parses_response():
    agent = CareerForecastAgent(DummyLLM())
    result = asyncio.run(agent.generate_forecast({"skills": ["Python"]}, {"applications": []}))
    assert isinstance(result, ForecastResponse)


def test_coach_agent_parses_response():
    agent = CareerCoachAgent(DummyLLM())
    result = asyncio.run(agent.generate_chat_response({"skills": ["Python"]}, {"applications": []}, {"history": []}))
    assert isinstance(result, CoachChatResponse)


def test_market_and_learning_agents_parse_response():
    market_agent = MarketIntelligenceAgent(DummyLLM())
    learning_agent = LearningPlannerAgent(DummyLLM())
    market_result = asyncio.run(market_agent.generate_market_intelligence({"skills": ["Python"]}, {"jobs": []}))
    learning_result = asyncio.run(learning_agent.generate_learning_plan({"skills": ["Python"]}, {"applications": []}))
    assert isinstance(market_result, MarketIntelligenceResponse)
    assert isinstance(learning_result, LearningPlanResponse)


def test_services_and_router_endpoints():
    forecast_service = CareerForecastService(DummyLLM())
    coach_service = CareerCoachService(DummyLLM())
    market_service = MarketIntelligenceService(DummyLLM())
    learning_service = LearningPlannerService(DummyLLM())

    async def fake_get_profile_by_user(db, user_id):
        return None

    class FakeSession:
        def add(self, obj):
            return None

        async def commit(self):
            return None

        async def refresh(self, obj):
            return None

    async def fake_get_user(db, id):
        return SimpleNamespace(id=id)

    async def fake_empty_get_by_user(db, user_id):
        return []

    import src.services.career_intelligence_service as career_module
    career_module.career_profile_repo.get_by_user = fake_get_profile_by_user
    career_module.user_repo.get = fake_get_user
    career_module.resume_repo.get_by_user = fake_empty_get_by_user
    career_module.resume_version_repo.get_by_resume = fake_empty_get_by_user
    career_module.application_repo.get_by_user = fake_empty_get_by_user
    career_module.job_repo.get = fake_empty_get_by_user
    career_module.match_repo.get_by_user = fake_empty_get_by_user
    career_module.job_repo.get_by_user = fake_empty_get_by_user

    forecast = asyncio.run(forecast_service.build_forecast(FakeSession(), uuid.uuid4()))
    coach = asyncio.run(coach_service.generate_chat(FakeSession(), uuid.uuid4(), "How should I grow?"))
    market = asyncio.run(market_service.build_market_intelligence(FakeSession(), uuid.uuid4()))
    learning = asyncio.run(learning_service.build_learning_plan(FakeSession(), uuid.uuid4()))

    assert isinstance(forecast, ForecastResponse)
    assert isinstance(coach, CoachChatResponse)
    assert isinstance(market, MarketIntelligenceResponse)
    assert isinstance(learning, LearningPlanResponse)

    app = FastAPI()
    app.include_router(career_intelligence_router, prefix="/career-coach")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[get_db_session] = lambda: None
    app.dependency_overrides[get_career_forecast_service] = lambda: forecast_service
    app.dependency_overrides[get_career_coach_service] = lambda: coach_service
    app.dependency_overrides[get_market_intelligence_service] = lambda: market_service
    app.dependency_overrides[get_learning_planner_service] = lambda: learning_service

    client = TestClient(app)
    response = client.post("/career-coach/chat", json={"message": "hello"})
    assert response.status_code == 200
