from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db_session, get_resume_match_service
from src.db.models.user import User
from src.schemas.match import MatchComparisonRequest, MatchComparisonResponse, MatchResponse
from src.services.resume_match_service import ResumeMatchService

router = APIRouter()


@router.post("/compare", response_model=MatchResponse)
async def compare_resume_to_job(
    payload: MatchComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: ResumeMatchService = Depends(get_resume_match_service),
) -> Any:
    try:
        return await service.compare_resume_to_job(db, current_user.id, payload.resume_version_id, payload.job_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/{match_id}", response_model=MatchResponse)
async def read_match(
    match_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: ResumeMatchService = Depends(get_resume_match_service),
) -> Any:
    try:
        return await service.get_match(db, current_user.id, match_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/", response_model=list[MatchResponse])
async def list_matches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: ResumeMatchService = Depends(get_resume_match_service),
) -> Any:
    return await service.list_matches(db, current_user.id)


@router.get("/resume/{resume_version_id}", response_model=list[MatchResponse])
async def list_matches_for_resume(
    resume_version_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: ResumeMatchService = Depends(get_resume_match_service),
) -> Any:
    try:
        return await service.get_matches_for_resume(db, current_user.id, resume_version_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/job/{job_id}", response_model=list[MatchResponse])
async def list_matches_for_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: ResumeMatchService = Depends(get_resume_match_service),
) -> Any:
    try:
        return await service.get_matches_for_job(db, current_user.id, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{match_id}", response_model=MatchResponse)
async def delete_match(
    match_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: ResumeMatchService = Depends(get_resume_match_service),
) -> Any:
    try:
        return await service.delete_match(db, current_user.id, match_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
