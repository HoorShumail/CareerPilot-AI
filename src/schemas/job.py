import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class JobParsedData(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    remote: Optional[bool] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    education: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    soft_skills: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    raw_description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobInsights(BaseModel):
    executive_summary: Optional[Dict[str, Any]] = None
    ats_keywords: Optional[Dict[str, Any]] = None
    hidden_requirements: Optional[Dict[str, Any]] = None
    missing_certifications: Optional[Dict[str, Any]] = None
    interview_focus_areas: Optional[Dict[str, Any]] = None
    strengths: Optional[Dict[str, Any]] = None
    risks: Optional[Dict[str, Any]] = None
    important_technologies: Optional[Dict[str, Any]] = None
    recommended_learning_topics: Optional[Dict[str, Any]] = None
    resume_optimization_suggestions: Optional[Dict[str, Any]] = None
    company_insights: Optional[Dict[str, Any]] = None
    embedding: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class JobBase(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    company: str
    url: Optional[str] = None
    raw_description: Optional[str] = None
    parsed_jd: Optional[Dict[str, Any]] = None
    required_skills: Optional[Dict[str, Any]] = None
    preferred_skills: Optional[Dict[str, Any]] = None
    experience_level: Optional[str] = None
    salary_range: Optional[str] = None
    location: Optional[str] = None
    is_remote: bool
    ai_summary: Optional[Dict[str, Any]] = None
    ats_keywords: Optional[Dict[str, Any]] = None
    hidden_requirements: Optional[Dict[str, Any]] = None
    interview_focus: Optional[Dict[str, Any]] = None
    missing_certifications: Optional[Dict[str, Any]] = None
    red_flags: Optional[Dict[str, Any]] = None
    extracted_keywords: Optional[Dict[str, Any]] = None
    embedding: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobCreate(BaseModel):
    user_id: uuid.UUID
    title: str
    company: str
    url: Optional[str] = None
    raw_description: Optional[str] = None
    parsed_jd: Optional[Dict[str, Any]] = None
    required_skills: Optional[Dict[str, Any]] = None
    preferred_skills: Optional[Dict[str, Any]] = None
    experience_level: Optional[str] = None
    salary_range: Optional[str] = None
    location: Optional[str] = None
    is_remote: Optional[bool] = False
    ai_summary: Optional[Dict[str, Any]] = None
    ats_keywords: Optional[Dict[str, Any]] = None
    hidden_requirements: Optional[Dict[str, Any]] = None
    interview_focus: Optional[Dict[str, Any]] = None
    missing_certifications: Optional[Dict[str, Any]] = None
    red_flags: Optional[Dict[str, Any]] = None
    extracted_keywords: Optional[Dict[str, Any]] = None
    embedding: Optional[Dict[str, Any]] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    url: Optional[str] = None
    raw_description: Optional[str] = None
    parsed_jd: Optional[Dict[str, Any]] = None
    required_skills: Optional[Dict[str, Any]] = None
    preferred_skills: Optional[Dict[str, Any]] = None
    experience_level: Optional[str] = None
    salary_range: Optional[str] = None
    location: Optional[str] = None
    is_remote: Optional[bool] = None
    ai_summary: Optional[Dict[str, Any]] = None
    ats_keywords: Optional[Dict[str, Any]] = None
    hidden_requirements: Optional[Dict[str, Any]] = None
    interview_focus: Optional[Dict[str, Any]] = None
    missing_certifications: Optional[Dict[str, Any]] = None
    red_flags: Optional[Dict[str, Any]] = None
    extracted_keywords: Optional[Dict[str, Any]] = None
    embedding: Optional[Dict[str, Any]] = None


class JobCreateRequest(BaseModel):
    title: str
    company: str
    raw_description: Optional[str] = None
    url: Optional[str] = None


class JobResponse(JobBase):
    pass
