import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.strategy.gap_analysis_agent import GapAnalysisAgent
from src.agents.strategy.roadmap_agent import RoadmapAgent
from src.agents.strategy.strategy_agent import StrategyAgent
from src.db.models.career_strategy import CareerStrategy, CareerStrategyProgress
from src.db.repositories.application_repo import application_repo
from src.db.repositories.career_profile_repo import career_profile_repo
from src.db.repositories.career_strategy_repo import career_strategy_progress_repo, career_strategy_repo
from src.db.repositories.interview_repo import interview_repo
from src.db.repositories.job_repo import job_repo
from src.db.repositories.match_repo import match_repo
from src.db.repositories.resume_repo import resume_repo, resume_version_repo
from src.db.repositories.user_repo import user_repo
from src.infrastructure.llm.provider import LLMProvider
from src.schemas.career_strategy import CareerStrategyCreate, CareerStrategyProgressCreate, CareerStrategyProgressResponse, CareerStrategyResponse, CareerStrategyUpdate
from src.utils.token_counter import estimate_tokens

logger = logging.getLogger("careerpilot.career_strategy_service")


class CareerStrategyService:
    def __init__(self, llm_provider: LLMProvider, agent: Optional[StrategyAgent] = None):
        self.llm_provider = llm_provider
        self.gap_agent = GapAnalysisAgent(llm_provider)
        self.roadmap_agent = RoadmapAgent(llm_provider)
        self.agent = agent or StrategyAgent(llm_provider)

    async def _ensure_strategy(self, db: AsyncSession, user_id: UUID) -> CareerStrategy:
        logger.info("[TRACE] Loading strategy for user_id=%s", user_id)
        strategy = await career_strategy_repo.get_by_user(db, user_id=user_id)
        strategy_found = strategy is not None
        logger.info("[TRACE] Strategy found: %s", strategy_found)

        if not strategy:
            logger.info("[TRACE] Generating initial strategy for user_id=%s...", user_id)
            response = await self.generate_strategy(db, user_id)
            if db is not None:
                strategy = await career_strategy_repo.get_by_user(db, user_id=user_id)
                if not strategy:
                    strategy = await career_strategy_repo.get(db, id=response.id)
            else:
                strategy = response

        return strategy

    async def generate_strategy(self, db: AsyncSession, user_id: UUID) -> CareerStrategyResponse:
        total_start = time.perf_counter()
        logger.info("[TRACE] Entered generate_strategy() for user_id=%s", user_id)

        if db is not None:
            user = await user_repo.get(db, id=user_id)
            if not user:
                raise ValueError("User not found")

        profile = await career_profile_repo.get_by_user(db, user_id=user_id)
        profile_payload = {"career_profile": self._sanitize_profile(profile, user_id)}
        context_payload = await self._build_context(db, user_id)

        logger.info("[TRACE] Executing GapAnalysisAgent...")
        gap_analysis = await self.gap_agent.analyze(profile_payload, context_payload)

        logger.info("[TRACE] Executing RoadmapAgent...")
        roadmap_plan = await self.roadmap_agent.build_roadmap(gap_analysis.model_dump(), profile_payload, context_payload)

        logger.info("[TRACE] Executing StrategyAgent...")
        strategy_payload = await self.agent.build_strategy(gap_analysis.model_dump(), roadmap_plan.model_dump(), profile_payload, context_payload)

        strategy_data = strategy_payload.model_dump(exclude_unset=True, exclude={"strategy_id", "recommendations"})
        strategy_data["user_id"] = user_id
        strategy_data.setdefault("refresh_count", 0)
        strategy_data.setdefault("strategy_version", 1)
        strategy_data.setdefault("generated_at", datetime.utcnow())
        strategy_data.setdefault("last_refreshed_at", datetime.utcnow())

        logger.info("[TRACE] Saving new career strategy row to DB...")
        strategy = await career_strategy_repo.create(db, obj_in=CareerStrategyCreate(**strategy_data))

        existing_progress = await career_strategy_progress_repo.get_by_user(db, user_id=user_id)
        if not existing_progress:
            progress_payload = {
                "user_id": user_id,
                "strategy_id": strategy.id,
                "completed_skills": [],
                "completed_certifications": [],
                "completed_projects": [],
                "progress_percent": 0.0,
                "goal_completion": {"weekly": 0.0, "monthly": 0.0},
                "milestone_status": {},
            }
            logger.info("[TRACE] Creating initial career_strategy_progress row...")
            await career_strategy_progress_repo.create(db, obj_in=CareerStrategyProgressCreate(**progress_payload))

        total_duration_s = time.perf_counter() - total_start
        logger.info(
            "[PERF] Career Strategy Pipeline completed | user_id=%s | total_duration=%.3fs",
            user_id,
            total_duration_s,
        )
        return CareerStrategyResponse.model_validate(strategy)

    async def get_strategy(self, db: AsyncSession, user_id: UUID) -> CareerStrategyResponse:
        logger.info("[TRACE] Entered get_strategy() for user_id=%s", user_id)
        strategy = await self._ensure_strategy(db, user_id)
        return CareerStrategyResponse.model_validate(strategy)

    async def get_roadmap(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        logger.info("[TRACE] Entered get_roadmap() for user_id=%s", user_id)
        strategy = await self._ensure_strategy(db, user_id)
        return strategy.roadmap or {}

    async def get_weekly_goals(self, db: AsyncSession, user_id: UUID) -> List[Dict[str, Any]]:
        logger.info("[TRACE] Entered get_weekly_goals() for user_id=%s", user_id)
        strategy = await self._ensure_strategy(db, user_id)
        return strategy.weekly_goals or []

    async def get_monthly_goals(self, db: AsyncSession, user_id: UUID) -> List[Dict[str, Any]]:
        logger.info("[TRACE] Entered get_monthly_goals() for user_id=%s", user_id)
        strategy = await self._ensure_strategy(db, user_id)
        return strategy.monthly_goals or []

    async def get_certifications(self, db: AsyncSession, user_id: UUID) -> List[Dict[str, Any]]:
        logger.info("[TRACE] Entered get_certifications() for user_id=%s", user_id)
        strategy = await self._ensure_strategy(db, user_id)
        return strategy.certifications or []

    async def get_projects(self, db: AsyncSession, user_id: UUID) -> List[Dict[str, Any]]:
        logger.info("[TRACE] Entered get_projects() for user_id=%s", user_id)
        strategy = await self._ensure_strategy(db, user_id)
        return strategy.projects or []

    async def get_progress(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        logger.info("[TRACE] Entered get_progress() for user_id=%s", user_id)
        progress_entries = await career_strategy_progress_repo.get_by_user(db, user_id=user_id)
        if not progress_entries:
            logger.info("[TRACE] No progress entries found. Ensuring strategy created...")
            await self._ensure_strategy(db, user_id)
            progress_entries = await career_strategy_progress_repo.get_by_user(db, user_id=user_id)

        if not progress_entries:
            return {
                "completed_skills": [],
                "completed_certifications": [],
                "completed_projects": [],
                "progress_percent": 0.0,
                "goal_completion": {"weekly": 0.0, "monthly": 0.0},
                "milestone_status": {},
            }

        latest = progress_entries[-1]
        return {
            "completed_skills": latest.completed_skills or [],
            "completed_certifications": latest.completed_certifications or [],
            "completed_projects": latest.completed_projects or [],
            "progress_percent": latest.progress_percent or 0.0,
            "goal_completion": latest.goal_completion or {},
            "milestone_status": latest.milestone_status or {},
        }

    async def update_progress(self, db: AsyncSession, user_id: UUID, payload: CareerStrategyProgressCreate) -> CareerStrategyProgressResponse:
        logger.info("[TRACE] Entered update_progress() for user_id=%s", user_id)
        progress_entries = await career_strategy_progress_repo.get_by_user(db, user_id=user_id)
        if not progress_entries:
            logger.info("[TRACE] Progress entries missing. Ensuring strategy...")
            await self._ensure_strategy(db, user_id)
            progress_entries = await career_strategy_progress_repo.get_by_user(db, user_id=user_id)

        if not progress_entries:
            raise ValueError("Unable to initialize career strategy progress")

        latest = progress_entries[-1]
        update_data = payload.model_dump(exclude_unset=True)
        update_data.setdefault("user_id", user_id)
        update_data.setdefault("strategy_id", latest.strategy_id)
        updated = await career_strategy_progress_repo.update(db, db_obj=latest, obj_in=CareerStrategyProgressCreate(**update_data))
        return CareerStrategyProgressResponse.model_validate(updated)

    async def refresh_strategy(self, db: AsyncSession, user_id: UUID) -> CareerStrategyResponse:
        total_start = time.perf_counter()
        logger.info("[TRACE] Entered refresh_strategy() for user_id=%s", user_id)
        logger.info("[TRACE] Loading strategy...")

        strategy = await career_strategy_repo.get_by_user(db, user_id=user_id)
        strategy_found = strategy is not None
        logger.info("[TRACE] Strategy found: %s", strategy_found)

        if not strategy:
            logger.info("[TRACE] Generating initial strategy...")
            response = await self.generate_strategy(db, user_id)
            total_duration_s = time.perf_counter() - total_start
            logger.info(
                "[PERF] Refresh Strategy Pipeline completed | user_id=%s | total_duration=%.3fs",
                user_id,
                total_duration_s,
            )
            return response

        logger.info("[TRACE] Regenerating strategy in-place for existing strategy_id=%s...", strategy.id)
        profile = await career_profile_repo.get_by_user(db, user_id=user_id)
        profile_payload = {"career_profile": self._sanitize_profile(profile, user_id)}
        context_payload = await self._build_context(db, user_id)

        gap_analysis = await self.gap_agent.analyze(profile_payload, context_payload)
        roadmap_plan = await self.roadmap_agent.build_roadmap(gap_analysis.model_dump(), profile_payload, context_payload)
        strategy_payload = await self.agent.build_strategy(gap_analysis.model_dump(), roadmap_plan.model_dump(), profile_payload, context_payload)

        update_data = {
            "skill_gap_analysis": strategy_payload.skill_gap_analysis,
            "roadmap": strategy_payload.roadmap,
            "certifications": strategy_payload.certifications,
            "projects": strategy_payload.projects,
            "weekly_goals": strategy_payload.weekly_goals,
            "monthly_goals": strategy_payload.monthly_goals,
            "progress_snapshot": strategy_payload.progress_snapshot,
            "strategy_version": (strategy.strategy_version or 1) + 1,
            "refresh_count": (strategy.refresh_count or 0) + 1,
            "last_refreshed_at": datetime.utcnow(),
        }

        logger.info("[TRACE] Saving updated strategy in-place...")
        updated = await career_strategy_repo.update(db, db_obj=strategy, obj_in=CareerStrategyUpdate(**update_data))
        total_duration_s = time.perf_counter() - total_start
        logger.info(
            "[PERF] Refresh Strategy Pipeline completed | user_id=%s | total_duration=%.3fs",
            user_id,
            total_duration_s,
        )
        return CareerStrategyResponse.model_validate(updated)

    def _sanitize_profile(self, profile: Any, user_id: UUID) -> Dict[str, Any]:
        """Builds a lightweight profile summary containing only essential fields (no raw model dumps)."""
        if not profile:
            return {
                "top_skills": [],
                "career_goals": ["Career advancement"],
                "experience_summary": "Standard level",
                "education_summary": "No education data",
                "certifications": [],
                "completed_projects": [],
            }

        # Extract skills safely
        top_skills_raw = (getattr(profile, "strongest_skills", None) or getattr(profile, "skills", None) or [])
        top_skills = []
        if isinstance(top_skills_raw, list):
            top_skills = top_skills_raw
        elif isinstance(top_skills_raw, dict):
            # Extract lists of skills from dict values (e.g. {"mastered_skills": ["Python"]})
            for val in top_skills_raw.values():
                if isinstance(val, list):
                    top_skills.extend(val)
                elif isinstance(val, str):
                    top_skills.append(val)
        
        top_skills = list(set(top_skills))[:20]

        preferred_roles = getattr(profile, "preferred_roles", None) or []
        summary = getattr(profile, "career_summary", None) or ""
        career_goals = preferred_roles if isinstance(preferred_roles, list) and preferred_roles else [summary] if summary else ["Career advancement"]

        experience_summary = getattr(profile, "experience_summary", None) or getattr(profile, "experience_level", None) or "Standard level"
        education_summary = getattr(profile, "education_summary", None) or "No education data"

        certs = getattr(profile, "certifications", None) or []
        if isinstance(certs, dict):
            # If certs is a dict, extract values or keys
            cert_list = []
            for k, v in certs.items():
                if isinstance(v, list):
                    cert_list.extend(v)
                elif isinstance(v, str):
                    cert_list.append(v)
            certs = cert_list
        if not isinstance(certs, list):
            certs = []

        github_data = getattr(profile, "github_data", None) or {}
        projects = github_data.get("top_repos", []) if isinstance(github_data, dict) else []

        return {
            "top_skills": top_skills,
            "career_goals": career_goals,
            "experience_summary": experience_summary,
            "education_summary": education_summary,
            "certifications": certs[:10],
            "completed_projects": projects[:10],
        }

    async def _build_context(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        """
        Builds a lightweight context object containing top skills, missing skills,
        current match score, and roadmap summary. Never sends full resume content, JDs, or match objects.
        """
        start_time = time.perf_counter()

        top_skills = set()
        missing_skills = set()
        scores = []

        if db is not None:
            applications, matches, interviews = await asyncio.gather(
                application_repo.get_by_user(db, user_id=user_id),
                match_repo.get_by_user(db, user_id=user_id),
                interview_repo.get_by_user(db, user_id=user_id),
            )
            for m in matches[:5]:
                if getattr(m, "overall_match_score", None) is not None:
                    scores.append(m.overall_match_score)
                if getattr(m, "matched_skills", None) and isinstance(m.matched_skills, list):
                    top_skills.update(m.matched_skills[:10])
                if getattr(m, "missing_skills", None) and isinstance(m.missing_skills, list):
                    missing_skills.update(m.missing_skills[:10])

        current_match_score = round(sum(scores) / len(scores), 2) if scores else None

        existing_strategy = await career_strategy_repo.get_by_user(db, user_id=user_id) if db is not None else None
        roadmap_summary = "No previous roadmap"
        if existing_strategy and isinstance(existing_strategy.roadmap, dict):
            roadmap_summary = existing_strategy.roadmap.get("summary") or "Active learning roadmap in progress"

        context = {
            "top_skills": list(top_skills)[:10],
            "missing_skills": list(missing_skills)[:10],
            "current_match_score": current_match_score,
            "roadmap_summary": roadmap_summary,
        }

        context_json = json.dumps(context, default=str)
        context_tokens = estimate_tokens(context_json)
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "[PERF] Context generated | user_id=%s | char_count=%d | estimated_tokens=%d | duration=%.2fms",
            user_id,
            len(context_json),
            context_tokens,
            duration_ms,
        )
        return context