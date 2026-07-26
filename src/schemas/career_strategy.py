import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SkillGapItem(BaseModel):
    skill: str
    severity: str = "medium"
    reason: str = ""


class SkillGapAnalysis(BaseModel):
    gaps: List[SkillGapItem]
    weak_skills: List[SkillGapItem]
    emerging_skills: List[SkillGapItem]
    priority_skills: List[str]


class RoadmapStep(BaseModel):
    title: str = ""
    topic: str = ""
    duration_weeks: int = 1
    priority: str = "medium"
    dependencies: List[str] = []
    expected_outcomes: List[str] = []
    timeframe: str = "TBD"


class RoadmapPlan(BaseModel):
    weekly_roadmap: List[RoadmapStep]
    monthly_roadmap: List[RoadmapStep]
    quarterly_roadmap: List[RoadmapStep]
    roadmap: List[RoadmapStep]


class CertificationRecommendation(BaseModel):
    name: str
    provider: str
    difficulty: str
    estimated_study_time: str
    priority: str
    reason: str


class ProjectRecommendation(BaseModel):
    title: str
    description: str
    skills_gained: List[str]
    technologies: List[str]
    difficulty: str
    estimated_duration: str
    resume_value: str


class CareerStrategyCreate(BaseModel):
    user_id: Optional[uuid.UUID] = None
    strategy_version: int = 1
    skill_gap_analysis: Optional[Dict[str, Any]] = None
    roadmap: Optional[Dict[str, Any]] = None
    certifications: Optional[List[Dict[str, Any]]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    weekly_goals: Optional[List[Dict[str, Any]]] = None
    monthly_goals: Optional[List[Dict[str, Any]]] = None
    progress_snapshot: Optional[Dict[str, Any]] = None
    refresh_count: int = 0
    strategy_id: Optional[str] = None
    recommendations: Optional[List[Dict[str, Any]]] = None


class CareerStrategyUpdate(BaseModel):
    skill_gap_analysis: Optional[Dict[str, Any]] = None
    roadmap: Optional[Dict[str, Any]] = None
    certifications: Optional[List[Dict[str, Any]]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    weekly_goals: Optional[List[Dict[str, Any]]] = None
    monthly_goals: Optional[List[Dict[str, Any]]] = None
    progress_snapshot: Optional[Dict[str, Any]] = None
    refresh_count: Optional[int] = None


class CareerStrategyBase(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    strategy_version: int = 1
    skill_gap_analysis: Optional[Dict[str, Any]] = None
    roadmap: Optional[Dict[str, Any]] = None
    certifications: Optional[List[Dict[str, Any]]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    weekly_goals: Optional[List[Dict[str, Any]]] = None
    monthly_goals: Optional[List[Dict[str, Any]]] = None
    progress_snapshot: Optional[Dict[str, Any]] = None
    refresh_count: int = 0
    strategy_id: Optional[str] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    last_refreshed_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class CareerStrategyResponse(CareerStrategyBase):
    pass


class CareerStrategyProgressCreate(BaseModel):
    user_id: Optional[uuid.UUID] = None
    strategy_id: Optional[uuid.UUID] = None
    completed_skills: Optional[List[str]] = None
    completed_certifications: Optional[List[str]] = None
    completed_projects: Optional[List[str]] = None
    progress_percent: Optional[float] = None
    goal_completion: Optional[Dict[str, Any]] = None
    milestone_status: Optional[Dict[str, Any]] = None


class CareerStrategyProgressResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    strategy_id: Optional[uuid.UUID] = None
    completed_skills: Optional[List[str]] = None
    completed_certifications: Optional[List[str]] = None
    completed_projects: Optional[List[str]] = None
    progress_percent: Optional[float] = None
    goal_completion: Optional[Dict[str, Any]] = None
    milestone_status: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
