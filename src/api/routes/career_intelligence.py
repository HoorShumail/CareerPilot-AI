from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_career_coach_service, get_career_forecast_service, get_current_user, get_db_session, get_learning_planner_service, get_market_intelligence_service
from src.db.models.user import User
from src.schemas.career_intelligence import CoachActionPlanRequest, CoachAdviceRequest, CoachChatRequest, CoachChatResponse, CoachGoalsRequest, ForecastResponse, LearningPlanResponse, MarketIntelligenceResponse, SimulationRequest, SimulationResponse
from src.services.career_intelligence_service import CareerCoachService, CareerForecastService, LearningPlannerService, MarketIntelligenceService

router = APIRouter()


@router.post("/chat", response_model=CoachChatResponse)
async def chat(
    payload: CoachChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: CareerCoachService = Depends(get_career_coach_service),
) -> Any:
    try:
        return await service.generate_chat(db, current_user.id, payload.message, payload.conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/advice", response_model=CoachChatResponse)
async def advice(
    payload: CoachAdviceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: CareerCoachService = Depends(get_career_coach_service),
) -> Any:
    try:
        return await service.advice(db, current_user.id, payload.question, payload.conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/action-plan", response_model=CoachChatResponse)
async def action_plan(
    payload: CoachActionPlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: CareerCoachService = Depends(get_career_coach_service),
) -> Any:
    try:
        return await service.action_plan(db, current_user.id, payload.goal, payload.conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/goals", response_model=CoachChatResponse)
async def goals(
    payload: CoachGoalsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: CareerCoachService = Depends(get_career_coach_service),
) -> Any:
    try:
        return await service.goals(db, current_user.id, payload.goals, payload.conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/forecast", response_model=ForecastResponse)
async def forecast(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: CareerForecastService = Depends(get_career_forecast_service),
) -> Any:
    try:
        return await service.build_forecast(db, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/market-intelligence", response_model=MarketIntelligenceResponse)
async def market_intelligence(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: MarketIntelligenceService = Depends(get_market_intelligence_service),
) -> Any:
    try:
        return await service.build_market_intelligence(db, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/learning-plan", response_model=LearningPlanResponse)
async def learning_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: LearningPlannerService = Depends(get_learning_planner_service),
) -> Any:
    try:
        return await service.build_learning_plan(db, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
