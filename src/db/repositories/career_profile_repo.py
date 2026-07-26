import uuid
from typing import List, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.career_profile import CareerProfile, CareerProfileSnapshot
from src.db.repositories.base import BaseRepository


class CareerProfileRepository(BaseRepository[CareerProfile, dict, dict]):
    async def get_by_user(self, db: AsyncSession, *, user_id: Union[uuid.UUID, str]) -> CareerProfile | None:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        result = await db.execute(select(self.model).where(self.model.user_id == user_id))
        return result.scalars().first()


class CareerProfileSnapshotRepository(BaseRepository[CareerProfileSnapshot, dict, dict]):
    async def get_by_profile(self, db: AsyncSession, *, profile_id: str) -> List[CareerProfileSnapshot]:
        result = await db.execute(select(self.model).where(self.model.profile_id == profile_id))
        return list(result.scalars().all())


career_profile_repo = CareerProfileRepository(CareerProfile)
career_profile_snapshot_repo = CareerProfileSnapshotRepository(CareerProfileSnapshot)
