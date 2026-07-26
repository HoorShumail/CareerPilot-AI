import logging
import uuid
from typing import List, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.career_strategy import CareerStrategy, CareerStrategyProgress
from src.db.repositories.base import BaseRepository

logger = logging.getLogger("careerpilot.career_strategy_repo")


class CareerStrategyRepository(BaseRepository[CareerStrategy, dict, dict]):
    async def get_by_user(self, db: AsyncSession, *, user_id: Union[uuid.UUID, str]) -> CareerStrategy | None:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        logger.info("[TRACE] CareerStrategyRepository.get_by_user executing query for user_id=%s", user_id)
        result = await db.execute(select(self.model).where(self.model.user_id == user_id))
        row = result.scalars().first()
        logger.info("[TRACE] CareerStrategyRepository.get_by_user result found=%s", row is not None)
        return row


class CareerStrategyProgressRepository(BaseRepository[CareerStrategyProgress, dict, dict]):
    async def get_by_user(self, db: AsyncSession, *, user_id: Union[uuid.UUID, str]) -> List[CareerStrategyProgress]:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        result = await db.execute(select(self.model).where(self.model.user_id == user_id))
        return list(result.scalars().all())


career_strategy_repo = CareerStrategyRepository(CareerStrategy)
career_strategy_progress_repo = CareerStrategyProgressRepository(CareerStrategyProgress)