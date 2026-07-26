import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.career.career_coach_agent import CareerCoachAgent
from src.agents.career.career_forecast_agent import CareerForecastAgent
from src.agents.career.learning_planner_agent import LearningPlannerAgent
from src.agents.career.market_intelligence_agent import MarketIntelligenceAgent
from src.db.repositories.application_repo import application_repo
from src.db.repositories.career_profile_repo import career_profile_repo
from src.db.repositories.job_repo import job_repo
from src.db.repositories.match_repo import match_repo
from src.db.repositories.resume_repo import resume_repo, resume_version_repo
from src.db.repositories.user_repo import user_repo
from src.infrastructure.llm.provider import LLMProvider
from src.schemas.career_intelligence import CoachChatRequest, CoachChatResponse, ForecastResponse, LearningPlanResponse, MarketIntelligenceResponse, SimulationRequest, SimulationResponse

logger = logging.getLogger("careerpilot.career_intelligence_service")


class CareerForecastService:
    def __init__(self, llm_provider: LLMProvider, agent: Optional[CareerForecastAgent] = None):
        self.agent = agent or CareerForecastAgent(llm_provider)

    async def build_forecast(self, db: AsyncSession, user_id: UUID) -> ForecastResponse:
        profile = await career_profile_repo.get_by_user(db, user_id=str(user_id))
        profile_payload = {"career_profile": profile.__dict__} if profile else {"career_profile": {"user_id": str(user_id)}}

        context_payload = await self._build_context(db, user_id)
        return await self.agent.generate_forecast(profile_payload, context_payload)

    async def _build_context(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        resumes = await resume_repo.get_by_user(db, user_id=str(user_id))
        resume_versions = []
        for resume in resumes:
            versions = await resume_version_repo.get_by_resume(db, resume_id=str(resume.id))
            resume_versions.extend(versions)
        applications = await application_repo.get_by_user(db, user_id=str(user_id))
        jobs = []
        for application in applications:
            job = await job_repo.get(db, id=application.job_id)
            if job:
                jobs.append(job)
        matches = await match_repo.get_by_user(db, user_id=str(user_id))
        return {"resumes": [r.__dict__ for r in resumes], "resume_versions": [rv.__dict__ for rv in resume_versions], "applications": [a.__dict__ for a in applications], "jobs": [j.__dict__ for j in jobs], "matches": [m.__dict__ for m in matches]}


class CareerCoachService:
    def __init__(self, llm_provider: LLMProvider, agent: Optional[CareerCoachAgent] = None):
        self.agent = agent or CareerCoachAgent(llm_provider)
        self._history: Dict[UUID, List[Dict[str, Any]]] = {}

    async def generate_chat(self, db: AsyncSession, user_id: UUID, message: str, conversation_id: Optional[UUID] = None) -> CoachChatResponse:
        profile = await career_profile_repo.get_by_user(db, user_id=str(user_id))
        profile_payload = {"career_profile": profile.__dict__} if profile else {"career_profile": {"user_id": str(user_id)}}

        history = self._history.get(conversation_id or user_id, [])
        history.append({"role": "user", "message": message})
        context_payload = await self._build_context(db, user_id)
        response = await self.agent.generate_chat_response(profile_payload, context_payload, history)
        history.append({"role": "assistant", "message": response.message})
        self._history[conversation_id or user_id] = history
        return response

    async def advice(self, db: AsyncSession, user_id: UUID, question: str, conversation_id: Optional[UUID] = None) -> CoachChatResponse:
        return await self.generate_chat(db, user_id, question, conversation_id)

    async def action_plan(self, db: AsyncSession, user_id: UUID, goal: str, conversation_id: Optional[UUID] = None) -> CoachChatResponse:
        return await self.generate_chat(db, user_id, f"Create an action plan for: {goal}", conversation_id)

    async def goals(self, db: AsyncSession, user_id: UUID, goals: List[str], conversation_id: Optional[UUID] = None) -> CoachChatResponse:
        return await self.generate_chat(db, user_id, f"Set goals: {', '.join(goals)}", conversation_id)

    async def _build_context(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        resumes = await resume_repo.get_by_user(db, user_id=str(user_id))
        resume_versions = []
        for resume in resumes:
            versions = await resume_version_repo.get_by_resume(db, resume_id=str(resume.id))
            resume_versions.extend(versions)
        applications = await application_repo.get_by_user(db, user_id=str(user_id))
        jobs = []
        for application in applications:
            job = await job_repo.get(db, id=application.job_id)
            if job:
                jobs.append(job)
        matches = await match_repo.get_by_user(db, user_id=str(user_id))
        return {"resumes": [r.__dict__ for r in resumes], "resume_versions": [rv.__dict__ for rv in resume_versions], "applications": [a.__dict__ for a in applications], "jobs": [j.__dict__ for j in jobs], "matches": [m.__dict__ for m in matches]}


class MarketIntelligenceService:
    def __init__(self, llm_provider: LLMProvider, agent: Optional[MarketIntelligenceAgent] = None):
        self.agent = agent or MarketIntelligenceAgent(llm_provider)

    async def build_market_intelligence(self, db: AsyncSession, user_id: UUID) -> MarketIntelligenceResponse:
        profile = await career_profile_repo.get_by_user(db, user_id=str(user_id))
        profile_payload = {"career_profile": profile.__dict__} if profile else {"career_profile": {"user_id": str(user_id)}}
        context_payload = await self._build_context(db, user_id)
        return await self.agent.generate_market_intelligence(profile_payload, context_payload)

    async def _build_context(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        jobs = []
        all_jobs = await job_repo.get_by_user(db, user_id=str(user_id))
        jobs.extend(all_jobs)
        matches = await match_repo.get_by_user(db, user_id=str(user_id))
        return {"jobs": [j.__dict__ for j in jobs], "matches": [m.__dict__ for m in matches]}


class LearningPlannerService:
    def __init__(self, llm_provider: LLMProvider, agent: Optional[LearningPlannerAgent] = None):
        self.agent = agent or LearningPlannerAgent(llm_provider)

    async def build_learning_plan(self, db: AsyncSession, user_id: UUID) -> LearningPlanResponse:
        profile = await career_profile_repo.get_by_user(db, user_id=str(user_id))
        profile_payload = {"career_profile": profile.__dict__} if profile else {"career_profile": {"user_id": str(user_id)}}
        context_payload = await self._build_context(db, user_id)
        return await self.agent.generate_learning_plan(profile_payload, context_payload)

    async def _build_context(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        resumes = await resume_repo.get_by_user(db, user_id=str(user_id))
        resume_versions = []
        for resume in resumes:
            versions = await resume_version_repo.get_by_resume(db, resume_id=str(resume.id))
            resume_versions.extend(versions)
        applications = await application_repo.get_by_user(db, user_id=str(user_id))
        jobs = []
        for application in applications:
            job = await job_repo.get(db, id=application.job_id)
            if job:
                jobs.append(job)
        matches = await match_repo.get_by_user(db, user_id=str(user_id))
        return {"resumes": [r.__dict__ for r in resumes], "resume_versions": [rv.__dict__ for rv in resume_versions], "applications": [a.__dict__ for a in applications], "jobs": [j.__dict__ for j in jobs], "matches": [m.__dict__ for m in matches]}
