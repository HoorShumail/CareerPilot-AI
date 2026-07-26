from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.job import Job
from src.db.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job, dict, dict]):
    async def get_by_user(self, db: AsyncSession, *, user_id: str) -> List[Job]:
        result = await db.execute(select(self.model).where(self.model.user_id == user_id))
        return list(result.scalars().all())


job_repo = JobRepository(Job)
