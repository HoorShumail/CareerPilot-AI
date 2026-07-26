from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.user import User
from src.db.repositories.base import BaseRepository

class UserRepository(BaseRepository[User, dict, dict]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()
    
    async def is_active(self, user: User) -> bool:
        return user.is_active

user_repo = UserRepository(User)
