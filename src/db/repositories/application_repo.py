from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.application import Application
from src.db.repositories.base import BaseRepository


class ApplicationRepository(BaseRepository[Application, dict, dict]):
    async def get_by_user(self, db: AsyncSession, *, user_id: str) -> List[Application]:
        result = await db.execute(select(self.model).where(self.model.user_id == user_id))
        return list(result.scalars().all())

    async def get_by_job(self, db: AsyncSession, *, job_id: str) -> List[Application]:
        result = await db.execute(select(self.model).where(self.model.job_id == job_id))
        return list(result.scalars().all())


application_repo = ApplicationRepository(Application)
