from typing import List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.resume import Resume, ResumeVersion
from src.db.repositories.base import BaseRepository


class ResumeRepository(BaseRepository[Resume, dict, dict]):
    async def get_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: str,
    ) -> List[Resume]:
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.versions))
            .where(self.model.user_id == user_id)
        )
        return list(result.scalars().all())


class ResumeVersionRepository(BaseRepository[ResumeVersion, dict, dict]):
    async def get_by_resume(
        self,
        db: AsyncSession,
        *,
        resume_id: str,
    ) -> List[ResumeVersion]:
        result = await db.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.created_at.desc())
        )
        return list(result.scalars().all())


resume_repo = ResumeRepository(Resume)
resume_version_repo = ResumeVersionRepository(ResumeVersion)