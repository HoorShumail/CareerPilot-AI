import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.db.models.job import Job
from src.db.repositories.job_repo import JobRepository


class DummyResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def first(self):
        return self._rows[0] if self._rows else None


class DummySession:
    def __init__(self):
        self._objects = []

    def add(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        self._objects.append(obj)

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

    async def get(self, model, id):
        return next((obj for obj in self._objects if getattr(obj, "id", None) == id), None)

    async def delete(self, obj):
        self._objects = [item for item in self._objects if item is not obj]

    async def execute(self, query):
        return DummyResult(self._objects)


@pytest.mark.asyncio
async def test_get_by_user_returns_jobs():
    repository = JobRepository(Job)
    user_id = uuid.uuid4()

    job1 = Job(
        user_id=user_id,
        title="Data Scientist",
        company="ExampleCorp",
        raw_description="Test description",
    )
    job2 = Job(
        user_id=uuid.uuid4(),
        title="Backend Engineer",
        company="ExampleInc",
        raw_description="Another description",
    )

    async_session = SimpleNamespace()
    async_session.execute = AsyncMock(return_value=DummyResult([job1]))

    jobs = await repository.get_by_user(async_session, user_id=str(user_id))

    assert len(jobs) == 1
    assert jobs[0].company == "ExampleCorp"
    assert jobs[0].title == "Data Scientist"


@pytest.mark.asyncio
async def test_create_update_remove_job_with_dummy_session():
    repository = JobRepository(Job)
    user_id = uuid.uuid4()
    session = DummySession()

    job_data = {
        "user_id": user_id,
        "title": "Full Stack Engineer",
        "company": "BuildSoft",
        "raw_description": "Build modern applications",
    }

    created = await repository.create(session, obj_in=job_data)
    assert created.id is not None
    assert created.title == "Full Stack Engineer"
    assert created.company == "BuildSoft"

    updated = await repository.update(
        session,
        db_obj=created,
        obj_in={"title": "Senior Full Stack Engineer"},
    )

    assert updated.title == "Senior Full Stack Engineer"
    assert updated.company == "BuildSoft"

    removed = await repository.remove(session, id=created.id)
    assert removed.id == created.id
    assert removed.title == "Senior Full Stack Engineer"

    missing = await session.get(Job, id=created.id)
    assert missing is None
