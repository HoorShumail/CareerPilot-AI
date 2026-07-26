import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.schemas.auth import TokenPayload
from src.db.engine import get_db_session
from src.db.models.user import User
from src.db.repositories.user_repo import user_repo
from src.infrastructure.llm.openai_provider import OpenAIProvider
from src.services.application_service import ApplicationService
from src.services.career_intelligence_service import CareerCoachService, CareerForecastService, LearningPlannerService, MarketIntelligenceService
from src.services.career_strategy_service import CareerStrategyService
from src.services.career_twin_service import CareerTwinService
from src.services.interview_service import InterviewService
from src.services.job_service import JobService
from src.services.resume_match_service import ResumeMatchService
from src.utils.security import ALGORITHM, TOKEN_TYPE_ACCESS

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_current_user(
    db: AsyncSession = Depends(get_db_session),
    token: str = Depends(oauth2_scheme),
) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        token_data = TokenPayload(**payload)

    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_data.type != TOKEN_TYPE_ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(token_data.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid subject",
        )

    user = await user_repo.get(db, id=user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Inactive user",
        )

    return user


def get_llm_provider() -> OpenAIProvider:
    """
    Creates the LLM provider using official OpenAI API configuration.
    """
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("No LLM API key configured. Set OPENAI_API_KEY in .env.")

    return OpenAIProvider(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_API_BASE_URL,
        model=settings.LLM_MODEL,
        embedding_model=settings.EMBEDDING_MODEL,
    )



def get_job_service(
    llm_provider: OpenAIProvider = Depends(get_llm_provider),
) -> JobService:
    return JobService(llm_provider)


def get_application_service(
    llm_provider: OpenAIProvider = Depends(get_llm_provider),
) -> ApplicationService:
    return ApplicationService(llm_provider)


def get_resume_match_service(
    llm_provider: OpenAIProvider = Depends(get_llm_provider),
) -> ResumeMatchService:
    return ResumeMatchService(llm_provider)


def get_career_twin_service(
    llm_provider: OpenAIProvider = Depends(get_llm_provider),
) -> CareerTwinService:
    return CareerTwinService(llm_provider)


def get_career_forecast_service(
    llm_provider: OpenAIProvider = Depends(get_llm_provider),
) -> CareerForecastService:
    return CareerForecastService(llm_provider)


def get_career_coach_service(
    llm_provider: OpenAIProvider = Depends(get_llm_provider),
) -> CareerCoachService:
    return CareerCoachService(llm_provider)


def get_market_intelligence_service(
    llm_provider: OpenAIProvider = Depends(get_llm_provider),
) -> MarketIntelligenceService:
    return MarketIntelligenceService(llm_provider)


def get_learning_planner_service(
    llm_provider: OpenAIProvider = Depends(get_llm_provider),
) -> LearningPlannerService:
    return LearningPlannerService(llm_provider)


def get_career_strategy_service(
    llm_provider: OpenAIProvider = Depends(get_llm_provider),
) -> CareerStrategyService:
    return CareerStrategyService(llm_provider)


def get_interview_service(
    llm_provider: OpenAIProvider = Depends(get_llm_provider),
) -> InterviewService:
    return InterviewService(llm_provider)