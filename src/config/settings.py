from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus, urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    PROJECT_NAME: str = "CareerPilot-AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @staticmethod
    def _quote(value: str) -> str:
        return quote_plus(value)

    @property
    def sync_database_uri(self) -> str:
        user = self._quote(self.POSTGRES_USER)
        password = self._quote(self.POSTGRES_PASSWORD)
        return (
            f"postgresql://{user}:{password}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def async_database_uri(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI

        user = self._quote(self.POSTGRES_USER)
        password = self._quote(self.POSTGRES_PASSWORD)

        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @model_validator(mode="after")
    def validate_database_uri(self) -> "Settings":
        if self.SQLALCHEMY_DATABASE_URI:
            parsed = urlparse(self.SQLALCHEMY_DATABASE_URI)

            if parsed.username and parsed.username != self.POSTGRES_USER:
                raise ValueError(
                    "SQLALCHEMY_DATABASE_URI username does not match POSTGRES_USER"
                )

            if parsed.password and parsed.password != self.POSTGRES_PASSWORD:
                raise ValueError(
                    "SQLALCHEMY_DATABASE_URI password does not match POSTGRES_PASSWORD"
                )

            if parsed.hostname and parsed.hostname != self.POSTGRES_SERVER:
                raise ValueError(
                    "SQLALCHEMY_DATABASE_URI host does not match POSTGRES_SERVER"
                )

            if parsed.port and parsed.port != self.POSTGRES_PORT:
                raise ValueError(
                    "SQLALCHEMY_DATABASE_URI port does not match POSTGRES_PORT"
                )

            if parsed.path and parsed.path.lstrip("/") != self.POSTGRES_DB:
                raise ValueError(
                    "SQLALCHEMY_DATABASE_URI database name does not match POSTGRES_DB"
                )

        return self

    # Redis
    REDIS_URL: str

    # Resume storage
    RESUME_STORAGE_DIR: str = "uploads/resumes"

    # Vector DB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    # Email
    EMAILS_ENABLED: bool = False
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_STARTTLS: bool = True
    EMAILS_FROM: str = "no-reply@careerpilot.ai"

    # Token expiration
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 2

    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-large"

    ANTHROPIC_API_KEY: Optional[str] = None


    # Admin
    FIRST_SUPERUSER: Optional[str] = None
    FIRST_SUPERUSER_PASSWORD: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()