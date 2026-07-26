from src.db.models.base import Base, BaseModel
from src.db.models.user import User
from src.db.models.resume import Resume, ResumeVersion
from src.db.models.job import Job
from src.db.models.application import Application
from src.db.models.interview import InterviewSession, InterviewAnswer
from src.db.models.career_profile import (
    CareerProfile,
    SkillRecord,
    CareerGoal,
    LearningProgress,
    CareerProfileSnapshot,
)
from src.db.models.career_strategy import CareerStrategy, CareerStrategyProgress
from src.db.models.agent_run import AgentRun
from src.db.models.match import Match
from src.db.models.career_intelligence_memory import CareerIntelligenceMemory   # <-- ADDED

# Export all models for Alembic autogenerate
__all__ = [
    "Base",
    "BaseModel",
    "User",
    "Resume",
    "ResumeVersion",
    "Job",
    "Application",
    "InterviewSession",
    "InterviewAnswer",
    "CareerProfile",
    "SkillRecord",
    "CareerGoal",
    "LearningProgress",
    "CareerProfileSnapshot",
    "AgentRun",
    "Match",
    "CareerIntelligenceMemory",   # <-- ADDED
]