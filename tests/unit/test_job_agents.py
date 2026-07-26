import json
from typing import Any

import pytest

from src.agents.job.job_parser_agent import JobParserAgent
from src.agents.job.job_insights_agent import JobInsightsAgent
from src.agents.job.job_matcher_agent import JobMatcherAgent
from src.infrastructure.llm.provider import LLMProvider


class DummyLLM(LLMProvider):
    async def generate(self, prompt: str, system_prompt=None, **kwargs):
        if "Extract structured metadata" in prompt:
            return json.dumps({
                "title": "DevOps Engineer",
                "company": "TestCorp",
                "location": "Remote",
                "remote": True,
                "employment_type": "Full-time",
                "experience_level": "Mid",
                "salary": "100000-120000",
                "responsibilities": ["Manage CI/CD"],
                "required_skills": ["Docker", "Kubernetes"],
                "preferred_skills": ["Terraform"],
                "education": ["B.S. in Computer Science"],
                "certifications": ["AWS Certified"],
                "technologies": ["AWS", "Terraform"],
                "soft_skills": ["Communication"],
                "keywords": ["CI/CD", "Infrastructure"],
                "raw_description": "Sample job description",
            })
        if "Analyze a structured job description" in prompt:
            return json.dumps({
                "executive_summary": {"headline": "High-value DevOps role"},
                "ats_keywords": {"keywords": ["Docker", "Kubernetes"]},
                "hidden_requirements": {"details": "Team collaboration"},
                "missing_certifications": {"notes": "None"},
                "interview_focus_areas": {"topics": ["cloud architecture"]},
                "strengths": {"relevant_experience": "Good"},
                "risks": {"concerns": "None"},
                "important_technologies": {"technologies": ["AWS"]},
                "recommended_learning_topics": {"topics": ["Infrastructure as Code"]},
                "resume_optimization_suggestions": {"advice": "Highlight cloud automation"},
                "company_insights": {"culture": "fast-paced"},
                "embedding": {"values": [0.1, 0.2, 0.3]},
            })
        if "Compare a specific resume version" in prompt:
            return json.dumps({
                "overall_match_score": 85.0,
                "skills_match": {"matched": ["Docker"]},
                "missing_skills": {"skills": ["Terraform"]},
                "missing_technologies": {"technologies": ["AWS"]},
                "missing_certifications": {"certifications": []},
                "experience_gap": "Minor",
                "education_gap": "None",
                "strength_analysis": {"summary": "Strong"},
                "weakness_analysis": {"summary": "Needs cloud examples"},
                "ats_compatibility_score": 88.0,
                "priority_learning_roadmap": {"topics": ["IaC"]},
                "detailed_gap_analysis": {"analysis": "Focus on AWS"},
                "final_recommendation": "Apply now",
                "gap_analysis": {"summary": "Clear"},
                "strengths": {"skills": ["Automation"]},
                "learning_recommendations": {"learning": ["Terraform"]},
                "estimated_match_after_learning": 92.0,
            })
        return json.dumps({})

    async def generate_structured(self, prompt: str, response_schema: Any, system_prompt=None, **kwargs):
        response = await self.generate(prompt, system_prompt=system_prompt, **kwargs)
        return response_schema.model_validate(json.loads(response))

    async def get_embeddings(self, texts):
        return [[0.1] * 3 for _ in texts]


@pytest.mark.asyncio
async def test_job_parser_agent_parses_structured_data():
    parser = JobParserAgent(DummyLLM())
    parsed = await parser.parse("Sample raw description")

    assert parsed.title == "DevOps Engineer"
    assert "Docker" in parsed.required_skills


@pytest.mark.asyncio
async def test_job_insights_agent_generates_insights():
    insights = JobInsightsAgent(DummyLLM())
    result = await insights.generate_insights({"title": "DevOps Engineer"})

    assert result.executive_summary["headline"] == "High-value DevOps role"
    assert result.embedding["values"] == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_job_matcher_agent_compares_resume_and_job():
    matcher = JobMatcherAgent(DummyLLM())
    result = await matcher.compare(
        {"content": {"skills": ["Docker"]}},
        {"title": "DevOps Engineer"},
    )

    assert result.overall_match_score == 85.0
    assert result.learning_recommendations["learning"] == ["Terraform"]


@pytest.mark.asyncio
async def test_job_matcher_agent_normalizes_dict_in_string_fields():
    class DictInStringLLM(LLMProvider):
        async def generate(self, prompt: str, system_prompt=None, **kwargs):
            return json.dumps({
                "overall_match_score": 80.0,
                "experience_gap": {},
                "education_gap": {},
                "final_recommendation": {},
            })

        async def generate_structured(self, prompt: str, response_schema: Any, system_prompt=None, **kwargs):
            return response_schema.model_validate(json.loads(await self.generate(prompt)))

        async def get_embeddings(self, texts):
            return [[0.1] * 3 for _ in texts]

    matcher = JobMatcherAgent(DictInStringLLM())
    result = await matcher.compare({}, {})

    assert result.experience_gap == ""
    assert result.education_gap == ""
    assert result.final_recommendation == ""


def test_job_insights_prompt_includes_strict_json_hiring_guidance():
    from src.prompts.job_prompts import build_job_insights_prompt

    prompt = build_job_insights_prompt({"title": "Software Engineer"})

    assert "Return ONLY valid JSON." in prompt
    assert "Every top-level value MUST be a JSON object." in prompt
    assert "Never return arrays directly at the top level." in prompt
    assert "Rank ATS keywords by importance." in prompt
    assert "If information is unavailable, return {} instead of null." in prompt

