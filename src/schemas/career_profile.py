import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class CareerProfileCreate(BaseModel):
    user_id: Optional[uuid.UUID] = None
    career_summary: Optional[Dict[str, Any]] = None
    experience_level: Optional[str] = None
    strongest_skills: Optional[Dict[str, Any]] = None
    weakest_skills: Optional[Dict[str, Any]] = None
    ai_maturity_score: Optional[float] = None
    confidence_score: Optional[float] = None
    preferred_industries: Optional[Dict[str, Any] | list[Any]] = None
    preferred_roles: Optional[Dict[str, Any] | list[Any]] = None
    preferred_locations: Optional[Dict[str, Any] | list[Any]] = None
    salary_expectations: Optional[Dict[str, Any]] = None
    remote_preference: Optional[Dict[str, Any]] = None
    skills: Optional[Dict[str, Any]] = None
    experience_summary: Optional[Dict[str, Any]] = None
    education_summary: Optional[Dict[str, Any]] = None
    github_data: Optional[Dict[str, Any]] = None
    linkedin_data: Optional[Dict[str, Any]] = None
    certifications: Optional[Dict[str, Any]] = None
    strengths: Optional[Dict[str, Any]] = None
    weaknesses: Optional[Dict[str, Any]] = None
    overall_readiness_score: Optional[float] = None
    overall_growth_score: Optional[float] = None
    readiness_score: Optional[float] = None
    promotion_readiness: Optional[float] = None
    ai_career_level: Optional[str] = None
    growth_summary: Optional[Dict[str, Any]] = None
    learning_recommendations: Optional[Dict[str, Any]] = None
    learning_roadmap: Optional[Dict[str, Any]] = None
    skill_intelligence: Optional[Dict[str, Any]] = None
    career_gap_analysis: Optional[Dict[str, Any]] = None


class CareerProfileUpdate(BaseModel):
    career_summary: Optional[Dict[str, Any]] = None
    experience_level: Optional[str] = None
    strongest_skills: Optional[Dict[str, Any]] = None
    weakest_skills: Optional[Dict[str, Any]] = None
    ai_maturity_score: Optional[float] = None
    confidence_score: Optional[float] = None
    preferred_industries: Optional[Dict[str, Any] | list[Any]] = None
    preferred_roles: Optional[Dict[str, Any] | list[Any]] = None
    preferred_locations: Optional[Dict[str, Any] | list[Any]] = None
    salary_expectations: Optional[Dict[str, Any]] = None
    remote_preference: Optional[Dict[str, Any]] = None
    skills: Optional[Dict[str, Any]] = None
    experience_summary: Optional[Dict[str, Any]] = None
    education_summary: Optional[Dict[str, Any]] = None
    github_data: Optional[Dict[str, Any]] = None
    linkedin_data: Optional[Dict[str, Any]] = None
    certifications: Optional[Dict[str, Any]] = None
    strengths: Optional[Dict[str, Any]] = None
    weaknesses: Optional[Dict[str, Any]] = None
    overall_readiness_score: Optional[float] = None
    overall_growth_score: Optional[float] = None
    readiness_score: Optional[float] = None
    promotion_readiness: Optional[float] = None
    ai_career_level: Optional[str] = None
    growth_summary: Optional[Dict[str, Any]] = None
    learning_recommendations: Optional[Dict[str, Any]] = None
    learning_roadmap: Optional[Dict[str, Any]] = None
    skill_intelligence: Optional[Dict[str, Any]] = None
    career_gap_analysis: Optional[Dict[str, Any]] = None


class CareerProfileBase(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    career_summary: Optional[Dict[str, Any]] = None
    experience_level: Optional[str] = None
    strongest_skills: Optional[Dict[str, Any]] = None
    weakest_skills: Optional[Dict[str, Any]] = None
    ai_maturity_score: Optional[float] = None
    confidence_score: Optional[float] = None
    preferred_industries: Optional[Dict[str, Any] | list[Any]] = None
    preferred_roles: Optional[Dict[str, Any] | list[Any]] = None
    preferred_locations: Optional[Dict[str, Any] | list[Any]] = None
    salary_expectations: Optional[Dict[str, Any]] = None
    remote_preference: Optional[Dict[str, Any]] = None
    skills: Optional[Dict[str, Any]] = None
    experience_summary: Optional[Dict[str, Any]] = None
    education_summary: Optional[Dict[str, Any]] = None
    github_data: Optional[Dict[str, Any]] = None
    linkedin_data: Optional[Dict[str, Any]] = None
    certifications: Optional[Dict[str, Any]] = None
    strengths: Optional[Dict[str, Any]] = None
    weaknesses: Optional[Dict[str, Any]] = None
    overall_readiness_score: Optional[float] = None
    overall_growth_score: Optional[float] = None
    readiness_score: Optional[float] = None
    promotion_readiness: Optional[float] = None
    ai_career_level: Optional[str] = None
    growth_summary: Optional[Dict[str, Any]] = None
    learning_recommendations: Optional[Dict[str, Any]] = None
    learning_roadmap: Optional[Dict[str, Any]] = None
    skill_intelligence: Optional[Dict[str, Any]] = None
    career_gap_analysis: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CareerProfileResponse(CareerProfileBase):
    pass


class CareerProfileSnapshotCreate(BaseModel):
    profile_id: uuid.UUID
    snapshot_payload: Optional[Dict[str, Any]] = None
    snapshot_label: Optional[str] = None


class CareerProfileSnapshotResponse(BaseModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    snapshot_payload: Optional[Dict[str, Any]] = None
    snapshot_label: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
