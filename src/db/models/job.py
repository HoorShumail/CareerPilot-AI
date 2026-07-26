import uuid
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import BaseModel


class Job(BaseModel):
    __tablename__ = "jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    company: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_jd: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    required_skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    preferred_skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String, nullable=True)
    salary_range: Mapped[str | None] = mapped_column(String, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ats_keywords: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    hidden_requirements: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    interview_focus: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    missing_certifications: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    red_flags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    extracted_keywords: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    embedding: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    resume_versions = relationship("ResumeVersion", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="job", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="job", cascade="all, delete-orphan")
