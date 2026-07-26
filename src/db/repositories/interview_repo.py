from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.interview import InterviewAnswer, InterviewSession
from src.db.repositories.base import BaseRepository


class InterviewRepository(BaseRepository[InterviewSession, dict, dict]):
    async def get_by_user(self, db: AsyncSession, *, user_id: str) -> List[InterviewSession]:
        result = await db.execute(select(self.model).where(self.model.user_id == user_id))
        return list(result.scalars().all())


interview_repo = InterviewRepository(InterviewSession)
