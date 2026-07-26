from typing import Optional
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None

class Message(BaseModel):
    message: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class EmailVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerificationConfirm(BaseModel):
    token: str
