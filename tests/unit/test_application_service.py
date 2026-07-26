import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.services.application_service import ApplicationService
from src.schemas.application import MatchAnalysis


class DummyLLM:
    async def generate(self, prompt: str, system_prompt=None, **kwargs):
        if "Compare a specific resume version" in prompt:
            return '{"overall_match_score": 85.0, "skills_match": {"matched": ["Docker"]}, "missing_skills": {"skills": ["Terraform"]}, "missing_technologies": {"technologies": ["AWS"]}, "missing_certifications": {"certifications": []}, "experience_gap": "Minor", "education_gap": "None", "strength_analysis": {"summary": "Strong"}, "weakness_analysis": {"summary": "Needs cloud examples"}, "ats_compatibility_score": 88.0, "priority_learning_roadmap": {"topics": ["IaC"]}, "detailed_gap_analysis": {"analysis": "Focus on AWS"}, "final_recommendation": "Apply now", "gap_analysis": {"summary": "Clear"}, "strengths": {"skills": ["Automation"]}, "learning_recommendations": {"learning": ["Terraform"]}, "estimated_match_after_learning": 92.0}'
        return '{}'


@pytest.mark.asyncio
async def test_create_application_generates_match_analysis(monkeypatch):
    service = ApplicationService(llm_provider=DummyLLM())

    job = SimpleNamespace(id=uuid.uuid4(), user_id=uuid.uuid4())
    resume_version = SimpleNamespace(id=uuid.uuid4(), resume_id=uuid.uuid4())
    resume = SimpleNamespace(id=resume_version.resume_id, user_id=job.user_id)

    async def fake_get_job(db, id):
        return job

    async def fake_get_resume_version(db, id):
        return resume_version

    async def fake_get_resume(db, id):
        return resume

    async def fake_create_application(db, obj_in):
        data = obj_in.model_dump()
        return SimpleNamespace(**data, id=uuid.uuid4(), created_at=datetime.utcnow(), updated_at=datetime.utcnow())

    async def fake_get_by_resume(db, resume_version_id):
        return []

    async def fake_create_match(db, obj_in):
        return SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr("src.services.application_service.job_repo.get", fake_get_job)
    monkeypatch.setattr("src.services.application_service.resume_version_repo.get", fake_get_resume_version)
    monkeypatch.setattr("src.services.application_service.resume_repo.get", fake_get_resume)
    monkeypatch.setattr("src.services.application_service.application_repo.create", fake_create_application)
    monkeypatch.setattr("src.services.application_service.match_repo.get_by_resume", fake_get_by_resume)
    monkeypatch.setattr("src.services.application_service.match_repo.create", fake_create_match)

    service._compare_resume_to_job = AsyncMock(return_value=MatchAnalysis(
        overall_match_score=85.0,
        skills_match={"matched": ["Docker"]},
        missing_skills={"skills": ["Terraform"]},
        missing_technologies={"technologies": ["AWS"]},
        missing_certifications={"certifications": []},
        experience_gap="Minor",
        education_gap="None",
        strength_analysis={"summary": "Strong"},
        weakness_analysis={"summary": "Needs cloud examples"},
        ats_compatibility_score=88.0,
        priority_learning_roadmap={"topics": ["IaC"]},
        detailed_gap_analysis={"analysis": "Focus on AWS"},
        final_recommendation="Apply now",
        gap_analysis={"summary": "Clear"},
        strengths={"skills": ["Automation"]},
        learning_recommendations={"learning": ["Terraform"]},
        estimated_match_after_learning=92.0,
    ))

    db = SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())

    result = await service.create_application(
        db,
        job.user_id,
        job.id,
        resume_version.id,
        status="saved",
    )

    assert result.job_id == job.id
    assert result.resume_version_id == resume_version.id


@pytest.mark.asyncio
async def test_refresh_match_updates_analysis(monkeypatch):
    service = ApplicationService(llm_provider=DummyLLM())

    application = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        job_id=uuid.uuid4(),
        resume_version_id=uuid.uuid4(),
        status="saved",
        applied_date=None,
        match_score=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    resume_version = SimpleNamespace(id=application.resume_version_id, resume_id=uuid.uuid4())
    job = SimpleNamespace(id=application.job_id)

    async def fake_get_application(db, id):
        return application


    async def fake_get_resume_version(db, id):
        return resume_version

    async def fake_get_job(db, id):
        return job

    async def fake_update(db, db_obj, obj_in):
        await db.commit()
        await db.refresh(db_obj)
        return SimpleNamespace(
            id=db_obj.id,
            user_id=db_obj.user_id,
            job_id=db_obj.job_id,
            resume_version_id=db_obj.resume_version_id,
            status=getattr(db_obj, "status", "saved"),
            applied_date=getattr(db_obj, "applied_date", None),
            match_score=obj_in.match_score,
            skills_match=getattr(obj_in, "skills_match", None),
            missing_skills=obj_in.missing_skills,
            missing_technologies=getattr(obj_in, "missing_technologies", None),
            missing_certifications=getattr(obj_in, "missing_certifications", None),
            experience_gap=getattr(obj_in, "experience_gap", None),
            education_gap=getattr(obj_in, "education_gap", None),
            strength_analysis=getattr(obj_in, "strength_analysis", None),
            weakness_analysis=getattr(obj_in, "weakness_analysis", None),
            ats_compatibility_score=getattr(obj_in, "ats_compatibility_score", None),
            priority_learning_roadmap=getattr(obj_in, "priority_learning_roadmap", None),
            detailed_gap_analysis=getattr(obj_in, "detailed_gap_analysis", None),
            final_recommendation=getattr(obj_in, "final_recommendation", None),
            gap_analysis=obj_in.gap_analysis,
            strengths=obj_in.strengths,
            learning_recommendations=obj_in.learning_recommendations,
            estimated_match_after_learning=obj_in.estimated_match_after_learning,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


    async def fake_get_by_resume(db, resume_version_id):
        return []

    async def fake_create_match(db, obj_in):
        return SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr("src.services.application_service.application_repo.get", fake_get_application)
    monkeypatch.setattr("src.services.application_service.resume_version_repo.get", fake_get_resume_version)
    monkeypatch.setattr("src.services.application_service.job_repo.get", fake_get_job)
    monkeypatch.setattr("src.services.application_service.application_repo.update", fake_update)
    monkeypatch.setattr("src.services.application_service.match_repo.get_by_resume", fake_get_by_resume)
    monkeypatch.setattr("src.services.application_service.match_repo.create", fake_create_match)

    service._compare_resume_to_job = AsyncMock(return_value=MatchAnalysis(
        overall_match_score=85.0,
        skills_match={"matched": ["Docker"]},
        missing_skills={"skills": ["Terraform"]},
        missing_technologies={"technologies": ["AWS"]},
        missing_certifications={"certifications": []},
        experience_gap="Minor",
        education_gap="None",
        strength_analysis={"summary": "Strong"},
        weakness_analysis={"summary": "Needs cloud examples"},
        ats_compatibility_score=88.0,
        priority_learning_roadmap={"topics": ["IaC"]},
        detailed_gap_analysis={"analysis": "Focus on AWS"},
        final_recommendation="Apply now",
        gap_analysis={"summary": "Clear"},
        strengths={"skills": ["Automation"]},
        learning_recommendations={"learning": ["Terraform"]},
        estimated_match_after_learning=92.0,
    ))

    db = SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())

    result = await service.refresh_match(db, application.user_id, application.id)

    assert result.match_score == 85.0
    assert result.gap_analysis["summary"] == "Clear"
    db.commit.assert_called_once()
    db.refresh.assert_called_once()
