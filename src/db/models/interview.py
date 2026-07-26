import uuid
from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import BaseModel

class InterviewSession(BaseModel):
    __tablename__ = "interview_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    
    session_type: Mapped[str] = mapped_column(String, nullable=False, default="mock") # mock, prep, review
    interview_type: Mapped[str] = mapped_column(String, nullable=True)
    target_role: Mapped[str] = mapped_column(String, nullable=True)
    target_company: Mapped[str] = mapped_column(String, nullable=True)
    difficulty: Mapped[str] = mapped_column(String, nullable=True)
    questions: Mapped[dict] = mapped_column(JSONB, nullable=True)
    overall_score: Mapped[float] = mapped_column(Float, nullable=True)
    feedback_summary: Mapped[dict] = mapped_column(JSONB, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="interview_sessions")
    job = relationship("Job", back_populates="interview_sessions")
    answers = relationship("InterviewAnswer", back_populates="session", cascade="all, delete-orphan")

class InterviewAnswer(BaseModel):
    __tablename__ = "interview_answers"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False)
    
    question_index: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    user_answer: Mapped[str] = mapped_column(Text, nullable=True)
    ai_feedback: Mapped[dict] = mapped_column(JSONB, nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=True) # behavioral, technical, system_design
    
    # Relationships
    session = relationship("InterviewSession", back_populates="answers")
