import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import BaseModel


class CareerIntelligenceMemory(BaseModel):
    __tablename__ = "career_intelligence_memories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    memory_type: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )