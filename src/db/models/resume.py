import uuid
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import BaseModel


class Resume(BaseModel):
    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)  # pdf, docx
    parsed_content: Mapped[dict] = mapped_column(JSONB, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="resumes")
    versions = relationship(
        "ResumeVersion",
        back_populates="resume",
        cascade="all, delete-orphan",
    )


class ResumeVersion(BaseModel):
    __tablename__ = "resume_versions"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id"),
        nullable=False,
    )

    target_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id"),
        nullable=True,
    )

    version_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="upload",
    )

    source_description: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    content: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    # Relationships
    resume = relationship(
        "Resume",
        back_populates="versions",
    )

    job = relationship(
        "Job",
        back_populates="resume_versions",
    )

    applications = relationship(
        "Application",
        back_populates="resume_version",
        cascade="all, delete-orphan",
    )
    matches = relationship(
        "Match",
        back_populates="resume_version",
        cascade="all, delete-orphan",
    )