from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.schemas.auth import (
    EmailVerificationConfirm,
    EmailVerificationRequest,
    Message,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    Token,
)
from src.schemas.user import UserCreate, UserResponse, UserUpdate
from src.db.engine import get_db_session
from src.db.models.user import User
from src.services.auth_service import AuthService

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    *,
    db: AsyncSession = Depends(get_db_session),
    user_in: UserCreate,
) -> Any:
    """Create new user."""
    auth_service = AuthService(db)
    return await auth_service.register_user(user_in)

@router.post("/login", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db_session),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login, get an access token for future requests."""
    auth_service = AuthService(db)
    return await auth_service.authenticate_user(form_data.username, form_data.password)

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_request: RefreshTokenRequest = Depends(),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    auth_service = AuthService(db)
    return await auth_service.refresh_tokens(refresh_request.refresh_token)

@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get current user."""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    *,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    user_in: UserUpdate,
) -> Any:
    """Update current user profile."""
    auth_service = AuthService(db)
    return await auth_service.update_user_profile(current_user, user_in)

@router.post("/password-reset", response_model=Message)
async def request_password_reset(
    *,
    db: AsyncSession = Depends(get_db_session),
    request: PasswordResetRequest,
) -> Any:
    auth_service = AuthService(db)
    await auth_service.request_password_reset(request.email)
    return {"message": "If the email exists, a password reset link will be sent."}

@router.post("/password-reset/confirm", response_model=Message)
async def confirm_password_reset(
    *,
    db: AsyncSession = Depends(get_db_session),
    request: PasswordResetConfirm,
) -> Any:
    auth_service = AuthService(db)
    await auth_service.confirm_password_reset(request.token, request.new_password)
    return {"message": "Password reset successfully."}

@router.post("/email-verification", response_model=Message)
async def request_email_verification(
    *,
    db: AsyncSession = Depends(get_db_session),
    request: EmailVerificationRequest,
) -> Any:
    auth_service = AuthService(db)
    await auth_service.request_email_verification(request.email)
    return {"message": "If the email exists, verification instructions will be sent."}

@router.post("/email-verification/confirm", response_model=Message)
async def confirm_email_verification(
    *,
    db: AsyncSession = Depends(get_db_session),
    request: EmailVerificationConfirm,
) -> Any:
    auth_service = AuthService(db)
    await auth_service.confirm_email_verification(request.token)
    return {"message": "Email verified successfully."}
