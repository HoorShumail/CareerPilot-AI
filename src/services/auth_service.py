import uuid
from datetime import timedelta
from typing import Optional, Dict, Any

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.config.settings import settings
from src.constants.agent_names import ROLE_ADMIN
from src.infrastructure.email.smtp import EmailSender
from src.schemas.user import UserCreate, UserUpdate
from src.db.models.user import User
from src.db.repositories.user_repo import user_repo
from src.utils.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
    TOKEN_TYPE_EMAIL_VERIFICATION,
    TOKEN_TYPE_PASSWORD_RESET,
    TOKEN_TYPE_REFRESH,
)

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.email_sender = EmailSender()

    async def register_user(self, user_in: UserCreate) -> User:
        """Register a new user."""
        user = await user_repo.get_by_email(self.db, email=user_in.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this email already exists in the system.",
            )
        
        create_data = user_in.model_dump()
        create_data["password_hash"] = get_password_hash(create_data.pop("password"))
        
        user = User(**create_data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def ensure_superuser(self) -> None:
        """Create the first superuser from environment settings if configured."""
        if not settings.FIRST_SUPERUSER or not settings.FIRST_SUPERUSER_PASSWORD:
            return

        existing = await user_repo.get_by_email(self.db, email=settings.FIRST_SUPERUSER)
        if existing:
            return

        user = User(
            email=settings.FIRST_SUPERUSER,
            full_name="Administrator",
            password_hash=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            role=ROLE_ADMIN,
            email_verified=True,
            is_active=True,
            preferences={},
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

    async def authenticate_user(self, email: str, password: str) -> Dict[str, str]:
        """Authenticate user and return tokens."""
        user = await user_repo.get_by_email(self.db, email=email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Inactive user"
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        return {
            "access_token": create_access_token(user.id, expires_delta=access_token_expires),
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
        }

    async def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        try:
            payload = decode_token(refresh_token, expected_type=TOKEN_TYPE_REFRESH)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            user_id = uuid.UUID(payload["sub"])
        except (ValueError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload",
            )

        user = await user_repo.get(self.db, id=user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive or missing user",
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return {
            "access_token": create_access_token(user.id, expires_delta=access_token_expires),
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
        }

    async def update_user_profile(self, user: User, user_in: UserUpdate) -> User:
        if user_in.full_name is not None:
            user.full_name = user_in.full_name
        if user_in.avatar_url is not None:
            user.avatar_url = user_in.avatar_url
        if user_in.password:
            user.password_hash = get_password_hash(user_in.password)

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def request_password_reset(self, email: str) -> None:
        user = await user_repo.get_by_email(self.db, email=email)
        if not user:
            return

        token = create_password_reset_token(user.id)
        verification_body = (
            "Use the token below to reset your password:\n\n"
            f"{token}\n\n"
            "Submit the token to /auth/password-reset/confirm with your new password."
        )
        self.email_sender.send_email(
            to_email=user.email,
            subject="Password Reset Request",
            body=verification_body,
        )

    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        try:
            payload = decode_token(token, expected_type=TOKEN_TYPE_PASSWORD_RESET)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token",
            )

        try:
            user_id = uuid.UUID(payload["sub"])
        except (ValueError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password reset token payload",
            )

        user = await user_repo.get(self.db, id=user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.password_hash = get_password_hash(new_password)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

    async def request_email_verification(self, email: str) -> None:
        user = await user_repo.get_by_email(self.db, email=email)
        if not user or user.email_verified:
            return

        token = create_email_verification_token(user.id)
        verification_body = (
            "Use the token below to verify your email address:\n\n"
            f"{token}\n\n"
            "Submit the token to /auth/email-verification/confirm."
        )
        self.email_sender.send_email(
            to_email=user.email,
            subject="Email Verification",
            body=verification_body,
        )

    async def confirm_email_verification(self, token: str) -> None:
        try:
            payload = decode_token(token, expected_type=TOKEN_TYPE_EMAIL_VERIFICATION)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired email verification token",
            )

        try:
            user_id = uuid.UUID(payload["sub"])
        except (ValueError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email verification token payload",
            )

        user = await user_repo.get(self.db, id=user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.email_verified = True
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
