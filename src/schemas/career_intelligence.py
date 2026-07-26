from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ForecastItem(BaseModel):
    horizon: str
    predicted_job_titles: List[str]
    salary_projection: Dict[str, Any]
    hiring_probability: float
    promotion_probability: float
    career_trajectory: str
    confidence_score: float
    estimated_timeline: str


class ForecastResponse(BaseModel):
    forecasts: List[ForecastItem]
    summary: Optional[str] = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CoachChatRequest(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None


class CoachAdviceRequest(BaseModel):
    question: str
    conversation_id: Optional[UUID] = None


class CoachActionPlanRequest(BaseModel):
    goal: str
    conversation_id: Optional[UUID] = None


class CoachGoalsRequest(BaseModel):
    goals: List[str]
    conversation_id: Optional[UUID] = None


class CoachChatResponse(BaseModel):
    message: str
    action_items: List[str] = []
    confidence: float
    conversation_id: Optional[UUID] = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulationRequest(BaseModel):
    scenario: str


class SimulationResponse(BaseModel):
    scenario: str
    salary: Dict[str, Any]
    readiness: float
    opportunities: List[str]
    timeline: str
    new_skill_gaps: List[str]


class MarketIntelligenceResponse(BaseModel):
    demanded_skills: List[str]
    technologies: List[str]
    certifications: List[str]
    frameworks: List[str]
    ai_tools: List[str]
    cloud_providers: List[str]
    programming_languages: List[str]
    trends: List[str]
    generated_at: datetime


class LearningPlanResponse(BaseModel):
    daily: List[str]
    weekly: List[str]
    monthly: List[str]
    quarterly: List[str]
    yearly: List[str]
    books: List[str]
    projects: List[str]
    certifications: List[str]
    courses: List[str]
    research_papers: List[str]
    open_source_contributions: List[str]
    generated_at: datetime


class GoalProgressResponse(BaseModel):
    goal: str
    progress: float
    eta: str
    confidence: float
    remaining_skills: List[str]
    remaining_experience: List[str]
    milestones: List[str]
