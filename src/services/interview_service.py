import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.interview.interview_agent import InterviewAgent
from src.db.models.interview import InterviewAnswer, InterviewSession
from src.db.repositories.application_repo import application_repo
from src.db.repositories.career_profile_repo import career_profile_repo
from src.db.repositories.job_repo import job_repo
from src.db.repositories.match_repo import match_repo
from src.db.repositories.resume_repo import resume_repo, resume_version_repo
from src.infrastructure.llm.provider import LLMProvider
from src.schemas.interview import (
    InterviewAnswerRequest,
    InterviewQuestion,
    InterviewSessionResponse,
    InterviewStartRequest,
)

logger = logging.getLogger("careerpilot.interview_service")


class InterviewService:
    def __init__(self, llm_provider: LLMProvider, agent: Optional[InterviewAgent] = None):
        self.agent = agent or InterviewAgent(llm_provider)

    async def start_session(
        self,
        db: AsyncSession,
        user_id: UUID,
        payload: InterviewStartRequest,
    ) -> InterviewSessionResponse:
        profile = await career_profile_repo.get_by_user(db, user_id=str(user_id))
        profile_payload = {"career_profile": profile.__dict__} if profile else {"career_profile": {"user_id": str(user_id)}}
        context_payload = await self._build_context(db, user_id)
        generated = await self.agent.generate_session(profile_payload, context_payload, payload)

        questions_payload = {
            "questions": [
                q.model_dump() if hasattr(q, "model_dump") else q
                for q in (generated.questions or [])
            ]
        }
        session = InterviewSession(
            user_id=user_id,
            interview_type=generated.interview_type,
            target_role=generated.target_role,
            target_company=generated.target_company,
            difficulty=generated.difficulty,
            duration_seconds=generated.duration_seconds,
            questions=questions_payload,
            feedback_summary=generated.feedback_summary,
            overall_score=generated.overall_score,
            session_type=payload.interview_type or generated.interview_type or "mock",
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return self._serialize_session(session)

    # -------- FIXED: uses the correct question index --------
    async def answer_question(
        self,
        db: AsyncSession,
        user_id: UUID,
        session_id: UUID,
        payload: InterviewAnswerRequest,
    ) -> Dict[str, Any]:
        session = await db.get(InterviewSession, session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Interview session not found")

        questions = session.questions.get("questions", []) if isinstance(session.questions, dict) else []
        if not questions:
            raise ValueError("No questions in session")

        # Use the requested index
        idx = payload.question_index
        if idx < 0 or idx >= len(questions):
            raise ValueError("Question index out of range")

        question_data = questions[idx]
        question_text = question_data.get("question", "") if isinstance(question_data, dict) else str(question_data)

        evaluation = await self.agent.evaluate_answer(question_text, payload.answer)

        answer_record = InterviewAnswer(
            session_id=session_id,
            question_index=idx,                      # <-- fixed
            question_text=question_text,
            user_answer=payload.answer,
            ai_feedback=evaluation,
            score=evaluation.get("technical_score"),
            category="technical",
        )
        db.add(answer_record)
        await db.commit()
        await db.refresh(answer_record)
        return evaluation

    # -------- FIXED: loads answers and passes full interview data --------
    async def finish_session(
        self,
        db: AsyncSession,
        user_id: UUID,
        session_id: UUID,
    ) -> InterviewSessionResponse:
        session = await db.get(InterviewSession, session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Interview session not found")

        # Fetch all answers for this session
        stmt = select(InterviewAnswer).where(InterviewAnswer.session_id == session_id)
        result = await db.execute(stmt)
        answers = result.scalars().all()

        # Build the interview data structure required by the new prompt
        interview_data = {
            "questions": session.questions.get("questions", []) if isinstance(session.questions, dict) else [],
            "answers": [
                {
                    "question_index": a.question_index,
                    "question_text": a.question_text,
                    "user_answer": a.user_answer,
                    "ai_feedback": a.ai_feedback,
                    "score": a.score,
                }
                for a in answers
            ],
            "feedback_summary": session.feedback_summary or {},
        }

        # Generate final feedback using the new agent method
        feedback = await self.agent.generate_feedback(interview_data)

        # Update session with feedback and overall score
        session.feedback_summary = feedback
        session.overall_score = feedback.get("overall_score")  # <-- from the LLM

        db.add(session)
        await db.commit()
        await db.refresh(session)
        return self._serialize_session(session)

    async def get_history(self, db: AsyncSession, user_id: UUID) -> List[InterviewSessionResponse]:
        result = await db.execute(select(InterviewSession).where(InterviewSession.user_id == user_id))
        sessions = result.scalars().all()
        return [self._serialize_session(session) for session in sessions]

    async def get_session(
        self,
        db: AsyncSession,
        user_id: UUID,
        session_id: UUID,
    ) -> InterviewSessionResponse:
        session = await db.get(InterviewSession, session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Interview session not found")
        return self._serialize_session(session)

    async def get_analytics(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        result = await db.execute(select(InterviewSession).where(InterviewSession.user_id == user_id))
        sessions = result.scalars().all()
        scores = [session.overall_score or 0 for session in sessions if session.overall_score is not None]
        return {
            "average_score": sum(scores) / max(1, len(scores)),
            "best_score": max(scores) if scores else 0,
            "worst_score": min(scores) if scores else 0,
            "session_count": len(sessions),
        }

    async def get_feedback(
        self,
        db: AsyncSession,
        user_id: UUID,
        session_id: UUID,
    ) -> Dict[str, Any]:
        session = await db.get(InterviewSession, session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Interview session not found")
        return session.feedback_summary or {}

    def _serialize_session(self, session: InterviewSession) -> InterviewSessionResponse:
        questions_payload = []
        if isinstance(session.questions, dict):
            questions_payload = [
                InterviewQuestion(**q) if isinstance(q, dict) else InterviewQuestion(question=str(q), category="technical")
                for q in session.questions.get("questions", [])
            ]

        return InterviewSessionResponse(
            id=session.id or UUID("00000000-0000-0000-0000-000000000000"),
            user_id=session.user_id or UUID("00000000-0000-0000-0000-000000000000"),
            interview_type=session.interview_type,
            target_role=session.target_role,
            target_company=session.target_company,
            difficulty=session.difficulty,
            duration_seconds=session.duration_seconds,
            questions=questions_payload,
            overall_score=session.overall_score,
            feedback_summary=session.feedback_summary or {},
            created_at=session.created_at or datetime.utcnow(),
            updated_at=session.updated_at or datetime.utcnow(),
        )

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
        return {
            "resumes": [r.__dict__ for r in resumes],
            "resume_versions": [rv.__dict__ for rv in resume_versions],
            "applications": [a.__dict__ for a in applications],
            "jobs": [j.__dict__ for j in jobs],
            "matches": [m.__dict__ for m in matches],
        }