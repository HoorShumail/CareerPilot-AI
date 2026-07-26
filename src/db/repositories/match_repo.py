from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.match import Match
from src.db.repositories.base import BaseRepository


class MatchRepository(BaseRepository[Match, dict, dict]):
    async def get_by_user(self, db: AsyncSession, *, user_id: str) -> List[Match]:
        result = await db.execute(select(self.model).where(self.model.user_id == user_id))
        return list(result.scalars().all())

    async def get_by_resume(self, db: AsyncSession, *, resume_version_id: str) -> List[Match]:
        result = await db.execute(select(self.model).where(self.model.resume_version_id == resume_version_id))
        return list(result.scalars().all())

    async def get_by_job(self, db: AsyncSession, *, job_id: str) -> List[Match]:
        result = await db.execute(select(self.model).where(self.model.job_id == job_id))
        return list(result.scalars().all())


match_repo = MatchRepository(Match)
