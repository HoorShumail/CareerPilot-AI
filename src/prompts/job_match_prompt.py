import json
from typing import Any, Dict


def build_job_match_prompt(
    resume_version: Dict[str, Any],
    job_data: Dict[str, Any],
) -> str:
    formatted_resume = json.dumps(resume_version, indent=2, default=str) if isinstance(resume_version, dict) else resume_version
    formatted_job = json.dumps(job_data, indent=2, default=str) if isinstance(job_data, dict) else job_data

    return f"""
You are an expert Senior Technical Recruiter, ATS Expert, Resume Reviewer, and AI Hiring Manager.

Compare a specific resume version against a job description.

Analyze BOTH documents carefully before producing your answer.


Return STRICT JSON ONLY.

IMPORTANT RULES:

1. Return ONLY valid JSON.
2. Do NOT use markdown.
3. Do NOT wrap JSON inside ``` blocks.
4. Do NOT explain anything.
5. Every field MUST be present.
6. Never return null.
7. Never return empty objects unless absolutely nothing exists.
8. Calculate REAL scores.
9. overall_match_score MUST be between 0 and 100.
10. ats_score MUST be between 0 and 100.
11. estimated_match_after_learning MUST be greater than or equal to overall_match_score.
12. Compare actual skills from the resume with the required job skills.
13. Extract technologies separately.
14. Extract certifications separately.
15. If a skill exists in both resume and job description, include it in matched_skills.
16. If a required skill is missing from the resume, include it in missing_skills.
17. Never use default value 0 unless absolutely no information exists.
18. Never invent experience that is not present.
19. Base everything strictly on the supplied resume and job description.

Return EXACTLY this JSON structure:

{{
  "overall_match_score": 84,
  "ats_score": 81,

  "matched_skills": {{
    "Python": true,
    "FastAPI": true,
    "Git": true
  }},

  "missing_skills": {{
    "Kubernetes": true,
    "AWS": true
  }},

  "missing_technologies": {{
    "Redis": true,
    "Docker": true
  }},

  "missing_certifications": {{
    "AWS Certified Developer": true
  }},

  "experience_gap": {{
    "summary": "Candidate lacks production AI deployment experience."
  }},

  "education_gap": {{
    "summary": "Education satisfies minimum requirements."
  }},

  "strength_analysis": {{
    "summary": "Strong Python, AI, FastAPI, and backend engineering experience."
  }},

  "weakness_analysis": {{
    "summary": "Needs more cloud and DevOps experience."
  }},

  "priority_learning_roadmap": {{
    "topics": [
      "Docker",
      "Kubernetes",
      "AWS",
      "Production AI Deployment"
    ]
  }},

  "resume_improvements": {{
    "recommendations": [
      "Highlight AI projects.",
      "Quantify achievements.",
      "Add production deployment experience."
    ]
  }},

  "estimated_match_after_learning": 92,

  "interview_preparation": {{
    "topics": [
      "FastAPI",
      "RAG",
      "System Design",
      "Vector Databases"
    ]
  }},

  "final_recommendation": {{
    "summary": "Good candidate with moderate skill gaps."
  }}
}}

======================
RESUME
======================

{formatted_resume}

======================
JOB DESCRIPTION
======================

{formatted_job}

Now compare the resume against the job description and produce ONLY the JSON object.
"""