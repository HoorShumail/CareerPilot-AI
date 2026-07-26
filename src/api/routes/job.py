from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db_session, get_job_service
from src.db.models.user import User
from src.schemas.job import JobResponse, JobUpdate
from src.services.job_service import JobService

router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    request: Request,
    raw_description: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: JobService = Depends(get_job_service),
) -> Any:
    if request.headers.get("content-type", "").startswith("application/json"):
        payload = await request.json()
        raw_description = payload.get("raw_description")
        title = payload.get("title")
        company = payload.get("company")
        url = payload.get("url")
        file = None

    if file is not None:
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF uploads are supported for file-based job ingestion.",
            )
        if not title or not company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job title and company are required for PDF ingestion.",
            )

        file_bytes = await file.read()
        return await service.create_job_from_pdf(
            db,
            current_user.id,
            file_bytes,
            file.content_type,
            title,
            company,
            url,
        )

    if not raw_description or not title or not company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job title, company, and description are required when uploading job text.",
        )

    return await service.create_job_from_text(
        db,
        current_user.id,
        raw_description,
        title,
        company,
        url,
    )


@router.get("/", response_model=list[JobResponse])
async def list_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: JobService = Depends(get_job_service),
) -> Any:
    return await service.list_jobs(db, current_user.id)


@router.get("/{job_id}", response_model=JobResponse)
async def read_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: JobService = Depends(get_job_service),
) -> Any:
    try:
        return await service.get_job(db, current_user.id, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: UUID,
    update_data: JobUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: JobService = Depends(get_job_service),
) -> Any:
    try:
        return await service.update_job(db, current_user.id, job_id, update_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{job_id}", response_model=JobResponse)
async def delete_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: JobService = Depends(get_job_service),
) -> Any:
    try:
        return await service.delete_job(db, current_user.id, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{job_id}/insights", response_model=JobResponse)
async def refresh_job_insights(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: JobService = Depends(get_job_service),
) -> Any:
    try:
        return await service.refresh_job_insights(db, current_user.id, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
