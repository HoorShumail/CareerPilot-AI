import uuid
from datetime import datetime, date
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import BaseModel


class CareerProfile(BaseModel):
    __tablename__ = "career_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    career_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String, nullable=True)
    strongest_skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    weakest_skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_maturity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    preferred_industries: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    preferred_roles: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    preferred_locations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    salary_expectations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    remote_preference: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    experience_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    education_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    github_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    linkedin_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    certifications: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    strengths: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    weaknesses: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    overall_readiness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_growth_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    readiness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    promotion_readiness: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_career_level: Mapped[str | None] = mapped_column(String, nullable=True)
    growth_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    learning_recommendations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    learning_roadmap: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    skill_intelligence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    career_gap_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    last_synced: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="career_profile")
    skill_records = relationship("SkillRecord", back_populates="profile", cascade="all, delete-orphan")
    career_goals = relationship("CareerGoal", back_populates="profile", cascade="all, delete-orphan")
    snapshots = relationship("CareerProfileSnapshot", back_populates="profile", cascade="all, delete-orphan")


class SkillRecord(BaseModel):
    __tablename__ = "skill_records"

    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("career_profiles.id"), nullable=False)
    
    skill_name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=True) # technical, soft, domain
    proficiency: Mapped[float] = mapped_column(Float, nullable=True) # 0.0 - 1.0
    source: Mapped[str] = mapped_column(String, nullable=True) # resume, github, self, interview
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    profile = relationship("CareerProfile", back_populates="skill_records")


class CareerGoal(BaseModel):
    __tablename__ = "career_goals"

    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("career_profiles.id"), nullable=False)
    
    target_role: Mapped[str] = mapped_column(String, nullable=True)
    target_company_type: Mapped[str] = mapped_column(String, nullable=True)
    target_industry: Mapped[str] = mapped_column(String, nullable=True)
    target_salary_min: Mapped[int] = mapped_column(Integer, nullable=True)
    target_salary_max: Mapped[int] = mapped_column(Integer, nullable=True)
    location_pref: Mapped[str] = mapped_column(String, nullable=True)
    remote_pref: Mapped[bool] = mapped_column(Boolean, nullable=True)
    timeline: Mapped[str] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    profile = relationship("CareerProfile", back_populates="career_goals")


class LearningProgress(BaseModel):
    __tablename__ = "learning_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    skill_name: Mapped[str] = mapped_column(String, nullable=False)
    resource_type: Mapped[str] = mapped_column(String, nullable=False) # course, project, cert, practice
    resource_name: Mapped[str] = mapped_column(String, nullable=False)
    resource_url: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="not_started") # not_started, in_progress, completed
    completion_pct: Mapped[float] = mapped_column(Float, default=0.0)

    target_date: Mapped[date] = mapped_column(Date, nullable=True)
    completed_date: Mapped[date] = mapped_column(Date, nullable=True)

    # Relationships
    user = relationship("User", back_populates="learning_progress")


class CareerProfileSnapshot(BaseModel):
    __tablename__ = "career_profile_snapshots"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_profiles.id"),
        nullable=False,
        index=True,                     # <-- added index to fix Alembic warning
    )
    snapshot_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    snapshot_label: Mapped[str | None] = mapped_column(String, nullable=True)

    profile = relationship("CareerProfile", back_populates="snapshots")