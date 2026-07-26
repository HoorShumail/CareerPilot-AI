import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.services.job_service import JobService
from src.schemas.job import JobParsedData, JobInsights


class DummyLLM:
    async def generate(self, prompt: str, system_prompt=None, **kwargs):
        if "Extract structured metadata" in prompt:
            return '{"title":"DevOps Engineer","company":"TestCorp","location":"Remote","remote":true,"employment_type":"Full-time","experience_level":"Mid","salary":"100000-120000","responsibilities":["Manage CI/CD"],"required_skills":["Docker","Kubernetes"],"preferred_skills":["Terraform"],"education":["B.S. in Computer Science"],"certifications":["AWS Certified"],"technologies":["AWS","Terraform"],"soft_skills":["Communication"],"keywords":["CI/CD","Infrastructure"],"raw_description":"Sample job description"}'
        if "Analyze a structured job description" in prompt:
            return '{"executive_summary":{"headline":"High-value DevOps role"},"ats_keywords":{"keywords":["Docker","Kubernetes"]},"hidden_requirements":{"details":"Team collaboration"},"missing_certifications":{"notes":"None"},"interview_focus_areas":{"topics":["cloud architecture"]},"strengths":{"relevant_experience":"Good"},"risks":{"concerns":"None"},"important_technologies":{"technologies":["AWS"]},"recommended_learning_topics":{"topics":["Infrastructure as Code"]},"resume_optimization_suggestions":{"advice":"Highlight cloud automation"},"company_insights":{"culture":"fast-paced"},"embedding":{"values":[0.1,0.2,0.3]}}'
        return '{}'


@pytest.mark.asyncio
async def test_create_job_from_text_calls_parser_and_insights(monkeypatch):
    parsed_data = JobParsedData(
        title="DevOps Engineer",
        company="TestCorp",
        location="Remote",
        remote=True,
        employment_type="Full-time",
        experience_level="Mid",
        salary="100000-120000",
        responsibilities=["Manage CI/CD"],
        required_skills=["Docker", "Kubernetes"],
        preferred_skills=["Terraform"],
        education=["B.S. in Computer Science"],
        certifications=["AWS Certified"],
        technologies=["AWS", "Terraform"],
        soft_skills=["Communication"],
        keywords=["CI/CD", "Infrastructure"],
        raw_description="Sample job description",
    )
    insights_data = JobInsights(
        executive_summary={"headline": "High-value DevOps role"},
        ats_keywords={"keywords": ["Docker", "Kubernetes"]},
        hidden_requirements={"details": "Team collaboration"},
        missing_certifications={"notes": "None"},
        interview_focus_areas={"topics": ["cloud architecture"]},
        strengths={"relevant_experience": "Good"},
        risks={"concerns": "None"},
        important_technologies={"technologies": ["AWS"]},
        recommended_learning_topics={"topics": ["Infrastructure as Code"]},
        resume_optimization_suggestions={"advice": "Highlight cloud automation"},
        company_insights={"culture": "fast-paced"},
        embedding={"values": [0.1, 0.2, 0.3]},
    )

    service = JobService(llm_provider=DummyLLM())
    service._parse_job_description = AsyncMock(return_value=parsed_data)
    service._generate_insights = AsyncMock(return_value=insights_data)

    async def fake_create(db, obj_in):
        data = obj_in.model_dump()
        return SimpleNamespace(
            id=uuid.uuid4(),
            user_id=data["user_id"],
            title=data["title"],
            company=data["company"],
            raw_description=data["raw_description"],
            parsed_jd=data["parsed_jd"],
            required_skills=data["required_skills"],
            preferred_skills=data["preferred_skills"],
            experience_level=data["experience_level"],
            salary_range=data["salary_range"],
            location=data["location"],
            is_remote=data["is_remote"],
            ai_summary=data["ai_summary"],
            ats_keywords=data["ats_keywords"],
            hidden_requirements=data["hidden_requirements"],
            interview_focus=data["interview_focus"],
            missing_certifications=data["missing_certifications"],
            red_flags=data["red_flags"],
            extracted_keywords=data["extracted_keywords"],
            embedding=data["embedding"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    monkeypatch.setattr("src.services.job_service.job_repo.create", fake_create)

    result = await service.create_job_from_text(
        SimpleNamespace(),
        uuid.uuid4(),
        "Sample raw description",
        "DevOps Engineer",
        "TestCorp",
        "https://example.com/job",
    )

    assert result.title == "DevOps Engineer"
    assert result.company == "TestCorp"
    assert result.ai_summary == insights_data.executive_summary
    assert result.ats_keywords == insights_data.ats_keywords


@pytest.mark.asyncio
async def test_create_job_from_pdf_uses_pdf_extraction(monkeypatch):
    service = JobService(llm_provider=DummyLLM())
    extraction_called = {"count": 0}

    def extract_text(file_bytes, content_type):
        extraction_called["count"] += 1
        return "Extracted text"

    service._extract_text_from_pdf = extract_text
    service.create_job_from_text = AsyncMock(return_value=SimpleNamespace(title="PDF Role", company="PDFCorp", raw_description="Extracted text", parsed_jd={}, required_skills={}, preferred_skills={}, experience_level=None, salary_range=None, location=None, is_remote=False, ai_summary={}, ats_keywords={}, hidden_requirements={}, interview_focus={}, missing_certifications={}, red_flags={}, extracted_keywords={}, embedding={}, created_at=datetime.utcnow(), updated_at=datetime.utcnow()))

    result = await service.create_job_from_pdf(
        SimpleNamespace(),
        uuid.uuid4(),
        b"PDFDATA",
        "application/pdf",
        "PDF Role",
        "PDFCorp",
        "https://example.com/pdf",
    )

    assert result.title == "PDF Role"
    assert extraction_called["count"] == 1
    service.create_job_from_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_job_insights_updates_job(monkeypatch):
    service = JobService(llm_provider=DummyLLM())

    job = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        parsed_jd={"keywords": ["Docker"]},
        ai_summary=None,
        ats_keywords=None,
        hidden_requirements=None,
        interview_focus=None,
        missing_certifications=None,
        red_flags=None,
        extracted_keywords=None,
    )

    insights = JobInsights(
        executive_summary={"headline": "Updated summary"},
        ats_keywords={"keywords": ["Docker"]},
        hidden_requirements={"details": "Keep building"},
        missing_certifications={"notes": "None"},
        interview_focus_areas={"topics": ["collaboration"]},
        strengths={"relevant_experience": "Strong"},
        risks={"concerns": "None"},
        important_technologies={"technologies": ["Docker"]},
        recommended_learning_topics={"topics": ["Cloud"]},
        resume_optimization_suggestions={"advice": "Add more metrics"},
        company_insights={"culture": "collaborative"},
        embedding={"values": [0.2, 0.4]},
    )

    async def fake_get(db, id):
        return job

    async def fake_update(db, db_obj, obj_in):
        return SimpleNamespace(
            id=db_obj.id,
            user_id=db_obj.user_id,
            title="DevOps Engineer",
            company="TestCorp",
            url=None,
            raw_description="Sample job description",
            parsed_jd=db_obj.parsed_jd,
            required_skills={"required_skills": ["Docker"]},
            preferred_skills={"preferred_skills": ["Terraform"]},
            experience_level=None,
            salary_range=None,
            location=None,
            is_remote=False,
            ai_summary=obj_in.ai_summary,
            ats_keywords=obj_in.ats_keywords,
            hidden_requirements=obj_in.hidden_requirements,
            interview_focus=obj_in.interview_focus,
            missing_certifications=obj_in.missing_certifications,
            red_flags=obj_in.red_flags,
            extracted_keywords=obj_in.extracted_keywords,
            embedding=obj_in.embedding,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    monkeypatch.setattr("src.services.job_service.job_repo.get", fake_get)
    monkeypatch.setattr("src.services.job_service.job_repo.update", fake_update)
    service.insights_agent.generate_insights = AsyncMock(return_value=insights)

    result = await service.refresh_job_insights(SimpleNamespace(), job.user_id, job.id)

    assert result.ai_summary == insights.executive_summary
    assert result.ats_keywords == insights.ats_keywords
    assert result.hidden_requirements == insights.hidden_requirements
