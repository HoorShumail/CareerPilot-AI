import asyncio
import uuid
from datetime import datetime
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.agents.interview.interview_agent import InterviewAgent
from src.api.dependencies import get_current_user, get_db_session, get_interview_service
from src.api.routes.interview import router as interview_router
from src.prompts.interview_prompt import build_interview_prompt
from src.schemas.interview import InterviewAnswerRequest, InterviewStartRequest, InterviewSessionResponse
from src.services.interview_service import InterviewService


class DummyLLM:
    async def generate(self, prompt: str, system_prompt=None, **kwargs):
        return '{"questions": [{"question": "Explain a Python decorator", "category": "technical"}], "interview_type": "technical", "target_role": "Backend Engineer", "target_company": "Acme", "difficulty": "medium", "duration_seconds": 1800, "feedback": {"strengths": ["clarity"], "weaknesses": ["depth"], "missing_concepts": ["closures"], "recommended_learning": ["decorators"], "expected_performance": "good"}}'

    async def generate_structured(self, prompt: str, response_schema=None, system_prompt=None, **kwargs):
        return response_schema.model_validate({})

    async def get_embeddings(self, texts):
        return [[0.0] * 3 for _ in texts]


def test_build_interview_prompt_contains_strict_json_contract():
    prompt = build_interview_prompt({"profile": {}}, {"context": []})
    assert "Return STRICT JSON ONLY." in prompt
    assert "questions" in prompt


def test_interview_agent_parses_response():
    agent = InterviewAgent(DummyLLM())
    result = asyncio.run(
        agent.generate_session(
            {"profile": {}},
            {"context": []},
            InterviewStartRequest(
                interview_type="technical",
                target_role="Backend Engineer",
                target_company="Acme",
                difficulty="medium",
                duration_seconds=1800,
            ),
        )
    )
    assert isinstance(result, InterviewSessionResponse)


def test_interview_agent_surfaces_transport_error_as_503():
    class FailingLLM:
        async def generate(self, prompt: str, system_prompt=None, **kwargs):
            raise httpx.ConnectError("dns lookup failed")

        async def generate_structured(self, prompt: str, response_schema=None, system_prompt=None, **kwargs):
            raise AssertionError("should not be called")

        async def get_embeddings(self, texts):
            return []

    agent = InterviewAgent(FailingLLM())

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            agent.generate_session(
                {"profile": {}},
                {"context": []},
                InterviewStartRequest(interview_type="technical"),
            )
        )

    assert exc_info.value.status_code == 503
    assert "temporarily unavailable" in exc_info.value.detail.lower()


def test_interview_service_starts_and_answers():
    service = InterviewService(DummyLLM())

    class FakeSession:
        def __init__(self, stored_session=None):
            self.added = []
            self.stored_session = stored_session

        def add(self, obj):
            self.added.append(obj)
            if hasattr(obj, 'user_id'):
                self.stored_session = obj

        async def commit(self):
            return None

        async def refresh(self, obj):
            return None

        async def get(self, model, identifier):
            return self.stored_session

    async def fake_get_by_user(db, user_id):
        return []

    async def fake_get_profile(db, user_id):
        return None

    async def fake_get_by_resume(db, resume_id):
        return []

    async def fake_get(db, id):
        return None

    import src.services.interview_service as interview_module

    interview_module.career_profile_repo.get_by_user = fake_get_profile
    interview_module.resume_repo.get_by_user = fake_get_by_user
    interview_module.resume_version_repo.get_by_resume = fake_get_by_user
    interview_module.application_repo.get_by_user = fake_get_by_user
    interview_module.job_repo.get = fake_get
    interview_module.match_repo.get_by_user = fake_get_by_user
    interview_module.interview_repo = SimpleNamespace(create=lambda db, obj_in=None: None)

    fake_db = FakeSession()
    user_id = uuid.uuid4()
    session = asyncio.run(
        service.start_session(
            fake_db,
            user_id,
            InterviewStartRequest(
                interview_type="technical",
                target_role="Backend Engineer",
                target_company="Acme",
                difficulty="medium",
                duration_seconds=1800,
            ),
        )
    )
    assert isinstance(session, InterviewSessionResponse)

    # -------- FIXED: added question_index --------
    answer = asyncio.run(
        service.answer_question(
            fake_db,
            user_id,
            session.id,
            InterviewAnswerRequest(
                question_index=0,  # <-- added
                answer="I would explain it by using closures.",
            ),
        )
    )
    assert isinstance(answer, dict)


def test_interview_router_endpoints():
    class FakeService:
        async def start_session(self, db, user_id, payload):
            return InterviewSessionResponse(
                id=uuid.uuid4(),
                user_id=user_id,
                interview_type="technical",
                target_role="Backend Engineer",
                target_company="Acme",
                difficulty="medium",
                duration_seconds=1800,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        async def answer_question(self, db, user_id, session_id, payload):
            return {"status": "ok"}

        async def finish_session(self, db, user_id, session_id):
            return InterviewSessionResponse(
                id=session_id,
                user_id=user_id,
                interview_type="technical",
                target_role="Backend Engineer",
                target_company="Acme",
                difficulty="medium",
                duration_seconds=1800,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        async def get_history(self, db, user_id):
            return []

        async def get_session(self, db, user_id, session_id):
            return InterviewSessionResponse(
                id=session_id,
                user_id=user_id,
                interview_type="technical",
                target_role="Backend Engineer",
                target_company="Acme",
                difficulty="medium",
                duration_seconds=1800,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        async def get_analytics(self, db, user_id):
            return {"average_score": 0.0}

        async def get_feedback(self, db, user_id, session_id):
            return {"strengths": []}

    app = FastAPI()
    app.include_router(interview_router, prefix="/interview")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[get_db_session] = lambda: None
    app.dependency_overrides[get_interview_service] = lambda: FakeService()

    client = TestClient(app)
    response = client.post(
        "/interview/start",
        json={
            "interview_type": "technical",
            "target_role": "Backend Engineer",
            "target_company": "Acme",
            "difficulty": "medium",
            "duration_seconds": 1800,
        },
    )
    assert response.status_code == 200