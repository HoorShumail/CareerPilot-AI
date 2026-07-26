import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field  # <-- added Field


class InterviewStartRequest(BaseModel):
    interview_type: str
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    difficulty: Optional[str] = None
    duration_seconds: Optional[int] = None


class InterviewAnswerRequest(BaseModel):
    question_index: int = Field(..., ge=0)  # <-- added, with validation
    answer: str


class InterviewQuestion(BaseModel):
    question: str
    category: Optional[str] = None
    expected_answer: Optional[str] = None


class InterviewSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    interview_type: Optional[str] = None
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    difficulty: Optional[str] = None
    duration_seconds: Optional[int] = None
    questions: Optional[List[InterviewQuestion]] = None
    overall_score: Optional[float] = None
    feedback_summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)