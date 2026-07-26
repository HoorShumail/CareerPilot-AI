import logging
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.job.job_insights_agent import JobInsightsAgent
from src.agents.job.job_parser_agent import JobParserAgent
from src.db.repositories.job_repo import job_repo
from src.infrastructure.document_parser.resume_parser import ResumeParser
from src.infrastructure.llm.provider import LLMProvider
from src.schemas.job import JobCreate, JobInsights, JobParsedData, JobResponse, JobUpdate
from src.exceptions.database import DatabaseException

logger = logging.getLogger("careerpilot.job_service")


class JobService:
    def __init__(
        self,
        llm_provider: LLMProvider,
        parser_agent: Optional[JobParserAgent] = None,
        insights_agent: Optional[JobInsightsAgent] = None,
        resume_parser: Optional[ResumeParser] = None,
    ):
        self.parser_agent = parser_agent or JobParserAgent(llm_provider)
        self.insights_agent = insights_agent or JobInsightsAgent(llm_provider)
        self.resume_parser = resume_parser or ResumeParser()

    async def create_job_from_text(
        self,
        db: AsyncSession,
        user_id: UUID,
        raw_text: str,
        title: str,
        company: str,
        url: Optional[str] = None,
    ) -> JobResponse:
        logger.info("Creating job from text for user %s", user_id)
        parsed_data = await self._parse_job_description(raw_text)
        insights = await self._generate_insights(parsed_data)

        job_data = {
            "user_id": user_id,
            "title": title,
            "company": company,
            "url": url,
            "raw_description": raw_text,
            "parsed_jd": parsed_data.model_dump(),
            "required_skills": {
                "required_skills": parsed_data.required_skills or []
            },
            "preferred_skills": {
                "preferred_skills": parsed_data.preferred_skills or []
            },
            "experience_level": parsed_data.experience_level,
            "salary_range": parsed_data.salary or None,
            "location": parsed_data.location,
            "is_remote": bool(parsed_data.remote),
            "ai_summary": insights.executive_summary,
            "ats_keywords": insights.ats_keywords,
            "hidden_requirements": insights.hidden_requirements,
            "interview_focus": insights.interview_focus_areas,
            "missing_certifications": insights.missing_certifications,
            "red_flags": insights.risks,
            "extracted_keywords": {
                "keywords": parsed_data.keywords or []
            },
            "embedding": insights.embedding,
        }

        try:
            job = await job_repo.create(db, obj_in=JobCreate(**job_data))
            return JobResponse.model_validate(job)
        except Exception as exc:
            logger.exception("Failed to create job for user %s", user_id)
            raise DatabaseException("Unable to persist job record") from exc

    async def create_job_from_pdf(
        self,
        db: AsyncSession,
        user_id: UUID,
        file_bytes: bytes,
        content_type: str,
        title: str,
        company: str,
        url: Optional[str] = None,
    ) -> JobResponse:
        logger.info("Creating job from PDF for user %s", user_id)
        extracted_text = self._extract_text_from_pdf(file_bytes, content_type)
        return await self.create_job_from_text(db, user_id, extracted_text, title, company, url)

    async def get_job(self, db: AsyncSession, user_id: UUID, job_id: UUID) -> JobResponse:
        logger.info("Fetching job %s for user %s", job_id, user_id)
        job = await job_repo.get(db, id=job_id)
        if not job or job.user_id != user_id:
            logger.warning("Job not found or unauthorized %s", job_id)
            raise ValueError("Job not found")
        return JobResponse.model_validate(job)

    async def list_jobs(self, db: AsyncSession, user_id: UUID) -> list[JobResponse]:
        logger.info("Listing jobs for user %s", user_id)
        jobs = await job_repo.get_by_user(db, user_id=str(user_id))
        return [JobResponse.model_validate(job) for job in jobs]

    async def update_job(
        self,
        db: AsyncSession,
        user_id: UUID,
        job_id: UUID,
        update_data: JobUpdate,
    ) -> JobResponse:
        logger.info("Updating job %s for user %s", job_id, user_id)
        job = await job_repo.get(db, id=job_id)
        if not job or job.user_id != user_id:
            logger.warning("Job not found for update %s", job_id)
            raise ValueError("Job not found")

        try:
            updated = await job_repo.update(db, db_obj=job, obj_in=update_data)
            return JobResponse.model_validate(updated)
        except Exception as exc:
            logger.exception("Failed to update job %s", job_id)
            raise DatabaseException("Unable to update job record") from exc

    async def delete_job(self, db: AsyncSession, user_id: UUID, job_id: UUID) -> JobResponse:
        logger.info("Deleting job %s for user %s", job_id, user_id)
        job = await job_repo.get(db, id=job_id)
        if not job or job.user_id != user_id:
            logger.warning("Job not found for delete %s", job_id)
            raise ValueError("Job not found")

        deleted = await job_repo.remove(db, id=job_id)
        if not deleted:
            logger.warning("Delete failed for job %s", job_id)
            raise ValueError("Job not found")
        return JobResponse.model_validate(deleted)

    async def refresh_job_insights(self, db: AsyncSession, user_id: UUID, job_id: UUID) -> JobResponse:
        logger.info("Refreshing insights for job %s", job_id)
        job = await job_repo.get(db, id=job_id)
        if not job or job.user_id != user_id:
            logger.warning("Job not found or unauthorized %s", job_id)
            raise ValueError("Job not found")

        parsed_jd = job.parsed_jd or {}
        insights = await self.insights_agent.generate_insights(parsed_jd)

        update_data = JobUpdate(
            ai_summary=insights.executive_summary,
            ats_keywords=insights.ats_keywords,
            hidden_requirements=insights.hidden_requirements,
            interview_focus=insights.interview_focus_areas,
            missing_certifications=insights.missing_certifications,
            red_flags=insights.risks,
            extracted_keywords={"keywords": parsed_jd.get("keywords", []) if isinstance(parsed_jd, dict) else []},
            embedding=insights.embedding,
        )

        try:
            updated = await job_repo.update(db, db_obj=job, obj_in=update_data)
            return JobResponse.model_validate(updated)
        except Exception as exc:
            logger.exception("Failed to refresh insights for job %s", job_id)
            raise DatabaseException("Unable to update job record") from exc

    async def _parse_job_description(self, raw_text: str) -> JobParsedData:
        if not raw_text.strip():
            logger.error("Empty job description provided")
            raise ValueError("Job description is required")

        parsed_data = await self.parser_agent.parse(raw_text)
        if not parsed_data.title or not parsed_data.company:
            logger.warning("Parsed job description missing title or company")
        return parsed_data

    async def _generate_insights(self, parsed_data: JobParsedData) -> JobInsights:
        insights = await self.insights_agent.generate_insights(parsed_data.model_dump())
        return insights

    def _extract_text_from_pdf(self, file_bytes: bytes, content_type: str) -> str:
        content_type = content_type.lower()
        if content_type != "application/pdf":
            logger.error("Unsupported PDF content type: %s", content_type)
            raise ValueError("Unsupported file type for job upload")
        return self.resume_parser.extract_text_from_pdf(file_bytes)
