import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

class ResumeCreate(BaseModel):
    user_id: uuid.UUID
    original_filename: str
    file_path: str
    file_type: str
    parsed_content: Dict[str, Any]
    is_primary: Optional[bool] = False

class ResumeVersionCreate(BaseModel):
    resume_id: uuid.UUID
    content: Dict[str, Any]
    source_description: Optional[str] = None
    version_type: Optional[str] = "upload"

class ResumeBase(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    original_filename: str
    file_path: str
    file_type: str
    parsed_content: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ResumeVersionBase(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    content: Dict[str, Any]
    source_description: Optional[str]
    version_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ResumeResponse(ResumeBase):
    versions: List[ResumeVersionBase] = Field(default_factory=list)

class ResumeVersionResponse(ResumeVersionBase):
    pass

class ResumeUpdate(BaseModel):
    parsed_content: Dict[str, Any]
