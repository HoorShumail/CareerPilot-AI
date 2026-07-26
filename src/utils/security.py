from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
ALGORITHM = "HS256"

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
TOKEN_TYPE_PASSWORD_RESET = "password_reset"
TOKEN_TYPE_EMAIL_VERIFICATION = "email_verification"


def create_token(
    subject: Union[str, Any],
    expires_delta: timedelta,
    token_type: str,
) -> str:
    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": token_type,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_token(subject, expires_delta, TOKEN_TYPE_ACCESS)


def create_refresh_token(subject: Union[str, Any]) -> str:
    expire = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token(subject, expire, TOKEN_TYPE_REFRESH)


def create_password_reset_token(subject: Union[str, Any]) -> str:
    expire = timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
    return create_token(subject, expire, TOKEN_TYPE_PASSWORD_RESET)


def create_email_verification_token(subject: Union[str, Any]) -> str:
    expire = timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    return create_token(subject, expire, TOKEN_TYPE_EMAIL_VERIFICATION)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def decode_token(token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    token_type = payload.get("type")
    if expected_type and token_type != expected_type:
        raise JWTError("Invalid token type")
    return payload
