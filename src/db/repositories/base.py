import uuid
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=Any)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=Any)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        """
        self.model = model

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[ModelType]:
        result = await db.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else dict(obj_in)
        model_columns = {c.name for c in self.model.__table__.columns}
        valid_data = {k: v for k, v in obj_in_data.items() if k in model_columns}
        db_obj = self.model(**valid_data)  # type: ignore
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = {c.name: getattr(db_obj, c.name) for c in db_obj.__table__.columns}
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        if hasattr(db_obj, "updated_at") and "updated_at" in obj_data:
            setattr(db_obj, "updated_at", datetime.utcnow())

        db.add(db_obj)
        await db.commit()
        import logging
        logging.getLogger("careerpilot.base_repo").info("[TRACE 10] Executed db.commit() on model %s", self.model.__name__)
        await db.refresh(db_obj)
        logging.getLogger("careerpilot.base_repo").info("[TRACE 11] Executed db.refresh() on model %s", self.model.__name__)
        return db_obj



    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> ModelType:
        obj = await db.get(self.model, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
