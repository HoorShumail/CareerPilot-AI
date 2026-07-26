import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.job.job_matcher_agent import JobMatcherAgent
from src.db.repositories.application_repo import application_repo
from src.db.repositories.job_repo import job_repo
from src.db.repositories.match_repo import match_repo
from src.db.repositories.resume_repo import resume_repo, resume_version_repo
from src.exceptions.database import DatabaseException
from src.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    MatchAnalysis,
)
from src.schemas.match import MatchCreate
from src.schemas.resume import ResumeVersionResponse
from src.schemas.job import JobResponse
from src.infrastructure.llm.provider import LLMProvider

logger = logging.getLogger("careerpilot.application_service")


class ApplicationService:
    def __init__(
        self,
        llm_provider: LLMProvider,
        matcher_agent: Optional[JobMatcherAgent] = None,
    ):
        self.matcher_agent = matcher_agent or JobMatcherAgent(llm_provider)

    async def create_application(
        self,
        db: AsyncSession,
        user_id: UUID,
        job_id: UUID,
        resume_version_id: Optional[UUID] = None,
        status: str = "saved",
        applied_date: Optional[str] = None,
    ) -> ApplicationResponse:
        logger.info("Creating application for user %s, job %s", user_id, job_id)

        job = await job_repo.get(db, id=job_id)
        if not job:
            logger.warning("Job not found for application %s", job_id)
            raise ValueError("Job not found")

        resume_version = None
        match_analysis: Optional[MatchAnalysis] = None

        if resume_version_id:
            resume_version = await resume_version_repo.get(db, id=resume_version_id)
            if not resume_version:
                logger.warning("Resume version not found %s", resume_version_id)
                raise ValueError("Resume version not found")

            resume = await resume_repo.get(db, id=resume_version.resume_id)
            if not resume or resume.user_id != user_id:
                logger.warning("Unauthorized resume version access %s", resume_version_id)
                raise ValueError("Resume version not found")

            match_analysis = await self._compare_resume_to_job(resume_version, job)

        application_data = {
            "user_id": user_id,
            "job_id": job_id,
            "resume_version_id": resume_version_id,
            "status": status,
            "applied_date": applied_date,
        }

        if match_analysis:
            analysis_dict = match_analysis.model_dump()
            if "overall_match_score" in analysis_dict and analysis_dict["overall_match_score"] is not None:
                analysis_dict["match_score"] = analysis_dict.pop("overall_match_score")
            application_data.update(analysis_dict)

        try:
            application = await application_repo.create(db, obj_in=ApplicationCreate(**application_data))

            # Save Match record if analysis was generated
            if match_analysis and resume_version_id:
                await self._save_or_update_match_record(db, user_id, resume_version_id, job_id, match_analysis)

            return ApplicationResponse.model_validate(application)
        except Exception as exc:
            logger.exception("Failed to create application for user %s", user_id)
            raise DatabaseException("Unable to persist application record") from exc

    async def get_application(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
    ) -> ApplicationResponse:
        logger.info("Fetching application %s for user %s", application_id, user_id)
        application = await application_repo.get(db, id=application_id)
        if not application or application.user_id != user_id:
            logger.warning("Application not found or unauthorized %s", application_id)
            raise ValueError("Application not found")
        return ApplicationResponse.model_validate(application)

    async def list_applications(self, db: AsyncSession, user_id: UUID) -> list[ApplicationResponse]:
        logger.info("Listing applications for user %s", user_id)
        applications = await application_repo.get_by_user(db, user_id=str(user_id))
        return [ApplicationResponse.model_validate(item) for item in applications]

    async def update_application(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
        update_data: ApplicationUpdate,
    ) -> ApplicationResponse:
        logger.info("Updating application %s for user %s", application_id, user_id)
        application = await application_repo.get(db, id=application_id)
        if not application or application.user_id != user_id:
            logger.warning("Application not found or unauthorized %s", application_id)
            raise ValueError("Application not found")

        try:
            updated = await application_repo.update(db, db_obj=application, obj_in=update_data)
            return ApplicationResponse.model_validate(updated)
        except Exception as exc:
            logger.exception("Failed to update application %s", application_id)
            raise DatabaseException("Unable to update application record") from exc

    async def delete_application(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
    ) -> ApplicationResponse:
        logger.info("Deleting application %s for user %s", application_id, user_id)
        application = await application_repo.get(db, id=application_id)
        if not application or application.user_id != user_id:
            logger.warning("Application not found or unauthorized %s", application_id)
            raise ValueError("Application not found")

        deleted = await application_repo.remove(db, id=application_id)
        if not deleted:
            logger.warning("Delete failed for application %s", application_id)
            raise ValueError("Application not found")
        return ApplicationResponse.model_validate(deleted)

    async def refresh_match(
        self,
        db: AsyncSession,
        user_id: UUID,
        application_id: UUID,
    ) -> ApplicationResponse:
        logger.info("[TRACE 1] Entered refresh_match for application_id=%s, user_id=%s", application_id, user_id)
        
        # 1. Load application
        application = await application_repo.get(db, id=application_id)
        if not application or application.user_id != user_id:
            logger.warning("Application not found or unauthorized %s", application_id)
            raise ValueError("Application not found")
        logger.info("[TRACE 2] Loaded application.id=%s, match_score=%s, updated_at=%s", application.id, getattr(application, "match_score", None), getattr(application, "updated_at", None))

        if not application.resume_version_id:
            logger.warning("Application %s has no resume version to compare", application_id)
            raise ValueError("Application missing resume version")

        # 2. Load resume version
        resume_version = await resume_version_repo.get(db, id=application.resume_version_id)
        if not resume_version:
            logger.warning("Resume version not found %s", application.resume_version_id)
            raise ValueError("Resume version not found")
        logger.info("[TRACE 3] Loaded resume_version.id=%s", resume_version.id)

        # 3. Load job
        job = await job_repo.get(db, id=application.job_id)
        if not job:
            logger.warning("Job not found for application %s during match refresh", application_id)
            raise ValueError("Job not found")
        logger.info("[TRACE 4] Loaded job.id=%s", job.id)

        # 4 & 5. Run Matcher Agent & receive MatchAnalysis
        match_analysis = await self._compare_resume_to_job(resume_version, job)
        logger.info("[TRACE 5] MatchAnalysis.model_dump()=%s", match_analysis.model_dump())
        logger.info("[TRACE 5b] MatchAnalysis.overall_match_score=%s", getattr(match_analysis, "overall_match_score", None))

        # 6. Save or update Match record in matches table
        await self._save_or_update_match_record(
            db,
            user_id,
            application.resume_version_id,
            application.job_id,
            match_analysis,
        )

        # 7. Update Application record with MatchAnalysis fields
        update_data = ApplicationUpdate(
            match_score=match_analysis.overall_match_score,
            gap_analysis=match_analysis.gap_analysis or match_analysis.detailed_gap_analysis,
            strengths=match_analysis.strengths or match_analysis.strength_analysis,
            missing_skills=match_analysis.missing_skills,
            learning_recommendations=match_analysis.learning_recommendations or match_analysis.priority_learning_roadmap,
            estimated_match_after_learning=match_analysis.estimated_match_after_learning,
        )

        logger.info("[TRACE 6] ApplicationUpdate.model_dump(exclude_unset=False)=%s", update_data.model_dump(exclude_unset=False))
        logger.info("[TRACE 7] Application BEFORE update match_score=%s, updated_at=%s", getattr(application, "match_score", None), getattr(application, "updated_at", None))

        try:
            # 8. Call update
            updated = await application_repo.update(db, db_obj=application, obj_in=update_data)
            logger.info("[TRACE 8] Application AFTER application_repo.update() match_score=%s, updated_at=%s", getattr(updated, "match_score", None), getattr(updated, "updated_at", None))
            logger.info("[TRACE 9] updated.match_score=%s", getattr(updated, "match_score", None))

            # STEP 6 verification: Query fresh application from database
            fresh_app = await application_repo.get(db, id=application_id)
            if fresh_app:
                logger.info("[TRACE 13] Fresh application queried from DB match_score=%s, updated_at=%s", fresh_app.match_score, fresh_app.updated_at)

            response = ApplicationResponse.model_validate(updated)
            logger.info("[TRACE 12] ApplicationResponse.model_dump() before returning=%s", response.model_dump())
            return response
        except Exception as exc:
            logger.exception("Failed to refresh match for application %s", application_id)
            raise DatabaseException("Unable to update application record") from exc




    async def _save_or_update_match_record(
        self,
        db: AsyncSession,
        user_id: UUID,
        resume_version_id: UUID,
        job_id: UUID,
        match_analysis: MatchAnalysis,
    ):
        existing_matches = await match_repo.get_by_resume(db, resume_version_id=str(resume_version_id))
        existing_match = next(
            (m for m in existing_matches if str(m.job_id) == str(job_id) and str(m.user_id) == str(user_id)),
            None,
        )

        match_data = {
            "user_id": user_id,
            "resume_version_id": resume_version_id,
            "job_id": job_id,
            "overall_match_score": match_analysis.overall_match_score,
            "ats_score": match_analysis.ats_compatibility_score,
            "matched_skills": match_analysis.skills_match,
            "missing_skills": match_analysis.missing_skills,
            "missing_technologies": match_analysis.missing_technologies,
            "missing_certifications": match_analysis.missing_certifications,
            "experience_gap": {"gap": match_analysis.experience_gap} if isinstance(match_analysis.experience_gap, str) else match_analysis.experience_gap,
            "education_gap": {"gap": match_analysis.education_gap} if isinstance(match_analysis.education_gap, str) else match_analysis.education_gap,
            "strength_analysis": match_analysis.strength_analysis or match_analysis.strengths,
            "weakness_analysis": match_analysis.weakness_analysis,
            "priority_learning_roadmap": match_analysis.priority_learning_roadmap or match_analysis.learning_recommendations,
            "estimated_match_after_learning": match_analysis.estimated_match_after_learning,
            "final_recommendation": {"recommendation": match_analysis.final_recommendation} if isinstance(match_analysis.final_recommendation, str) else match_analysis.final_recommendation,
        }

        if existing_match:
            await match_repo.update(db, db_obj=existing_match, obj_in=match_data)
        else:
            await match_repo.create(db, obj_in=MatchCreate(**match_data))

    async def _compare_resume_to_job(self, resume_version, job) -> MatchAnalysis:
        resume_payload = ResumeVersionResponse.model_validate(resume_version).model_dump()
        job_payload = JobResponse.model_validate(job).model_dump()

        return await self.matcher_agent.compare(resume_payload, job_payload)
