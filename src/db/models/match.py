import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import BaseModel


class Match(BaseModel):
    __tablename__ = "matches"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    resume_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resume_versions.id"),
        nullable=False,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    overall_match_score: Mapped[float | None] = mapped_column(default=None, nullable=True)
    ats_score: Mapped[float | None] = mapped_column(default=None, nullable=True)
    matched_skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    missing_skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    missing_technologies: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    missing_certifications: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    experience_gap: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    education_gap: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    strength_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    weakness_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    priority_learning_roadmap: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resume_improvements: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    estimated_match_after_learning: Mapped[float | None] = mapped_column(default=None, nullable=True)
    interview_preparation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    final_recommendation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    user = relationship("User", back_populates="matches")
    resume_version = relationship("ResumeVersion", back_populates="matches")
    job = relationship("Job", back_populates="matches")
