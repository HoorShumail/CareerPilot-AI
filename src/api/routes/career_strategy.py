print(">>> career_strategy router loaded")
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_career_strategy_service, get_current_user, get_db_session
from src.db.models.user import User
from src.exceptions.ai_service import AIServiceException
from src.exceptions.base import CareerPilotException
from src.schemas.career_strategy import CareerStrategyProgressCreate, CareerStrategyProgressResponse, CareerStrategyResponse
from src.services.career_strategy_service import CareerStrategyService
from src.utils.json_repair import JSONParsingError

router = APIRouter()


def _handle_route_exception(exc: Exception) -> None:
    """
    Maps domain exceptions to HTTP status codes.

    Mapping rules:
    - JSONParsingError / AIServiceException → 500 (AI processing failure)
    - CareerPilotException → uses its own status_code
    - ValueError with 'not found' → 404 (resource not found)
    - All other exceptions → 500 (internal server error)

    NEVER returns 404 for AI/JSON processing failures.
    """
    # AI response parsing failures → always 500
    if isinstance(exc, JSONParsingError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Career strategy generation failed due to malformed AI response: {str(exc)}",
        ) from exc

    # Typed AI service exceptions → always 500
    if isinstance(exc, AIServiceException):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Career strategy generation failed: {exc.message}",
        ) from exc

    # CareerPilot domain exceptions → use their built-in status code
    if isinstance(exc, CareerPilotException):
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

    # ValueError: distinguish between "not found" (404) and other errors (500)
    if isinstance(exc, ValueError):
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg) from exc
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg) from exc

    # RuntimeError from LLM provider → 500
    if isinstance(exc, RuntimeError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(exc)}",
        ) from exc

    # All other exceptions → 500
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/career-strategy",
    response_model=CareerStrategyResponse,
    summary="Get the latest career strategy",
    description="Returns the latest generated strategy. If none exists, one is generated automatically.",
    responses={
        status.HTTP_200_OK: {"description": "Career strategy returned successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "AI processing or internal error"},
    },
)
async def get_strategy(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: Any = Depends(get_career_strategy_service),
) -> Any:
    try:
        return await service.get_strategy(db, current_user.id)
    except Exception as exc:
        _handle_route_exception(exc)


@router.get(
    "/career-strategy/roadmap",
    response_model=dict,
    summary="Get the roadmap",
    description="Returns the roadmap section from the latest strategy.",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "AI processing or internal error"},
    },
)
async def get_roadmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: Any = Depends(get_career_strategy_service),
) -> Any:
    try:
        return await service.get_roadmap(db, current_user.id)
    except Exception as exc:
        _handle_route_exception(exc)


@router.get(
    "/career-strategy/weekly-goals",
    response_model=list,
    summary="Get weekly goals",
    description="Returns the weekly goals from the latest strategy.",
)
async def get_weekly_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: Any = Depends(get_career_strategy_service),
) -> Any:
    try:
        return await service.get_weekly_goals(db, current_user.id)
    except Exception as exc:
        _handle_route_exception(exc)


@router.get(
    "/career-strategy/monthly-goals",
    response_model=list,
    summary="Get monthly goals",
    description="Returns the monthly goals from the latest strategy.",
)
async def get_monthly_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: Any = Depends(get_career_strategy_service),
) -> Any:
    try:
        return await service.get_monthly_goals(db, current_user.id)
    except Exception as exc:
        _handle_route_exception(exc)


@router.get(
    "/career-strategy/certifications",
    response_model=list,
    summary="Get certification recommendations",
    description="Returns the certification recommendations from the latest strategy.",
)
async def get_certifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: Any = Depends(get_career_strategy_service),
) -> Any:
    try:
        return await service.get_certifications(db, current_user.id)
    except Exception as exc:
        _handle_route_exception(exc)


@router.get(
    "/career-strategy/projects",
    response_model=list,
    summary="Get project recommendations",
    description="Returns the project recommendations from the latest strategy.",
)
async def get_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: Any = Depends(get_career_strategy_service),
) -> Any:
    try:
        return await service.get_projects(db, current_user.id)
    except Exception as exc:
        _handle_route_exception(exc)


@router.get(
    "/career-strategy/progress",
    response_model=dict,
    summary="Get progress snapshot",
    description="Returns the latest progress snapshot for the user's strategy.",
)
async def get_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: Any = Depends(get_career_strategy_service),
) -> Any:
    try:
        return await service.get_progress(db, current_user.id)
    except Exception as exc:
        _handle_route_exception(exc)


@router.patch(
    "/career-strategy/progress",
    response_model=CareerStrategyProgressResponse,
    summary="Update progress snapshot",
    description="Updates the user progress snapshot for the latest strategy.",
)
async def update_progress(
    payload: CareerStrategyProgressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: Any = Depends(get_career_strategy_service),
) -> Any:
    try:
        return await service.update_progress(db, current_user.id, payload)
    except Exception as exc:
        _handle_route_exception(exc)


@router.post(
    "/career-strategy/refresh",
    response_model=CareerStrategyResponse,
    summary="Refresh or generate the latest strategy",
    description="Refreshes the career digital twin, regenerates the strategy, and saves the new progress snapshot.",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "AI processing or internal error"},
    },
)
async def refresh_strategy(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: Any = Depends(get_career_strategy_service),
) -> Any:
    try:
        return await service.refresh_strategy(db, current_user.id)
    except Exception as exc:
        _handle_route_exception(exc)
