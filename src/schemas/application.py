import uuid
from datetime import date, datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class MatchAnalysis(BaseModel):
    overall_match_score: Optional[float] = None
    skills_match: Optional[Dict[str, Any]] = None
    missing_skills: Optional[Dict[str, Any]] = None
    missing_technologies: Optional[Dict[str, Any]] = None
    missing_certifications: Optional[Dict[str, Any]] = None
    experience_gap: Optional[str] = None
    education_gap: Optional[str] = None
    strength_analysis: Optional[Dict[str, Any]] = None
    weakness_analysis: Optional[Dict[str, Any]] = None
    ats_compatibility_score: Optional[float] = None
    priority_learning_roadmap: Optional[Dict[str, Any]] = None
    detailed_gap_analysis: Optional[Dict[str, Any]] = None
    final_recommendation: Optional[str] = None
    gap_analysis: Optional[Dict[str, Any]] = None
    strengths: Optional[Dict[str, Any]] = None
    learning_recommendations: Optional[Dict[str, Any]] = None
    estimated_match_after_learning: Optional[float] = None


class ApplicationBase(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    resume_version_id: Optional[uuid.UUID] = None
    status: str
    applied_date: Optional[date] = None
    match_score: Optional[float] = None
    skills_match: Optional[Dict[str, Any]] = None
    missing_skills: Optional[Dict[str, Any]] = None
    missing_technologies: Optional[Dict[str, Any]] = None
    missing_certifications: Optional[Dict[str, Any]] = None
    experience_gap: Optional[str] = None
    education_gap: Optional[str] = None
    strength_analysis: Optional[Dict[str, Any]] = None
    weakness_analysis: Optional[Dict[str, Any]] = None
    ats_compatibility_score: Optional[float] = None
    priority_learning_roadmap: Optional[Dict[str, Any]] = None
    detailed_gap_analysis: Optional[Dict[str, Any]] = None
    final_recommendation: Optional[str] = None
    gap_analysis: Optional[Dict[str, Any]] = None
    strengths: Optional[Dict[str, Any]] = None
    learning_recommendations: Optional[Dict[str, Any]] = None
    estimated_match_after_learning: Optional[float] = None
    recruiter_notes: Optional[Dict[str, Any]] = None
    recruiter_sim_results: Optional[Dict[str, Any]] = None
    cover_letter: Optional[Dict[str, Any]] = None
    notes: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationCreate(BaseModel):
    user_id: uuid.UUID
    job_id: uuid.UUID
    resume_version_id: Optional[uuid.UUID] = None
    status: Optional[str] = "saved"
    applied_date: Optional[date] = None
    match_score: Optional[float] = None
    skills_match: Optional[Dict[str, Any]] = None
    missing_skills: Optional[Dict[str, Any]] = None
    missing_technologies: Optional[Dict[str, Any]] = None
    missing_certifications: Optional[Dict[str, Any]] = None
    experience_gap: Optional[str] = None
    education_gap: Optional[str] = None
    strength_analysis: Optional[Dict[str, Any]] = None
    weakness_analysis: Optional[Dict[str, Any]] = None
    ats_compatibility_score: Optional[float] = None
    priority_learning_roadmap: Optional[Dict[str, Any]] = None
    detailed_gap_analysis: Optional[Dict[str, Any]] = None
    final_recommendation: Optional[str] = None
    gap_analysis: Optional[Dict[str, Any]] = None
    strengths: Optional[Dict[str, Any]] = None
    learning_recommendations: Optional[Dict[str, Any]] = None
    estimated_match_after_learning: Optional[float] = None
    recruiter_notes: Optional[Dict[str, Any]] = None
    recruiter_sim_results: Optional[Dict[str, Any]] = None
    cover_letter: Optional[Dict[str, Any]] = None
    notes: Optional[Dict[str, Any]] = None


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    applied_date: Optional[date] = None
    match_score: Optional[float] = None
    skills_match: Optional[Dict[str, Any]] = None
    missing_skills: Optional[Dict[str, Any]] = None
    missing_technologies: Optional[Dict[str, Any]] = None
    missing_certifications: Optional[Dict[str, Any]] = None
    experience_gap: Optional[str] = None
    education_gap: Optional[str] = None
    strength_analysis: Optional[Dict[str, Any]] = None
    weakness_analysis: Optional[Dict[str, Any]] = None
    ats_compatibility_score: Optional[float] = None
    priority_learning_roadmap: Optional[Dict[str, Any]] = None
    detailed_gap_analysis: Optional[Dict[str, Any]] = None
    final_recommendation: Optional[str] = None
    gap_analysis: Optional[Dict[str, Any]] = None
    strengths: Optional[Dict[str, Any]] = None
    learning_recommendations: Optional[Dict[str, Any]] = None
    estimated_match_after_learning: Optional[float] = None
    recruiter_notes: Optional[Dict[str, Any]] = None
    recruiter_sim_results: Optional[Dict[str, Any]] = None
    cover_letter: Optional[Dict[str, Any]] = None
    notes: Optional[Dict[str, Any]] = None


class ApplicationCreateRequest(BaseModel):
    job_id: uuid.UUID
    resume_version_id: Optional[uuid.UUID] = None
    status: Optional[str] = "saved"
    applied_date: Optional[date] = None


class ApplicationUpdateRequest(BaseModel):
    status: Optional[str] = None
    applied_date: Optional[date] = None
    notes: Optional[Dict[str, Any]] = None


class ApplicationResponse(ApplicationBase):
    pass
