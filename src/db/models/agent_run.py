import uuid
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import BaseModel

class AgentRun(BaseModel):
    __tablename__ = "agent_runs"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    graph_name: Mapped[str] = mapped_column(String, nullable=False)
    
    input_summary: Mapped[dict] = mapped_column(JSONB, nullable=True)
    output_summary: Mapped[dict] = mapped_column(JSONB, nullable=True)
    
    latency_ms: Mapped[float] = mapped_column(Float, nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=True)
    
    status: Mapped[str] = mapped_column(String, nullable=False, default="running") # running, success, failed
    
    # Relationships
    user = relationship("User", back_populates="agent_runs")
