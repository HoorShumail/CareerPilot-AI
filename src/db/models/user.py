from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.constants.agent_names import ROLE_USER
from src.db.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    avatar_url: Mapped[str] = mapped_column(String, nullable=True)
    preferences: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)
    role: Mapped[str] = mapped_column(String, default=ROLE_USER, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    career_profile = relationship("CareerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="user", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")
    learning_progress = relationship("LearningProgress", back_populates="user", cascade="all, delete-orphan")
    career_strategies = relationship("CareerStrategy", back_populates="user", cascade="all, delete-orphan")
    career_strategy_progress = relationship("CareerStrategyProgress", back_populates="user", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="user", cascade="all, delete-orphan")
