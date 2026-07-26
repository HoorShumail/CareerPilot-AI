import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import BaseModel


class CareerStrategy(BaseModel):
    __tablename__ = "career_strategies"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    strategy_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    skill_gap_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    roadmap: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    certifications: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    projects: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    weekly_goals: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    monthly_goals: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    progress_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    refresh_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="career_strategies")
    progress_entries = relationship("CareerStrategyProgress", back_populates="strategy", cascade="all, delete-orphan")


class CareerStrategyProgress(BaseModel):
    __tablename__ = "career_strategy_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    strategy_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("career_strategies.id"), nullable=True)
    completed_skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    completed_certifications: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    completed_projects: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    progress_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    goal_completion: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    milestone_status: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    user = relationship("User", back_populates="career_strategy_progress")
    strategy = relationship("CareerStrategy", back_populates="progress_entries")
