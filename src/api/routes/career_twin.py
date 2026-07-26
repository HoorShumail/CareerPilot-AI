from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db_session, get_career_twin_service
from src.db.models.user import User
from src.schemas.career_profile import CareerProfileResponse, CareerProfileSnapshotResponse
from src.services.career_twin_service import CareerTwinService

router = APIRouter()


@router.get("/profile", response_model=CareerProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: CareerTwinService = Depends(get_career_twin_service),
) -> Any:
    try:
        return await service.get_profile(db, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/timeline", response_model=list[CareerProfileSnapshotResponse])
async def get_timeline(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: CareerTwinService = Depends(get_career_twin_service),
) -> Any:
    try:
        return await service.get_timeline(db, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/refresh", response_model=CareerProfileResponse)
async def refresh_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: CareerTwinService = Depends(get_career_twin_service),
) -> Any:
    try:
        return await service.refresh_profile(db, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/recommendations", response_model=dict)
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: CareerTwinService = Depends(get_career_twin_service),
) -> Any:
    try:
        return await service.get_recommendations(db, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/strengths", response_model=dict)
async def get_strengths(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: CareerTwinService = Depends(get_career_twin_service),
) -> Any:
    try:
        return await service.get_strengths(db, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/weaknesses", response_model=dict)
async def get_weaknesses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: CareerTwinService = Depends(get_career_twin_service),
) -> Any:
    try:
        return await service.get_weaknesses(db, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/learning-roadmap", response_model=dict)
async def get_learning_roadmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: CareerTwinService = Depends(get_career_twin_service),
) -> Any:
    try:
        return await service.get_learning_roadmap(db, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
