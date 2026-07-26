from datetime import date
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db_session, get_application_service
from src.db.models.user import User
from src.schemas.application import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationUpdateRequest,
)
from src.services.application_service import ApplicationService

router = APIRouter()


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    application_in: ApplicationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: ApplicationService = Depends(get_application_service),
) -> Any:
    return await service.create_application(
        db,
        current_user.id,
        application_in.job_id,
        application_in.resume_version_id,
        status=application_in.status,
        applied_date=application_in.applied_date,
    )


@router.get("/", response_model=list[ApplicationResponse])
async def list_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: ApplicationService = Depends(get_application_service),
) -> Any:
    return await service.list_applications(db, current_user.id)


@router.get("/{application_id}", response_model=ApplicationResponse)
async def read_application(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: ApplicationService = Depends(get_application_service),
) -> Any:
    try:
        return await service.get_application(db, current_user.id, application_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{application_id}/match", response_model=ApplicationResponse)
async def refresh_application_match(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: ApplicationService = Depends(get_application_service),
) -> Any:
    try:
        return await service.refresh_match(db, current_user.id, application_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: UUID,
    update_data: ApplicationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: ApplicationService = Depends(get_application_service),
) -> Any:
    try:
        return await service.update_application(db, current_user.id, application_id, update_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{application_id}", response_model=ApplicationResponse)
async def delete_application(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: ApplicationService = Depends(get_application_service),
) -> Any:
    try:
        return await service.delete_application(db, current_user.id, application_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
