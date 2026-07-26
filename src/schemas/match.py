import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class MatchCreate(BaseModel):
    user_id: uuid.UUID
    resume_version_id: uuid.UUID
    job_id: uuid.UUID
    overall_match_score: Optional[float] = None
    ats_score: Optional[float] = None
    matched_skills: Optional[Dict[str, Any]] = None
    missing_skills: Optional[Dict[str, Any]] = None
    missing_technologies: Optional[Dict[str, Any]] = None
    missing_certifications: Optional[Dict[str, Any]] = None
    experience_gap: Optional[Dict[str, Any]] = None
    education_gap: Optional[Dict[str, Any]] = None
    strength_analysis: Optional[Dict[str, Any]] = None
    weakness_analysis: Optional[Dict[str, Any]] = None
    priority_learning_roadmap: Optional[Dict[str, Any]] = None
    resume_improvements: Optional[Dict[str, Any]] = None
    estimated_match_after_learning: Optional[float] = None
    interview_preparation: Optional[Dict[str, Any]] = None
    final_recommendation: Optional[Dict[str, Any]] = None


class MatchUpdate(BaseModel):
    overall_match_score: Optional[float] = None
    ats_score: Optional[float] = None
    matched_skills: Optional[Dict[str, Any]] = None
    missing_skills: Optional[Dict[str, Any]] = None
    missing_technologies: Optional[Dict[str, Any]] = None
    missing_certifications: Optional[Dict[str, Any]] = None
    experience_gap: Optional[Dict[str, Any]] = None
    education_gap: Optional[Dict[str, Any]] = None
    strength_analysis: Optional[Dict[str, Any]] = None
    weakness_analysis: Optional[Dict[str, Any]] = None
    priority_learning_roadmap: Optional[Dict[str, Any]] = None
    resume_improvements: Optional[Dict[str, Any]] = None
    estimated_match_after_learning: Optional[float] = None
    interview_preparation: Optional[Dict[str, Any]] = None
    final_recommendation: Optional[Dict[str, Any]] = None


class MatchBase(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_version_id: uuid.UUID
    job_id: uuid.UUID
    overall_match_score: Optional[float] = None
    ats_score: Optional[float] = None
    matched_skills: Optional[Dict[str, Any]] = None
    missing_skills: Optional[Dict[str, Any]] = None
    missing_technologies: Optional[Dict[str, Any]] = None
    missing_certifications: Optional[Dict[str, Any]] = None
    experience_gap: Optional[Dict[str, Any]] = None
    education_gap: Optional[Dict[str, Any]] = None
    strength_analysis: Optional[Dict[str, Any]] = None
    weakness_analysis: Optional[Dict[str, Any]] = None
    priority_learning_roadmap: Optional[Dict[str, Any]] = None
    resume_improvements: Optional[Dict[str, Any]] = None
    estimated_match_after_learning: Optional[float] = None
    interview_preparation: Optional[Dict[str, Any]] = None
    final_recommendation: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchResponse(MatchBase):
    pass


class MatchComparisonRequest(BaseModel):
    resume_version_id: uuid.UUID
    job_id: uuid.UUID


class MatchComparisonResponse(BaseModel):
    overall_match_score: Optional[float] = None
    ats_score: Optional[float] = None
    matched_skills: Optional[Dict[str, Any]] = None
    missing_skills: Optional[Dict[str, Any]] = None
    missing_technologies: Optional[Dict[str, Any]] = None
    missing_certifications: Optional[Dict[str, Any]] = None
    experience_gap: Optional[Dict[str, Any]] = None
    education_gap: Optional[Dict[str, Any]] = None
    strength_analysis: Optional[Dict[str, Any]] = None
    weakness_analysis: Optional[Dict[str, Any]] = None
    priority_learning_roadmap: Optional[Dict[str, Any]] = None
    resume_improvements: Optional[Dict[str, Any]] = None
    estimated_match_after_learning: Optional[float] = None
    interview_preparation: Optional[Dict[str, Any]] = None
    final_recommendation: Optional[Dict[str, Any]] = None
