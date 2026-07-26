import uuid
from datetime import date
from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import BaseModel

class Application(BaseModel):
    __tablename__ = "applications"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    resume_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_versions.id"), nullable=True)

    status: Mapped[str] = mapped_column(String, nullable=False, default="saved")  # saved, applied, screening, interview, offer, rejected
    applied_date: Mapped[date] = mapped_column(Date, nullable=True)

    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    gap_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    strengths: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    missing_skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    learning_recommendations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    estimated_match_after_learning: Mapped[float | None] = mapped_column(Float, nullable=True)
    recruiter_notes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    recruiter_sim_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cover_letter: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume_version = relationship("ResumeVersion", back_populates="applications")
