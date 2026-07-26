import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.career.career_twin_agent import CareerTwinAgent
from src.db.models.career_profile import CareerProfile, CareerProfileSnapshot
from src.db.repositories.application_repo import application_repo
from src.db.repositories.career_profile_repo import career_profile_repo, career_profile_snapshot_repo
from src.db.repositories.job_repo import job_repo
from src.db.repositories.match_repo import match_repo
from src.db.repositories.resume_repo import resume_repo, resume_version_repo
from src.db.repositories.user_repo import user_repo
from src.infrastructure.llm.provider import LLMProvider
from src.schemas.career_profile import CareerProfileCreate, CareerProfileResponse, CareerProfileSnapshotResponse

logger = logging.getLogger("careerpilot.career_twin_service")


class CareerTwinService:
    def __init__(self, llm_provider: LLMProvider, agent: Optional[CareerTwinAgent] = None):
        self.agent = agent or CareerTwinAgent(llm_provider)

    async def get_profile(self, db: AsyncSession, user_id: UUID) -> CareerProfileResponse:
        profile = await career_profile_repo.get_by_user(db, user_id=str(user_id))
        if not profile:
            raise ValueError("Career profile not found")
        return CareerProfileResponse.model_validate(profile)

    async def get_timeline(self, db: AsyncSession, user_id: UUID) -> list[CareerProfileSnapshotResponse]:
        profile = await career_profile_repo.get_by_user(db, user_id=str(user_id))
        if not profile:
            raise ValueError("Career profile not found")
        snapshots = await career_profile_snapshot_repo.get_by_profile(db, profile_id=str(profile.id))
        return [CareerProfileSnapshotResponse.model_validate(snapshot) for snapshot in snapshots]

    async def refresh_profile(self, db: AsyncSession, user_id: UUID) -> CareerProfileResponse:
        user = await user_repo.get(db, id=user_id)
        if not user:
            raise ValueError("User not found")

        profile = await career_profile_repo.get_by_user(db, user_id=str(user_id))
        if not profile:
            profile_data = {
                "user_id": user_id,
                "career_summary": {},
                "skills": {},
                "experience_summary": {},
                "education_summary": {},
                "strengths": {},
                "weaknesses": {},
                "certifications": {},
                "overall_readiness_score": 0.0,
            }
            profile = CareerProfile(**profile_data)
            db.add(profile)
            await db.commit()
            await db.refresh(profile)

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

        profile_payload = {
            "career_summary": profile.career_summary or {},
            "experience_level": profile.experience_level,
            "strongest_skills": profile.strongest_skills or {},
            "weakest_skills": profile.weakest_skills or {},
            "ai_maturity_score": profile.ai_maturity_score,
            "confidence_score": profile.confidence_score,
            "preferred_industries": profile.preferred_industries or [],
            "preferred_roles": profile.preferred_roles or [],
            "preferred_locations": profile.preferred_locations or [],
            "salary_expectations": profile.salary_expectations or {},
            "remote_preference": profile.remote_preference or {},
            "skills": profile.skills or {},
            "experience_summary": profile.experience_summary or {},
            "education_summary": profile.education_summary or {},
            "strengths": profile.strengths or {},
            "weaknesses": profile.weaknesses or {},
            "certifications": profile.certifications or {},
            "overall_readiness_score": profile.overall_readiness_score,
        }

        context_payload = {
            "resumes": [resume.__dict__ for resume in resumes],
            "resume_versions": [rv.__dict__ for rv in resume_versions],
            "applications": [application.__dict__ for application in applications],
            "jobs": [job.__dict__ for job in jobs],
            "matches": [match.__dict__ for match in matches],
        }

        analysis = await self.agent.refresh_profile(profile_payload, context_payload)
        update_data = analysis.model_dump(exclude_unset=True)
        update_data["user_id"] = user_id

        for field, value in update_data.items():
            if field in {"user_id"}:
                continue
            setattr(profile, field, value)

        profile.last_synced = __import__("datetime").datetime.utcnow()
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

        # Recursively convert UUIDs to strings for JSON serialization
        def _convert_uuids(obj):
            if isinstance(obj, dict):
                return {k: _convert_uuids(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_convert_uuids(i) for i in obj]
            elif isinstance(obj, UUID):
                return str(obj)
            else:
                return obj

        snapshot_payload = _convert_uuids(update_data)
        snapshot = CareerProfileSnapshot(
            profile_id=profile.id,
            snapshot_payload=snapshot_payload,
            snapshot_label="refresh",
        )
        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)

        return CareerProfileResponse.model_validate(profile)

    async def get_recommendations(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        profile = await career_profile_repo.get_by_user(db, user_id=str(user_id))
        if not profile:
            raise ValueError("Career profile not found")
        return profile.learning_recommendations or {"courses": [], "certifications": [], "projects": [], "books": []}

    async def get_strengths(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        profile = await career_profile_repo.get_by_user(db, user_id=str(user_id))
        if not profile:
            raise ValueError("Career profile not found")
        return profile.strengths or {}

    async def get_weaknesses(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        profile = await career_profile_repo.get_by_user(db, user_id=str(user_id))
        if not profile:
            raise ValueError("Career profile not found")
        return profile.weaknesses or {}

    async def get_learning_roadmap(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        profile = await career_profile_repo.get_by_user(db, user_id=str(user_id))
        if not profile:
            raise ValueError("Career profile not found")
        return profile.learning_roadmap or {}