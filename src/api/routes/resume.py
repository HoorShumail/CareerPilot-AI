from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.db.engine import get_db_session
from src.schemas.resume import (
    ResumeResponse,
    ResumeVersionResponse,
    ResumeUpdate,
)
from src.services.resume_service import ResumeService
from src.db.models.user import User

router = APIRouter()
service = ResumeService()


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:

    allowed_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type",
        )

    file_bytes = await file.read()

    resume = await service.upload_resume(
        db,
        current_user.id,
        file.filename,
        file_bytes,
        file.content_type,
    )

    versions = await service.get_resume_versions(
        db,
        resume.id,
    )

    response = ResumeResponse.model_validate(resume)

    response.versions = [
        ResumeVersionResponse.model_validate(v)
        for v in versions
    ]

    return response


@router.get(
    "/",
    response_model=list[ResumeResponse],
)
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:

    resumes = await service.get_user_resumes(
        db,
        current_user.id,
    )

    response_items = []

    for resume in resumes:

        versions = await service.get_resume_versions(
            db,
            resume.id,
        )

        response = ResumeResponse.model_validate(resume)

        response.versions = [
            ResumeVersionResponse.model_validate(v)
            for v in versions
        ]

        response_items.append(response)

    return response_items


@router.get(
    "/{resume_id}/versions",
    response_model=list[ResumeVersionResponse],
)
async def list_resume_versions(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:

    resumes = await service.get_user_resumes(
        db,
        current_user.id,
    )

    if not any(r.id == resume_id for r in resumes):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    versions = await service.get_resume_versions(
        db,
        resume_id,
    )

    return [
        ResumeVersionResponse.model_validate(v)
        for v in versions
    ]


@router.get(
    "/{resume_id}/download",
)
async def download_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:

    resumes = await service.get_user_resumes(
        db,
        current_user.id,
    )

    resume = next(
        (r for r in resumes if r.id == resume_id),
        None,
    )

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    resume_path = Path(resume.file_path)
    if not resume_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file not found on server",
        )

    media_type = resume.file_type or "application/octet-stream"
    return FileResponse(
        path=str(resume_path),
        filename=resume.original_filename,
        media_type=media_type,
    )


@router.put(
    "/{resume_id}",
    response_model=ResumeResponse,
)
async def update_resume(
    resume_id: UUID,
    parsed_content: ResumeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:

    resumes = await service.get_user_resumes(
        db,
        current_user.id,
    )

    resume = next(
        (r for r in resumes if r.id == resume_id),
        None,
    )

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    updated = await service.update_resume(
        db,
        resume,
        parsed_content.parsed_content,
    )

    versions = await service.get_resume_versions(
        db,
        resume.id,
    )

    response = ResumeResponse.model_validate(updated)

    response.versions = [
        ResumeVersionResponse.model_validate(v)
        for v in versions
    ]

    return response