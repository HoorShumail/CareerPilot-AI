from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db_session, get_interview_service
from src.db.models.user import User
from src.schemas.interview import InterviewAnswerRequest, InterviewSessionResponse, InterviewStartRequest
from src.services.interview_service import InterviewService

router = APIRouter()


@router.post("/start", response_model=InterviewSessionResponse)
async def start_session(
    payload: InterviewStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: InterviewService = Depends(get_interview_service),
) -> Any:
    try:
        return await service.start_session(db, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{session_id}/answer", response_model=dict)
async def answer_question(
    session_id: UUID,
    payload: InterviewAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: InterviewService = Depends(get_interview_service),
) -> Any:
    try:
        return await service.answer_question(db, current_user.id, session_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{session_id}/finish", response_model=InterviewSessionResponse)
async def finish_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: InterviewService = Depends(get_interview_service),
) -> Any:
    try:
        return await service.finish_session(db, current_user.id, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/history", response_model=list[InterviewSessionResponse])
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: InterviewService = Depends(get_interview_service),
) -> Any:
    return await service.get_history(db, current_user.id)


@router.get("/{session_id}", response_model=InterviewSessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: InterviewService = Depends(get_interview_service),
) -> Any:
    try:
        return await service.get_session(db, current_user.id, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/analytics", response_model=dict)
async def get_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: InterviewService = Depends(get_interview_service),
) -> Any:
    return await service.get_analytics(db, current_user.id)


@router.get("/{session_id}/feedback", response_model=dict)
async def get_feedback(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: InterviewService = Depends(get_interview_service),
) -> Any:
    try:
        return await service.get_feedback(db, current_user.id, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
