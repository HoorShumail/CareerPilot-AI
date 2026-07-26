import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.job.job_matcher_agent import JobMatcherAgent
from src.db.repositories.job_repo import job_repo
from src.db.repositories.match_repo import match_repo
from src.db.repositories.resume_repo import resume_repo, resume_version_repo
from src.exceptions.database import DatabaseException
from src.infrastructure.llm.provider import LLMProvider
from src.schemas.match import MatchCreate, MatchResponse
from src.schemas.resume import ResumeVersionResponse
from src.schemas.job import JobResponse

logger = logging.getLogger("careerpilot.resume_match_service")


class ResumeMatchService:
    def __init__(
        self,
        llm_provider: LLMProvider,
        matcher_agent: Optional[JobMatcherAgent] = None,
    ):
        self.matcher_agent = matcher_agent or JobMatcherAgent(llm_provider)

    async def compare_resume_to_job(
        self,
        db: AsyncSession,
        user_id: UUID,
        resume_version_id: UUID,
        job_id: UUID,
    ) -> MatchResponse:
        logger.info("Match started", extra={"user_id": str(user_id), "resume_version_id": str(resume_version_id), "job_id": str(job_id)})

        resume_version = await resume_version_repo.get(db, id=resume_version_id)
        if not resume_version:
            logger.warning("Resume version not found", extra={"resume_version_id": str(resume_version_id)})
            raise ValueError("Resume version not found")

        resume_id = getattr(resume_version, "resume_id", None)
        resume = await resume_repo.get(db, id=resume_id)
        if not resume or getattr(resume, "user_id", None) != user_id:
            logger.warning("Unauthorized resume access", extra={"user_id": str(user_id), "resume_version_id": str(resume_version_id)})
            raise ValueError("Resume version not found")

        logger.info("Resume loaded", extra={"resume_version_id": str(resume_version_id)})

        job = await job_repo.get(db, id=job_id)
        if not job:
            logger.warning("Job not found", extra={"job_id": str(job_id)})
            raise ValueError("Job not found")

        logger.info("Job loaded", extra={"job_id": str(job_id)})

        resume_payload = ResumeVersionResponse.model_validate(
            {
                "id": getattr(resume_version, "id", None),
                "resume_id": getattr(resume_version, "resume_id", None),
                "content": getattr(resume_version, "content", {}),
                "source_description": getattr(resume_version, "source_description", None),
                "version_type": getattr(resume_version, "version_type", "upload"),
                "created_at": getattr(resume_version, "created_at", None),
                "updated_at": getattr(resume_version, "updated_at", None),
            }
        ).model_dump()

        job_payload = JobResponse.model_validate(
            {
                "id": getattr(job, "id", None),
                "user_id": getattr(job, "user_id", None),
                "title": getattr(job, "title", None),
                "company": getattr(job, "company", None),
                "is_remote": getattr(job, "is_remote", False),   # <-- ADDED
                "description": getattr(job, "description", None),
                "location": getattr(job, "location", None),
                "employment_type": getattr(job, "employment_type", None),
                "salary_range": getattr(job, "salary_range", None),
                "requirements": getattr(job, "requirements", None),
                "created_at": getattr(job, "created_at", None),
                "updated_at": getattr(job, "updated_at", None),
            }
        ).model_dump()

        comparison_payload = await self.matcher_agent.compare_resume_job(resume_payload, job_payload)

        logger.info("AI comparison completed", extra={"job_id": str(job_id), "resume_version_id": str(resume_version_id)})

        match_data = {
            "user_id": user_id,
            "resume_version_id": resume_version_id,
            "job_id": job_id,
            "overall_match_score": comparison_payload.overall_match_score,
            "ats_score": comparison_payload.ats_score,
            "matched_skills": comparison_payload.matched_skills,
            "missing_skills": comparison_payload.missing_skills,
            "missing_technologies": comparison_payload.missing_technologies,
            "missing_certifications": comparison_payload.missing_certifications,
            "experience_gap": comparison_payload.experience_gap,
            "education_gap": comparison_payload.education_gap,
            "strength_analysis": comparison_payload.strength_analysis,
            "weakness_analysis": comparison_payload.weakness_analysis,
            "priority_learning_roadmap": comparison_payload.priority_learning_roadmap,
            "resume_improvements": comparison_payload.resume_improvements,
            "estimated_match_after_learning": comparison_payload.estimated_match_after_learning,
            "interview_preparation": comparison_payload.interview_preparation,
            "final_recommendation": comparison_payload.final_recommendation,
        }

        try:
            saved_match = await match_repo.create(db, obj_in=MatchCreate(**match_data))
            logger.info("Database save completed", extra={"match_id": str(getattr(saved_match, "id", ""))})
        except Exception as exc:
            logger.exception("Failed to persist match record")
            raise DatabaseException("Unable to persist match record") from exc

        logger.info("Completion", extra={"match_id": str(getattr(saved_match, "id", ""))})
        return MatchResponse.model_validate(saved_match)

    async def get_match(self, db: AsyncSession, user_id: UUID, match_id: UUID) -> MatchResponse:
        match = await match_repo.get(db, id=match_id)
        if not match or match.user_id != user_id:
            raise ValueError("Match not found")
        return MatchResponse.model_validate(match)

    async def list_matches(self, db: AsyncSession, user_id: UUID) -> list[MatchResponse]:
        matches = await match_repo.get_by_user(db, user_id=str(user_id))
        return [MatchResponse.model_validate(match) for match in matches]

    async def get_matches_for_resume(self, db: AsyncSession, user_id: UUID, resume_version_id: UUID) -> list[MatchResponse]:
        resume_version = await resume_version_repo.get(db, id=resume_version_id)
        if not resume_version:
            raise ValueError("Resume version not found")

        resume = await resume_repo.get(db, id=resume_version.resume_id)
        if not resume or resume.user_id != user_id:
            raise ValueError("Resume version not found")

        matches = await match_repo.get_by_resume(db, resume_version_id=str(resume_version_id))
        return [MatchResponse.model_validate(match) for match in matches]

    async def get_matches_for_job(self, db: AsyncSession, user_id: UUID, job_id: UUID) -> list[MatchResponse]:
        job = await job_repo.get(db, id=job_id)
        if not job or job.user_id != user_id:
            raise ValueError("Job not found")

        matches = await match_repo.get_by_job(db, job_id=str(job_id))
        return [MatchResponse.model_validate(match) for match in matches]

    async def delete_match(self, db: AsyncSession, user_id: UUID, match_id: UUID) -> MatchResponse:
        match = await match_repo.get(db, id=match_id)
        if not match or match.user_id != user_id:
            raise ValueError("Match not found")
        deleted = await match_repo.remove(db, id=match_id)
        if not deleted:
            raise ValueError("Match not found")
        return MatchResponse.model_validate(deleted)